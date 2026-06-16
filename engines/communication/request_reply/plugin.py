# engines/communication/request_reply/plugin.py
from __future__ import annotations

from abc import abstractmethod

from ..plugin import BaseChannel
from ..models.communication_models import ChannelMessage


class RequestReplyChannel(BaseChannel):
    """Request-reply channel. Sends a request and waits for a correlated response."""

    @abstractmethod
    async def request(self, message: ChannelMessage, timeout: float = 30.0) -> ChannelMessage:
        ...
