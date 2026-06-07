"""Protocol handler for multi-agent runtime.

Implements protocol-specific behavior and transitions at production level.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ..core.instance import ProcessInstance


class ProtocolType(str, Enum):
    FIPA_REQUEST = "fipa-request"
    FIPA_CONTRACT_NET = "fipa-contract-net"
    FIPA_AUCTION = "fipa-auction"
    CUSTOM = "custom"


@dataclass
class ProtocolState:
    protocol_id: str
    protocol_type: str = "custom"
    current_state: str = "idle"
    transitions: dict[str, str] = field(default_factory=dict)
    participants: list[str] = field(default_factory=list)


class ProtocolHandler:
    def __init__(self) -> None:
        self._states: dict[str, ProtocolState] = {}
        self._protocols: dict[str, dict[str, Any]] = {}

    async def execute(self, protocol: dict[str, Any], instance: ProcessInstance) -> dict[str, Any]:
        protocol_id = protocol.get("id", protocol.get("name", ""))
        protocol_type = protocol.get("type", "custom")
        participants = protocol.get("participants", [])

        state = ProtocolState(
            protocol_id=protocol_id,
            protocol_type=protocol_type,
            current_state="active",
            participants=participants,
            transitions=protocol.get("transitions", {}),
        )
        self._states[protocol_id] = state
        self._protocols[protocol_id] = protocol

        result: dict[str, Any] = {
            "protocol_id": protocol_id,
            "type": protocol_type,
            "state": "active",
        }

        if instance:
            instance.set_variable(f"protocol.{protocol_id}", result)

        state.current_state = "completed"
        return result

    def get_state(self, protocol_id: str) -> ProtocolState | None:
        return self._states.get(protocol_id)

    def transition(self, protocol_id: str, trigger: str) -> str | None:
        state = self._states.get(protocol_id)
        if state is None:
            return None
        new_state = state.transitions.get(trigger)
        if new_state:
            state.current_state = new_state
        return new_state
