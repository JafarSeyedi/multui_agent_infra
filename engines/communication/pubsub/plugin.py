# engines/communication/pubsub/plugin.py
from __future__ import annotations

from abc import abstractmethod

from ..plugin import BaseChannel, HandlerType
from ..models.communication_models import ChannelMessage


class PubSubChannel(BaseChannel):
    """Pub-sub channel. Supports topic-based publish and subscribe."""

    @abstractmethod
    async def publish(self, topic: str, message: ChannelMessage) -> None:
        ...

    @abstractmethod
    async def subscribe(self, topic: str, handler: HandlerType) -> None:
        ...

    @abstractmethod
    async def unsubscribe(self, topic: str, handler: HandlerType) -> None:
        ...
