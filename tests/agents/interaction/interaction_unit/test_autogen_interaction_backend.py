# tests/agents/orchestration/unit/test_autogen_orchestration_backend.py

import pytest

from engines.interaction.backends.autogen_backend import AutoGenOrchestrationBackend
from engines.buses.base_message_bus import MessageBus, HandlerType


class DummyRegistry1:
    async def execute(self, agent_name, payload):
        return {"ok": agent_name}


class DummyMessageBus2(MessageBus):
    async def publish(self, message):
        pass # intentionally empty
    async def subscribe(self, recipient: str, handler: HandlerType) -> None:
        pass
    async def unsubscribe(self, recipient: str, handler: HandlerType) -> None:
        pass


class DummyResult:
    def __init__(self):
        self.backend_used = None
        self.notes = []

    async def execute(self, *args, **kwargs):
        pass # intentionally empty


class SimpleRequest:
    def __init__(self):
        self.workflow_id = "wf"
        self.scenario = "pipeline"
        self.tasks = []
        self.shared_context = {}
        self.max_rounds = 1
        self.selected_agent = None


@pytest.mark.asyncio
async def test_autogen_falls_back_to_native_note(monkeypatch):
    registry = DummyRegistry1()
    backend = AutoGenOrchestrationBackend(registry=registry, message_bus=DummyMessageBus2())
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
    registry = DummyRegistry1()
    backend = AutoGenOrchestrationBackend(registry=registry, message_bus=DummyMessageBus2())
    monkeypatch.setattr(
        AutoGenOrchestrationBackend,
        "is_available",
        lambda self: True,
    )

    request = SimpleRequest()
    result = await backend.execute(request)

    assert result.backend_used == "autogen-wrapper"
    assert any("AutoGen is available" in note for note in result.notes)