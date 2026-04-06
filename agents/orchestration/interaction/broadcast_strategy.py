# agents/orchestration/interaction/broadcast_strategy.py
import asyncio
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .base_strategy import InteractionStrategy
from ..models import (
    OrchestrationRequest,
    OrchestrationResult,
    TaskDefinition,
    TaskResult,
)


class BroadcastStrategy(InteractionStrategy):
    async def execute(self, request: OrchestrationRequest) -> OrchestrationResult:
        context: Dict[str, Any] = dict(request.context or {})
        tasks: List[TaskDefinition] = request.tasks or []

        if not tasks:
            raise ValueError("BroadcastStrategy requires at least one task.")

        mode = request.metadata.get("aggregator", "merge")
        results: List[TaskResult] = []

        coroutines = [self._execute_task(task, dict(context)) for task in tasks]
        task_results = await asyncio.gather(*coroutines, return_exceptions=True)

        task_results = self._normalize_gather_results(task_results)
        results.extend(task_results)

        final_output = self._aggregate_outputs(results, mode)

        return OrchestrationResult(
            success=all(result.success for result in results),
            results=results,
            final_context={
                **context,
                "broadcast_output": final_output,
                "aggregation_mode": mode,
                "task_count": len(results),
            },
        )

    async def _execute_task(self, task: TaskDefinition, context_snapshot: Dict[str, Any]) -> TaskResult:
        payload = {**task.payload, "context": context_snapshot}

        if self.message_bus:
            await self.message_bus.publish(
                {"event": "broadcast_task_started", "task_id": task.task_id, "agent": task.agent_name}
            )

        agent = self.registry.get(task.agent_name)
        if agent is None:
            return TaskResult(
                task_id=task.task_id,
                agent_name=task.agent_name,
                success=False,
                error=f"Agent '{task.agent_name}' not found.",
            )

        try:
            output = await agent.execute(payload)
            if self.message_bus:
                await self.message_bus.publish(
                    {"event": "broadcast_task_completed", "task_id": task.task_id, "agent": task.agent_name}
                )

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

    @staticmethod
    def _normalize_gather_results(results: Iterable[Any]) -> List[TaskResult]:
        normalized: List[TaskResult] = []
        for item in results:
            if isinstance(item, TaskResult):
                normalized.append(item)
            elif isinstance(item, Exception):
                normalized.append(
                    TaskResult(
                        task_id="unknown",
                        agent_name="unknown",
                        success=False,
                        error=str(item),
                    )
                )
        return normalized

    def _aggregate_outputs(self, results: List[TaskResult], mode: str) -> Any:
        if mode == "merge":
            return {res.agent_name: res.output for res in results if res.success}
        if mode == "list":
            return [
                {"agent": res.agent_name, "output": res.output, "success": res.success, "error": res.error}
                for res in results
            ]
        if mode == "vote":
            votes: Dict[Any, int] = {}
            for res in results:
                if res.success and isinstance(res.output, str):
                    votes[res.output] = votes.get(res.output, 0) + 1
            if not votes:
                return None
            return max(votes.items(), key=lambda kv: kv[1])[0]
        # fallback
        return [res.output for res in results if res.success]