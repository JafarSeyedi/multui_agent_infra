# engines/state/plugin.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from .models.state_models import StateEntry, CacheEntry


class IStateBackend(ABC):
    name: str = "base"

    @abstractmethod
    async def load(self, instance_id: str) -> Optional[StateEntry]: ...

    @abstractmethod
    async def save(self, entry: StateEntry) -> None: ...

    @abstractmethod
    async def delete(self, instance_id: str) -> None: ...


class ICache(ABC):
    name: str = "base"

    @abstractmethod
    async def get(self, key: str) -> Optional[CacheEntry]: ...

    @abstractmethod
    async def set(self, key: str, entry: CacheEntry) -> None: ...

    @abstractmethod
    async def invalidate(self, key: str) -> None: ...


class IDistributedLock(ABC):
    name: str = "base"

    @abstractmethod
    async def acquire(self, resource: str, ttl: float = 30.0) -> bool: ...

    @abstractmethod
    async def release(self, resource: str) -> None: ...
