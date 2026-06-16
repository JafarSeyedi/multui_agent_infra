# engines/agentic/tests/test_agentic_backends.py
import pytest
from engines.agentic.backends.in_memory.in_memory_agentic import (
    InMemoryAgentOrchestrator,
    InMemoryAgentDelegate,
)


@pytest.mark.asyncio
async def test_orchestrator_run_workflow():
    orch = InMemoryAgentOrchestrator()
    result = await orch.run_workflow("data_pipeline", {"source": "s3"})
    assert result["status"] == "completed"
    assert "workflow_id" in result


@pytest.mark.asyncio
async def test_orchestrator_get_status():
    orch = InMemoryAgentOrchestrator()
    result = await orch.run_workflow("etl", {})
    status = await orch.get_status(result["workflow_id"])
    assert status == "completed"


@pytest.mark.asyncio
async def test_orchestrator_get_status_unknown():
    orch = InMemoryAgentOrchestrator()
    status = await orch.get_status("nonexistent")
    assert status == "unknown"


@pytest.mark.asyncio
async def test_delegate():
    delegate = InMemoryAgentDelegate()
    result = await delegate.delegate("summarize", {"text": "hello"})
    assert result["status"] == "delegated"
    assert len(delegate._delegations) == 1
