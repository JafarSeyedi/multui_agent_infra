
#  Request-Reply Bus
# یک عامل پیام می‌فرستد و منتظر پاسخ می‌ماند (RPC-style).
# agents/buses/request_reply_bus.py

import asyncio
import logging
from typing import Callable, Awaitable, Dict
from .base_message_bus import MessageBus, HandlerType
from engines.interaction.interaction_models import AgentMessage

logger = logging.getLogger(__name__)

class RequestReplyBus(MessageBus):
    """RPC-style request/reply bus."""

    def __init__(self) -> None:
        self._handlers: Dict[str, HandlerType] = {}

    async def subscribe(self, recipient: str, handler: HandlerType) -> None:
        self._handlers[recipient] = handler

    async def unsubscribe(self, recipient: str, handler: HandlerType) -> None:
        self._handlers.pop(recipient, None)

    async def publish(self, message: AgentMessage) -> None:
        """Not supported in request/reply pattern."""
        raise NotImplementedError("Use request() instead of publish()")

    async def request(self, message: AgentMessage, timeout: float = 5.0) -> AgentMessage:
        handler = self._handlers.get(message.recipient)
        if not handler:
            raise ValueError(f"No handler for {message.recipient!r}")
        
        result = await asyncio.wait_for(handler(message), timeout=timeout)
        
        if result is None:
            raise ValueError(f"Handler for {message.recipient!r} returned no response")
        
        return result
