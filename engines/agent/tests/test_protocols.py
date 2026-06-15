import pytest
from engines.agent.protocols import (
    AgentMessage,
    AgentProtocol,
    InMemoryProtocol,
    A2AProtocol,
    FIPAProtocol,
)


@pytest.mark.asyncio
async def test_in_memory_protocol_connect_disconnect():
    p = InMemoryProtocol()
    await p.connect()
    await p.disconnect()


@pytest.mark.asyncio
async def test_a2a_protocol_rejects_send_without_connect():
    p = A2AProtocol(base_url="http://localhost:9999")
    msg = AgentMessage(sender="a", recipient="b", payload={"test": True})
    with pytest.raises(RuntimeError, match="not connected"):
        await p.send_message(msg)


@pytest.mark.asyncio
async def test_fipa_protocol_connect_disconnect():
    p = FIPAProtocol()
    await p.connect()
    await p.disconnect()


def test_agent_message_defaults():
    msg = AgentMessage(sender="a", recipient="b")
    assert msg.message_type == "request"
    assert msg.message_id == ""
    assert msg.correlation_id == ""


def test_protocol_is_abstract():
    with pytest.raises(TypeError):
        AgentProtocol()
