from typing import Any

from ..._types import FeelContext, RawData, VariableValue
from ..models import AgentOutput
from .base_strategy import InteractionStrategy
from ..interaction_models import InteractionRequest
from ..interaction_models import InteractionResult


class DebateStrategy(InteractionStrategy):
    scenario_name = "debate"

    async def execute(self, request: InteractionRequest) -> InteractionResult:
        context: FeelContext = dict(request.context or {})
        agents = request.agents or []

        if len(agents) < 2:
            raise ValueError("DebateStrategy requires at least two agents (proposer & critic).")

        # Extract agent names
        proposer_agent_meta = agents[0]
        critic_agent_meta = agents[1]

        proposer_name = proposer_agent_meta.agent_name
        critic_name = critic_agent_meta.agent_name

        max_rounds = int(request.metadata.get("max_rounds", 5))
        history: list[RawData] = []
        results: list[AgentOutput] = []
        current_answer: VariableValue | None = None
        approved_round: int | None = None

        for round_id in range(1, max_rounds + 1):
            # ✅ Fix Missing recipient error
            await self._emit(
                message_type="debate_round_started",
                payload={"round": round_id},
                sender="DebateStrategy",
                recipient="all_participants",
                message_id=f"debate_start_{round_id}",
            )

            # --- Step 1: Proposer ---
            proposer_output = await self._run_agent(
                agent_name=proposer_name,
                agent_id=f"proposer_round_{round_id}",
                context=context,
                payload={
                    "history": history,
                    "round": round_id,
                    "mode": "propose"
                }
            )
            results.append(proposer_output)

            if proposer_output.error:
                break  # Stop on error

            # Extract current response from agent output
            current_answer = proposer_output.payload or proposer_output.message

            # --- Step 2: Critic ---
            critic_output = await self._run_agent(
                agent_name=critic_name,
                agent_id=f"critic_round_{round_id}",
                context=context,
                payload={
                    "answer": current_answer,
                    "history": history,
                    "round": round_id,
                    "mode": "critique"
                }
            )
            results.append(critic_output)

            if critic_output.error:
                break

            # Record in history for next round
            critic_data = critic_output.payload or critic_output.message
            history.append({
                "round": round_id,
                "answer": current_answer,
                "critique": critic_data
            })

            # ✅ Confirmation logic (check Critic output)
            if isinstance(critic_data, dict) and critic_data.get("approved") is True:
                approved_round = round_id
                await self._emit(
                    message_type="debate_finished",
                    payload={"round": round_id, "status": "approved"},
                    sender="DebateStrategy",
                    recipient="orchestrator",
                    message_id=f"debate_finished_{round_id}",
                )
                break

            # ✅ Notify end of round
            await self._emit(
                message_type="debate_round_completed",
                payload={"round": round_id},
                sender="DebateStrategy",
                recipient="all_participants",
                message_id=f"debate_round_{round_id}",
            )

        # Update final context
        context["debate_history"] = history
        context["final_answer"] = current_answer

        # Calculate overall success: if no agent had errors
        is_overall_success = all(res.error is None for res in results)

        return InteractionResult(
            success=is_overall_success,
            results=results,
            final_context=context,
            metadata={
                "rounds_executed": len(history),
                "approved_round": approved_round,
                "max_rounds_reached": len(history) >= max_rounds and not approved_round
            },
        )
