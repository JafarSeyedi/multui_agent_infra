from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engines.communication.buses.message_models import AgentMessage

import asyncio
import logging

from .base_message_bus import HandlerType
from .base_message_bus import MessageBus

_agent_message_cls = None
def _get_agent_message():
    global _agent_message_cls
    if _agent_message_cls is None:
        from engines.communication.buses.message_models import AgentMessage as _agent_message_cls
    return _agent_message_cls

logger = logging.getLogger(__name__)

class RequestReplyBus(MessageBus):
    """RPC-style request/reply bus."""

    def __init__(self) -> None:
        self._handlers: dict[str, HandlerType] = {}

    async def subscribe(self, recipient: str, handler: HandlerType) -> None:
        self._handlers[recipient] = handler

    async def unsubscribe(self, recipient: str, handler: HandlerType) -> None:
        self._handlers.pop(recipient, None)

    async def publish(self, message: "AgentMessage") -> None:
        """Not supported in request/reply pattern."""
        raise NotImplementedError("Use request() instead of publish()")

    async def request(self, message: "AgentMessage", timeout: float = 5.0) -> "AgentMessage":
        handler = self._handlers.get(message.recipient)
        if not handler:
            raise ValueError(f"No handler for {message.recipient!r}")

        result = await asyncio.wait_for(handler(message), timeout=timeout)

        if result is None:
            raise ValueError(f"Handler for {message.recipient!r} returned no response")

        return result
