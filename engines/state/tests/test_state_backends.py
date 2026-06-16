# engines/state/tests/test_state_backends.py
import pytest
from engines.state.backends.in_memory.in_memory_state import (
    InMemoryStateBackend,
    InMemoryCache,
    InMemoryDistributedLock,
)
from engines.state.models.state_models import StateEntry, CacheEntry


@pytest.mark.asyncio
async def test_state_backend_save_load():
    backend = InMemoryStateBackend()
    entry = StateEntry(instance_id="i1", data={"key": "val"})
    await backend.save(entry)
    loaded = await backend.load("i1")
    assert loaded is not None
    assert loaded.data["key"] == "val"


@pytest.mark.asyncio
async def test_state_backend_delete():
    backend = InMemoryStateBackend()
    await backend.save(StateEntry(instance_id="i1"))
    await backend.delete("i1")
    assert await backend.load("i1") is None


@pytest.mark.asyncio
async def test_cache_set_get():
    cache = InMemoryCache()
    entry = CacheEntry(key="k", value="v")
    await cache.set("k", entry)
    loaded = await cache.get("k")
    assert loaded is not None
    assert loaded.value == "v"


@pytest.mark.asyncio
async def test_cache_invalidate():
    cache = InMemoryCache()
    await cache.set("k", CacheEntry(key="k", value="v"))
    await cache.invalidate("k")
    assert await cache.get("k") is None


@pytest.mark.asyncio
async def test_lock_acquire_release():
    lock = InMemoryDistributedLock()
    assert await lock.acquire("resource-1") is True
    assert await lock.acquire("resource-1") is False
    await lock.release("resource-1")
    assert await lock.acquire("resource-1") is True
