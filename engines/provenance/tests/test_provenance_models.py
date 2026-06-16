# engines/provenance/tests/test_provenance_models.py
from engines.provenance.models.provenance_models import ProvenanceEvent
from engines.provenance.models.parsers.provenance_parser import parse_provenance_event
from engines.provenance.models.writers.provenance_writer import write_provenance_event


def test_provenance_event():
    evt = ProvenanceEvent(entity_id="doc-1", action="created", actor="alice")
    assert evt.action == "created"


def test_provenance_roundtrip():
    evt = ProvenanceEvent(event_id="e1", entity_id="doc-1", action="updated", actor="bob", metadata={"reason": "review"})
    data = write_provenance_event(evt)
    parsed = parse_provenance_event(data)
    assert parsed.actor == "bob"
    assert parsed.metadata["reason"] == "review"
