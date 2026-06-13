from __future__ import annotations

import time
from typing import Any

from engines.memory.backends import MemoryBackend
from engines.memory.backends import NullMemoryBackend
from engines.memory.models import MemoryItem
from engines.memory.models import MemoryQuery
from engines.memory.models import MemoryResult


class MemoryMediator:
    """Mediator pattern — coordinates store/retrieve/search/forget across
    multiple backends with optional event broadcasting."""

    def __init__(
        self,
        primary: MemoryBackend,
        secondary: MemoryBackend | None = None,
    ) -> None:
        self._primary = primary
        self._secondary = secondary or NullMemoryBackend()
        self._listeners: list[Any] = []

    def add_listener(self, listener: Any) -> None:
        self._listeners.append(listener)

    async def store(
        self,
        key: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryItem:
        item = MemoryItem(
            id=0,
            key=key,
            content=content,
            metadata=metadata or {},
            timestamp=time.time(),
        )
        result = await self._primary.store(item)
        await self._secondary.store(item)
        self._notify("store", result)
        return result

    async def retrieve(self, key: str) -> MemoryItem | None:
        item = await self._primary.retrieve(key)
        if item is not None:
            return item
        item = await self._secondary.retrieve(key)
        if item is not None:
            await self._primary.store(item)
        return item

    async def search(self, query: MemoryQuery) -> MemoryResult:
        result = await self._primary.search(query)
        if result.total > 0:
            return result
        return await self._secondary.search(query)

    async def forget(self, key: str) -> bool:
        p = await self._primary.forget(key)
        s = await self._secondary.forget(key)
        result = p or s
        if result:
            self._notify("forget", key)
        return result

    async def clear(self) -> None:
        await self._primary.clear()
        await self._secondary.clear()
        self._notify("clear", None)

    async def count(self) -> int:
        return await self._primary.count()

    def _notify(self, event: str, data: Any) -> None:
        for listener in self._listeners:
            try:
                listener.on_memory_event(event, data)
            except Exception:
                pass
