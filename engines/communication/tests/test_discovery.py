# engines/communication/tests/test_discovery.py
import pytest
from engines.communication.discovery.backends.static.static_discovery import StaticDiscovery
from engines.communication.models.communication_models import Endpoint


@pytest.mark.asyncio
async def test_static_discovery_resolve():
    ep = Endpoint(host="localhost", port=8080, transport="http")
    discovery = StaticDiscovery({"my-service": [ep]})
    results = await discovery.resolve("my-service")
    assert len(results) == 1
    assert results[0].host == "localhost"


@pytest.mark.asyncio
async def test_static_discovery_register():
    discovery = StaticDiscovery()
    ep = Endpoint(host="test", port=9090, transport="grpc")
    await discovery.register("svc", ep)
    results = await discovery.resolve("svc")
    assert len(results) == 1


@pytest.mark.asyncio
async def test_static_discovery_deregister():
    ep = Endpoint(host="h", port=1, transport="http")
    discovery = StaticDiscovery({"s": [ep]})
    await discovery.deregister("s", ep)
    results = await discovery.resolve("s")
    assert len(results) == 0
