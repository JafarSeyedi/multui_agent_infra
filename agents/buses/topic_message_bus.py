# agents/buses/topic_message_bus.py

# Topic-Based (Pub/Sub) Bus
# عامل‌ها به topic subscribe می‌کنند، نه recipient مشخص.

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Awaitable, Callable, Dict, List, Optional
from .base import MessageBus, HandlerType
from config.models.system.interaction_models import AgentMessage

logger = logging.getLogger(__name__)

class TopicMessageBus(MessageBus):
    """Agents subscribe to topics; messages are routed by topic, not recipient."""

    def __init__(self) -> None:
        self._topics: dict[str, list[HandlerType]] = defaultdict(list)

    def subscribe(self, topic: str, handler: HandlerType) -> None:
        self._topics[topic].append(handler)

    def unsubscribe(self, topic: str, handler: HandlerType) -> None:
        try:
            self._topics[topic].remove(handler)
        except ValueError:
            pass

    async def publish(self, topic: str, message: AgentMessage) -> None:
        handlers = list(self._topics.get(topic, []))
        if not handlers:
            return
        results = await asyncio.gather(*[h(message) for h in handlers], return_exceptions=True)
        for h, r in zip(handlers, results):
            if isinstance(r, Exception):
                logger.error("Topic %r handler %r failed: %r", topic, h, r)
