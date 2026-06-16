# engines/persistence/models/parsers/vector_persistence_parser.py
from __future__ import annotations

from ..persistence_models import VectorRecord


def parse_vector_record(data: dict) -> VectorRecord:
    return VectorRecord(
        collection=data["collection"],
        id=data["id"],
        vector=data.get("vector", []),
        metadata=data.get("metadata", {}),
    )
