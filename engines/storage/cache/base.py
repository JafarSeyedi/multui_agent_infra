from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import Any

from engines.storage.base_storage import BaseStorage


class CacheStorage(BaseStorage, ABC):
    """Cache abstraction for temporary values with optional TTL support."""

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        ...

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        ...

    @abstractmethod
    async def exists(self, key: str) -> bool:
        ...

    @abstractmethod
    async def list_keys(self, prefix: str | None = None) -> list[str]:
        ...

    async def invalidate(self, key: str) -> None:
        await self.delete(key)

    async def clear(self) -> None:
        for key in await self.list_keys():
            await self.delete(key)
