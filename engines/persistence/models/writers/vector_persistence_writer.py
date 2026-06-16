# engines/persistence/models/writers/vector_persistence_writer.py
from __future__ import annotations

from ..persistence_models import VectorRecord


def write_vector_record(record: VectorRecord) -> dict:
    return {
        "collection": record.collection,
        "id": record.id,
        "vector": record.vector,
        "metadata": record.metadata,
    }
