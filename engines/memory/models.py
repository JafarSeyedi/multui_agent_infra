from __future__ import annotations

import time
from dataclasses import dataclass
from dataclasses import field
from typing import Any


@dataclass(slots=True)
class MemoryItem:
    id: int
    key: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass(slots=True)
class MemoryQuery:
    query: str
    limit: int = 10
    threshold: float = 0.0
    filter_metadata: dict[str, Any] | None = None


@dataclass(slots=True)
class MemoryResult:
    items: list[MemoryItem]
    total: int = 0
    took_ms: float = 0.0
