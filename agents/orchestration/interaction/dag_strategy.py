# agents/orchestration/interaction/dag_strategy.py
import asyncio
from typing import Any, Dict, List, Set

from .base_strategy import InteractionStrategy
from ..models import (
    OrchestrationRequest,
    OrchestrationResult,
    TaskDefinition,
    TaskResult,
)


class DAGStrategy(InteractionStrategy):
    scenario_name = "dag"

    async def execute(self, request: OrchestrationRequest) -> OrchestrationResult:
        context: Dict[str, Any] = dict(request.context or {})
        tasks = {task.task_id: task for task in request.tasks if task.task_id}
        self._validate_dag(tasks)

        completed: Set[str] = set()
        running: Set[str] = set()
        results: List[TaskResult] = []
        context_lock = asyncio.Lock()

        while len(completed) < len(tasks):
            ready = [
                task_id
                for task_id, task in tasks.items()
                if task_id not in completed
                and task_id not in running
                and all(dep in completed for dep in task.depends_on)
            ]

            if not ready:
                break

            running.update(ready)

            coroutines = [
                self._execute_task(tasks[task_id], dict(context), context_lock)
                for task_id in ready
            ]
            gathered = await asyncio.gather(*coroutines, return_exceptions=True)

            # ✅ حل خطاهای 54-70: فیلتر BaseException قبل از استفاده
            for outcome in gathered:
                if isinstance(outcome, BaseException):
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
                running.discard(outcome.task_id)

                if outcome.success:
                    completed.add(outcome.task_id)
                    await self._emit(
                        message_type="task_completed",
                        payload={"task_id": outcome.task_id, "agent": outcome.agent_name},
                        sender="DAGStrategy",
                        recipient=outcome.agent_name,
                        message_id=f"dag_done_{outcome.task_id}",
                    )
                else:
                    await self._emit(
                        message_type="task_failed",
                        payload={
                            "task_id": outcome.task_id,
                            "agent": outcome.agent_name,
                            "error": outcome.error,
                        },
                        sender="DAGStrategy",
                        recipient=outcome.agent_name,
                        message_id=f"dag_fail_{outcome.task_id}",
                    )
                    return OrchestrationResult(
                        success=False,
                        results=results,
                        final_context=context,
                    )

        return OrchestrationResult(success=True, results=results, final_context=context)

    def _validate_dag(self, tasks: Dict[str, TaskDefinition]) -> None:
        visited: Set[str] = set()
        stack: Set[str] = set()

        def visit(node: str) -> None:
            if node in stack:
                raise ValueError("Cycle detected in DAG.")
            if node in visited:
                return
            stack.add(node)
            for dep in tasks[node].depends_on:
                if dep not in tasks:
                    raise ValueError(f"Unknown dependency: {dep}")
                visit(dep)
            stack.remove(node)
            visited.add(node)

        for task_id in tasks:
            visit(task_id)

    async def _execute_task(
        self,
        task: TaskDefinition,
        context_snapshot: Dict[str, Any],
        context_lock: asyncio.Lock,
    ) -> TaskResult:
        # ✅ حل خطای 104
        await self._emit(
            message_type="task_started",
            payload={"task_id": task.task_id, "agent": task.agent_name},
            sender="DAGStrategy",
            recipient=task.agent_name,
            message_id=f"dag_start_{task.task_id}",
        )

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
            if isinstance(output, dict):
                async with context_lock:
                    context_snapshot.update(output)
            return TaskResult(
                task_id=task.task_id,
                agent_name=task.agent_name,
                success=True,
                output=output,
            )
        except Exception as exc:
            return TaskResult(
                task_id=task.task_id,
                agent_name=task.agent_name,
                success=False,
                error=str(exc),
            )
