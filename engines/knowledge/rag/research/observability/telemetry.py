from __future__ import annotations

import time
from abc import ABC
from typing import Any

class TelemetryEvent(ABC):
    def __init__(self, name: str, payload: dict[str, Any]):
        self.name = name
        self.payload = payload
        self.timestamp = time.time()

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "payload": self.payload, "timestamp": self.timestamp}


class Telemetry(ABC):
    def __init__(self, collector):
        self.collector = collector

    def emit(self, name: str, payload: dict[str, Any]):
        event = TelemetryEvent(name, payload)
        self.collector.collect(event)
        return event
