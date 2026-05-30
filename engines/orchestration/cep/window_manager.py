"""Window abstraction for CEP event aggregation."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class TimeWindow:
    max_size: int
    ttl_seconds: int


class WindowManager:
    def __init__(self) -> None:
        self._windows: dict[str, deque[tuple[datetime, dict]]] = {}

    def push(self, window_id: str, event: dict, *, window: TimeWindow) -> list[dict]:
        now = datetime.utcnow()
        bucket = self._windows.setdefault(window_id, deque())
        bucket.append((now, dict(event)))
        cutoff = now - timedelta(seconds=window.ttl_seconds)
        while bucket and bucket[0][0] < cutoff:
            bucket.popleft()
        while len(bucket) > window.max_size:
            bucket.popleft()
        return [item[1] for item in bucket]
