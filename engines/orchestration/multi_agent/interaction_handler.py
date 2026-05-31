"""Interaction handler for multi-agent runtime.

Manages interaction state and OSDM interaction model semantics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ...core.instance import ProcessInstance


@dataclass
class InteractionState:
    interaction_id: str
    participants: list[str] = field(default_factory=list)
    messages: list[dict[str, Any]] = field(default_factory=list)
    state: str = "pending"
    current_turn: str | None = None


class InteractionHandler:
    def __init__(self) -> None:
        self._states: dict[str, InteractionState] = {}

    async def handle(
        self,
        interaction: dict[str, Any],
        instance: ProcessInstance,
        agents: list[dict[str, Any]],
    ) -> dict[str, Any]:
        interaction_id = interaction.get("id", f"interaction_{id(interaction)}")
        interaction_type = interaction.get("type", "message")
        participants = interaction.get("participants", [a.get("id", "") for a in agents])

        state = InteractionState(
            interaction_id=interaction_id,
            participants=participants,
            state="active",
            current_turn=participants[0] if participants else None,
        )
        self._states[interaction_id] = state

        result: dict[str, Any] = {
            "interaction_id": interaction_id,
            "type": interaction_type,
            "participants": participants,
            "status": "completed",
        }

        messages = interaction.get("messages", [])
        for msg in messages:
            state.messages.append(msg)
            if state.current_turn == msg.get("from"):
                for p in participants:
                    if p != msg.get("from"):
                        state.current_turn = p
                        break

        state.state = "completed"
        return result

    def get_state(self, interaction_id: str) -> InteractionState | None:
        return self._states.get(interaction_id)

    def list_states(self) -> list[str]:
        return list(self._states.keys())
