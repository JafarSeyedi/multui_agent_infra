"""Milestone support for case management."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Milestone:
    milestone_id: str
    reached: bool = False


class MilestoneHandler:
    def set_reached(self, milestone: Milestone) -> Milestone:
        return Milestone(milestone_id=milestone.milestone_id, reached=True)

    def evaluate(self, milestones: list[Milestone]) -> list[Milestone]:
        return [self.set_reached(m) for m in milestones]
