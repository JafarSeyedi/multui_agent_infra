# agents/orchestration/interaction/pipeline_strategy.py
from typing import Any, Dict, List

from .base_strategy import InteractionStrategy
from ..models import (
    OrchestrationRequest,
    OrchestrationResult,
    TaskDefinition,
    TaskResult,
)


class PipelineStrategy(InteractionStrategy):
    async def execute(self, request: OrchestrationRequest) -> OrchestrationResult:
        context: Dict[str, Any] = dict(request.context or {})
        results: List[TaskResult] = []

        for task in request.tasks or []:
            if self.message_bus:
                await self.message_bus.publish(
                    {"event": "task_started", "task_id": task.task_id, "agent": task.agent_name}
                )

            result = await self._execute_task(task, dict(context))
            results.append(result)

            if result.success:
                if isinstance(result.output, dict):
                    context.update(result.output)
                if self.message_bus:
                    await self.message_bus.publish(
                        {"event": "task_completed", "task_id": task.task_id, "agent": task.agent_name}
                    )
            else:
                if self.message_bus:
                    await self.message_bus.publish(
                        {
                            "event": "task_failed",
                            "task_id": task.task_id,
                            "agent": task.agent_name,
                            "error": result.error,
                        }
                    )
                return OrchestrationResult(
                    success=False,
                    results=results,
                    final_context=context,
                    metadata={"failed_task": task.task_id},
                )

        return OrchestrationResult(success=True, results=results, final_context=context)

    async def _execute_task(self, task: TaskDefinition, context_snapshot: Dict[str, Any]) -> TaskResult:
        agent = self.registry.get(task.agent_name)
        if agent is None:
            return TaskResult(
                task_id=task.task_id,
                agent_name=task.agent_name,
                success=False,
                error=f"Agent '{task.agent_name}' not found.",
            )

        payload = {**task.payload, "context": context_snapshot}
        try:
            output = await agent.execute(payload)
            return TaskResult(task_id=task.task_id, agent_name=task.agent_name, success=True, output=output)
        except Exception as exc:
            return TaskResult(task_id=task.task_id, agent_name=task.agent_name, success=False, error=str(exc))