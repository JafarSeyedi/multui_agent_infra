# engines/integration/tests/test_integration_backends.py
import pytest
from engines.integration.backends.in_memory.in_memory_integration import (
    InMemoryConnector,
    InMemoryTransformer,
    InMemorySyncEngine,
)


@pytest.mark.asyncio
async def test_connector_connect_send():
    conn = InMemoryConnector()
    assert await conn.connect({"endpoint": "http://localhost"}) is True
    resp = await conn.send({"msg": "hello"})
    assert resp["status"] == "sent"
    assert len(conn._sent) == 1


@pytest.mark.asyncio
async def test_transformer():
    t = InMemoryTransformer()
    result = await t.transform({"a": 1, "b": 2}, {"x": "a", "y": "b"})
    assert result["x"] == 1
    assert result["y"] == 2


@pytest.mark.asyncio
async def test_transformer_missing_source():
    t = InMemoryTransformer()
    result = await t.transform({"a": 1}, {"x": "a", "y": "missing"})
    assert result["x"] == 1
    assert result["y"] is None


@pytest.mark.asyncio
async def test_sync_engine():
    engine = InMemorySyncEngine()
    result = await engine.sync("source-api", "target-db", [{"id": 1}, {"id": 2}])
    assert result["success_count"] == 2
    assert len(engine._synced) == 2
