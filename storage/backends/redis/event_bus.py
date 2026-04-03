import json
import asyncio
from typing import Callable, Any
from .connection import RedisManager

class RedisEventBus:
    """
    High-speed message bus for Agent communication using Redis Pub/Sub.
    """
    def __init__(self, manager: RedisManager):
        self.manager = manager

    async def publish(self, channel: str, message: Any):
        client = await self.manager.get_client()
        payload = json.dumps(message)
        await client.publish(channel, payload)

    async def subscribe(self, channel: str, handler: Callable):
        client = await self.manager.get_client()
        pubsub = client.pubsub()
        await pubsub.subscribe(channel)
        
        async def listen():
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    data = json.loads(message['data'])
                    await handler(data)
        
        asyncio.create_task(listen())
