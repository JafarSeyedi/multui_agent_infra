# engines/communication/pubsub/backends/in_memory/in_memory_pubsub.py
from __future__ import annotations

from ....plugin import HandlerType
from ....models.communication_models import ChannelMessage
from ...plugin import PubSubChannel


class InMemoryPubSub(PubSubChannel):
    """In-memory pub-sub — for testing and monolith mode."""

    name = "in_memory"

    def __init__(self) -> None:
        self._handlers: dict[str, list[HandlerType]] = {}
        self._started = False

    async def publish(self, topic: str, message: ChannelMessage) -> None:
        handlers = self._handlers.get(topic, [])
        for handler in handlers:
            await handler(message)

    async def subscribe(self, topic: str, handler: HandlerType) -> None:
        self._handlers.setdefault(topic, []).append(handler)

    async def unsubscribe(self, topic: str, handler: HandlerType) -> None:
        handlers = self._handlers.get(topic, [])
        if handler in handlers:
            handlers.remove(handler)

    async def send(self, message: ChannelMessage) -> None:
        await self.publish(message.subject or "", message)

    async def receive(self, handler: HandlerType) -> None:
        await self.subscribe("*", handler)

    async def start(self) -> None:
        self._started = True

    async def stop(self) -> None:
        self._handlers.clear()
        self._started = False
