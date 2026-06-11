import pytest
from engines.orchestration.bam.realtime.ring_buffer import RingBuffer
from engines.orchestration.bam.realtime.cep_bridge import CepBridge


def test_ring_buffer_push_and_get():
    buf = RingBuffer(capacity=5)
    buf.push("a")
    buf.push("b")
    buf.push("c")
    items = buf.get_all()
    assert items == ["a", "b", "c"]


def test_ring_buffer_capacity():
    buf = RingBuffer(capacity=3)
    buf.push(1)
    buf.push(2)
    buf.push(3)
    buf.push(4)
    items = buf.get_all()
    assert items == [2, 3, 4]
    assert len(items) == 3


def test_ring_buffer_clear():
    buf = RingBuffer(capacity=10)
    buf.push("a")
    buf.push("b")
    buf.clear()
    assert buf.get_all() == []


def test_ring_buffer_empty():
    buf = RingBuffer(capacity=5)
    assert buf.get_all() == []


@pytest.mark.asyncio
async def test_cep_bridge():
    bridge = CepBridge()
    bridge.register_rule("cpu_high", {"metric": "cpu", "operator": "gt", "value": 90})
    alert = bridge.evaluate("cpu", 95.0)
    assert alert is not None
    assert alert["rule_id"] == "cpu_high"


@pytest.mark.asyncio
async def test_cep_bridge_no_match():
    bridge = CepBridge()
    bridge.register_rule("cpu_high", {"metric": "cpu", "operator": "gt", "value": 90})
    alert = bridge.evaluate("cpu", 50.0)
    assert alert is None
