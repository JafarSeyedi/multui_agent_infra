"""Choreography-oriented BPMN handler."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ChoreographyStep:
    choreography_id: str
    participants: list[str]


class ChoreographyHandler:
    def execute(self, step: ChoreographyStep, context: dict[str, Any]) -> dict[str, Any]:
        return {"choreography_id": step.choreography_id, "participants": step.participants, "context": dict(context)}
