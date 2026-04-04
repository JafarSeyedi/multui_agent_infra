from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Awaitable, Callable, Dict, List
from config.models.system.interaction_models import AgentMessage

logger = logging.getLogger(__name__)

HandlerType = Callable[[AgentMessage], Awaitable[None]]


class InMemoryMessageBus:
    """Simple async agent-to-agent bus for local orchestration and tests."""

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[HandlerType]] =  defaultdict(list)

    def subscribe(self, recipient: str, handler: HandlerType) -> None:
        """
        Subscribe a handler coroutine to messages for the given recipient.
        """
        self._subscribers.setdefault(recipient, []).append(handler)

    def unsubscribe(self, recipient: str, handler: HandlerType) -> None:
        """
        Unsubscribe a previously registered handler.
        If the handler is not found, this is a no-op.
        """
        handlers = self._subscribers.get(recipient)
        if not handlers:
            return
        try:
            handlers.remove(handler)
        except ValueError:
            # Handler not registered; ignore
            return
        if not handlers:
            # Clean up empty list to avoid memory leaks over time
            self._subscribers.pop(recipient, None)

    async def publish(self, message: AgentMessage) -> None:
        """
        Publish a message to all handlers subscribed for `message.recipient`.

        - Uses `asyncio.gather(..., return_exceptions=True)` to avoid one failing
          handler bringing down the whole publish call.
        - Logs exceptions for observability.
        """
        handlers = list(self._subscribers.get(message.recipient, []))
        if not handlers:
            return

        coros = [handler(message) for handler in handlers]
        results = await asyncio.gather(*coros, return_exceptions=True)

        for handler, result in zip(handlers, results):
            if isinstance(result, Exception):
                logger.error(
                    "Error in message handler %r for recipient %r: %r",
                    handler,
                    message.recipient,
                    result,
                    exc_info=result,
                )
