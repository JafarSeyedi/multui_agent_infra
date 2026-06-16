# engines/persistence/models/persistence_models.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class VectorRecord:
    collection: str
    id: str
    vector: list[float] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class BlobRecord:
    path: str
    data: bytes = b""
