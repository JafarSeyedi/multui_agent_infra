"""ID generation utilities with optional prefix/scoped counters."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from uuid import UUID, uuid4
from typing import ClassVar


@dataclass(frozen=True)
class IdPrefix:
    """Configurable ID prefix for generated identifiers."""

    value: str


class IdGenerator:
    """Thread-safe identifier generator for orchestration internals."""

    _lock = threading.Lock()
    _counter: ClassVar[int] = 0

    def __init__(self, prefix: str | None = None) -> None:
        self._prefix = prefix or "ors"

    def next_id(self, *, suffix: str | None = None) -> str:
        """Generate a unique identifier with optional suffix."""
        with self._lock:
            IdGenerator._counter += 1
            token = IdGenerator._counter
        random_part = uuid4().hex[:10]
        base = f"{self._prefix}-{token}-{random_part}"
        return f"{base}:{suffix}" if suffix else base

    def next_uuid(self, *, prefix: str | None = None) -> str:
        """Generate a random UUID-based identifier."""
        base = uuid4().hex
        if prefix:
            return f"{prefix}-{base}"
        if self._prefix:
            return f"{self._prefix}-{base}"
        return base

    def parse_uuid(self, value: str) -> UUID:
        """Validate and parse a UUID string."""
        return UUID(value)
