# engines/config/models/parsers/config_yaml_parser.py
from __future__ import annotations

from ..config_models import ConfigEntry


def parse_config_entry(data: dict) -> ConfigEntry:
    return ConfigEntry(key=data["key"], value=data.get("value"), source=data.get("source", ""))
