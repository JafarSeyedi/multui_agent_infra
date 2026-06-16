# engines/provenance/backends/in_memory/in_memory_provenance.py
from __future__ import annotations

import uuid
from typing import Any

from ...models.provenance_models import ProvenanceEvent
from ...plugin import IProvenanceTracker


class InMemoryProvenanceTracker(IProvenanceTracker):
    name = "in_memory"

    def __init__(self) -> None:
        self._events: list[ProvenanceEvent] = []

    async def record(self, entity_id: str, action: str, actor: str, metadata: dict[str, Any] | None = None) -> str:
        event_id = str(uuid.uuid4())
        self._events.append(ProvenanceEvent(
            event_id=event_id, entity_id=entity_id, action=action, actor=actor, metadata=metadata or {}
        ))
        return event_id

    async def get_lineage(self, entity_id: str) -> list[dict[str, Any]]:
        return [
            {"event_id": e.event_id, "action": e.action, "actor": e.actor, "metadata": e.metadata}
            for e in self._events
            if e.entity_id == entity_id
        ]
