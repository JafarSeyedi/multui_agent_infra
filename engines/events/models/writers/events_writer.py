# engines/events/models/writers/events_writer.py
from __future__ import annotations

from ..events_models import EventRecord


def write_event_record(record: EventRecord) -> dict:
    return {"topic": record.topic, "data": record.data, "event_id": record.event_id}
