"""Transition resolution for state machine execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .guard_evaluator import GuardEvaluator


@dataclass(frozen=True)
class Transition:
    source: str
    target: str
    event: str | None = None
    guard: str | None = None


class TransitionHandler:
    def __init__(self) -> None:
        self.guard_evaluator = GuardEvaluator()

    def resolve(self, current: str | None, transitions: list[dict[str, Any]], context: dict[str, Any]) -> dict[str, Any] | None:
        for transition in transitions:
            if transition.get("source") != current:
                continue
            condition = transition.get("guard")
            if condition and not self.guard_evaluator.evaluate(condition, context):
                continue
            return transition
        return None
