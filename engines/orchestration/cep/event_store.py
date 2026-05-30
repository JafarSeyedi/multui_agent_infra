"""In-memory event store used by CEP runtime."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from threading import Lock


@dataclass(frozen=True)
class StoredEvent:
    event_id: str
    event_type: str
    payload: dict
    occurred_at: datetime


class EventStore:
    def __init__(self) -> None:
        self._events: list[StoredEvent] = []
        self._lock = Lock()

    def append(self, event_id: str, event_type: str, payload: dict) -> None:
        with self._lock:
            self._events.append(StoredEvent(event_id, event_type, payload, datetime.utcnow()))

    def query(self, *, event_type: str | None = None, limit: int | None = None) -> list[StoredEvent]:
        with self._lock:
            events = [e for e in self._events if event_type is None or e.event_type == event_type]
            if limit:
                events = events[-limit:]
            return list(events)

    def clear(self) -> None:
        with self._lock:
            self._events.clear()
