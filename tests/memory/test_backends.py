from __future__ import annotations

import pytest

from engines.memory.backends import InMemoryBackend
from engines.memory.backends import NullMemoryBackend
from engines.memory.models import MemoryItem
from engines.memory.models import MemoryQuery


class TestInMemoryBackend:
    @pytest.fixture
    def backend(self) -> InMemoryBackend:
        return InMemoryBackend()

    async def test_store_and_retrieve(self, backend: InMemoryBackend) -> None:
        item = MemoryItem(id=0, key="test-key", content="hello world")
        stored = await backend.store(item)
        assert stored.id == 1
        assert stored.key == "test-key"

        retrieved = await backend.retrieve("test-key")
        assert retrieved is not None
        assert retrieved.content == "hello world"

    async def test_retrieve_missing(self, backend: InMemoryBackend) -> None:
        result = await backend.retrieve("nonexistent")
        assert result is None

    async def test_search(self, backend: InMemoryBackend) -> None:
        await backend.store(MemoryItem(id=0, key="k1", content="python programming"))
        await backend.store(MemoryItem(id=0, key="k2", content="java programming"))
        await backend.store(MemoryItem(id=0, key="k3", content="machine learning"))

        query = MemoryQuery(query="programming", limit=5, threshold=0.3)
        result = await backend.search(query)
        assert result.total == 2  # k3 "machine learning" has 0 overlap with "programming"

    async def test_search_with_threshold(self, backend: InMemoryBackend) -> None:
        await backend.store(MemoryItem(id=0, key="k1", content="hello world"))
        await backend.store(MemoryItem(id=0, key="k2", content="goodbye world"))

        query = MemoryQuery(query="hello", limit=5, threshold=0.5)
        result = await backend.search(query)
        assert result.total == 1

    async def test_forget(self, backend: InMemoryBackend) -> None:
        await backend.store(MemoryItem(id=0, key="k1", content="data"))
        assert await backend.forget("k1") is True
        assert await backend.retrieve("k1") is None

    async def test_forget_missing(self, backend: InMemoryBackend) -> None:
        assert await backend.forget("nonexistent") is False

    async def test_clear(self, backend: InMemoryBackend) -> None:
        await backend.store(MemoryItem(id=0, key="k1", content="a"))
        await backend.store(MemoryItem(id=0, key="k2", content="b"))
        await backend.clear()
        assert await backend.count() == 0

    async def test_count(self, backend: InMemoryBackend) -> None:
        assert await backend.count() == 0
        await backend.store(MemoryItem(id=0, key="k1", content="a"))
        assert await backend.count() == 1


class TestNullMemoryBackend:
    @pytest.fixture
    def backend(self) -> NullMemoryBackend:
        return NullMemoryBackend()

    async def test_store_returns_item(self, backend: NullMemoryBackend) -> None:
        item = MemoryItem(id=0, key="k1", content="x")
        result = await backend.store(item)
        assert result.key == "k1"

    async def test_retrieve_returns_none(self, backend: NullMemoryBackend) -> None:
        assert await backend.retrieve("anything") is None

    async def test_search_empty(self, backend: NullMemoryBackend) -> None:
        result = await backend.search(MemoryQuery(query="x"))
        assert result.total == 0

    async def test_forget_always_true(self, backend: NullMemoryBackend) -> None:
        assert await backend.forget("anything") is True

    async def test_clear_noop(self, backend: NullMemoryBackend) -> None:
        await backend.clear()
        assert await backend.count() == 0
