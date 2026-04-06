# agents/buses/base_bus.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Awaitable, Callable
from config.models.system.interaction_models import AgentMessage

HandlerType = Callable[[AgentMessage], Awaitable[None]]


class MessageBus(ABC):
    """Abstract base for all message bus implementations."""

    @abstractmethod
    async def publish(self, message: AgentMessage) -> None:
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
        pass

    async def stop(self) -> None:
        """Clean up bus resources."""
        pass
