# agents/orchestration/interaction/pipeline_strategy.py
from typing import Any, Dict, List

from agents.orchestration.models import AgentMessage
from .base_strategy import InteractionStrategy
from ..models import (
    OrchestrationRequest,
    OrchestrationResult,
    TaskDefinition,
    TaskResult,
)


class PipelineStrategy(InteractionStrategy):
    scenario_name = "pipeline"

    async def execute(self, request: OrchestrationRequest) -> OrchestrationResult:
        context: Dict[str, Any] = dict(request.context or {})
        results: List[TaskResult] = []

        for task in request.tasks or []:
            # ✅ استفاده از _emit
            await self._emit(
                message_type="task_started",
                payload={"task_id": task.task_id, "agent": task.agent_name},
                sender="PipelineStrategy",
                recipient=task.agent_name,
                message_id=f"task_{task.task_id}",
            )

            result = await self._execute_task(task, dict(context))
            results.append(result)

            if result.success:
                if isinstance(result.output, dict):
                    context.update(result.output)
                await self._emit(
                    message_type="task_completed",
                    payload={"task_id": task.task_id, "agent": task.agent_name},
                    sender="PipelineStrategy",
                    recipient=task.agent_name,
                    message_id=f"task_done_{task.task_id}",
                )
            else:
                await self._emit(
                    message_type="task_failed",
                    payload={"task_id": task.task_id, "agent": task.agent_name, "error": result.error},
                    sender="PipelineStrategy",
                    recipient=task.agent_name,
                    message_id=f"task_fail_{task.task_id}",
                )
                return OrchestrationResult(
                    success=False,
                    results=results,
                    final_context=context,
                    metadata={"failed_task": task.task_id},
                )

        return OrchestrationResult(success=True, results=results, final_context=context)

    async def _execute_task(self, task: TaskDefinition, context_snapshot: Dict[str, Any]) -> TaskResult:
        agent = self.agent_registry.get(task.agent_name)
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
