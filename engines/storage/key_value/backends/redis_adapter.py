from __future__ import annotations

import json
import logging
from collections.abc import Awaitable
from typing import Any
from typing import cast
from typing import Union

from redis.asyncio import Redis
from redis.asyncio import Sentinel
from redis.asyncio.cluster import RedisCluster
from redis.asyncio.retry import Retry
from redis.backoff import ExponentialBackoff

from ..base import KeyValueStorage


RedisClient = Union[Redis, RedisCluster]


class RedisManager:
    """Advanced Redis connection manager supporting standalone, sentinel, and cluster modes."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.client: RedisClient | None = None
        self.logger = logging.getLogger("RedisManager")

        self._retry: Retry = Retry(
            ExponentialBackoff(base=1, cap=10),
            retries=3,
        )

    async def connect(self) -> None:
        mode = self.config.get("mode", "standalone")

        try:
            if mode == "cluster":
                self.client = RedisCluster(
                    host=self.config["host"],
                    port=self.config["port"],
                    decode_responses=True,
                    retry=self._retry,
                )

            elif mode == "sentinel":
                sentinel = Sentinel(
                    self.config["nodes"],
                    decode_responses=True,
                )

                self.client = sentinel.master_for(
                    self.config["master_name"],
                    retry=self._retry,
                )

            else:
                self.client = Redis(
                    host=self.config.get("host", "localhost"),
                    port=self.config.get("port", 6379),
                    db=self.config.get("db", 0),
                    decode_responses=True,
                    retry=self._retry,
                    health_check_interval=30,
                )

            assert self.client is not None

            result = self.client.ping()
            await cast(Awaitable[Any], result)

            self.logger.info("Connected to Redis in %s mode.", mode)

        except Exception as exc:
            self.logger.error("Redis connection failed: %s", exc)
            raise

    async def disconnect(self) -> None:
        if self.client is not None:
            await self.client.close()

        self.client = None

    async def get_client(self) -> RedisClient:
        if self.client is None:
            await self.connect()

        assert self.client is not None
        return self.client


class RedisStorageAdapter(KeyValueStorage):
    """Key-value storage backed by Redis with JSON serialization helpers."""

    def __init__(self, manager: RedisManager, namespace: str = "tutor") -> None:
        super().__init__()
        self.manager = manager
        self.namespace = namespace

    def _get_key(self, key: str) -> str:
        return f"{self.namespace}:{key}"

    async def connect(self) -> None:
        await self.manager.connect()
        self._connected = True

    async def disconnect(self) -> None:
        await self.manager.disconnect()
        self._connected = False

    async def health(self) -> bool:
        try:
            client = await self.manager.get_client()

            result = client.ping()
            if hasattr(result, "__await__"):
                result = await result

            return bool(result)

        except Exception:
            return False

    async def _client(self) -> RedisClient:
        return await self.manager.get_client()

    async def set(self, key: str, value: Any) -> None:
        client = await self._client()

        payload = (
            json.dumps(value)
            if isinstance(value, (dict, list))
            else value
        )

        await client.set(self._get_key(key), payload)

    async def get(self, key: str) -> Any | None:
        client = await self._client()

        data = await client.get(self._get_key(key))

        if data is None:
            return None

        try:
            return json.loads(data)
        except (TypeError, json.JSONDecodeError):
            return data

    async def delete(self, key: str) -> None:
        client = await self._client()
        await client.delete(self._get_key(key))

    async def exists(self, key: str) -> bool:
        client = await self._client()
        return bool(await client.exists(self._get_key(key)))

    async def list_keys(self, prefix: str | None = None) -> list[str]:
        client = await self._client()

        pattern = f"{self.namespace}:{prefix if prefix else ''}*"

        keys = await client.keys(pattern)

        return [
            key.replace(f"{self.namespace}:", "", 1)
            for key in keys
        ]

    async def save(
        self,
        key: str,
        data: dict[str, Any],
        ttl: int | None = None,
    ) -> None:

        client = await self._client()

        await client.set(
            self._get_key(key),
            json.dumps(data),
            ex=ttl,
        )

    async def load(self, key: str) -> dict[str, Any] | None:
        value = await self.get(key)

        return value if isinstance(value, dict) else None
