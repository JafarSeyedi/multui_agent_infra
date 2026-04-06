# tests/agents/orchestration/performance/test_orchestrator_agent_performance.py
import time

import pytest

from agents.orchestration.orchestrator_agent import OrchestratorAgent


class DummyBackend:
    def __init__(self, *args, **kwargs):
        self.calls = 0

    async def execute(self, request):
        self.calls += 1
        class Result:
            def model_dump(self_inner):
                return {"success": True}
        return Result()


@pytest.mark.asyncio
async def test_run_handles_multiple_invocations_quickly(monkeypatch):
    dummy_backend = DummyBackend()
    monkeypatch.setattr(
        "agents.orchestration.orchestrator_agent.NativeOrchestrationBackend",
        lambda *args, **kwargs: dummy_backend,
    )

    agent = OrchestratorAgent(name="performance", agent_registry=None, message_bus: Optional[MessageBus] = None)
    payload = {"workflow_id": "wf-perf", "scenario": "sequential", "tasks": []}

    start = time.perf_counter()
    for _ in range(30):
        await agent.run(payload)
    duration = time.perf_counter() - start

    assert dummy_backend.calls == 30
    assert duration < 2.0
