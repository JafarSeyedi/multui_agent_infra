# engines/communication/pubsub/decorators/circuit_breaker.py
from __future__ import annotations

from enum import Enum

from ...models.communication_models import ChannelMessage
from ..plugin import PubSubChannel


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerPubSub(PubSubChannel):
    def __init__(self, inner: PubSubChannel, threshold: int = 5) -> None:
        self._inner = inner
        self._threshold = threshold
        self._failures = 0
        self.state = CircuitState.CLOSED

    async def publish(self, topic: str, message: ChannelMessage) -> None:
        if self.state == CircuitState.OPEN:
            raise RuntimeError("Circuit breaker is open")
        try:
            await self._inner.publish(topic, message)
            self._failures = 0
            self.state = CircuitState.CLOSED
        except Exception:
            self._failures += 1
            if self._failures >= self._threshold:
                self.state = CircuitState.OPEN
            raise

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
