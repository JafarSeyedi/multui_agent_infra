import asyncio
from typing import Dict, Any, List

from .base_strategy import InteractionStrategy

from ..models import (
    OrchestrationRequest,
    OrchestrationResult,
    TaskResult,
    TaskDefinition
)


class PipelineStrategy(InteractionStrategy):
    """
    اجرای خطی تسک‌ها
    """

    async def execute(self, request: OrchestrationRequest) -> OrchestrationResult:

        context: Dict[str, Any] = dict(request.context)
        results: List[TaskResult] = []

        for task in request.tasks:

            await self.message_bus.publish({
                "event": "task_started",
                "task_id": task.task_id,
                "agent": task.agent_name
            })

            result = await self._execute_task(
                task=task,
                context=context
            )

            results.append(result)

            if result.success:

                if isinstance(result.output, dict):
                    context.update(result.output)

                await self.message_bus.publish({
                    "event": "task_completed",
                    "task_id": task.task_id,
                    "agent": task.agent_name
                })

            else:

                await self.message_bus.publish({
                    "event": "task_failed",
                    "task_id": task.task_id,
                    "agent": task.agent_name,
                    "error": result.error
                })

                return OrchestrationResult(
                    success=False,
                    results=results,
                    final_context=context
                )

        return OrchestrationResult(
            success=True,
            results=results,
            final_context=context
        )

    async def _execute_task(
        self,
        task: TaskDefinition,
        context: Dict[str, Any]
    ) -> TaskResult:

        agent = self.registry.get(task.agent_name)

        if agent is None:

            return TaskResult(
                task_id=task.task_id,
                agent_name=task.agent_name,
                success=False,
                error=f"Agent '{task.agent_name}' not found"
            )

        payload = dict(task.payload)

        payload["context"] = context

        try:

            output = await agent.execute(payload)

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
