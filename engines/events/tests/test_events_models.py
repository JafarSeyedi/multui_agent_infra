# engines/events/tests/test_events_models.py
from engines.events.models.events_models import EventRecord
from engines.events.models.parsers.events_parser import parse_event_record
from engines.events.models.writers.events_writer import write_event_record


def test_event_record():
    rec = EventRecord(topic="order.created", data={"order_id": "123"})
    assert rec.topic == "order.created"


def test_event_roundtrip():
    rec = EventRecord(topic="t", data={"k": "v"}, event_id="evt-1")
    data = write_event_record(rec)
    parsed = parse_event_record(data)
    assert parsed.topic == "t"
    assert parsed.data["k"] == "v"
    assert parsed.event_id == "evt-1"
