# tests/agents/orchestration/unit/test_interaction_agent.py
import pytest
from pydantic import ValidationError

from engines.agent.base_agents.interaction_agent import InteractionAgent
from engines.interaction.backends.base_backend import BaseOrchestrationBackend
from engines.interaction.interaction_models import InteractionRequest
from engines.interaction.interaction_models import InteractionResult


class DummyBackend(BaseOrchestrationBackend):
    def __init__(self, *args, **kwargs):
        self.calls = []

    async def execute(self, request: InteractionRequest) -> InteractionResult:
        self.calls.append(request)
        class Result(InteractionResult):
            def model_dump(self_inner):
                return {"success": True}
        return Result(results=[])


@pytest.mark.asyncio
async def test_run_returns_serialized_result(monkeypatch):
    dummy_backend = DummyBackend()
    monkeypatch.setattr(
        "engines.agent.base_agents.interaction_agent.NativeOrchestrationBackend",
        lambda *args, **kwargs: dummy_backend,
    )

    agent = InteractionAgent(name="orc", agent_registry=None, message_bus=None)
    payload = {"workflow_id": "wf-1", "scenario": "pipeline", "tasks": []}
    response = await agent.run(payload)

    assert response["success"] is True
    assert response["workflow"] == "wf-1"
    assert dummy_backend.calls


@pytest.mark.asyncio
async def test_run_raises_when_request_invalid(monkeypatch):
    dummy_backend = DummyBackend()
    monkeypatch.setattr(
        "engines.agent.base_agents.interaction_agent.NativeOrchestrationBackend",
        lambda *args, **kwargs: dummy_backend,
    )

    agent = InteractionAgent(name="orc", agent_registry=None, message_bus=None)
    with pytest.raises(ValidationError):
        await agent.run({"invalid_field": True})
