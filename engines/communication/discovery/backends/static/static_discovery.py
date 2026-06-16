# engines/communication/discovery/backends/static/static_discovery.py
from __future__ import annotations

from ....models.communication_models import Endpoint
from ...plugin import ServiceDiscovery


class StaticDiscovery(ServiceDiscovery):
    """Static list-based discovery — endpoints defined in config."""

    name = "static"

    def __init__(self, endpoints: dict[str, list[Endpoint]] | None = None) -> None:
        self._endpoints: dict[str, list[Endpoint]] = endpoints or {}

    async def resolve(self, service_name: str) -> list[Endpoint]:
        return self._endpoints.get(service_name, [])

    async def register(self, service_name: str, endpoint: Endpoint) -> None:
        self._endpoints.setdefault(service_name, []).append(endpoint)

    async def deregister(self, service_name: str, endpoint: Endpoint) -> None:
        self._endpoints[service_name] = [e for e in self._endpoints.get(service_name, []) if e != endpoint]
