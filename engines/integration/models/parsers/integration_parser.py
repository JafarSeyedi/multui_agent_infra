# engines/integration/models/parsers/integration_parser.py
from __future__ import annotations

from ..integration_models import ConnectionConfig


def parse_connection_config(data: dict) -> ConnectionConfig:
    return ConnectionConfig(
        endpoint=data.get("endpoint", ""),
        credentials=data.get("credentials", {}),
        options=data.get("options", {}),
    )
