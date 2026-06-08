from __future__ import annotations

from typing import Any

from ..agents.models import AgentOutput
from ..buses.base_message_bus import MessageBus
from .base_strategy import InteractionStrategy
from .interaction_models import InteractionRequest
from .interaction_models import InteractionResult


class RoundRobinStrategy(InteractionStrategy):
    """
    Round Robin Strategy (Turn-Taking).
    Agent execution order is based on the input list and performed periodically (Rounds).
    """

    scenario_name = "round_robin"

    def __init__(
        self,
        agent_registry,
        message_bus: MessageBus | None = None,
        storage = None,
        default_rounds: int = 1
    ):
        super().__init__(agent_registry, message_bus, storage)
        self.default_rounds = max(1, default_rounds)

    async def execute(self, request: InteractionRequest) -> InteractionResult:
        agents = request.agents
        if not agents:
            return InteractionResult(
                results=[],
                success=True,
                final_context=dict(request.context),
                metadata={"note": "No agents provided for round robin strategy."},
            )

        # Extract settings from metadata
        max_rounds = int(request.metadata.get("rounds", self.default_rounds))
        max_rounds = max(1, max_rounds)
        stop_on_failure = bool(request.metadata.get("stop_on_failure", False))

        # Memory and context management
        history: list[dict[str, Any]] = list(request.context.get("history", []))
        shared_context: dict[str, Any] = dict(request.context)
        results: list[AgentOutput] = []

        for round_index in range(max_rounds):
            shared_context["current_round"] = round_index

            for turn_index, agent_spec in enumerate(agents, start=1):
                agent_id = agent_spec.agent_id or f"{agent_spec.agent_name}_{round_index}_{turn_index}"

                # Prepare Payload for sending to agent
                execution_payload = {
                    "history": list(history),
                    "round_index": round_index,
                    "turn_index": turn_index,
                    "total_rounds": max_rounds
                }

                # Execute agent via standard base layer method
                output = await self._run_agent(
                    agent_name=agent_spec.agent_name,
                    agent_id=agent_id,
                    payload=execution_payload,
                    context=shared_context
                )

                results.append(output)

                # Check for errors
                if output.error:
                    error_entry = {
                        "agent": agent_spec.agent_name,
                        "round": round_index,
                        "turn": turn_index,
                        "error": output.error
                    }
                    history.append(error_entry)
                    shared_context["last_error"] = output.error

                    if stop_on_failure:
                        return InteractionResult(
                            results=results,
                            success=False,
                            final_context=shared_context,
                            metadata={
                                "stopped_on_failure": True,
                                "failed_agent": agent_spec.agent_name,
                                "round": round_index
                            }
                        )
                else:
                    # On success, add output to history and context
                    agent_data = output.payload or {"message": output.message}

                    history_entry = {
                        "agent": agent_spec.agent_name,
                        "agent_id": agent_id,
                        "round": round_index,
                        "turn": turn_index,
                        "output": agent_data,
                    }
                    history.append(history_entry)

                    # Record output in context for other layers to access
                    shared_context[f"round_{round_index}_{agent_spec.agent_name}"] = agent_data

                # Notify on Bus
                await self._emit(
                    message_type="turn_completed",
                    payload={
                        "round": round_index,
                        "agent": agent_spec.agent_name,
                        "success": output.error is None
                    },
                    sender="RoundRobinStrategy",
                    recipient=agent_spec.agent_name,
                    message_id=f"broadcast_start_{agent_id}",
                )

        # Calculate overall success: if no agent had errors
        overall_success = all(res.error is None for res in results)

        final_context = dict(shared_context)
        final_context["history"] = history

        return InteractionResult(
            results=results,
            success=overall_success,
            final_context=final_context,
            metadata={
                "rounds_executed": max_rounds,
                "history_length": len(history),
                "agents_involved": [a.agent_name for a in agents],
            },
        )
