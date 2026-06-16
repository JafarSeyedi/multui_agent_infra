# engines/communication/tests/test_request_reply.py
import pytest
from engines.communication.request_reply.backends.in_memory.in_memory_reqreply import InMemoryRequestReply
from engines.communication.models.communication_models import ChannelMessage


@pytest.mark.asyncio
async def test_request_reply():
    channel = InMemoryRequestReply()
    await channel.start()

    async def handler(msg: ChannelMessage) -> ChannelMessage:
        return ChannelMessage(id="resp-1", source="handler", type="response", data={"echo": msg.data})

    await channel.receive(handler)
    req = ChannelMessage(id="req-1", source="test", type="ping", data={"hello": "world"})
    response = await channel.request(req)
    assert response.data["echo"]["hello"] == "world"
    await channel.stop()


@pytest.mark.asyncio
async def test_request_no_handler():
    channel = InMemoryRequestReply()
    await channel.start()
    req = ChannelMessage(id="req-1", source="test", type="ping")
    with pytest.raises(RuntimeError, match="No handler registered"):
        await channel.request(req)
    await channel.stop()
