from .connection import RedisManager

class RedisStreamAdapter:
    """
    Uses Redis Streams for durable event logging and task distribution.
    Supports Consumer Groups for scaling agent processing.
    """
    def __init__(self, manager: RedisManager):
        self.manager = manager

    async def add_event(self, stream_name: str, data: dict):
        client = await self.manager.get_client()
        # Maxlen prevents the stream from growing infinitely
        await client.xadd(stream_name, data, maxlen=10000, approximate=True)

    async def read_group(self, stream_name: str, group_name: str, consumer_name: str):
        client = await self.manager.get_client()
        # This is where agents read their assigned tasks
        return await client.xreadgroup(group_name, consumer_name, {stream_name: ">"}, count=1)
