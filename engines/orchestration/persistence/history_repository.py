"""Execution history persistence."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from ..runtime.runtime_records import AUDIT_RECORD
from .repository import PersistentRuntimeRepository


class HistoryRepository(PersistentRuntimeRepository):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            record_type=AUDIT_RECORD,
            key_prefix="orchestration:history:",
            measurement="orchestration_history",
            **kwargs,
        )

    def append(self, instance_id: str, data: dict[str, Any]) -> None:
        payload = dict(data)
        payload.setdefault("instance_id", instance_id)
        payload.setdefault("created_at", datetime.utcnow().isoformat())
        super().save(f"{instance_id}:{payload['created_at']}", payload)

    async def append_persisted(self, instance_id: str, data: dict[str, Any]) -> dict[str, Any]:
        payload = dict(data)
        payload.setdefault("instance_id", instance_id)
        payload.setdefault("created_at", datetime.utcnow().isoformat())
        payload.setdefault("action", payload.get("action", "history.append"))
        key = f"{instance_id}:{payload['created_at']}"
        return await self.save_persisted(key, payload)

    def query(self, instance_id: str) -> list[dict[str, Any]]:
        rows = self.list(predicate=lambda row: row.get("instance_id") == instance_id)
        return sorted(rows, key=lambda item: item.get("created_at", ""))
