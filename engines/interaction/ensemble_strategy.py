from __future__ import annotations

from collections import Counter
from typing import Any

from ..agent.models import AgentOutput
from ..communication.buses.base_message_bus import MessageBus
from .base_strategy import InteractionStrategy
from .interaction_models import AgentMessage
from .interaction_models import InteractionRequest
from .interaction_models import InteractionResult


class EnsembleStrategy(InteractionStrategy):
    """
    Ensemble / Voting Strategy:
    Collects outputs from multiple agents and aggregates them
    via voting or an optional aggregator agent.
    """

    scenario_name = "ensemble"

    def __init__(
        self,
        agent_registry,
        message_bus: MessageBus | None = None,
        storage=None,
        vote_key: str = "final_answer",
        aggregator_agent: str | None = None,
    ):
        super().__init__(agent_registry, message_bus, storage)
        self.vote_key = vote_key
        self.aggregator_agent = aggregator_agent

    async def execute(self, request: InteractionRequest) -> InteractionResult:
        shared_context: dict[str, Any] = dict(request.context or {})
        votes: list[Any] = []
        results: list[AgentOutput] = []

        for agent_meta in request.agents:
            agent_name = agent_meta.agent_name
            agent_id = agent_meta.agent_id or f"ensemble:{agent_name}"

            output = await self._run_agent(
                agent_name=agent_name,
                agent_id=str(agent_id),
                context=shared_context,
                payload={
                    "shared_context": dict(shared_context),
                    "mode": "ensemble_vote",
                },
            )

            results.append(output)

            if output.error:
                shared_context.setdefault("errors", []).append(
                    {agent_name: output.error}
                )
                continue

            normalized = self._normalize_output(
                output.payload or output.message
            )

            vote_value = (
                normalized.get(self.vote_key, normalized)
                if isinstance(normalized, dict)
                else normalized
            )

            votes.append(vote_value)

            shared_context.setdefault("votes", []).append(
                {"agent": agent_name, "vote": vote_value}
            )

            await self._publish_vote(agent_name, str(agent_id), vote_value)

        final_vote = await self._aggregate_votes(votes, shared_context)

        overall_success = all(res.error is None for res in results)

        return InteractionResult(
            results=results,
            success=overall_success,
            final_context={
                **shared_context,
                "ensemble_vote": final_vote,
            },
            metadata={
                "vote_key": self.vote_key,
                "aggregator_agent": self.aggregator_agent,
            },
        )

    # ---------------------------------------------------------
    # Vote aggregation
    # ---------------------------------------------------------

    async def _aggregate_votes(
        self,
        votes: list[Any],
        shared_context: dict[str, Any],
    ) -> Any:

        if self.aggregator_agent:
            output = await self._run_agent(
                agent_name=self.aggregator_agent,
                agent_id=f"aggregator:{self.aggregator_agent}",
                context=shared_context,
                payload={
                    "votes": votes,
                    "shared_context": dict(shared_context),
                },
            )

            if output.error:
                shared_context.setdefault("aggregation_errors", []).append(output.error)
                return {"error": output.error}

            aggregated = output.payload or output.message
            shared_context["aggregator_output"] = aggregated
            return aggregated

        # Default: majority voting
        counter = Counter(votes)
        if not counter:
            return None

        most_common = counter.most_common(1)[0][0]
        shared_context["vote_summary"] = dict(counter)
        return most_common

    # ---------------------------------------------------------
    # Event publishing
    # ---------------------------------------------------------

    async def _publish_vote(self, agent_name: str, agent_id: str, vote: Any) -> None:
        if self.message_bus is None:
            return

        await self.message_bus.publish(
            AgentMessage(
                message_id=f"ensemble-{agent_id}",
                sender="EnsembleStrategy",
                recipient=agent_name,
                message_type="vote",
                payload={
                    "agent_id": agent_id,
                    "vote": vote,
                },
            )
        )

    # ---------------------------------------------------------
    # Output normalization
    # ---------------------------------------------------------

    @staticmethod
    def _normalize_output(output: Any) -> Any:
        if hasattr(output, "model_dump"):
            return output.model_dump()
        if hasattr(output, "dict"):
            return output.dict()
        if isinstance(output, dict):
            return output
        return {"value": output}
