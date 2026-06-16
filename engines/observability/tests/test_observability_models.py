# engines/observability/tests/test_observability_models.py
from engines.observability.models.observability_models import MetricPoint, LogEntry, Span
from engines.observability.models.parsers.metrics_parser import parse_metric_point
from engines.observability.models.writers.metrics_writer import write_metric_point


def test_metric_point():
    m = MetricPoint(name="requests.count", value=1.0, tags={"host": "web-1"})
    assert m.name == "requests.count"


def test_metric_roundtrip():
    m = MetricPoint(name="cpu", value=0.5, tags={"region": "us-east"})
    data = write_metric_point(m)
    parsed = parse_metric_point(data)
    assert parsed.name == "cpu"
    assert parsed.value == 0.5


def test_log_entry():
    entry = LogEntry(level="error", message="timeout", context={"service": "db"})
    assert entry.level == "error"


def test_span():
    s = Span(span_id="abc", name="http.request")
    assert s.name == "http.request"
