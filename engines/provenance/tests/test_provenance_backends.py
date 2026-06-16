# engines/provenance/tests/test_provenance_backends.py
import pytest
from engines.provenance.backends.in_memory.in_memory_provenance import InMemoryProvenanceTracker


@pytest.mark.asyncio
async def test_record_and_lineage():
    tracker = InMemoryProvenanceTracker()
    eid = await tracker.record("doc-1", "created", "alice")
    assert eid is not None
    await tracker.record("doc-1", "updated", "bob", {"field": "title"})
    lineage = await tracker.get_lineage("doc-1")
    assert len(lineage) == 2
    assert lineage[0]["action"] == "created"
    assert lineage[1]["action"] == "updated"


@pytest.mark.asyncio
async def test_lineage_empty():
    tracker = InMemoryProvenanceTracker()
    lineage = await tracker.get_lineage("nonexistent")
    assert lineage == []


@pytest.mark.asyncio
async def test_lineage_multiple_entities():
    tracker = InMemoryProvenanceTracker()
    await tracker.record("doc-1", "created", "alice")
    await tracker.record("doc-2", "created", "bob")
    assert len(await tracker.get_lineage("doc-1")) == 1
    assert len(await tracker.get_lineage("doc-2")) == 1
