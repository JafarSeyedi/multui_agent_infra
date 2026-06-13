from __future__ import annotations

import time
from collections import OrderedDict
from typing import Any

from engines.memory.backends import MemoryBackend
from engines.memory.models import MemoryItem
from engines.memory.models import MemoryQuery
from engines.memory.models import MemoryResult


class LazyMemoryBackend(MemoryBackend):
    """Proxy pattern — defers backend creation until first use."""

    def __init__(self, factory: Any, **factory_kwargs: Any) -> None:
        self._factory = factory
        self._factory_kwargs = factory_kwargs
        self._backend: MemoryBackend | None = None

    async def _ensure(self) -> MemoryBackend:
        if self._backend is None:
            self._backend = self._factory(**self._factory_kwargs)
            if hasattr(self._backend, "connect"):
                await self._backend.connect()
        return self._backend

    async def store(self, item: MemoryItem) -> MemoryItem:
        b = await self._ensure()
        return await b.store(item)

    async def retrieve(self, key: str) -> MemoryItem | None:
        b = await self._ensure()
        return await b.retrieve(key)

    async def search(self, query: MemoryQuery) -> MemoryResult:
        b = await self._ensure()
        return await b.search(query)

    async def forget(self, key: str) -> bool:
        b = await self._ensure()
        return await b.forget(key)

    async def clear(self) -> None:
        b = await self._ensure()
        return await b.clear()

    async def count(self) -> int:
        if self._backend is None:
            return 0
        return await self._backend.count()


class CachingMemoryBackend(MemoryBackend):
    """Proxy pattern — decorates a backend with an LRU read cache."""

    def __init__(self, backend: MemoryBackend, maxsize: int = 128) -> None:
        self._backend = backend
        self._maxsize = maxsize
        self._cache: OrderedDict[str, MemoryItem] = OrderedDict()

    async def store(self, item: MemoryItem) -> MemoryItem:
        result = await self._backend.store(item)
        self._cache[item.key] = result
        self._evict_if_needed()
        return result

    async def retrieve(self, key: str) -> MemoryItem | None:
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        item = await self._backend.retrieve(key)
        if item is not None:
            self._cache[key] = item
            self._evict_if_needed()
        return item

    async def search(self, query: MemoryQuery) -> MemoryResult:
        return await self._backend.search(query)

    async def forget(self, key: str) -> bool:
        self._cache.pop(key, None)
        return await self._backend.forget(key)

    async def clear(self) -> None:
        self._cache.clear()
        await self._backend.clear()

    async def count(self) -> int:
        return await self._backend.count()

    def _evict_if_needed(self) -> None:
        while len(self._cache) > self._maxsize:
            self._cache.popitem(last=False)
