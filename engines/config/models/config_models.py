# engines/config/models/config_models.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConfigEntry:
    key: str
    value: Any = None
    source: str = ""


@dataclass
class SecretRef:
    ref: str
    resolver: str = "environment"
