"""CEP event store with persistence.

Persists/queries event streams in time-series/event-log storage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class StoredEvent:
    event_id: str
    event_type: str
    payload: dict[str, Any]
    timestamp: str
    instance_id: str


class CEPEventStore:
    def __init__(self) -> None:
        self._events: list[StoredEvent] = []

    def store(
        self,
        instance_id: str,
        event_id: str,
        event_type: str,
        payload: dict[str, Any],
        timestamp: str | None = None,
    ) -> StoredEvent:
        ts = timestamp or datetime.utcnow().isoformat()
        event = StoredEvent(
            event_id=event_id,
            event_type=event_type,
            payload=payload,
            timestamp=ts,
            instance_id=instance_id,
        )
        self._events.append(event)
        return event

    def query(
        self,
        instance_id: str | None = None,
        event_type: str | None = None,
        since: str | None = None,
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for evt in self._events:
            if instance_id and evt.instance_id != instance_id:
                continue
            if event_type and evt.event_type != event_type:
                continue
            if since and evt.timestamp < since:
                continue
            results.append({
                "id": evt.event_id,
                "type": evt.event_type,
                "timestamp": evt.timestamp,
                "instance_id": evt.instance_id,
                "payload": evt.payload,
            })
        return results

    def get_by_instance(self, instance_id: str) -> list[dict[str, Any]]:
        return self.query(instance_id=instance_id)

    def get_by_type(self, event_type: str) -> list[dict[str, Any]]:
        return self.query(event_type=event_type)

    def count(self, instance_id: str | None = None) -> int:
        if instance_id:
            return sum(1 for e in self._events if e.instance_id == instance_id)
        return len(self._events)

    def clear(self, instance_id: str | None = None) -> int:
        if instance_id:
            before = len(self._events)
            self._events = [e for e in self._events if e.instance_id != instance_id]
            return before - len(self._events)
        count = len(self._events)
        self._events.clear()
        return count
