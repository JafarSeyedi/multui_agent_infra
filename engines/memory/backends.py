from __future__ import annotations

import time
from abc import ABC
from abc import abstractmethod
from typing import Any

from engines.memory.models import MemoryItem
from engines.memory.models import MemoryQuery
from engines.memory.models import MemoryResult


class MemoryBackend(ABC):
    """Strategy interface for memory storage backends."""

    @abstractmethod
    async def store(self, item: MemoryItem) -> MemoryItem:
        ...

    @abstractmethod
    async def retrieve(self, key: str) -> MemoryItem | None:
        ...

    @abstractmethod
    async def search(self, query: MemoryQuery) -> MemoryResult:
        ...

    @abstractmethod
    async def forget(self, key: str) -> bool:
        ...

    @abstractmethod
    async def clear(self) -> None:
        ...

    @abstractmethod
    async def count(self) -> int:
        ...


class InMemoryBackend(MemoryBackend):
    """Ephemeral in-memory backend — default for tests and local dev."""

    def __init__(self) -> None:
        self._items: dict[str, MemoryItem] = {}
        self._next_id = 1

    async def store(self, item: MemoryItem) -> MemoryItem:
        stored = MemoryItem(
            id=self._next_id,
            key=item.key,
            content=item.content,
            metadata=item.metadata,
            timestamp=item.timestamp or time.time(),
        )
        self._next_id += 1
        self._items[stored.key] = stored
        return stored

    async def retrieve(self, key: str) -> MemoryItem | None:
        return self._items.get(key)

    async def search(self, query: MemoryQuery) -> MemoryResult:
        start = time.monotonic()
        scored: list[tuple[float, MemoryItem]] = []
        for item in self._items.values():
            score = self._score(item, query)
            if score >= query.threshold:
                scored.append((score, item))
        scored.sort(key=lambda x: x[0], reverse=True)
        items = [item for _, item in scored[: query.limit]]
        took = (time.monotonic() - start) * 1000
        return MemoryResult(items=items, total=len(items), took_ms=round(took, 2))

    async def forget(self, key: str) -> bool:
        return self._items.pop(key, None) is not None

    async def clear(self) -> None:
        self._items.clear()

    async def count(self) -> int:
        return len(self._items)

    @staticmethod
    def _score(item: MemoryItem, query: MemoryQuery) -> float:
        q = query.query.lower()
        content = item.content.lower()
        overlap = len(set(q.split()) & set(content.split()))
        union = max(1, len(set(q.split()) | set(content.split())))
        score = overlap / union
        if query.filter_metadata:
            matches = sum(
                1 for k, v in query.filter_metadata.items()
                if item.metadata.get(k) == v
            )
            score += 0.1 * matches
        return score


class NullMemoryBackend(MemoryBackend):
    """Null Object pattern — safe no-op for optional memory."""

    async def store(self, item: MemoryItem) -> MemoryItem:
        return item

    async def retrieve(self, key: str) -> MemoryItem | None:
        return None

    async def search(self, query: MemoryQuery) -> MemoryResult:
        return MemoryResult(items=[])

    async def forget(self, key: str) -> bool:
        return True

    async def clear(self) -> None:
        pass

    async def count(self) -> int:
        return 0
