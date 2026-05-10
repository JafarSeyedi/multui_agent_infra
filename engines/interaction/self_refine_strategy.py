from typing import Any

from ..agents.models import AgentOutput
from .base_strategy import InteractionStrategy
from .interaction_models import InteractionRequest
from .interaction_models import InteractionResult


class SelfRefineStrategy(InteractionStrategy):
    """
    Strategy برای الگوی Self-Refinement:

    Generator → Critic → Refiner → (loop)
    """

    scenario_name = "self_refine"

    async def execute(self, request: InteractionRequest) -> InteractionResult:

        context: dict[str, Any] = dict(request.context or {})
        metadata = request.metadata or {}

        generator_name = metadata.get("generator_agent")
        critic_name = metadata.get("critic_agent")
        refiner_name = metadata.get("refiner_agent")

        if not (generator_name and critic_name and refiner_name):
            raise ValueError(
                "generator_agent, critic_agent and refiner_agent must be defined in metadata."
            )

        max_refinements = int(metadata.get("max_refinements", 3))
        quality_threshold = float(metadata.get("quality_threshold", 0.9))

        results: list[AgentOutput] = []

        # ---------------------------
        # Step 1: initial generation
        # ---------------------------

        gen_output = await self._run_agent(
            agent_name=generator_name,
            agent_id="generate",
            payload={"context": dict(context)},
            context=context,
        )

        results.append(gen_output)

        if gen_output.error:
            return InteractionResult(
                success=False,
                results=results,
                final_context=context,
                metadata={"stage": "generation_failed"},
            )

        answer = gen_output.payload or gen_output.message

        iterations = 0
        converged_round: int | None = None

        # ---------------------------
        # refinement loop
        # ---------------------------

        while iterations < max_refinements:

            iterations += 1

            # --- critique ---
            critic_output = await self._run_agent(
                agent_name=critic_name,
                agent_id=f"critique_{iterations}",
                payload={
                    "answer": answer,
                    "context": dict(context),
                },
                context=context,
            )

            results.append(critic_output)

            if critic_output.error:
                return InteractionResult(
                    success=False,
                    results=results,
                    final_context=context,
                    metadata={"stage": "critique_failed"},
                )

            critique = critic_output.payload or critic_output.message
            score = self._extract_score(critique)

            if score >= quality_threshold:
                converged_round = iterations
                break

            # --- refine ---
            refine_output = await self._run_agent(
                agent_name=refiner_name,
                agent_id=f"refine_{iterations}",
                payload={
                    "answer": answer,
                    "critique": critique,
                    "context": dict(context),
                },
                context=context,
            )

            results.append(refine_output)

            if refine_output.error:
                return InteractionResult(
                    success=False,
                    results=results,
                    final_context=context,
                    metadata={"stage": "refine_failed"},
                )

            answer = refine_output.payload or refine_output.message

        # ---------------------------
        # final result
        # ---------------------------

        context["final_answer"] = answer

        return InteractionResult(
            success=True,
            results=results,
            final_context=context,
            metadata={
                "iterations": iterations,
                "converged_round": converged_round,
                "threshold": quality_threshold,
            },
        )

    @staticmethod
    def _extract_score(critique: Any) -> float:
        if isinstance(critique, dict):
            score = critique.get("score")
            if isinstance(score, (int, float)):
                return float(score)
        return 0.0
