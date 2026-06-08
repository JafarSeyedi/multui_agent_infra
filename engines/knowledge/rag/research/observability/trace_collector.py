from __future__ import annotations

from collections import deque
from collections.abc import Iterable

from .telemetry import TelemetryEvent


class TraceCollector:
    def __init__(self, max_traces: int = 10000) -> None:
        self.events: deque[TelemetryEvent] = deque(maxlen=max_traces)  # ← explicit deque type

    def collect(self, event: TelemetryEvent) -> None:
        self.events.append(event)

    def extend(self, events: Iterable[TelemetryEvent]) -> None:
        for event in events:
            self.collect(event)

    def get_recent(self, n: int = 100) -> list[TelemetryEvent]:
        return list(self.events)[-n:]

    def clear(self) -> None:
        self.events.clear()
