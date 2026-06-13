from __future__ import annotations

import logging
from collections import OrderedDict
from collections.abc import Callable
from typing import Any

from engines.storage.base_storage import BaseStorage

logger = logging.getLogger(__name__)


class LazyInitStorageProxy(BaseStorage):
    """Proxy pattern — defers storage backend creation until first operation.

    Useful when the backend requires expensive setup (connection pool,
    file handles, etc.) or when the backend config is available but
    should not be eagerly initialized.
    """

    def __init__(self, factory: Callable[..., BaseStorage], **factory_kwargs: Any) -> None:
        super().__init__()
        self._factory = factory
        self._factory_kwargs = factory_kwargs
        self._backend: BaseStorage | None = None

    async def _ensure(self) -> BaseStorage:
        if self._backend is None:
            self._backend = self._factory(**self._factory_kwargs)
            if self._backend is not None:
                await self._backend.connect()
        return self._backend

    async def connect(self) -> None:
        await self._ensure()
        if self._backend is not None:
            await self._backend.connect()
        self._connected = True

    async def disconnect(self) -> None:
        if self._backend is not None:
            await self._backend.disconnect()
        self._backend = None
        self._connected = False

    async def health(self) -> bool:
        if self._backend is None:
            return False
        return await self._backend.health()

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        if self._backend is None:
            raise RuntimeError("Backend not initialized — call connect() first")
        return getattr(self._backend, name)


class CachingStorageProxy(BaseStorage):
    """Proxy pattern — adds an LRU read cache on top of any storage backend.

    Frequently-read items are served from an in-memory OrderedDict cache
    to avoid redundant network/IO operations.
    """

    def __init__(self, backend: BaseStorage, maxsize: int = 128) -> None:
        super().__init__()
        self._backend = backend
        self._maxsize = maxsize
        self._cache: OrderedDict[str, Any] = OrderedDict()

    async def connect(self) -> None:
        await self._backend.connect()
        self._connected = True

    async def disconnect(self) -> None:
        self._cache.clear()
        await self._backend.disconnect()
        self._connected = False

    async def health(self) -> bool:
        return await self._backend.health()

    async def get(self, key: str) -> Any | None:
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        value = await self._get_from_backend(key)
        if value is not None:
            self._cache[key] = value
            self._evict_if_needed()
        return value

    async def set(self, key: str, value: Any) -> None:
        self._cache[key] = value
        self._evict_if_needed()
        await self._set_in_backend(key, value)

    async def delete(self, key: str) -> None:
        self._cache.pop(key, None)
        await self._delete_in_backend(key)

    async def invalidate(self, key: str) -> None:
        self._cache.pop(key, None)
        if hasattr(self._backend, "invalidate"):
            await self._backend.invalidate(key)

    async def clear_cache(self) -> None:
        self._cache.clear()

    def _evict_if_needed(self) -> None:
        while len(self._cache) > self._maxsize:
            self._cache.popitem(last=False)

    async def _get_from_backend(self, key: str) -> Any | None:
        if hasattr(self._backend, "get"):
            return await self._backend.get(key)
        return None

    async def _set_in_backend(self, key: str, value: Any) -> None:
        if hasattr(self._backend, "set"):
            await self._backend.set(key, value)

    async def _delete_in_backend(self, key: str) -> None:
        if hasattr(self._backend, "delete"):
            await self._backend.delete(key)


class NullStorage(BaseStorage):
    """Null Object pattern — safe no-op for optional storage dependencies.

    Eliminates if-None checks throughout the codebase. Every method
    succeeds silently and returns sensible defaults.
    """

    async def connect(self) -> None:
        self._connected = True

    async def disconnect(self) -> None:
        self._connected = False

    async def health(self) -> bool:
        return True

    async def get(self, key: str) -> Any | None:
        return None

    async def set(self, key: str, value: Any) -> None:
        pass

    async def delete(self, key: str) -> None:
        pass

    async def exists(self, key: str) -> bool:
        return False

    async def list_keys(self, prefix: str | None = None) -> list[str]:
        return []
