# engines/communication/plugin.py
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Optional

from .models.communication_models import ChannelMessage

HandlerType = Callable[[ChannelMessage], Awaitable[Optional[ChannelMessage]]]


class BaseChannel(ABC):
    """Abstract base for all channel implementations.

    Config selects a backend by dotted import path. No dynamic
    plugin loading — all backends are compiled in.
    """

    name: str = "base"

    @abstractmethod
    async def send(self, message: ChannelMessage) -> None:
        ...

    @abstractmethod
    async def receive(self, handler: HandlerType) -> None:
        ...

    @abstractmethod
    async def start(self) -> None:
        ...

    @abstractmethod
    async def stop(self) -> None:
        ...
