# engines/artifacts/tests/test_artifacts_backends.py
import pytest
from engines.artifacts.backends.in_memory.in_memory_artifacts import (
    InMemoryArtifactStore,
    InMemoryArtifactVersioner,
)


@pytest.mark.asyncio
async def test_artifact_store_retrieve():
    store = InMemoryArtifactStore()
    aid = await store.store("test.txt", b"hello", {"type": "text"})
    data = await store.retrieve(aid)
    assert data == b"hello"


@pytest.mark.asyncio
async def test_artifact_store_delete():
    store = InMemoryArtifactStore()
    aid = await store.store("tmp", b"data")
    await store.delete(aid)
    assert await store.retrieve(aid) is None


@pytest.mark.asyncio
async def test_artifact_store_missing():
    store = InMemoryArtifactStore()
    assert await store.retrieve("nonexistent") is None


@pytest.mark.asyncio
async def test_versioner_create_get():
    v = InMemoryArtifactVersioner()
    ver1 = await v.create_version("artifact-1", b"v1 data")
    ver2 = await v.create_version("artifact-1", b"v2 data")
    assert ver1 == 1
    assert ver2 == 2
    assert await v.get_version("artifact-1", 1) == b"v1 data"
    assert await v.get_version("artifact-1", 2) == b"v2 data"


@pytest.mark.asyncio
async def test_versioner_missing():
    v = InMemoryArtifactVersioner()
    assert await v.get_version("unknown", 1) is None
