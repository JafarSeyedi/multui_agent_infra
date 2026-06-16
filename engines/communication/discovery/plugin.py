# engines/communication/discovery/plugin.py
from __future__ import annotations

from abc import ABC, abstractmethod

from ..models.communication_models import Endpoint


class ServiceDiscovery(ABC):
    """Abstract service discovery."""

    name: str = "base"

    @abstractmethod
    async def resolve(self, service_name: str) -> list[Endpoint]:
        ...

    @abstractmethod
    async def register(self, service_name: str, endpoint: Endpoint) -> None:
        ...

    @abstractmethod
    async def deregister(self, service_name: str, endpoint: Endpoint) -> None:
        ...
