# engines/communication/tests/test_decorators.py
import pytest
from engines.communication.pubsub.backends.in_memory.in_memory_pubsub import InMemoryPubSub
from engines.communication.pubsub.decorators.durable import DurablePubSub
from engines.communication.pubsub.decorators.logging import LoggingPubSub
from engines.communication.pubsub.decorators.metrics import MetricsPubSub
from engines.communication.pubsub.decorators.circuit_breaker import CircuitBreakerPubSub, CircuitState
from engines.communication.models.communication_models import ChannelMessage


@pytest.mark.asyncio
async def test_durable_decorator():
    inner = InMemoryPubSub()
    durable = DurablePubSub(inner)
    await durable.start()
    msg = ChannelMessage(id="1", source="t", type="t")
    await durable.publish("t", msg)
    assert len(durable.stored_messages) == 1
    await durable.stop()


@pytest.mark.asyncio
async def test_metrics_decorator():
    inner = InMemoryPubSub()
    metrics = MetricsPubSub(inner)
    await metrics.start()
    msg = ChannelMessage(id="1", source="t", type="t")
    await metrics.publish("t", msg)
    await metrics.publish("t", msg)
    assert metrics.publish_count == 2
    await metrics.stop()


@pytest.mark.asyncio
async def test_circuit_breaker():
    class FailingPubSub(InMemoryPubSub):
        async def publish(self, topic, message):
            raise RuntimeError("fail")

    inner = FailingPubSub()
    cb = CircuitBreakerPubSub(inner, threshold=2)
    await cb.start()
    for _ in range(2):
        with pytest.raises(RuntimeError):
            await cb.publish("t", ChannelMessage(id="1", source="t", type="t"))
    assert cb.state == CircuitState.OPEN
    await cb.stop()
