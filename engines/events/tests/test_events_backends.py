# engines/events/tests/test_events_backends.py
import pytest
from engines.events.backends.in_memory.in_memory_events import (
    InMemoryEventProducer,
    InMemoryEventConsumer,
)


@pytest.fixture
def bus():
    return {}


@pytest.mark.asyncio
async def test_producer_publish(bus):
    producer = InMemoryEventProducer(bus)
    await producer.publish("orders", {"id": "1"})
    assert "orders" in bus
    assert len(bus["orders"]) == 1


@pytest.mark.asyncio
async def test_consumer_subscribe_consume(bus):
    producer = InMemoryEventProducer(bus)
    consumer = InMemoryEventConsumer(bus)
    await consumer.subscribe("orders", "handler-1")
    await producer.publish("orders", {"id": "1"})
    event = await consumer.consume("orders")
    assert event is not None
    assert event["id"] == "1"


@pytest.mark.asyncio
async def test_consumer_consume_empty(bus):
    consumer = InMemoryEventConsumer(bus)
    await consumer.subscribe("empty", "h")
    result = await consumer.consume("empty")
    assert result is None
