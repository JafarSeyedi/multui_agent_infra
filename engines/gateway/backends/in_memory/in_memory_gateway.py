# engines/gateway/backends/in_memory/in_memory_gateway.py
from __future__ import annotations

import time
from typing import Any, Optional

from ...models.gateway_models import RateLimitState
from ...plugin import IApiGateway, IRateLimiter, IRouter


class InMemoryApiGateway(IApiGateway):
    name = "in_memory"

    def __init__(self, routes: dict[str, str] | None = None) -> None:
        self._routes = routes or {}
        self._requests: list[dict[str, Any]] = []

    async def route(self, method: str, path: str, headers: dict[str, str], body: Any = None) -> dict[str, Any]:
        self._requests.append({"method": method, "path": path, "body": body})
        target = self._routes.get(f"{method}:{path}")
        if target is None:
            return {"status_code": 404, "body": {"error": "not found"}}
        return {"status_code": 200, "body": {"result": f"routed to {target}"}}


class InMemoryRateLimiter(IRateLimiter):
    name = "in_memory"

    def __init__(self) -> None:
        self._states: dict[str, RateLimitState] = {}

    async def check(self, key: str, max_requests: int, window_seconds: float) -> bool:
        now = time.time()
        state = self._states.get(key)
        if state is None or (now - state.window_start.timestamp()) > window_seconds:
            self._states[key] = RateLimitState(key=key, count=1)
            return True
        if state.count >= max_requests:
            return False
        state.count += 1
        return True


class InMemoryRouter(IRouter):
    name = "in_memory"

    def __init__(self, routes: dict[str, str] | None = None) -> None:
        self._routes = routes or {}

    async def resolve(self, path: str, method: str) -> Optional[str]:
        return self._routes.get(f"{method}:{path}")
