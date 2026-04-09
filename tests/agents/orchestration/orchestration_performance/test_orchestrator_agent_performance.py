# tests/agents/orchestration/performance/test_orchestrator_agent_performance.py
import time

import pytest

from agents.orchestration.orchestrator_agent import OrchestratorAgent
from agents.orchestration.models import OrchestrationRequest, OrchestrationResult
from agents.orchestration.backends.base_backend import BaseOrchestrationBackend


class DummyBackend(BaseOrchestrationBackend):
    def __init__(self, *args, **kwargs):
        self.calls = 0

    async def execute(self, request: OrchestrationRequest) -> OrchestrationResult:
        self.calls += 1
        class Result(OrchestrationResult):
            def model_dump(self_inner):
                return {"success": True}
        return Result(results=[])


@pytest.mark.asyncio
async def test_run_handles_multiple_invocations_quickly(monkeypatch):
    dummy_backend = DummyBackend()
    monkeypatch.setattr(
        "agents.orchestration.orchestrator_agent.NativeOrchestrationBackend",
        lambda *args, **kwargs: dummy_backend,
    )

    agent = OrchestratorAgent(name="performance", agent_registry=None, message_bus=None)
    payload = {"workflow_id": "wf-perf", "scenario": "pipeline", "tasks": []}

    start = time.perf_counter()
    for _ in range(30):
        await agent.run(payload)
    duration = time.perf_counter() - start

    assert dummy_backend.calls == 30
    assert duration < 2.0
