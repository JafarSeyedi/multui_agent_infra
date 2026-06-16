# engines/provenance/models/parsers/provenance_parser.py
from __future__ import annotations

from ..provenance_models import ProvenanceEvent


def parse_provenance_event(data: dict) -> ProvenanceEvent:
    return ProvenanceEvent(
        event_id=data.get("event_id", ""),
        entity_id=data.get("entity_id", ""),
        action=data.get("action", ""),
        actor=data.get("actor", ""),
        metadata=data.get("metadata", {}),
    )
