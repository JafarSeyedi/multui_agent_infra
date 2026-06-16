# engines/provenance/models/writers/provenance_writer.py
from __future__ import annotations

from ..provenance_models import ProvenanceEvent


def write_provenance_event(event: ProvenanceEvent) -> dict:
    return {
        "event_id": event.event_id,
        "entity_id": event.entity_id,
        "action": event.action,
        "actor": event.actor,
        "metadata": event.metadata,
    }
