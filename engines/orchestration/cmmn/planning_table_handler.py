"""Planning table execution support."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PlanningEntry:
    entry_id: str
    order: int


class PlanningTableHandler:
    def resolve(self, entries: list[PlanningEntry]) -> list[PlanningEntry]:
        return sorted(entries, key=lambda item: item.order)
