# tests/agents/orchestration/unit/test_autogen_orchestration_backend.py

import pytest

from agents.orchestration.autogen_backend import AutoGenOrchestrationBackend


class DummyRegistry:
    async def execute(self, agent_name, payload):
        return {"ok": agent_name}


class DummyMessageBus:
    async def publish(self, message):
        pass


class DummyResult:
    def __init__(self):
        self.backend_used = None
        self.notes = []

    async def execute(self, *args, **kwargs):
        pass


class SimpleRequest:
    def __init__(self):
        self.workflow_id = "wf"
        self.scenario = "sequential"
        self.tasks = []
        self.shared_context = {}
        self.max_rounds = 1
        self.selected_agent = None


@pytest.mark.asyncio
async def test_autogen_falls_back_to_native_note(monkeypatch):
    registry = DummyRegistry()
    backend = AutoGenOrchestrationBackend(registry=registry, message_bus=DummyMessageBus())
    monkeypatch.setattr(
        AutoGenOrchestrationBackend,
        "is_available",
        lambda self: False,
    )

    request = SimpleRequest()
    result = await backend.execute(request)

    assert result.backend_used == "native"
    assert any("AutoGen requested" in note for note in result.notes)


@pytest.mark.asyncio
async def test_autogen_keeps_wrapper_note_when_available(monkeypatch):
    registry = DummyRegistry()
    backend = AutoGenOrchestrationBackend(registry=registry, message_bus=DummyMessageBus())
    monkeypatch.setattr(
        AutoGenOrchestrationBackend,
        "is_available",
        lambda self: True,
    )

    request = SimpleRequest()
    result = await backend.execute(request)

    assert result.backend_used == "autogen-wrapper"
    assert any("AutoGen is available" in note for note in result.notes)