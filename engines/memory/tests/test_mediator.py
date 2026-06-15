from __future__ import annotations

from typing import Any

import pytest

from engines.memory.backends import InMemoryBackend
from engines.memory.backends import NullMemoryBackend
from engines.memory.mediator import MemoryMediator
from engines.memory.models import MemoryQuery


class TestMemoryMediator:
    @pytest.fixture
    def mediator(self) -> MemoryMediator:
        return MemoryMediator(primary=InMemoryBackend(), secondary=InMemoryBackend())

    async def test_store(self, mediator: MemoryMediator) -> None:
        item = await mediator.store("k1", "hello world")
        assert item.key == "k1"
        assert item.content == "hello world"

    async def test_retrieve_from_primary(self, mediator: MemoryMediator) -> None:
        await mediator.store("k1", "data")
        result = await mediator.retrieve("k1")
        assert result is not None
        assert result.content == "data"

    async def test_retrieve_falls_back_to_secondary(self) -> None:
        primary = InMemoryBackend()
        secondary = InMemoryBackend()
        med = MemoryMediator(primary=primary, secondary=secondary)
        from engines.memory.models import MemoryItem

        await secondary.store(MemoryItem(id=0, key="k1", content="fallback"))
        result = await med.retrieve("k1")
        assert result is not None
        assert result.content == "fallback"

    async def test_search_falls_back(self) -> None:
        primary = InMemoryBackend()
        secondary = InMemoryBackend()
        med = MemoryMediator(primary=primary, secondary=secondary)
        from engines.memory.models import MemoryItem

        await secondary.store(MemoryItem(id=0, key="k1", content="test data"))
        result = await med.search(MemoryQuery(query="test"))
        assert result.total >= 1

    async def test_forget_both(self, mediator: MemoryMediator) -> None:
        await mediator.store("k1", "data")
        assert await mediator.forget("k1") is True
        assert await mediator.retrieve("k1") is None

    async def test_forget_missing(self, mediator: MemoryMediator) -> None:
        assert await mediator.forget("nonexistent") is False

    async def test_clear(self, mediator: MemoryMediator) -> None:
        await mediator.store("k1", "a")
        await mediator.store("k2", "b")
        await mediator.clear()
        assert await mediator.count() == 0

    async def test_listener_notified(self, mediator: MemoryMediator) -> None:
        events: list[str] = []

        class Listener:
            def on_memory_event(self, event: str, data: Any) -> None:
                events.append(event)

        mediator.add_listener(Listener())
        await mediator.store("k1", "data")
        await mediator.forget("k1")
        assert events == ["store", "forget"]

    async def test_secondary_is_null_by_default(self) -> None:
        med = MemoryMediator(primary=InMemoryBackend())
        assert isinstance(med._secondary, NullMemoryBackend)
