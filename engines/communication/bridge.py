from __future__ import annotations

import logging
from typing import Any

from engines.communication.buses.base_message_bus import MessageBus
from engines.communication.buses.message_models import AgentMessage

__all__ = ["MessageBusBridge", "LoggingBusBridge", "MetricsBusBridge"]

logger = logging.getLogger(__name__)


class MessageBusBridge:
    """Bridge pattern — adds cross-cutting behavior to any MessageBus.

    Separates the MessageBus abstraction from optional concerns like
    logging, metrics, retry, and filtering.
    """

    def __init__(self, bus: MessageBus) -> None:
        self._bus = bus

    async def publish(self, message: AgentMessage) -> None:
        await self._bus.publish(message)

    async def subscribe(self, recipient: str, handler: Any) -> None:
        await self._bus.subscribe(recipient, handler)

    async def unsubscribe(self, recipient: str, handler: Any) -> None:
        await self._bus.unsubscribe(recipient, handler)

    async def start(self) -> None:
        await self._bus.start()

    async def stop(self) -> None:
        await self._bus.stop()


class LoggingBusBridge(MessageBusBridge):
    """Decorates a MessageBusBridge with structured logging."""

    async def publish(self, message: AgentMessage) -> None:
        logger.info("Bus publish: %s -> %s [%s]", message.sender, message.recipient, message.message_type)
        await super().publish(message)

    async def subscribe(self, recipient: str, handler: Any) -> None:
        logger.debug("Bus subscribe: %s", recipient)
        await super().subscribe(recipient, handler)

    async def unsubscribe(self, recipient: str, handler: Any) -> None:
        logger.debug("Bus unsubscribe: %s", recipient)
        await super().unsubscribe(recipient, handler)


class MetricsBusBridge(MessageBusBridge):
    """Tracks message counts and latency."""

    def __init__(self, bus: MessageBus) -> None:
        super().__init__(bus)
        self.publish_count = 0
        self.message_counts: dict[str, int] = {}

    async def publish(self, message: AgentMessage) -> None:
        self.publish_count += 1
        self.message_counts[message.message_type] = self.message_counts.get(message.message_type, 0) + 1
        await super().publish(message)
