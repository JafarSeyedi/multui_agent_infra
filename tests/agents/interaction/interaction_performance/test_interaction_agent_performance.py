# tests/agents/orchestration/performance/test_interaction_agent_performance.py
import time

import pytest

from engines.agents.base_agents.interaction_agent import InteractionAgent
from engines.interaction.interaction_models import InteractionRequest, InteractionResult
from engines.interaction.backends.base_backend import BaseOrchestrationBackend


class DummyBackend(BaseOrchestrationBackend):
    def __init__(self, *args, **kwargs):
        self.calls = 0

    async def execute(self, request: InteractionRequest) -> InteractionResult:
        self.calls += 1
        class Result(InteractionResult):
            def model_dump(self_inner):
                return {"success": True}
        return Result(results=[])


@pytest.mark.asyncio
async def test_run_handles_multiple_invocations_quickly(monkeypatch):
    dummy_backend = DummyBackend()
    monkeypatch.setattr(
        "engines.agents.base_agents.interaction_agent.NativeOrchestrationBackend",
        lambda *args, **kwargs: dummy_backend,
    )

    agent = InteractionAgent(name="performance", agent_registry=None, message_bus=None)
    payload = {"workflow_id": "wf-perf", "scenario": "pipeline", "tasks": []}

    start = time.perf_counter()
    for _ in range(30):
        await agent.run(payload)
    duration = time.perf_counter() - start

    assert dummy_backend.calls == 30
    assert duration < 2.0
