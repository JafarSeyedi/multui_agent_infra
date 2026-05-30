"""Protocol handlers for request/response and evented interactions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class ProtocolStep:
    name: str
    payload: dict[str, Any]


class ProtocolHandler:
    def execute(self, steps: Iterable[ProtocolStep]) -> list[str]:
        return [step.name for step in steps]
