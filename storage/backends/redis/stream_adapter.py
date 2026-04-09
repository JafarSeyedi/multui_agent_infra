from typing import Union
from redis.asyncio import Redis, RedisCluster
from .connection import RedisManager


class RedisStreamAdapter:
    """
    Uses Redis Streams for durable event logging and task distribution.
    Supports Consumer Groups for scaling agent processing.
    """

    def __init__(self, manager: RedisManager) -> None:
        self.manager = manager

    async def _client(self) -> Union[Redis, RedisCluster]:
        client = await self.manager.get_client()
        if client is None:
            raise RuntimeError("Redis client is not connected.")
        return client

    async def add_event(self, stream_name: str, data: dict) -> None:
        client = await self._client()
        await client.xadd(stream_name, data, maxlen=10000, approximate=True)

    async def read_group(self, stream_name: str, group_name: str, consumer_name: str):
        client = await self._client()
        return await client.xreadgroup(group_name, consumer_name, {stream_name: ">"}, count=1)
