"""Event persistence repository used for audit and replay."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from ..runtime.runtime_records import EVENT_RECORD
from .repository import PersistentRuntimeRepository


class EventRepository(PersistentRuntimeRepository):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            record_type=EVENT_RECORD,
            key_prefix="orchestration:events:",
            measurement="orchestration_events",
            **kwargs,
        )

    def append(self, event: dict[str, Any]) -> None:
        payload = dict(event)
        payload.setdefault("recorded_at", datetime.utcnow().isoformat())
        key = payload.get("event_id") or f"{payload.get('type', 'event')}:{payload['recorded_at']}"
        super().save(str(key), payload)

    async def append_persisted(self, event: dict[str, Any]) -> dict[str, Any]:
        payload = dict(event)
        payload.setdefault("recorded_at", datetime.utcnow().isoformat())
        payload.setdefault("event_type", payload.get("type", "event"))
        key = str(payload.get("event_id") or f"{payload.get('event_type', 'event')}:{payload['recorded_at']}")
        return await self.save_persisted(key, payload)

    def by_correlation(self, correlation_id: str) -> list[dict[str, Any]]:
        return self.list(predicate=lambda row: row.get("correlation_id") == correlation_id)
