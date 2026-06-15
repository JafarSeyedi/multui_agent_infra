from __future__ import annotations

import pytest

from engines.storage.key_value.backends.memory_adapter import InMemoryKeyValueStorage
from engines.storage.proxies import CachingStorageProxy
from engines.storage.proxies import LazyInitStorageProxy
from engines.storage.proxies import NullStorage


class TestLazyInitStorageProxy:
    async def test_lazy_init(self) -> None:
        created = False

        def factory() -> InMemoryKeyValueStorage:
            nonlocal created
            created = True
            return InMemoryKeyValueStorage()

        proxy = LazyInitStorageProxy(factory)
        assert created is False

        await proxy.connect()
        assert created is True

    async def test_store_and_retrieve(self) -> None:
        proxy = LazyInitStorageProxy(
            lambda: InMemoryKeyValueStorage()
        )
        await proxy.connect()
        await proxy.set("k1", "v1")
        result = await proxy.get("k1")
        assert result == "v1"

    async def test_health_false_before_init(self) -> None:
        proxy = LazyInitStorageProxy(lambda: InMemoryKeyValueStorage())
        assert await proxy.health() is False

    async def test_disconnect_resets_backend(self) -> None:
        proxy = LazyInitStorageProxy(lambda: InMemoryKeyValueStorage())
        await proxy.connect()
        await proxy.disconnect()
        assert await proxy.health() is False


class TestCachingStorageProxy:
    @pytest.fixture
    def proxy(self) -> CachingStorageProxy:
        return CachingStorageProxy(InMemoryKeyValueStorage(), maxsize=3)

    async def test_cache_hit(self, proxy: CachingStorageProxy) -> None:
        await proxy.set("k1", "value1")
        r1 = await proxy.get("k1")
        r2 = await proxy.get("k1")
        assert r1 == "value1"
        assert r2 == "value1"

    async def test_cache_miss(self, proxy: CachingStorageProxy) -> None:
        await proxy.set("k1", "data")
        assert await proxy.get("k1") == "data"
        assert await proxy.get("nonexistent") is None

    async def test_invalidation(self, proxy: CachingStorageProxy) -> None:
        await proxy.set("k1", "data")
        assert await proxy.get("k1") is not None
        await proxy.delete("k1")
        assert await proxy.get("k1") is None

    async def test_clear_cache(self, proxy: CachingStorageProxy) -> None:
        await proxy.set("k1", "v1")
        await proxy.set("k2", "v2")
        await proxy.clear_cache()
        assert await proxy.get("k1") == "v1"

    async def test_lru_eviction(self, proxy: CachingStorageProxy) -> None:
        for i in range(5):
            await proxy.set(f"k{i}", f"v{i}")

        assert await proxy.get("k2") == "v2"
        assert await proxy.get("k3") == "v3"
        assert await proxy.get("k4") == "v4"


class TestNullStorage:
    @pytest.fixture
    def storage(self) -> NullStorage:
        return NullStorage()

    async def test_connect(self, storage: NullStorage) -> None:
        await storage.connect()
        assert storage.is_connected

    async def test_health(self, storage: NullStorage) -> None:
        assert await storage.health() is True

    async def test_get_returns_none(self, storage: NullStorage) -> None:
        value = await storage.get("anything")
        assert value is None

    async def test_set_noop(self, storage: NullStorage) -> None:
        await storage.set("k1", "v1")
        value = await storage.get("k1")
        assert value is None

    async def test_exists_false(self, storage: NullStorage) -> None:
        assert await storage.exists("anything") is False

    async def test_list_keys_empty(self, storage: NullStorage) -> None:
        assert await storage.list_keys() == []

    async def test_delete_noop(self, storage: NullStorage) -> None:
        await storage.delete("k1")
        assert await storage.exists("k1") is False
