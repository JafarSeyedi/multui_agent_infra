"""Parallel state handling for orthogonal regions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ParallelRegion:
    region_id: str
    active_states: list[str]


class ParallelStateHandler:
    def execute(self, regions: list[ParallelRegion], context: dict[str, Any]) -> list[str]:
        return [state for region in regions for state in region.active_states]
