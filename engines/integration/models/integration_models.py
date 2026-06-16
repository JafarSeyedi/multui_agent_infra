# engines/integration/models/integration_models.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConnectionConfig:
    endpoint: str = ""
    credentials: dict[str, str] = field(default_factory=dict)
    options: dict[str, Any] = field(default_factory=dict)


@dataclass
class TransformationMapping:
    source_field: str = ""
    target_field: str = ""
    default: Any = None


@dataclass
class SyncResult:
    success_count: int = 0
    failure_count: int = 0
    errors: list[str] = field(default_factory=list)
