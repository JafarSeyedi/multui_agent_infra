"""CMMN task execution strategies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CMMNTask:
    task_id: str
    task_type: str
    payload: dict[str, Any]


class CMMNTaskHandler:
    def execute(self, task: CMMNTask) -> dict[str, Any]:
        return {"task_id": task.task_id, "type": task.task_type, "status": "done", "payload": task.payload}
