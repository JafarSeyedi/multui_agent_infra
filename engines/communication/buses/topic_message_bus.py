# engines/communication/buses/topic_message_bus.py
# Topic-Based (Pub/Sub) Bus
# Agents subscribe to topics, not specific recipients.
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engines.communication.buses.message_models import AgentMessage

import asyncio
import logging
from collections import defaultdict

from .base_message_bus import HandlerType
from .base_message_bus import MessageBus

_agent_message_cls = None
def _get_agent_message():
    global _agent_message_cls
    if _agent_message_cls is None:
        from engines.communication.buses.message_models import AgentMessage as _agent_message_cls
    return _agent_message_cls

logger = logging.getLogger(__name__)

class TopicMessageBus(MessageBus):
    """Agents subscribe to topics; messages are routed by topic, not recipient."""

    def __init__(self) -> None:
        self._topics: dict[str, list[HandlerType]] = defaultdict(list)

    async def subscribe(self, recipient: str, handler: HandlerType) -> None:
        """Subscribe to a topic. In this implementation, recipient is the topic name."""
        self._topics[recipient].append(handler)

    async def unsubscribe(self, recipient: str, handler: HandlerType) -> None:
        """Unsubscribe from a topic. In this implementation, recipient is the topic name."""
        try:
            self._topics[recipient].remove(handler)
        except ValueError:
            pass

    async def publish(self, message: "AgentMessage") -> None:
        handlers = list(self._topics.get(message.recipient, []))
        if not handlers:
            return
        results = await asyncio.gather(*[h(message) for h in handlers], return_exceptions=True)
        for h, r in zip(handlers, results):
            if isinstance(r, Exception):
                logger.error("Topic %r handler %r failed: %r", message.recipient, h, r)
