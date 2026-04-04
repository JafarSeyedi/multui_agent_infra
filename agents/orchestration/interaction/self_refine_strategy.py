from typing import Dict, Any, List

from .base_strategy import InteractionStrategy

from ..models import (
    OrchestrationRequest,
    OrchestrationResult,
    TaskResult
)


class SelfRefineStrategy(InteractionStrategy):

    async def execute(
        self,
        request: OrchestrationRequest,
        agent_registry,
        message_bus
    ) -> OrchestrationResult:

        context: Dict[str, Any] = dict(request.context)

        metadata = request.metadata

        generator_name = metadata["generator_agent"]
        critic_name = metadata["critic_agent"]
        refiner_name = metadata["refiner_agent"]

        max_refinements = metadata.get("max_refinements", 3)
        quality_threshold = metadata.get("quality_threshold", 0.9)

        results: List[TaskResult] = []

        generator = agent_registry.get(generator_name)
        critic = agent_registry.get(critic_name)
        refiner = agent_registry.get(refiner_name)

        if not generator or not critic or not refiner:
            raise ValueError("Required agents not registered")

        await message_bus.publish({
            "event": "self_refine_started"
        })

        # Step 1 — Generate initial answer
        output = await generator.run(context)

        results.append(
            TaskResult(
                task_id="generate",
                agent_name=generator_name,
                success=True,
                output=output
            )
        )

        iteration = 0

        while iteration < max_refinements:

            iteration += 1

            await message_bus.publish({
                "event": "self_refine_iteration",
                "iteration": iteration
            })

            critique_input = {
                "answer": output,
                "context": context
            }

            critique = await critic.run(critique_input)

            results.append(
                TaskResult(
                    task_id=f"critique_{iteration}",
                    agent_name=critic_name,
                    success=True,
                    output=critique
                )
            )

            score = self._extract_score(critique)

            if score >= quality_threshold:

                await message_bus.publish({
                    "event": "self_refine_converged",
                    "score": score
                })

                break

            refine_input = {
                "answer": output,
                "critique": critique,
                "context": context
            }

            output = await refiner.run(refine_input)

            results.append(
                TaskResult(
                    task_id=f"refine_{iteration}",
                    agent_name=refiner_name,
                    success=True,
                    output=output
                )
            )

        context["final_answer"] = output

        return OrchestrationResult(
            success=True,
            results=results,
            final_context=context
        )

    def _extract_score(self, critique):

        if isinstance(critique, dict):
            score = critique.get("score")

            if isinstance(score, (int, float)):
                return float(score)

        return 0.0
