# engines/communication/pubsub/decorators/metrics.py
from __future__ import annotations

from ...models.communication_models import ChannelMessage
from ..plugin import PubSubChannel


class MetricsPubSub(PubSubChannel):
    def __init__(self, inner: PubSubChannel) -> None:
        self._inner = inner
        self.publish_count = 0

    async def publish(self, topic: str, message: ChannelMessage) -> None:
        self.publish_count += 1
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
