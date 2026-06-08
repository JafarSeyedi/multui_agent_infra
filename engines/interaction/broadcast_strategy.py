# agents/orchestration/interaction/broadcast_strategy.py
import asyncio
from collections.abc import Iterable
from typing import Any

from ..agents.base_agents.base_agent import BaseAgent
from ..agents.models import AgentInput
from ..agents.models import AgentOutput
from .base_strategy import InteractionStrategy
from .interaction_models import InteractionRequest
from .interaction_models import InteractionResult


class BroadcastStrategy(InteractionStrategy):
    scenario_name = "broadcast"

    async def execute(self, request: InteractionRequest) -> InteractionResult:
        context: dict[str, Any] = dict(request.context or {})
        agents: list[BaseAgent] = request.agents or []

        if not agents:
            raise ValueError("BroadcastStrategy requires at least one agent.")

        mode = request.metadata.get("aggregator", "merge")

        coroutines = [self._execute_agent(agent, dict(context)) for agent in agents]
        raw_results = await asyncio.gather(*coroutines, return_exceptions=True)

        # ✅ Filter with _normalize_gather_results - broadcast error 28/29
        results: list[AgentOutput] = self._normalize_gather_results(raw_results)

        final_output = self._aggregate_outputs(results, mode)

        return InteractionResult(
            success=all(result.error is None for result in results),
            results=results,
            final_context={
                **context,
                "broadcast_output": final_output,
                "aggregation_mode": mode,
                "agent_count": len(results),
            },
        )

    async def _execute_agent(self, agent: BaseAgent, context_snapshot: dict[str, Any]) -> AgentOutput:

        await self._emit(
            message_type="broadcast_agent_started",
            payload={"agent_id": agent.agent_id, "agent": agent.agent_name},
            sender="BroadcastStrategy",
            recipient=agent.agent_name,
            message_id=f"broadcast_start_{agent.agent_id}",
        )

        agent_instance = self.agent_registry.get(agent.agent_name)

        if agent_instance is None:
            return AgentOutput(
                agent_id=agent.agent_id,
                agent_name=agent.agent_name,
                error=f"Agent '{agent.agent_name}' not found",
            )

        try:

            agent_input = AgentInput(
                agent_name=agent.agent_name,
                context=context_snapshot,
            )

            output: AgentOutput = await agent_instance.run(agent_input)

            await self._emit(
                message_type="broadcast_agent_completed",
                payload={"agent_id": agent.agent_id, "agent": agent.agent_name},
                sender="BroadcastStrategy",
                recipient=agent.agent_name,
                message_id=f"broadcast_done_{agent.agent_id}",
            )

            return output

        except Exception as exc:

            return AgentOutput(
                agent_id=agent.agent_id,
                agent_name=agent.agent_name,
                error=str(exc),
            )

    @staticmethod
    def _normalize_gather_results(results: Iterable[Any]) -> list[AgentOutput]:
        """✅ Fix assignment and extend error - convert Exception to AgentOutput"""
        normalized: list[AgentOutput] = []
        for item in results:
            if isinstance(item, AgentOutput):
                normalized.append(item)
            elif isinstance(item, BaseException):  # BaseException not just Exception
                normalized.append(
                    AgentOutput(
                        agent_id="unknown",
                        agent_name="unknown",
                        error=str(item),
                    )
                )
        return normalized

    def _aggregate_outputs(self, results: list[AgentOutput], mode: str) -> Any:

        successful = [r for r in results if r.error is None]

        if mode == "merge":
            return {
                res.agent_name: (res.payload or res.message)
                for res in successful
            }

        if mode == "list":
            return [
                {
                    "agent": res.agent_name,
                    "message": res.message,
                    "payload": res.payload,
                    "error": res.error,
                }
                for res in results
            ]

        if mode == "vote":

            votes: dict[str, int] = {}

            for res in successful:
                if isinstance(res.message, str):
                    votes[res.message] = votes.get(res.message, 0) + 1

            if not votes:
                return None

            return max(votes.items(), key=lambda kv: kv[1])[0]

        return [res.payload or res.message for res in successful]
