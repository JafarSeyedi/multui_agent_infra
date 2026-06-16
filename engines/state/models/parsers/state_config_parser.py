# engines/state/models/parsers/state_config_parser.py
from __future__ import annotations

from ..state_models import StateEntry


def parse_state_entry(data: dict) -> StateEntry:
    return StateEntry(
        instance_id=data["instance_id"],
        data=data.get("data", {}),
        version=data.get("version", 1),
    )
