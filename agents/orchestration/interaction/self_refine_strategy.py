# agents/orchestration/interaction/self_refine_strategy.py
from typing import Any, Dict, List

from .base_strategy import InteractionStrategy
from ..models import (
    OrchestrationRequest,
    OrchestrationResult,
    TaskResult,
)


class SelfRefineStrategy(InteractionStrategy):
    async def execute(self, request: OrchestrationRequest) -> OrchestrationResult:
        context: Dict[str, Any] = dict(request.context or {})
        metadata = request.metadata or {}

        generator_name = metadata.get("generator_agent")
        critic_name = metadata.get("critic_agent")
        refiner_name = metadata.get("refiner_agent")
        if not (generator_name and critic_name and refiner_name):
            raise ValueError("generator_agent, critic_agent and refiner_agent must be defined in metadata.")

        max_refinements = int(metadata.get("max_refinements", 3))
        quality_threshold = float(metadata.get("quality_threshold", 0.9))

        generator = self.registry.get(generator_name)
        critic = self.registry.get(critic_name)
        refiner = self.registry.get(refiner_name)
        if not generator or not critic or not refiner:
            raise ValueError("Self-refine agents must be registered before executing strategy.")

        results: List[TaskResult] = []

        output = await self._safe_execute(
            generator,
            generator_name,
            {"context": dict(context)},
            "generate",
            results,
        )

        iterations = 0
        converged_round: int | None = None

        while iterations < max_refinements:
            iterations += 1

            critique = await self._safe_execute(
                critic,
                critic_name,
                {"answer": output, "context": dict(context)},
                f"critique_{iterations}",
                results,
            )

            score = self._extract_score(critique)
            if score >= quality_threshold:
                converged_round = iterations
                break

            output = await self._safe_execute(
                refiner,
                refiner_name,
                {"answer": output, "critique": critique, "context": dict(context)},
                f"refine_{iterations}",
                results,
            )

        context["final_answer"] = output
        return OrchestrationResult(
            success=True,
            results=results,
            final_context=context,
            metadata={
                "iterations": iterations,
                "converged_round": converged_round,
                "threshold": quality_threshold,
            },
        )

    async def _safe_execute(
        self, agent, agent_name: str, payload: Dict[str, Any], task_id: str, results: List[TaskResult]
    ) -> Any:
        try:
            output = await agent.execute(payload)
            results.append(TaskResult(task_id=task_id, agent_name=agent_name, success=True, output=output))
            return output
        except Exception as exc:
            results.append(TaskResult(task_id=task_id, agent_name=agent_name, success=False, error=str(exc)))
            raise

    @staticmethod
    def _extract_score(critique: Any) -> float:
        if isinstance(critique, dict):
            score = critique.get("score")
            if isinstance(score, (int, float)):
                return float(score)
        return 0.0