import asyncio
from typing import Dict, Any, List

from .base_strategy import InteractionStrategy
from ..models import (
    OrchestrationRequest,
    OrchestrationResult,
    TaskDefinition,
    TaskResult
)


class BroadcastStrategy(InteractionStrategy):

    async def execute(
        self,
        request: OrchestrationRequest,
        agent_registry,
        message_bus
    ) -> OrchestrationResult:

        context: Dict[str, Any] = dict(request.context)

        tasks: List[TaskDefinition] = request.tasks

        if not tasks:
            raise ValueError("BroadcastStrategy requires at least one task")

        results: List[TaskResult] = []

        aggregator_mode = request.metadata.get("aggregator", "merge")

        async def run_single(task: TaskDefinition) -> TaskResult:

            await message_bus.publish({
                "event": "broadcast_task_started",
                "task_id": task.task_id,
                "agent": task.agent_name
            })

            agent = agent_registry.get(task.agent_name)

            if agent is None:
                return TaskResult(
                    task_id=task.task_id,
                    agent_name=task.agent_name,
                    success=False,
                    error=f"Agent '{task.agent_name}' not found"
                )

            payload = {**task.payload, "context": context}

            try:
                output = await agent.run(payload)

                await message_bus.publish({
                    "event": "broadcast_task_completed",
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

        coroutines = [run_single(task) for task in tasks]
        task_results = await asyncio.gather(*coroutines)

        results.extend(task_results)

        final_output = self._aggregate_outputs(
            results=task_results,
            mode=aggregator_mode
        )

        return OrchestrationResult(
            success=True,
            results=results,
            final_context={
                **context,
                "broadcast_output": final_output
            }
        )

    def _aggregate_outputs(
        self,
        results: List[TaskResult],
        mode: str
    ) -> Any:

        if mode == "merge":

            merged = {}

            for r in results:
                if r.success:
                    merged[r.agent_name] = r.output

            return merged

        if mode == "list":

            return [
                {
                    "agent": r.agent_name,
                    "output": r.output,
                    "success": r.success
                }
                for r in results
            ]

        if mode == "vote":

            votes = {}

            for r in results:

                if not r.success:
                    continue

                if not isinstance(r.output, str):
                    continue

                votes[r.output] = votes.get(r.output, 0) + 1

            if not votes:
                return None

            return max(votes.items(), key=lambda kv: kv[1])[0]

        return [
            {
                "agent": r.agent_name,
                "output": r.output
            }
            for r in results
        ]
