from __future__ import annotations

import time
from typing import Any, Dict


class TelemetryEvent:
    def __init__(self, name: str, payload: Dict[str, Any]):
        self.name = name
        self.payload = payload
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "payload": self.payload, "timestamp": self.timestamp}


class Telemetry:
    def __init__(self, collector):
        self.collector = collector

    def emit(self, name: str, payload: Dict[str, Any]):
        event = TelemetryEvent(name, payload)
        self.collector.collect(event)
        return event
