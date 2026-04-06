# agents/orchestration/interaction/round_robin_strategy.py
from __future__ import annotations

from typing import Any, Dict, List, Sequence

from agents.message_bus import AgentMessage
from agents.orchestration.models import (
    OrchestrationRequest,
    OrchestrationResult,
    TaskDefinition,
    TaskResult,
)
from .base_strategy import InteractionStrategy


class RoundRobinStrategy(InteractionStrategy):
    """
    استراتژی Round Robin (یا TurnTaking) برای سناریوهای ساده‌ی group chat،
    brainstorming یا simulation که ترتیب صحبت عوامل کاملاً deterministic است.
    """

    scenario = "round_robin"

    def __init__(self, registry, message_bus: Optional[MessageBus] = None, storage = None, default_rounds: int = 3):
        super().__init__(registry, message_bus, storage)
        self.default_rounds = max(1, default_rounds)

    async def execute(self, request: OrchestrationRequest) -> OrchestrationResult:
        tasks: Sequence[TaskDefinition] = request.tasks
        if not tasks:
            return OrchestrationResult(
                results=[],
                success=True,
                final_context=dict(request.context),
                metadata={"note": "No agents/tasks provided for round robin strategy."},
            )

        max_rounds = int(request.metadata.get("rounds", self.default_rounds))
        max_rounds = max(1, max_rounds)
        stop_on_failure = bool(request.metadata.get("stop_on_failure", False))

        history: List[Dict[str, Any]] = list(request.context.get("history", []))
        shared_context: Dict[str, Any] = dict(request.context)
        results: List[TaskResult] = []

        for round_index in range(max_rounds):
            shared_context["round_index"] = round_index
            for turn_index, task in enumerate(tasks, start=1):
                task_payload = dict(task.payload)
                task_payload.setdefault("history", list(history))
                task_payload.setdefault("round_index", round_index)
                task_payload.setdefault("turn_index", turn_index)

                task_id = task.task_id or f"{task.agent_name}-{round_index}-{turn_index}"
                try:
                    output_model = await self.registry.execute(task.agent_name, task_payload)
                    output_payload = self._normalize_output(output_model)

                    history_entry = {
                        "agent": task.agent_name,
                        "task_id": task_id,
                        "round": round_index,
                        "turn": turn_index,
                        "output": output_payload,
                    }
                    history.append(history_entry)
                    shared_context[f"round:{round_index}:{task.agent_name}"] = output_payload

                    results.append(
                        TaskResult(
                            task_id=task_id,
                            agent_name=task.agent_name,
                            success=True,
                            output=output_payload,
                            metadata={"round_index": round_index, "turn_index": turn_index},
                        )
                    )

                    if self.message_bus is not None:
                        await self.message_bus.publish(
                            AgentMessage(
                                message_id=f"rr-{task_id}",
                                sender="RoundRobinStrategy",
                                recipient=task.agent_name,
                                message_type="round_robin_turn",
                                payload={
                                    "round_index": round_index,
                                    "turn_index": turn_index,
                                    "input_payload": task_payload,
                                    "output_payload": output_payload,
                                },
                            )
                        )

                except Exception as exc:  # noqa: BLE001
                    error_message = str(exc)
                    results.append(
                        TaskResult(
                            task_id=task_id,
                            agent_name=task.agent_name,
                            success=False,
                            error=error_message,
                            metadata={"round_index": round_index, "turn_index": turn_index},
                        )
                    )
                    shared_context["last_error"] = error_message
                    history.append(
                        {
                            "agent": task.agent_name,
                            "task_id": task_id,
                            "round": round_index,
                            "turn": turn_index,
                            "error": error_message,
                        }
                    )
                    if stop_on_failure:
                        return OrchestrationResult(
                            results=results,
                            success=False,
                            final_context=shared_context,
                            metadata={
                                "rounds_executed": round_index + 1,
                                "history_length": len(history),
                                "stopped_on_failure": True,
                            },
                        )
                    continue

        final_context = dict(shared_context)
        final_context["history"] = history
        overall_success = all(result.success for result in results)

        return OrchestrationResult(
            results=results,
            success=overall_success,
            final_context=final_context,
            metadata={
                "rounds_executed": max_rounds,
                "history_length": len(history),
                "agents": [t.agent_name for t in tasks],
            },
        )

    @staticmethod
    def _normalize_output(output_model: Any) -> Any:
        if hasattr(output_model, "model_dump"):
            return output_model.model_dump()
        if hasattr(output_model, "dict"):
            return output_model.dict()
        if isinstance(output_model, dict):
            return output_model
        return {"value": output_model}
    