# engines/observability/tests/test_observability_backends.py
import pytest
from engines.observability.backends.in_memory_observability import (
    InMemoryMetricsCollector,
    InMemoryLogger,
    InMemoryTracer,
)


@pytest.mark.asyncio
async def test_metrics_collector():
    c = InMemoryMetricsCollector()
    await c.increment("req.count", tags={"host": "web-1"})
    await c.gauge("cpu.pct", 0.75)
    await c.histogram("latency.ms", 42.0)
    assert len(c.metrics) == 3
    assert c.metrics[0].name == "req.count"
    assert c.metrics[0].tags["host"] == "web-1"


@pytest.mark.asyncio
async def test_logger():
    logger = InMemoryLogger()
    await logger.log("error", "db connection failed", {"db": "primary"})
    assert len(logger.entries) == 1
    assert logger.entries[0].level == "error"
    assert logger.entries[0].message == "db connection failed"


@pytest.mark.asyncio
async def test_logger_empty_context():
    logger = InMemoryLogger()
    await logger.log("info", "startup complete")
    assert logger.entries[0].context == {}


@pytest.mark.asyncio
async def test_tracer_start_end():
    tracer = InMemoryTracer()
    span_id = await tracer.start_span("http.request")
    assert span_id in tracer.spans
    assert tracer.spans[span_id].end_time is None
    await tracer.end_span(span_id)
    assert tracer.spans[span_id].end_time is not None


@pytest.mark.asyncio
async def test_tracer_with_parent():
    tracer = InMemoryTracer()
    parent = await tracer.start_span("parent")
    child = await tracer.start_span("child", parent_id=parent)
    assert tracer.spans[child].parent_id == parent


@pytest.mark.asyncio
async def test_tracer_end_unknown_span():
    tracer = InMemoryTracer()
    await tracer.end_span("nonexistent")
    assert True
