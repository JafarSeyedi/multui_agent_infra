# agents/orchestration/interaction/memory_augmented_strategy.py
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from agents.buses.base import MessageBus
from agents.orchestration.models import AgentMessage
from agents.orchestration.models import (
    OrchestrationRequest,
    OrchestrationResult,
    TaskDefinition,
    TaskResult,
)
from .base_strategy import InteractionStrategy


class MemoryAugmentedStrategy(InteractionStrategy):
    """
    استراتژی‌ای که state بلندمدت (memory) را مدیریت می‌کند و بر اساس آن مسیر مناسب را انتخاب می‌نماید.
    """

    scenario_name = "memory_augmented"

    def __init__(
        self,
        agent_registry,
        message_bus: Optional[MessageBus] = None,
        storage=None,
        memory_key: str = "long_term_memory",
        max_memory_size: int = 50,
    ):
        super().__init__(agent_registry, message_bus, storage)
        self.memory_key = memory_key
        self.max_memory_size = max(1, max_memory_size)

    async def execute(self, request: OrchestrationRequest) -> OrchestrationResult:
        shared_context: Dict[str, Any] = dict(request.context)
        memory: List[Any] = list(shared_context.get(self.memory_key, []))
        tasks: Sequence[TaskDefinition] = self._prioritize_tasks(request.tasks, memory)
        results: List[TaskResult] = []

        for task in tasks:
            payload = dict(task.payload)
            payload.setdefault("memory", list(memory))
            payload.setdefault("shared_context", dict(shared_context))
            task_id = task.task_id or f"memory:{task.agent_name}"

            try:
                output_model = await self.agent_registry.execute(task.agent_name, payload)
                normalized = self._normalize_output(output_model)

                memory.append({"agent": task.agent_name, "output": normalized})
                if len(memory) > self.max_memory_size:
                    memory = memory[-self.max_memory_size :]

                shared_context[self.memory_key] = memory
                results.append(
                    TaskResult(
                        task_id=task_id,
                        agent_name=task.agent_name,
                        success=True,
                        output=normalized,
                        metadata={"memory_snapshot_size": len(memory)},
                    )
                )

                await self._publish_memory_update(task_id, task.agent_name, normalized)

            except Exception as exc:  # noqa: BLE001
                error_message = str(exc)
                results.append(
                    TaskResult(
                        task_id=task_id,
                        agent_name=task.agent_name,
                        success=False,
                        error=error_message,
                    )
                )
                shared_context.setdefault("errors", []).append({task.agent_name: error_message})

        overall_success = all(result.success for result in results)
        final_context = {**shared_context, self.memory_key: memory}

        return OrchestrationResult(
            results=results,
            success=overall_success,
            final_context=final_context,
            metadata={"memory_size": len(memory)},
        )

    def _prioritize_tasks(
        self, tasks: Sequence[TaskDefinition], memory: List[Any]
    ) -> Sequence[TaskDefinition]:
        if not memory:
            return tasks
        if memory and isinstance(memory[-1], dict) and memory[-1].get("agent"):
            last_agent = memory[-1]["agent"]
            ordered = sorted(tasks, key=lambda task: task.agent_name != last_agent)
            return ordered
        return tasks

    async def _publish_memory_update(self, task_id: str, agent_name: str, output: Any) -> None:
        # ✅ استفاده از _emit
        await self._emit(
            message_type="memory_update",
            payload={"task_id": task_id, "output": output},
            sender="MemoryAugmentedStrategy",
            recipient=agent_name,
            message_id=f"memory-{task_id}",
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
