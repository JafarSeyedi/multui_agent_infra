import asyncio
from typing import Dict, Any, List, Set

from .base_strategy import InteractionStrategy

from ..models import (
    OrchestrationRequest,
    OrchestrationResult,
    TaskResult,
    TaskDefinition
)


class DAGStrategy(InteractionStrategy):

    async def execute(self, request: OrchestrationRequest) -> OrchestrationResult:

        context: Dict[str, Any] = dict(request.context)
        results: List[TaskResult] = []

        tasks_by_id: Dict[str, TaskDefinition] = {
            t.task_id: t for t in request.tasks
        }

        self._validate_dag(tasks_by_id)

        completed: Set[str] = set()
        running: Set[str] = set()

        context_lock = asyncio.Lock()

        while len(completed) < len(tasks_by_id):

            ready_tasks = self._get_ready_tasks(
                tasks_by_id,
                completed,
                running
            )

            if not ready_tasks:
                break

            coroutines = [
                self._execute_task(
                    task=tasks_by_id[task_id],
                    context=context,
                    context_lock=context_lock
                )
                for task_id in ready_tasks
            ]

            running.update(ready_tasks)

            task_results = await asyncio.gather(*coroutines)

            for result in task_results:

                results.append(result)

                running.remove(result.task_id)

                if result.success:

                    completed.add(result.task_id)

                else:

                    await self.message_bus.publish({
                        "event": "task_failed",
                        "task_id": result.task_id,
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

    def _validate_dag(self, tasks: Dict[str, TaskDefinition]):

        visited = set()
        stack = set()

        def visit(task_id):

            if task_id in stack:
                raise ValueError("Cycle detected in DAG")

            if task_id in visited:
                return

            stack.add(task_id)

            for dep in tasks[task_id].depends_on:

                if dep not in tasks:
                    raise ValueError(f"Unknown dependency: {dep}")

                visit(dep)

            stack.remove(task_id)
            visited.add(task_id)

        for task_id in tasks:
            visit(task_id)

    def _get_ready_tasks(
        self,
        tasks: Dict[str, TaskDefinition],
        completed: Set[str],
        running: Set[str]
    ) -> List[str]:

        ready = []

        for task_id, task in tasks.items():

            if task_id in completed or task_id in running:
                continue

            if all(dep in completed for dep in task.depends_on):
                ready.append(task_id)

        return ready

    async def _execute_task(
        self,
        task: TaskDefinition,
        context: Dict[str, Any],
        context_lock
    ) -> TaskResult:

        await self.message_bus.publish({
            "event": "task_started",
            "task_id": task.task_id,
            "agent": task.agent_name
        })

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

            if isinstance(output, dict):

                async with context_lock:
                    context.update(output)

            await self.message_bus.publish({
                "event": "task_completed",
                "task_id": task.task_id,
                "agent": task.agent_name
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
