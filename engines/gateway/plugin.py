# engines/gateway/plugin.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional


class IApiGateway(ABC):
    name: str = "base"

    @abstractmethod
    async def route(self, method: str, path: str, headers: dict[str, str], body: Any = None) -> dict[str, Any]: ...


class IRateLimiter(ABC):
    name: str = "base"

    @abstractmethod
    async def check(self, key: str, max_requests: int, window_seconds: float) -> bool: ...


class IRouter(ABC):
    name: str = "base"

    @abstractmethod
    async def resolve(self, path: str, method: str) -> Optional[str]: ...
