"""BPMN event handlers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BPMNEvent:
    event_id: str
    event_type: str
    payload: dict[str, Any]


class EventHandler:
    def start(self, event: BPMNEvent) -> None:
        _ = (event.event_id, event.event_type, event.payload)

    def end(self, event: BPMNEvent) -> None:
        _ = (event.event_id, event.event_type, event.payload)

    def signal(self, event: BPMNEvent) -> None:
        _ = (event.event_id, event.event_type, event.payload)
