from typing import Dict, Any, List

from .base_strategy import InteractionStrategy

from ..models import (
    OrchestrationRequest,
    OrchestrationResult,
    TaskResult,
    TaskDefinition
)


class ConditionalStrategy(InteractionStrategy):

    async def execute(self, request: OrchestrationRequest) -> OrchestrationResult:

        context: Dict[str, Any] = dict(request.context)

        tasks: Dict[str, TaskDefinition] = {
            t.task_id: t for t in request.tasks
        }

        start_task = request.metadata.get("start_task")

        if start_task is None:
            start_task = request.tasks[0].task_id

        current_task_id = start_task

        results: List[TaskResult] = []

        visited = set()

        while current_task_id:

            if current_task_id in visited:
                raise RuntimeError("Conditional loop detected")

            visited.add(current_task_id)

            task = tasks.get(current_task_id)

            if task is None:
                raise ValueError(f"Task '{current_task_id}' not found")

            await self.message_bus.publish({
                "event": "conditional_task_started",
                "task_id": task.task_id,
                "agent": task.agent_name
            })

            agent = self.registry.get(task.agent_name)

            if agent is None:
                raise ValueError(f"Agent '{task.agent_name}' not registered")

            payload = {**task.payload, "context": context}

            try:

                output = await agent.execute(payload)

                result = TaskResult(
                    task_id=task.task_id,
                    agent_name=task.agent_name,
                    success=True,
                    output=output
                )

                results.append(result)

                if isinstance(output, dict):
                    context.update(output)

            except Exception as e:

                result = TaskResult(
                    task_id=task.task_id,
                    agent_name=task.agent_name,
                    success=False,
                    error=str(e)
                )

                results.append(result)

                return OrchestrationResult(
                    success=False,
                    results=results,
                    final_context=context
                )

            await self.message_bus.publish({
                "event": "conditional_task_completed",
                "task_id": task.task_id
            })

            next_task = self._select_next_task(task, output)

            current_task_id = next_task

        return OrchestrationResult(
            success=True,
            results=results,
            final_context=context
        )

    def _select_next_task(
        self,
        task: TaskDefinition,
        output: Any
    ) -> str | None:

        routes = getattr(task, "routes", None)

        if not routes:
            return None

        if isinstance(output, dict):

            route_key = output.get("route")

            if route_key in routes:
                return routes[route_key]

        if isinstance(output, str):

            if output in routes:
                return routes[output]

        return routes.get("default")
