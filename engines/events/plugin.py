# engines/events/plugin.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional


class IEventProducer(ABC):
    name: str = "base"

    @abstractmethod
    async def publish(self, topic: str, event: dict[str, Any]) -> None: ...


class IEventConsumer(ABC):
    name: str = "base"

    @abstractmethod
    async def subscribe(self, topic: str, handler_name: str) -> None: ...

    @abstractmethod
    async def consume(self, topic: str) -> Optional[dict[str, Any]]: ...
