# engines/communication/load_balancing/backends/round_robin/round_robin_lb.py
from __future__ import annotations

from typing import Any

from ....models.communication_models import Endpoint
from ...plugin import LoadBalancer


class RoundRobinLoadBalancer(LoadBalancer):
    """Round-robin load balancer."""

    name = "round_robin"

    def __init__(self) -> None:
        self._index = 0

    def select(self, endpoints: list[Endpoint], context: dict[str, Any] | None = None) -> Endpoint:
        if not endpoints:
            raise ValueError("No endpoints available")
        idx = self._index % len(endpoints)
        self._index += 1
        return endpoints[idx]
