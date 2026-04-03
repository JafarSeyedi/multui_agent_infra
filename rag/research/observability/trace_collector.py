from __future__ import annotations

from collections import deque
from typing import Iterable, List


class TraceCollector:
    def __init__(self, max_traces: int = 10000):
        self.events = deque(maxlen=max_traces)

    def collect(self, event) -> None:
        self.events.append(event)

    def extend(self, events: Iterable) -> None:
        for event in events:
            self.collect(event)

    def get_recent(self, n: int = 100) -> List:
        return list(self.events)[-n:]

    def clear(self) -> None:
        self.events.clear()
