# engines/persistence/tests/test_persistence_backends.py
import pytest
from engines.persistence.backends.in_memory_persistence import InMemoryVectorStore, InMemoryBlobStorage


@pytest.mark.asyncio
async def test_vector_store_upsert_and_search():
    store = InMemoryVectorStore()
    await store.upsert("docs", "1", [1.0, 0.0], {"title": "doc1"})
    await store.upsert("docs", "2", [0.0, 1.0], {"title": "doc2"})
    results = await store.search("docs", [1.0, 0.0], top_k=2)
    assert len(results) == 2
    assert results[0]["id"] == "1"
    assert results[0]["score"] > 0.99


@pytest.mark.asyncio
async def test_vector_store_empty_collection():
    store = InMemoryVectorStore()
    results = await store.search("empty", [1.0, 0.0])
    assert results == []


@pytest.mark.asyncio
async def test_vector_store_delete():
    store = InMemoryVectorStore()
    await store.upsert("docs", "1", [1.0, 0.0], {})
    await store.delete("docs", "1")
    results = await store.search("docs", [1.0, 0.0])
    assert len(results) == 0


@pytest.mark.asyncio
async def test_blob_upload_download():
    store = InMemoryBlobStorage()
    path = await store.upload("test.txt", b"hello world")
    assert path == "test.txt"
    data = await store.download("test.txt")
    assert data == b"hello world"


@pytest.mark.asyncio
async def test_blob_missing():
    store = InMemoryBlobStorage()
    data = await store.download("nonexistent.txt")
    assert data is None


@pytest.mark.asyncio
async def test_blob_delete():
    store = InMemoryBlobStorage()
    await store.upload("tmp.bin", b"data")
    await store.delete("tmp.bin")
    assert await store.download("tmp.bin") is None
