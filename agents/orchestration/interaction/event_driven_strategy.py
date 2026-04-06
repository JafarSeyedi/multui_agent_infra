# agents/orchestration/interaction/event_driven_strategy.py
import asyncio
from collections import defaultdict, deque
from typing import Any, Dict, Iterable, List

from .base_strategy import InteractionStrategy
from ..models import (
    OrchestrationRequest,
    OrchestrationResult,
    TaskDefinition,
    TaskResult,
)


class EventDrivenStrategy(InteractionStrategy):
    async def execute(self, request: OrchestrationRequest) -> OrchestrationResult:
        context: Dict[str, Any] = dict(request.context or {})
        tasks = request.tasks or []
        event_map = self._build_event_map(tasks)
        event_queue = deque()
        event_queue.append(
            {"type": request.metadata.get("initial_event", "start"), "payload": dict(context)}
        )

        results: List[TaskResult] = []
        max_iterations = int(request.metadata.get("max_iterations", 50))
        max_queue_size = int(request.metadata.get("max_queue_size", 500))
        context_lock = asyncio.Lock()
        iterations = 0

        while event_queue and iterations < max_iterations:
            iterations += 1
            event = event_queue.popleft()
            event_type = event["type"]
            payload = event.get("payload", {})

            if self.message_bus:
                await self.message_bus.publish({"event": "event_received", "type": event_type})

            listeners = event_map.get(event_type, [])
            if not listeners:
                continue

            coroutines = [
                self._execute_listener(listener, payload, dict(context), context_lock) for listener in listeners
            ]
            gathered = await asyncio.gather(*coroutines, return_exceptions=True)

            for outcome in gathered:
                if isinstance(outcome, Exception):
                    continue
                results.append(outcome)
                emitted = self._extract_events(outcome.output)
                for emitted_event in emitted:
                    if len(event_queue) < max_queue_size:
                        event_queue.append(emitted_event)

        return OrchestrationResult(
            success=True,
            results=results,
            final_context=context,
            metadata={"iterations": iterations, "events_processed": len(results)},
        )

    def _build_event_map(self, tasks: List[TaskDefinition]) -> Dict[str, List[TaskDefinition]]:
        mapping: Dict[str, List[TaskDefinition]] = defaultdict(list)
        for task in tasks:
            events = getattr(task, "on_events", None)
            if not events:
                continue
            normalized = [events] if isinstance(events, str) else list(events)
            for ev in normalized:
                mapping[ev].append(task)
        return mapping

    async def _execute_listener(
        self,
        task: TaskDefinition,
        payload: Dict[str, Any],
        context_snapshot: Dict[str, Any],
        context_lock: asyncio.Lock,
    ) -> TaskResult:
        if self.message_bus:
            await self.message_bus.publish(
                {"event": "event_listener_started", "task_id": task.task_id, "agent": task.agent_name}
            )

        agent = self.registry.get(task.agent_name)
        if agent is None:
            return TaskResult(
                task_id=task.task_id,
                agent_name=task.agent_name,
                success=False,
                error="Agent not found",
            )

        merged_payload = {**task.payload, **payload, "context": context_snapshot}

        try:
            output = await agent.execute(merged_payload)
            if isinstance(output, dict):
                async with context_lock:
                    context_snapshot.update(output)
            if self.message_bus:
                await self.message_bus.publish(
                    {"event": "event_listener_completed", "task_id": task.task_id, "agent": task.agent_name}
                )
            return TaskResult(task_id=task.task_id, agent_name=task.agent_name, success=True, output=output)
        except Exception as exc:
            return TaskResult(task_id=task.task_id, agent_name=task.agent_name, success=False, error=str(exc))

    @staticmethod
    def _extract_events(output: Any) -> List[Dict[str, Any]]:
        events: List[Dict[str, Any]] = []
        if not isinstance(output, dict):
            return events
        raw_events = output.get("emit_events")
        if not raw_events:
            return events
        normalized = [raw_events] if isinstance(raw_events, dict) else list(raw_events)
        for event in normalized:
            event_type = event.get("type")
            if not event_type:
                continue
            events.append({"type": event_type, "payload": event.get("payload", {})})
        return events