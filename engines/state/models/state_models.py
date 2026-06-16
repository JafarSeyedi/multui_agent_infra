# engines/state/models/state_models.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class StateEntry:
    instance_id: str
    data: dict[str, Any] = field(default_factory=dict)
    version: int = 1
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class CacheEntry:
    key: str
    value: Any = None
    ttl: float = 300.0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class LockEntry:
    resource: str
    holder: str = ""
    acquired_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ttl: float = 30.0
