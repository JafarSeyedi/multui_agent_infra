import asyncio
from collections import defaultdict, deque
from typing import Dict, Any, List

from .base_strategy import InteractionStrategy

from ..models import (
    OrchestrationRequest,
    OrchestrationResult,
    TaskResult,
    TaskDefinition
)


class EventDrivenStrategy(InteractionStrategy):

    async def execute(self, request: OrchestrationRequest) -> OrchestrationResult:

        context: Dict[str, Any] = dict(request.context)

        tasks: List[TaskDefinition] = request.tasks

        event_map = self._build_event_map(tasks)

        event_queue = deque()

        initial_event = request.metadata.get(
            "initial_event",
            "start"
        )

        event_queue.append({
            "type": initial_event,
            "payload": context
        })

        results: List[TaskResult] = []

        max_iterations = request.metadata.get("max_iterations", 50)

        iteration = 0

        while event_queue and iteration < max_iterations:

            iteration += 1

            event = event_queue.popleft()

            event_type = event["type"]
            payload = event.get("payload", {})

            await self.message_bus.publish({
                "event": "event_received",
                "type": event_type
            })

            listeners = event_map.get(event_type, [])

            if not listeners:
                continue

            coroutines = [
                self._execute_listener(
                    task,
                    payload,
                    context
                )
                for task in listeners
            ]

            task_results = await asyncio.gather(
                *coroutines,
                return_exceptions=True
            )

            for r in task_results:

                if isinstance(r, Exception):
                    continue

                results.append(r)

                emitted = self._extract_events(r.output)

                for e in emitted:
                    event_queue.append(e)

        return OrchestrationResult(
            success=True,
            results=results,
            final_context=context
        )

    def _build_event_map(
        self,
        tasks: List[TaskDefinition]
    ) -> Dict[str, List[TaskDefinition]]:

        event_map = defaultdict(list)

        for task in tasks:

            events = getattr(task, "on_events", None)

            if not events:
                continue

            if isinstance(events, str):
                events = [events]

            for ev in events:
                event_map[ev].append(task)

        return event_map

    async def _execute_listener(
        self,
        task: TaskDefinition,
        payload: Dict[str, Any],
        context: Dict[str, Any]
    ) -> TaskResult:

        await self.message_bus.publish({
            "event": "event_listener_started",
            "task_id": task.task_id,
            "agent": task.agent_name
        })

        agent = self.registry.get(task.agent_name)

        if agent is None:

            return TaskResult(
                task_id=task.task_id,
                agent_name=task.agent_name,
                success=False,
                error="Agent not found"
            )

        merged_payload = {
            **task.payload,
            **payload,
            "context": context
        }

        try:

            output = await agent.execute(merged_payload)

            if isinstance(output, dict):
                context.update(output)

            await self.message_bus.publish({
                "event": "event_listener_completed",
                "task_id": task.task_id
            })

            return TaskResult(
                task_id=task.task_id,
                agent_name=task.agent_name,
                success=True,
                output=output
            )

        except Exception as e:

            return TaskResult(
                task_id=task.task_id,
                agent_name=task.agent_name,
                success=False,
                error=str(e)
            )

    def _extract_events(self, output: Any):

        events = []

        if not isinstance(output, dict):
            return events

        emit = output.get("emit_events")

        if not emit:
            return events

        if isinstance(emit, dict):
            emit = [emit]

        for e in emit:

            events.append({
                "type": e.get("type"),
                "payload": e.get("payload", {})
            })

        return events
