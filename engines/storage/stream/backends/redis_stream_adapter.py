from __future__ import annotations

import json
import logging
from typing import Any, Awaitable, Dict, List, Optional, Union, Mapping, cast

from redis.asyncio import Redis, Sentinel
from redis.asyncio.cluster import RedisCluster
from redis.asyncio.retry import Retry
from redis.backoff import ExponentialBackoff

from ..base import StreamStorage


RedisClient = Union[Redis, RedisCluster]

RedisField = Union[bytes, bytearray, memoryview, str, int, float]
RedisPayload = Mapping[RedisField, RedisField]


class RedisManagerStream:
    """Redis connection manager for stream backends."""

    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.client: Optional[RedisClient] = None
        self.logger = logging.getLogger("RedisManagerStream")

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

            self.logger.info("Connected to Redis Streams (%s mode)", mode)

        except Exception as exc:
            self.logger.error("Redis Streams connection failed: %s", exc)
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


class RedisStreamAdapter(StreamStorage):
    """Redis Streams backend for durable event streaming."""

    def __init__(self, manager: RedisManagerStream) -> None:
        super().__init__()
        self.manager = manager

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

    async def publish(
        self,
        topic: str,
        message: Dict[str, Any],
    ) -> None:

        client = await self._client()

        payload: Dict[str, Union[str, int, float]] = {}

        for key, value in message.items():
            if isinstance(value, (dict, list)):
                payload[key] = json.dumps(value)
            elif isinstance(value, (str, int, float)):
                payload[key] = value
            else:
                payload[key] = str(value)

        redis_payload = cast(Dict[RedisField, RedisField], payload)

        await client.xadd(
            topic,
            redis_payload,
            maxlen=10000,
            approximate=True,
        )

    async def consume(
        self,
        topic: str,
        group: str,
    ) -> List[Dict[str, Any]]:

        client = await self._client()
        consumer_name = f"{group}-consumer"

        try:
            await client.xgroup_create(
                topic,
                group,
                id="0",
                mkstream=True,
            )
        except Exception:
            pass

        records = await client.xreadgroup(
            group,
            consumer_name,
            {topic: ">"},
            count=100,
        )

        messages: List[Dict[str, Any]] = []

        for _, entries in records:
            for entry_id, payload in entries:

                normalized: Dict[str, Any] = {}

                for key, value in payload.items():
                    try:
                        normalized[key] = json.loads(value)
                    except (TypeError, json.JSONDecodeError):
                        normalized[key] = value

                normalized["_id"] = entry_id

                messages.append(normalized)

                await client.xack(topic, group, entry_id)

        return messages

    async def add_event(
        self,
        stream_name: str,
        data: Dict[str, Any],
    ) -> None:
        await self.publish(stream_name, data)

    async def read_group(
        self,
        stream_name: str,
        group_name: str,
        consumer_name: str,
    ) -> List[Dict[str, Any]]:

        client = await self._client()

        try:
            await client.xgroup_create(
                stream_name,
                group_name,
                id="0",
                mkstream=True,
            )
        except Exception:
            pass

        entries = await client.xreadgroup(
            group_name,
            consumer_name,
            {stream_name: ">"},
            count=100,
        )

        return [
            {
                "stream": stream,
                "entries": records,
            }
            for stream, records in entries
        ]
