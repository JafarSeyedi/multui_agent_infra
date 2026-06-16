# engines/consistency/models/parsers/consistency_parser.py
from __future__ import annotations

from ..consistency_models import IdempotencyRecord


def parse_idempotency_record(data: dict) -> IdempotencyRecord:
    return IdempotencyRecord(
        key=data["key"],
        processed=data.get("processed", False),
        result=data.get("result"),
    )
