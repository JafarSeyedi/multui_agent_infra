import pytest
from engines.observability.core.types import Span, Metric, Event
from engines.observability.core.backends import ObservabilityBackend


def test_span_defaults():
    span = Span(name="test.operation")
    assert span.name == "test.operation"
    assert span.attributes == {}
    assert span.status == "ok"


def test_backend_is_abstract():
    with pytest.raises(TypeError):
        ObservabilityBackend()
