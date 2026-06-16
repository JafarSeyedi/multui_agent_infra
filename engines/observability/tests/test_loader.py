import pytest
from engines.observability.core.loader import discover_trace_definitions


def test_discover_trace_definitions_returns_dict():
    defs = discover_trace_definitions()
    assert isinstance(defs, dict)
