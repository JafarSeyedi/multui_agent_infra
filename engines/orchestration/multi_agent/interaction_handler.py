"""Interaction lifecycle for protocol-driven multi-agent coordination."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Interaction:
    interaction_id: str
    participants: list[str]


class InteractionHandler:
    def start(self, interaction: Interaction) -> None:
        _ = interaction

    def complete(self, interaction: Interaction) -> None:
        _ = interaction
