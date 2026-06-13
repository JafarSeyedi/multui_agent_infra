from __future__ import annotations

import asyncio
import logging

from .base_message_bus import HandlerType
from .base_message_bus import MessageBus
from .message_models import AgentMessage

logger = logging.getLogger(__name__)


class DurableMessageBus(MessageBus):
    """Queue-based durable bus."""

    def __init__(self, maxsize: int = 0) -> None:
        self._queues: dict[str, asyncio.Queue["AgentMessage"]] = {}
        self._maxsize = maxsize
        self._consumer_tasks: dict[str, asyncio.Task] = {}

    async def subscribe(self, recipient: str, handler: HandlerType) -> None:
        if recipient not in self._queues:
            self._queues[recipient] = asyncio.Queue(maxsize=self._maxsize)
        if recipient not in self._consumer_tasks:
            self._consumer_tasks[recipient] = asyncio.create_task(self._consume(recipient, handler))

    async def unsubscribe(self, recipient: str, handler: HandlerType) -> None:
        task = self._consumer_tasks.pop(recipient, None)
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    async def publish(self, message: "AgentMessage") -> None:
        q = self._queues.get(message.recipient)
        if q is None:
            logger.warning("No queue for recipient %r", message.recipient)
            return
        await q.put(message)

    async def _consume(self, recipient: str, handler: HandlerType) -> None:
        q = self._queues[recipient]
        try:
            while True:
                msg = await q.get()
                try:
                    await handler(msg)
                except Exception as e:
                    logger.error("Handler error: %r", e)
        except asyncio.CancelledError:
            pass
