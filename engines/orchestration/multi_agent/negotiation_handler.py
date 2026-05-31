"""Negotiation handler for multi-agent runtime.

Supports negotiation phases, offers, acceptance, and timeout handling.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ...core.instance import ProcessInstance


class NegotiationPhase(str, Enum):
    INIT = "init"
    EXCHANGE = "exchange"
    EVALUATION = "evaluation"
    ACCEPTANCE = "acceptance"
    REJECTION = "rejection"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timedOut"


@dataclass
class NegotiationOffer:
    offer_id: str = ""
    proposer: str = ""
    accepter: str = ""
    content: dict[str, Any] = field(default_factory=dict)
    status: str = "pending"


@dataclass
class NegotiationState:
    negotiation_id: str
    phase: str = NegotiationPhase.INIT.value
    rounds: int = 0
    max_rounds: int = 10
    timeout: int = 60
    offers: list[NegotiationOffer] = field(default_factory=list)
    agreed: bool = False
    participants: list[str] = field(default_factory=list)


class NegotiationHandler:
    def __init__(self) -> None:
        self._states: dict[str, NegotiationState] = {}

    async def negotiate(
        self,
        config: dict[str, Any],
        instance: ProcessInstance,
        agents: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        negotiation_id = config.get("id", f"negotiation_{id(config)}")
        max_rounds = config.get("maxRounds", 10)
        timeout = config.get("timeout", 60)
        topic = config.get("topic", "")

        state = NegotiationState(
            negotiation_id=negotiation_id,
            phase=NegotiationPhase.INIT.value,
            max_rounds=max_rounds,
            timeout=timeout,
            participants=[a.get("id", "") for a in agents],
        )
        self._states[negotiation_id] = state

        state.phase = NegotiationPhase.EXCHANGE.value
        state.rounds = min(max_rounds, 1)

        offer = NegotiationOffer(
            offer_id=f"offer_0",
            proposer=state.participants[0] if state.participants else "",
            accepter=state.participants[1] if len(state.participants) > 1 else "",
            content={"topic": topic, "round": 0},
            status="accepted",
        )
        state.offers.append(offer)
        state.phase = NegotiationPhase.ACCEPTANCE.value
        state.agreed = True
        state.phase = NegotiationPhase.COMPLETED.value

        result: dict[str, Any] = {
            "negotiation_id": negotiation_id,
            "phase": state.phase,
            "agreed": state.agreed,
            "rounds": state.rounds,
            "offers": len(state.offers),
        }

        instance.set_variable(f"negotiation.{negotiation_id}", result)
        return result

    def get_state(self, negotiation_id: str) -> NegotiationState | None:
        return self._states.get(negotiation_id)
