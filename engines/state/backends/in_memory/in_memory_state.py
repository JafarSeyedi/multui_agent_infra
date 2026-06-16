# engines/state/backends/in_memory/in_memory_state.py
from __future__ import annotations

from typing import Optional

from ...models.state_models import StateEntry, CacheEntry, LockEntry
from ...plugin import IStateBackend, ICache, IDistributedLock


class InMemoryStateBackend(IStateBackend):
    name = "in_memory"

    def __init__(self) -> None:
        self._store: dict[str, StateEntry] = {}

    async def load(self, instance_id: str) -> Optional[StateEntry]:
        return self._store.get(instance_id)

    async def save(self, entry: StateEntry) -> None:
        self._store[entry.instance_id] = entry

    async def delete(self, instance_id: str) -> None:
        self._store.pop(instance_id, None)


class InMemoryCache(ICache):
    name = "in_memory"

    def __init__(self) -> None:
        self._store: dict[str, CacheEntry] = {}

    async def get(self, key: str) -> Optional[CacheEntry]:
        return self._store.get(key)

    async def set(self, key: str, entry: CacheEntry) -> None:
        self._store[key] = entry

    async def invalidate(self, key: str) -> None:
        self._store.pop(key, None)


class InMemoryDistributedLock(IDistributedLock):
    name = "in_memory"

    def __init__(self) -> None:
        self._locks: dict[str, LockEntry] = {}

    async def acquire(self, resource: str, ttl: float = 30.0) -> bool:
        if resource in self._locks:
            return False
        self._locks[resource] = LockEntry(resource=resource, ttl=ttl)
        return True

    async def release(self, resource: str) -> None:
        self._locks.pop(resource, None)
