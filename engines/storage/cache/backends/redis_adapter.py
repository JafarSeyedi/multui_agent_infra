from __future__ import annotations

from typing import Any, List, Optional

from engines.storage.key_value.backends.redis_adapter import RedisManager
from ..base import CacheStorage


class RedisCacheStorage(CacheStorage):
    """Cache backend backed by Redis string values."""

    def __init__(self, manager: RedisManager, namespace: str = "cache") -> None:
        super().__init__()
        self.manager = manager
        self.namespace = namespace

    def _key(self, key: str) -> str:
        return f"{self.namespace}:{key}"

    async def connect(self) -> None:
        await self.manager.connect()
        self._connected = True

    async def disconnect(self) -> None:
        if self.manager.client is not None:
            await self.manager.disconnect()
        self._connected = False

    async def health(self) -> bool:
        client = await self.manager.get_client()

        try:
            result = client.ping()

            if hasattr(result, "__await__"):
                result = await result

            return bool(result)

        except Exception:
            return False

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        client = await self.manager.get_client()
        await client.set(self._key(key), value, ex=ttl)

    async def get(self, key: str) -> Optional[Any]:
        client = await self.manager.get_client()
        return await client.get(self._key(key))

    async def delete(self, key: str) -> None:
        client = await self.manager.get_client()
        await client.delete(self._key(key))

    async def exists(self, key: str) -> bool:
        client = await self.manager.get_client()
        result = await client.exists(self._key(key))
        return bool(result)

    async def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        client = await self.manager.get_client()

        pattern = self._key(prefix or "") + "*"
        keys = await client.keys(pattern)

        return [
            key.replace(f"{self.namespace}:", "", 1)
            for key in keys
        ]
