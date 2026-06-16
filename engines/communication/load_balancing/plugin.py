# engines/communication/load_balancing/plugin.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ..models.communication_models import Endpoint


class LoadBalancer(ABC):
    """Abstract load balancer."""

    name: str = "base"

    @abstractmethod
    def select(self, endpoints: list[Endpoint], context: dict[str, Any] | None = None) -> Endpoint:
        ...
