# engines/communication/priority/plugin.py
from __future__ import annotations

from abc import abstractmethod

from ..plugin import BaseChannel
from ..models.communication_models import ChannelMessage, MessagePriority


class PriorityChannel(BaseChannel):
    """Priority queue channel. Delivers messages ordered by priority level."""

    @abstractmethod
    async def enqueue(self, message: ChannelMessage, priority: MessagePriority | None = None) -> None:
        ...
