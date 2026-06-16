# engines/communication/pubsub/decorators/durable.py
from __future__ import annotations

from ...models.communication_models import ChannelMessage
from ..plugin import PubSubChannel


class DurablePubSub(PubSubChannel):
    def __init__(self, inner: PubSubChannel) -> None:
        self._inner = inner
        self._store: list[ChannelMessage] = []

    async def publish(self, topic: str, message: ChannelMessage) -> None:
        self._store.append(message)
        await self._inner.publish(topic, message)

    async def subscribe(self, topic: str, handler) -> None:
        await self._inner.subscribe(topic, handler)

    async def unsubscribe(self, topic: str, handler) -> None:
        await self._inner.unsubscribe(topic, handler)

    async def send(self, message: ChannelMessage) -> None:
        await self.publish(message.subject or "", message)

    async def receive(self, handler) -> None:
        await self.subscribe("*", handler)

    async def start(self) -> None:
        await self._inner.start()

    async def stop(self) -> None:
        await self._inner.stop()

    @property
    def stored_messages(self) -> list[ChannelMessage]:
        return list(self._store)
