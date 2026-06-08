from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from ..agents.base_agents.base_agent import BaseAgent
from ..agents.models import AgentOutput
from .base_strategy import InteractionStrategy
from .interaction_models import InteractionRequest
from .interaction_models import InteractionResult
from engines.communication.buses.base_message_bus import MessageBus


class CoordinatorStrategy(InteractionStrategy):

    scenario_name = "manager"

    def __init__(
        self,
        agent_registry,
        message_bus: MessageBus | None = None,
        storage=None,
        validation_agent: str | None = None,
        aggregator_agent: str | None = None,
    ):
        super().__init__(agent_registry, message_bus, storage)
        self.validation_agent = validation_agent
        self.aggregator_agent = aggregator_agent

    async def execute(self, request: InteractionRequest) -> InteractionResult:

        shared_context: dict[str, Any] = dict(request.context)
        results: list[AgentOutput] = []

        worker_agents: Sequence[BaseAgent] = request.agents

        if not worker_agents:
            return InteractionResult(
                results=[],
                success=True,
                final_context=shared_context,
                metadata={"note": "coordinator received no agents"},
            )

        for agent in worker_agents:

            agent_id = str(agent.agent_id)
            agent_name = str(agent.agent_name)

            payload = {
                "shared_context": dict(shared_context)
            }

            output = await self._run_agent(
                agent_name=agent_name,
                agent_id=agent_id,
                context=shared_context,
                payload=payload,
            )

            results.append(output)

            if output.error is None:
                shared_context.setdefault("worker_outputs", {})[agent_name] = (
                    output.payload or output.message
                )
            else:
                shared_context.setdefault("errors", []).append(
                    {agent_name: output.error}
                )

            await self._publish_turn_message(
                agent_name,
                agent_id,
                payload,
                output.payload or output.message,
            )

        if self.validation_agent:
            await self._run_validation(shared_context, results)

        final_payload = await self._aggregate(shared_context, results)

        overall_success = all(res.error is None for res in results)

        return InteractionResult(
            results=results,
            success=overall_success,
            final_context={**shared_context, "final_payload": final_payload},
            metadata={
                "validation_agent": self.validation_agent,
                "aggregator_agent": self.aggregator_agent,
            },
        )

    async def _run_validation(self, shared_context: dict[str, Any], results: list[AgentOutput]) -> None:
        if not self.validation_agent:
            return
        payload = {
            "worker_results": [res.model_dump() for res in results],
            "shared_context": dict(shared_context),
        }

        output = await self._run_agent(
            agent_name=self.validation_agent,
            agent_id=f"validator:{self.validation_agent}",
            context=shared_context,
            payload=payload,
        )

        if output.error is None:
            shared_context["validation"] = output.payload or output.message
        else:
            shared_context.setdefault("validation_errors", []).append(output.error)

    async def _aggregate(self, shared_context: dict[str, Any], results: list[AgentOutput]) -> Any:

        if not self.aggregator_agent:
            return shared_context.get("worker_outputs", {})

        payload = {
            "worker_results": [res.model_dump() for res in results],
            "shared_context": dict(shared_context),
        }

        output = await self._run_agent(
            agent_name=self.aggregator_agent,
            agent_id=f"aggregator:{self.aggregator_agent}",
            context=shared_context,
            payload=payload,
        )

        if output.error is None:
            aggregated = output.payload or output.message
            shared_context["aggregated_result"] = aggregated
            return aggregated

        shared_context.setdefault("aggregation_errors", []).append(output.error)

        return {"error": output.error}

    async def _publish_turn_message(
        self,
        agent_name: str,
        agent_id: str,
        input_payload: dict[str, Any],
        output_payload: Any,
    ) -> None:

        await self._emit(
            message_type="agent_result",
            payload={
                "agent_id": agent_id,
                "input": input_payload,
                "output": output_payload,
            },
            sender="CoordinatorStrategy",
            recipient=agent_name,
            message_id=f"manager-{agent_id}",
        )
