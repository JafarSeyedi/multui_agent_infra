"""User task adapter."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable


@dataclass(frozen=True)
class UserTaskAdapter:
    callback: Callable[[str, dict[str, object]], dict[str, object]]

    def assign(self, task_id: str, payload: dict[str, object]) -> dict[str, object]:
        return self.callback(task_id, payload)

    def complete(self, task_id: str, output: dict[str, object] | None = None) -> dict[str, object]:
        return {
            "task_id": task_id,
            "status": "completed",
            "output": output or {},
            "completed_at": datetime.utcnow().isoformat(),
        }
