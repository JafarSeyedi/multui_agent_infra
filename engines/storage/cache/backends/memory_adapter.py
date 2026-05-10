from __future__ import annotations

import time
from typing import Any

from ..base import CacheStorage


class InMemoryCacheStorage(CacheStorage):
    """Simple in-process cache backend with optional TTL expiration."""

    def __init__(self) -> None:
        super().__init__()
        self._store: dict[str, tuple[Any, float | None]] = {}

    async def connect(self) -> None:
        self._connected = True

    async def disconnect(self) -> None:
        self._store.clear()
        self._connected = False

    async def health(self) -> bool:
        return True

    def _purge_expired(self) -> None:
        now = time.time()
        expired = [key for key, (_, expiry) in self._store.items() if expiry is not None and expiry <= now]
        for key in expired:
            self._store.pop(key, None)

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        self._purge_expired()
        expiry = time.time() + ttl if ttl else None
        self._store[key] = (value, expiry)

    async def get(self, key: str) -> Any | None:
        self._purge_expired()
        item = self._store.get(key)
        return item[0] if item else None

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def exists(self, key: str) -> bool:
        self._purge_expired()
        return key in self._store

    async def list_keys(self, prefix: str | None = None) -> list[str]:
        self._purge_expired()
        keys = list(self._store.keys())
        if prefix is None:
            return keys
        return [key for key in keys if key.startswith(prefix)]
