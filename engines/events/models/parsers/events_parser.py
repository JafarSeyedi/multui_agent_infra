# engines/events/models/parsers/events_parser.py
from __future__ import annotations

from ..events_models import EventRecord


def parse_event_record(data: dict) -> EventRecord:
    return EventRecord(
        topic=data["topic"],
        data=data.get("data", {}),
        event_id=data.get("event_id", ""),
    )
