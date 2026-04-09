# agents/orchestration/interaction/conditional_strategy.py
from typing import Any, Dict, List, Optional

from .base_strategy import InteractionStrategy
from ..models import (
    OrchestrationRequest,
    OrchestrationResult,
    TaskDefinition,
    TaskResult,
)


class ConditionalStrategy(InteractionStrategy):
    scenario_name = "conditional"

    async def execute(self, request: OrchestrationRequest) -> OrchestrationResult:
        context: Dict[str, Any] = dict(request.context or {})
        tasks = {task.task_id: task for task in request.tasks if task.task_id}
        start_task = request.metadata.get("start_task") or (next(iter(tasks), None))

        if not start_task:
            raise ValueError("No valid start_task provided for ConditionalStrategy.")

        current_task_id: Optional[str] = start_task
        results: List[TaskResult] = []
        visited: set[str] = set()

        while current_task_id:
            if current_task_id in visited:
                raise RuntimeError("Detected cycle in conditional routing.")
            visited.add(current_task_id)

            task = tasks.get(current_task_id)
            if not task:
                raise ValueError(f"Task '{current_task_id}' is not defined.")

            # ✅ حل خطای 37
            await self._emit(
                message_type="conditional_task_started",
                payload={"task_id": task.task_id, "agent": task.agent_name},
                sender="ConditionalStrategy",
                recipient=task.agent_name,
                message_id=f"cond_start_{task.task_id}",
            )

            agent = self.agent_registry.get(task.agent_name)
            if agent is None:
                raise ValueError(f"Agent '{task.agent_name}' not registered.")

            payload = {**task.payload, "context": dict(context)}
            output: Any = None

            try:
                output = await agent.execute(payload)
                results.append(
                    TaskResult(task_id=task.task_id, agent_name=task.agent_name, success=True, output=output)
                )
                if isinstance(output, dict):
                    context.update(output)
            except Exception as exc:
                results.append(
                    TaskResult(task_id=task.task_id, agent_name=task.agent_name, success=False, error=str(exc))
                )
                return OrchestrationResult(success=False, results=results, final_context=context)

            # ✅ حل خطای 61
            await self._emit(
                message_type="conditional_task_completed",
                payload={"task_id": task.task_id, "output": output},
                sender="ConditionalStrategy",
                recipient=task.agent_name,
                message_id=f"cond_done_{task.task_id}",
            )

            current_task_id = self._select_next_task(task, output)

        return OrchestrationResult(success=True, results=results, final_context=context)

    @staticmethod
    def _select_next_task(task: TaskDefinition, output: Any) -> Optional[str]:
        routes = getattr(task, "routes", None) or {}
        if not routes:
            return None
        if isinstance(output, dict):
            route_key = output.get("route")
            if route_key and route_key in routes:
                return routes[route_key]
        if isinstance(output, str) and output in routes:
            return routes[output]
        return routes.get("default")
