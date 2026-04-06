# tests/agents/unit/test_message_bus.py
from types import SimpleNamespace

import pytest

from agents.buses.in_memory_message_bus import InMemoryMessageBus


@pytest.mark.asyncio
async def test_publish_dispatches_to_subscribers():
    bus = InMemoryMessageBus()
    received = []

    async def handler(message):
        received.append(message)

    bus.subscribe("agent.x", handler)
    await bus.publish(SimpleNamespace(recipient="agent.x", payload={"ok": True}))

    assert len(received) == 1
    assert received[0].recipient == "agent.x"


@pytest.mark.asyncio
async def test_unsubscribe_removes_handler():
    bus = InMemoryMessageBus()
    received = []

    async def handler(message):
        received.append(message)

    bus.subscribe("agent.x", handler)
    bus.unsubscribe("agent.x", handler)
    await bus.publish(SimpleNamespace(recipient="agent.x"))

    assert not received


@pytest.mark.asyncio
async def test_publish_swallows_handler_exceptions(caplog):
    bus = InMemoryMessageBus()

    async def faulty_handler(message):
        raise RuntimeError("oops")

    bus.subscribe("agent.x", faulty_handler)
    await bus.publish(SimpleNamespace(recipient="agent.x"))

    assert "Error in message handler" in caplog.text