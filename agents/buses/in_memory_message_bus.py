# agents/buses/in_memory_message_bus.py

import asyncio
import logging
from collections import defaultdict
from typing import Dict, List
from .base import MessageBus, HandlerType
from agents.interaction.interaction_models import AgentMessage

logger = logging.getLogger(__name__)
BROADCAST = "*"


class InMemoryMessageBus(MessageBus):
    """In-memory async bus with broadcast support."""

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[HandlerType]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def subscribe(self, recipient: str, handler: HandlerType) -> None:
        async with self._lock:
            self._subscribers[recipient].append(handler)

    async def unsubscribe(self, recipient: str, handler: HandlerType) -> None:
        async with self._lock:
            try:
                self._subscribers[recipient].remove(handler)
                if not self._subscribers[recipient]:
                    del self._subscribers[recipient]
            except (ValueError, KeyError):
                pass

    async def publish(self, message: AgentMessage) -> None:
        async with self._lock:
            handlers = list(self._subscribers.get(message.recipient, []))
            broadcast = list(self._subscribers.get(BROADCAST, []))
            all_handlers = handlers + [h for h in broadcast if h not in handlers]

        if not all_handlers:
            return

        results = await asyncio.gather(*[h(message) for h in all_handlers], return_exceptions=True)
        for handler, result in zip(all_handlers, results):
            if isinstance(result, Exception):
                logger.error("Handler %r failed: %r", handler, result, exc_info=result)
