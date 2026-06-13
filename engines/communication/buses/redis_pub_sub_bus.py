from __future__ import annotations

import asyncio
import logging

from redis.asyncio import Redis

from .base_message_bus import HandlerType
from .base_message_bus import MessageBus
from .message_models import AgentMessage

logger = logging.getLogger(__name__)


class RedisMessageBus(MessageBus):
    """Redis Pub/Sub bus for multi-process communication."""

    def __init__(self, redis: Redis) -> None:
        self._redis = redis
        self._pubsub = redis.pubsub()
        self._handlers: dict[str, list[HandlerType]] = {}
        self._listener_task: asyncio.Task | None = None
        self._running = False

    async def start(self) -> None:
        self._running = True
        self._listener_task = asyncio.create_task(self._listen())

    async def stop(self) -> None:
        self._running = False
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
        await self._pubsub.close()

    async def subscribe(self, recipient: str, handler: HandlerType) -> None:
        if recipient not in self._handlers:
            self._handlers[recipient] = []
            await self._pubsub.subscribe(recipient)
        self._handlers[recipient].append(handler)

    async def unsubscribe(self, recipient: str, handler: HandlerType) -> None:
        if recipient not in self._handlers:
            return
        try:
            self._handlers[recipient].remove(handler)
            if not self._handlers[recipient]:
                del self._handlers[recipient]
                await self._pubsub.unsubscribe(recipient)
        except ValueError:
            pass

    async def publish(self, message: AgentMessage) -> None:
        await self._redis.publish(message.recipient, message.model_dump_json())

    async def _listen(self) -> None:
        while self._running:
            try:
                raw = await self._pubsub.get_message(ignore_subscribe_messages=True, timeout=0.1)
                if raw and raw["type"] == "message":
                    channel = raw["channel"].decode()
                    handlers = self._handlers.get(channel, [])
                    msg = AgentMessage.model_validate_json(raw["data"])
                    await asyncio.gather(*[h(msg) for h in handlers], return_exceptions=True)
            except Exception as e:
                logger.error("Redis listener error: %r", e)
