from typing import Dict, Any, List

from .base_strategy import InteractionStrategy

from ..models import (
    OrchestrationRequest,
    OrchestrationResult,
    TaskResult
)


class DebateStrategy(InteractionStrategy):

    async def execute(
        self,
        request: OrchestrationRequest,
        agent_registry,
        message_bus
    ) -> OrchestrationResult:

        context: Dict[str, Any] = dict(request.context)

        tasks = request.tasks

        if len(tasks) < 2:
            raise ValueError("DebateStrategy requires at least two agents")

        proposer_task = tasks[0]
        critic_task = tasks[1]

        proposer = agent_registry.get(proposer_task.agent_name)
        critic = agent_registry.get(critic_task.agent_name)

        if proposer is None or critic is None:
            raise ValueError("Debate agents not found")

        max_rounds = request.metadata.get("max_rounds", 5)

        history: List[Dict[str, Any]] = []

        results: List[TaskResult] = []

        current_answer = None

        for round_id in range(1, max_rounds + 1):

            await message_bus.publish({
                "event": "debate_round_started",
                "round": round_id
            })

            proposer_payload = {
                **proposer_task.payload,
                "context": context,
                "previous_answer": current_answer,
                "history": history,
                "round": round_id
            }

            proposer_output = await proposer.run(proposer_payload)

            results.append(
                TaskResult(
                    task_id=f"proposer_round_{round_id}",
                    agent_name=proposer_task.agent_name,
                    success=True,
                    output=proposer_output
                )
            )

            current_answer = proposer_output

            critic_payload = {
                **critic_task.payload,
                "context": context,
                "answer": current_answer,
                "history": history,
                "round": round_id
            }

            critic_output = await critic.run(critic_payload)

            results.append(
                TaskResult(
                    task_id=f"critic_round_{round_id}",
                    agent_name=critic_task.agent_name,
                    success=True,
                    output=critic_output
                )
            )

            history.append({
                "round": round_id,
                "answer": current_answer,
                "critique": critic_output
            })

            if isinstance(critic_output, dict):

                if critic_output.get("approved") is True:

                    await message_bus.publish({
                        "event": "debate_finished",
                        "round": round_id
                    })

                    break

            await message_bus.publish({
                "event": "debate_round_completed",
                "round": round_id
            })

        context["debate_history"] = history
        context["final_answer"] = current_answer

        return OrchestrationResult(
            success=True,
            results=results,
            final_context=context
        )
