"""State entry/exit action execution."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ActionExecutionError(RuntimeError):
    pass


class ActionExecutor:
    def run(self, action: str) -> None:
        if not callable(action):
            return
        action()
