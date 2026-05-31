"""Milestone support for case management.

Supports milestone state, criteria, and auditing at CMMN 1.1 level.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ...core.instance import ProcessInstance


class MilestoneState(str, Enum):
    AVAILABLE = "available"
    ACTIVE = "active"
    ACHIEVED = "achieved"
    SUSPENDED = "suspended"


@dataclass
class Milestone:
    milestone_id: str
    name: str | None = None
    reached: bool = False
    state: str = MilestoneState.AVAILABLE.value
    entry_criteria: list[dict[str, Any]] = field(default_factory=list)
    achievement_date: str | None = None
    audit_log: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class MilestoneAuditEntry:
    milestone_id: str
    action: str
    timestamp: str
    instance_id: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


class MilestoneHandler:
    def __init__(self) -> None:
        self._milestones: dict[str, Milestone] = {}
        self._audit_log: list[MilestoneAuditEntry] = []

    def register(self, milestone: Milestone) -> None:
        self._milestones[milestone.milestone_id] = milestone

    def get_milestone(self, milestone_id: str) -> Milestone | None:
        return self._milestones.get(milestone_id)

    def set_reached(self, milestone: Milestone, instance: ProcessInstance | None = None) -> Milestone:
        milestone.reached = True
        milestone.state = MilestoneState.ACHIEVED.value
        from datetime import datetime
        milestone.achievement_date = datetime.utcnow().isoformat()

        entry = MilestoneAuditEntry(
            milestone_id=milestone.milestone_id,
            action="achieved",
            timestamp=milestone.achievement_date,
            instance_id=instance.id if instance else None,
        )
        self._audit_log.append(entry)
        milestone.audit_log.append({
            "action": "achieved",
            "timestamp": milestone.achievement_date,
        })

        if instance:
            instance.set_variable(f"milestone.{milestone.milestone_id}.achieved", True)
            instance.set_variable(f"milestone.{milestone.milestone_id}.date", milestone.achievement_date)

        self._milestones[milestone.milestone_id] = milestone
        return milestone

    def evaluate(self, milestones: list[Milestone], instance: ProcessInstance | None = None) -> list[Milestone]:
        result: list[Milestone] = []
        for m in milestones:
            if not m.reached:
                m = self.set_reached(m, instance)
            result.append(m)
        return result

    def is_achieved(self, milestone_id: str) -> bool:
        m = self._milestones.get(milestone_id)
        return m is not None and m.reached

    def get_achieved_milestones(self) -> list[Milestone]:
        return [m for m in self._milestones.values() if m.reached]

    def get_pending_milestones(self) -> list[Milestone]:
        return [m for m in self._milestones.values() if not m.reached]

    def get_audit_log(self, milestone_id: str | None = None) -> list[MilestoneAuditEntry]:
        if milestone_id is None:
            return list(self._audit_log)
        return [e for e in self._audit_log if e.milestone_id == milestone_id]

    def get_summary(self) -> dict[str, Any]:
        total = len(self._milestones)
        achieved = sum(1 for m in self._milestones.values() if m.reached)
        return {
            "total": total,
            "achieved": achieved,
            "pending": total - achieved,
        }
