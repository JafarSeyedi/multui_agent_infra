# engines/consistency/models/writers/consistency_writer.py
from __future__ import annotations

from ..consistency_models import IdempotencyRecord


def write_idempotency_record(record: IdempotencyRecord) -> dict:
    return {"key": record.key, "processed": record.processed, "result": record.result}
