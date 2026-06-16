# engines/communication/tests/test_pubsub.py
import pytest
from engines.communication.pubsub.backends.in_memory.in_memory_pubsub import InMemoryPubSub
from engines.communication.models.communication_models import ChannelMessage


@pytest.mark.asyncio
async def test_publish_subscribe():
    channel = InMemoryPubSub()
    await channel.start()
    received = []

    async def handler(msg: ChannelMessage) -> None:
        received.append(msg)

    await channel.subscribe("test-topic", handler)
    msg = ChannelMessage(id="1", source="test", type="test.event")
    await channel.publish("test-topic", msg)
    assert len(received) == 1
    assert received[0].id == "1"
    await channel.stop()


@pytest.mark.asyncio
async def test_unsubscribe():
    channel = InMemoryPubSub()
    await channel.start()
    received = []

    async def handler(msg: ChannelMessage) -> None:
        received.append(msg)

    await channel.subscribe("t", handler)
    await channel.unsubscribe("t", handler)
    await channel.publish("t", ChannelMessage(id="1", source="s", type="t"))
    assert len(received) == 0
    await channel.stop()
