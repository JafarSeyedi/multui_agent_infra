# engines/communication/request_reply/backends/in_memory/in_memory_reqreply.py
from __future__ import annotations

from ....models.communication_models import ChannelMessage
from ...plugin import RequestReplyChannel


class InMemoryRequestReply(RequestReplyChannel):
    """In-memory request-reply — direct call pattern for testing."""

    name = "in_memory"

    def __init__(self) -> None:
        self._handler = None
        self._started = False

    async def request(self, message: ChannelMessage, timeout: float = 30.0) -> ChannelMessage:
        if self._handler is None:
            raise RuntimeError("No handler registered")
        result = await self._handler(message)
        if result is None:
            raise TimeoutError("No response from handler")
        return result

    async def send(self, message: ChannelMessage) -> None:
        pass

    async def receive(self, handler) -> None:
        self._handler = handler

    async def start(self) -> None:
        self._started = True

    async def stop(self) -> None:
        self._handler = None
        self._started = False
