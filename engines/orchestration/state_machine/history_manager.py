"""History state management for state machine execution."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StateMachineHistory:
    visited: list[str]

    def __init__(self) -> None:
        self.visited = []

    def record(self, state_id: str) -> None:
        self.visited.append(state_id)

    def clear(self) -> None:
        self.visited.clear()
