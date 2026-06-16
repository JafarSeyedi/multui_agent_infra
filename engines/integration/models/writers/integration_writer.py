# engines/integration/models/writers/integration_writer.py
from __future__ import annotations

from ..integration_models import SyncResult


def write_sync_result(result: SyncResult) -> dict:
    return {
        "success_count": result.success_count,
        "failure_count": result.failure_count,
        "errors": result.errors,
    }
