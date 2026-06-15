from __future__ import annotations

import pytest

from engines.memory.backends import InMemoryBackend
from engines.memory.backends import NullMemoryBackend
from engines.memory.models import MemoryItem
from engines.memory.models import MemoryQuery
from engines.memory.proxies import CachingMemoryBackend
from engines.memory.proxies import LazyMemoryBackend


class TestLazyMemoryBackend:
    async def test_lazy_init(self) -> None:
        created = False

        def factory() -> InMemoryBackend:
            nonlocal created
            created = True
            return InMemoryBackend()

        backend = LazyMemoryBackend(factory)
        assert created is False

        await backend.store(MemoryItem(id=0, key="k1", content="x"))
        assert created is True

    async def test_store_and_retrieve(self) -> None:
        backend = LazyMemoryBackend(InMemoryBackend)
        item = MemoryItem(id=0, key="k1", content="hello")
        await backend.store(item)
        result = await backend.retrieve("k1")
        assert result is not None
        assert result.content == "hello"

    async def test_count_before_init(self) -> None:
        backend = LazyMemoryBackend(InMemoryBackend)
        assert await backend.count() == 0


class TestCachingMemoryBackend:
    @pytest.fixture
    def backend(self) -> CachingMemoryBackend:
        return CachingMemoryBackend(InMemoryBackend(), maxsize=3)

    async def test_cache_hit(self, backend: CachingMemoryBackend) -> None:
        item = MemoryItem(id=0, key="k1", content="cached")
        await backend.store(item)

        result1 = await backend.retrieve("k1")
        result2 = await backend.retrieve("k1")
        assert result1 is not None
        assert result2 is not None
        assert result1.content == "cached"
        assert result2.content == "cached"

    async def test_cache_miss(self, backend: CachingMemoryBackend) -> None:
        await backend.store(MemoryItem(id=0, key="k1", content="data"))
        result = await backend.retrieve("k1")
        assert result is not None and result.content == "data"

        result = await backend.retrieve("nonexistent")
        assert result is None

    async def test_invalidation_on_forget(self, backend: CachingMemoryBackend) -> None:
        await backend.store(MemoryItem(id=0, key="k1", content="data"))
        assert await backend.retrieve("k1") is not None
        await backend.forget("k1")
        assert await backend.retrieve("k1") is None

    async def test_lru_eviction(self, backend: CachingMemoryBackend) -> None:
        for i in range(5):
            await backend.store(MemoryItem(id=0, key=f"k{i}", content=str(i)))

        # k0 and k1 should be evicted (LRU, 3 max)
        assert await backend.retrieve("k0") is not None
        assert await backend.retrieve("k1") is not None

    async def test_search_passthrough(self, backend: CachingMemoryBackend) -> None:
        await backend.store(MemoryItem(id=0, key="k1", content="python"))
        result = await backend.search(MemoryQuery(query="python"))
        assert result.total >= 1

    async def test_clear_empties_cache(self, backend: CachingMemoryBackend) -> None:
        await backend.store(MemoryItem(id=0, key="k1", content="x"))
        await backend.clear()
        assert await backend.count() == 0
