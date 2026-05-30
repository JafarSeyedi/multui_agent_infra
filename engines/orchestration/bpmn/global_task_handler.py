"""Global task execution helper for BPMN global tasks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GlobalTask:
    task_id: str
    payload: dict[str, Any]


class GlobalTaskHandler:
    def execute(self, task: GlobalTask) -> dict[str, Any]:
        return {"task_id": task.task_id, "status": "executed", "payload": task.payload}
