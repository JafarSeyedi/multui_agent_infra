# engines/communication/buses/base_message_bus.py
from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from collections.abc import Awaitable
from collections.abc import Callable
from typing import Optional

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from engines.communication.buses.message_models import AgentMessage

HandlerType = Callable[["AgentMessage"], Awaitable[Optional["AgentMessage"]]]


class MessageBus(ABC):
    """Abstract base for all message bus implementations."""

    @abstractmethod
    async def publish(self, message: "AgentMessage") -> None:
        """Send a message to the bus."""
        ...

    @abstractmethod
    async def subscribe(self, recipient: str, handler: HandlerType) -> None:
        """Register a handler for messages to a specific recipient."""
        ...

    @abstractmethod
    async def unsubscribe(self, recipient: str, handler: HandlerType) -> None:
        """Remove a previously registered handler."""
        ...

    async def start(self) -> None:
        """Initialize bus resources (connections, channels, etc.)."""
        ...

    async def stop(self) -> None:
        """Clean up bus resources."""
        ...
