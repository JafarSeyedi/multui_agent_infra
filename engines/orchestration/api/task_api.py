"""Task-level API for completing and querying tasks."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..core.instance import ProcessInstance


@dataclass(frozen=True)
class TaskAPI:
    instance: ProcessInstance

    def complete_activity(self, activity_id: str, payload: dict[str, object] | None = None) -> dict[str, object]:
        self.instance.set_variable("_last_activity_payload", {"activity_id": activity_id, "payload": payload or {}, "completed_at": datetime.utcnow().isoformat()})
        return {"activity_id": activity_id, "status": "completed"}

    def active_activity(self) -> str | None:
        return self.instance.current_activity_id

    def variables(self) -> dict[str, object]:
        return self.instance.get_all_variables()
