# engines/communication/tests/test_priority.py
import pytest
from engines.communication.priority.backends.priority_message.priority_queue import InMemoryPriorityQueue
from engines.communication.models.communication_models import ChannelMessage, MessagePriority


@pytest.mark.asyncio
async def test_priority_ordering():
    channel = InMemoryPriorityQueue()
    await channel.start()

    low = ChannelMessage(id="low", source="test", type="e", priority=MessagePriority.LOW)
    high = ChannelMessage(id="high", source="test", type="e", priority=MessagePriority.HIGH)
    normal = ChannelMessage(id="normal", source="test", type="e", priority=MessagePriority.NORMAL)

    await channel.enqueue(low)
    await channel.enqueue(high)
    await channel.enqueue(normal)

    msg1 = await channel.dequeue()
    msg2 = await channel.dequeue()
    msg3 = await channel.dequeue()

    assert msg1.id == "high"
    assert msg2.id == "normal"
    assert msg3.id == "low"
    await channel.stop()


@pytest.mark.asyncio
async def test_empty_dequeue():
    channel = InMemoryPriorityQueue()
    await channel.start()
    result = await channel.dequeue()
    assert result is None
    await channel.stop()
