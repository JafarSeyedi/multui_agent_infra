# engines/config/models/writers/config_yaml_writer.py
from __future__ import annotations

from ..config_models import ConfigEntry


def write_config_entry(entry: ConfigEntry) -> dict:
    return {"key": entry.key, "value": entry.value, "source": entry.source}
