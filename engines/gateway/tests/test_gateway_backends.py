# engines/gateway/tests/test_gateway_backends.py
import pytest
from engines.gateway.backends.in_memory.in_memory_gateway import (
    InMemoryApiGateway,
    InMemoryRateLimiter,
    InMemoryRouter,
)


@pytest.mark.asyncio
async def test_gateway_route_found():
    gw = InMemoryApiGateway(routes={"GET:/health": "health_handler"})
    resp = await gw.route("GET", "/health", {})
    assert resp["status_code"] == 200
    assert "health_handler" in resp["body"]["result"]


@pytest.mark.asyncio
async def test_gateway_route_not_found():
    gw = InMemoryApiGateway(routes={})
    resp = await gw.route("GET", "/unknown", {})
    assert resp["status_code"] == 404


@pytest.mark.asyncio
async def test_rate_limiter_allows():
    limiter = InMemoryRateLimiter()
    assert await limiter.check("client-1", 5, 60.0) is True


@pytest.mark.asyncio
async def test_rate_limiter_blocks():
    limiter = InMemoryRateLimiter()
    for _ in range(3):
        await limiter.check("client-1", 3, 60.0)
    assert await limiter.check("client-1", 3, 60.0) is False


@pytest.mark.asyncio
async def test_router_resolve():
    router = InMemoryRouter({"GET:/users": "users_handler"})
    assert await router.resolve("/users", "GET") == "users_handler"
    assert await router.resolve("/unknown", "GET") is None
