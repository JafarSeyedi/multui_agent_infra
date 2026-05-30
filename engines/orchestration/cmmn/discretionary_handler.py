"""Discretionary item operations for CMMN."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DiscretionaryTask:
    task_id: str
    name: str
    payload: dict[str, Any]


class DiscretionaryHandler:
    def choose(self, candidates: list[DiscretionaryTask]) -> list[str]:
        return [task.task_id for task in candidates]
