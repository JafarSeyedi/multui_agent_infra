"""Tests for Proxy pattern (M4) — LazyInitProxy, CachingProxy, EngineProtectionProxy."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from engines.orchestration.core.proxies import (
    CachingProxy,
    EngineProtectionProxy,
    LazyInitProxy,
)
from engines.orchestration.core.factories import InMemoryBackend


@pytest.fixture
def real_backend():
    return InMemoryBackend()


@pytest.fixture
def sample_data():
    return {"key": "value", "num": 42}


class TestLazyInitProxy:
    """LazyInitProxy defers backend creation until first use."""

    @pytest.mark.asyncio
    async def test_factory_not_called_on_construction(self):
        factory = MagicMock()
        LazyInitProxy(factory)
        factory.assert_not_called()

    @pytest.mark.asyncio
    async def test_factory_called_on_first_operation(self):
        backend = InMemoryBackend()
        factory = MagicMock(return_value=backend)
        proxy = LazyInitProxy(factory)

        await proxy.save("col", "k", {"v": 1})
        factory.assert_called_once()

    @pytest.mark.asyncio
    async def test_delegates_save_and_load(self, real_backend, sample_data):
        proxy = LazyInitProxy(lambda: real_backend)
        await proxy.save("col1", "key1", sample_data)
        result = await proxy.load("col1", "key1")
        assert result == sample_data

    @pytest.mark.asyncio
    async def test_delete_and_clear(self, real_backend):
        proxy = LazyInitProxy(lambda: real_backend)
        await proxy.save("col", "k", {"v": 1})
        assert await proxy.load("col", "k") == {"v": 1}
        await proxy.delete("col", "k")
        assert await proxy.load("col", "k") is None

    @pytest.mark.asyncio
    async def test_list(self, real_backend):
        proxy = LazyInitProxy(lambda: real_backend)
        await proxy.save("col", "a", {"v": 1})
        await proxy.save("col", "b", {"v": 2})
        items = await proxy.list("col")
        assert len(items) == 2

    @pytest.mark.asyncio
    async def test_clear(self, real_backend):
        proxy = LazyInitProxy(lambda: real_backend)
        await proxy.save("col", "k", {"v": 1})
        await proxy.clear("col")
        assert await proxy.list("col") == []

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        proxy = LazyInitProxy(lambda: InMemoryBackend())
        async with proxy as p:
            await p.save("col", "k", {"v": 1})
            assert await p.load("col", "k") == {"v": 1}


class TestCachingProxy:
    """CachingProxy adds in-memory LRU cache over backend."""

    @pytest.mark.asyncio
    async def test_cache_hit_skips_backend(self):
        backend = AsyncMock()
        backend.load.return_value = {"cached": True}
        proxy = CachingProxy(backend, maxsize=10)

        result1 = await proxy.load("col", "key")
        assert result1 == {"cached": True}
        assert backend.load.call_count == 1

        result2 = await proxy.load("col", "key")
        assert result2 == {"cached": True}
        assert backend.load.call_count == 1

    @pytest.mark.asyncio
    async def test_cache_miss_hits_backend(self):
        backend = AsyncMock()
        backend.load.side_effect = [None, {"second": True}]
        proxy = CachingProxy(backend, maxsize=10)

        result = await proxy.load("col", "key")
        assert result is None
        assert backend.load.call_count == 1

        result = await proxy.load("col", "key")
        assert result == {"second": True}
        assert backend.load.call_count == 2

    @pytest.mark.asyncio
    async def test_save_updates_cache(self):
        backend = AsyncMock()
        proxy = CachingProxy(backend, maxsize=10)
        data = {"fresh": True}

        await proxy.save("col", "k", data)
        backend.save.assert_awaited_once_with("col", "k", data)

        result = await proxy.load("col", "k")
        assert result == data
        backend.load.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_invalidates_cache(self):
        backend = AsyncMock()
        backend.load.return_value = {"data": 1}
        proxy = CachingProxy(backend, maxsize=10)

        await proxy.load("col", "k")
        assert backend.load.call_count == 1

        await proxy.delete("col", "k")
        await proxy.load("col", "k")
        assert backend.load.call_count == 2

    @pytest.mark.asyncio
    async def test_clear_invalidates_all_for_collection(self):
        backend = AsyncMock()
        backend.load.side_effect = [{"a": 1}, {"b": 2}, {"a": 1}]
        proxy = CachingProxy(backend, maxsize=10)

        await proxy.load("col", "a")
        await proxy.load("col", "b")
        assert backend.load.call_count == 2

        await proxy.clear("col")
        await proxy.load("col", "a")
        assert backend.load.call_count == 3

    @pytest.mark.asyncio
    async def test_lru_eviction(self):
        backend = AsyncMock()
        backend.load.return_value = {"v": 1}
        proxy = CachingProxy(backend, maxsize=2)

        await proxy.load("col", "a")
        await proxy.load("col", "b")
        await proxy.load("col", "c")

        backend.load.reset_mock()
        await proxy.load("col", "a")
        assert backend.load.call_count == 1

    @pytest.mark.asyncio
    async def test_list_not_cached(self):
        backend = AsyncMock()
        backend.list.return_value = [{"id": 1}]
        proxy = CachingProxy(backend)

        assert await proxy.list("col") == [{"id": 1}]
        assert await proxy.list("col") == [{"id": 1}]
        assert backend.list.call_count == 2


class TestEngineProtectionProxy:
    """EngineProtectionProxy checks roles before delegating."""

    @pytest.fixture
    def mock_engine(self):
        engine = AsyncMock()
        engine.engine_type = "bpmn"
        return engine

    @pytest.fixture
    def mock_instance(self):
        inst = MagicMock()
        inst.id = "inst-1"
        inst.variables = {}
        return inst

    @pytest.fixture
    def mock_definition(self):
        return MagicMock()

    @pytest.mark.asyncio
    async def test_allows_admin_role(self, mock_engine, mock_instance, mock_definition):
        mock_instance.variables["role"] = "admin"
        proxy = EngineProtectionProxy(mock_engine, allowed_roles={"admin", "operator"})
        await proxy.execute(mock_instance, mock_definition)
        mock_engine.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_denies_viewer_role(self, mock_engine, mock_instance, mock_definition):
        mock_instance.variables["role"] = "viewer"
        proxy = EngineProtectionProxy(mock_engine, allowed_roles={"admin", "operator"})
        with pytest.raises(PermissionError, match="'viewer' is not allowed to execute"):
            await proxy.execute(mock_instance, mock_definition)
        mock_engine.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_default_role_is_allowed(self, mock_engine, mock_instance, mock_definition):
        mock_instance.variables = {}
        mock_instance.role = "admin"
        proxy = EngineProtectionProxy(mock_engine)
        await proxy.execute(mock_instance, mock_definition)
        mock_engine.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_set_allowed_roles(self, mock_engine, mock_instance, mock_definition):
        mock_instance.variables["role"] = "supervisor"
        proxy = EngineProtectionProxy(mock_engine, allowed_roles={"admin"})
        with pytest.raises(PermissionError):
            await proxy.execute(mock_instance, mock_definition)

        proxy.set_allowed_roles({"admin", "supervisor"})
        await proxy.execute(mock_instance, mock_definition)
        mock_engine.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_validate_and_cancel_delegate(self, mock_engine, mock_instance, mock_definition):
        proxy = EngineProtectionProxy(mock_engine)
        assert await proxy.validate(mock_definition) == mock_engine.validate.return_value
        await proxy.cancel("x")
        mock_engine.cancel.assert_awaited_once_with("x")

    def test_engine_type(self, mock_engine):
        proxy = EngineProtectionProxy(mock_engine)
        assert proxy.engine_type == "bpmn"
