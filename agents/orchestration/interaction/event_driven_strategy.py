# agents/orchestration/interaction/event_driven_strategy.py
import asyncio
from collections import defaultdict, deque
from typing import Any, Dict, List

from agents.orchestration.models import AgentMessage
from .base_strategy import InteractionStrategy
from ..models import (
    OrchestrationRequest,
    OrchestrationResult,
    TaskDefinition,
    TaskResult,
)


class EventDrivenStrategy(InteractionStrategy):
    scenario_name = "event_driven"

    async def execute(self, request: OrchestrationRequest) -> OrchestrationResult:
        context: Dict[str, Any] = dict(request.context or {})
        tasks = request.tasks or []
        event_map = self._build_event_map(tasks)
        event_queue: deque[Dict[str, Any]] = deque()
        event_queue.append({"type": request.metadata.get("initial_event", "start"), "payload": dict(context)})

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

            # ✅ استفاده از _emit
            await self._emit(
                message_type="event_received",
                payload={"type": event_type},
                sender="EventDrivenStrategy",
                recipient="system",
                message_id=f"event_{event_type}",
            )

            listeners = event_map.get(event_type, [])
            if not listeners:
                continue

            coroutines = [
                self._execute_listener(listener, payload, dict(context), context_lock) for listener in listeners
            ]
            gathered = await asyncio.gather(*coroutines, return_exceptions=True)

            # ✅ فیلتر BaseException قبل از استفاده
            for outcome in gathered:
                if isinstance(outcome, BaseException):
                    # تبدیل Exception به TaskResult
                    results.append(
                        TaskResult(
                            task_id="unknown",
                            agent_name="unknown",
                            success=False,
                            error=str(outcome),
                        )
                    )
                    continue

                # اینجا مطمئنیم outcome از نوع TaskResult است
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
        # ✅ استفاده از _emit
        await self._emit(
            message_type="event_listener_started",
            payload={"task_id": task.task_id, "agent": task.agent_name},
            sender="EventDrivenStrategy",
            recipient=task.agent_name,
            message_id=f"listener_{task.task_id}",
        )

        agent = self.agent_registry.get(task.agent_name)
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

            # ✅ استفاده از _emit
            await self._emit(
                message_type="event_listener_completed",
                payload={"task_id": task.task_id, "agent": task.agent_name},
                sender="EventDrivenStrategy",
                recipient=task.agent_name,
                message_id=f"listener_done_{task.task_id}",
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
