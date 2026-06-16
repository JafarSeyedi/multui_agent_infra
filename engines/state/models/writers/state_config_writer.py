# engines/state/models/writers/state_config_writer.py
from __future__ import annotations

from ..state_models import StateEntry


def write_state_entry(entry: StateEntry) -> dict:
    return {
        "instance_id": entry.instance_id,
        "data": entry.data,
        "version": entry.version,
    }
