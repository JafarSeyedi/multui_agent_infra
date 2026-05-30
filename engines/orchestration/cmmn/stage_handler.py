"""Stage lifecycle management for CMMN."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Stage:
    stage_id: str
    tasks: list[str]


class StageHandler:
    def activate(self, stage: Stage) -> dict[str, Any]:
        return {"stage_id": stage.stage_id, "status": "active", "tasks": stage.tasks}

    def complete(self, stage: Stage) -> dict[str, Any]:
        return {"stage_id": stage.stage_id, "status": "completed"}
