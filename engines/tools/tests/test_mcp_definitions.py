import pytest
from engines.tools.models.mcp.definitions.loader import load_mcp_definitions


def test_load_mcp_definitions_returns_list():
    defs = load_mcp_definitions()
    assert isinstance(defs, list)


def test_load_mcp_definitions_contains_dapr():
    defs = load_mcp_definitions()
    dapr = [d for d in defs if d["id"] == "dapr-mcp"]
    assert len(dapr) == 1
    assert "pubsub" in dapr[0]["tools"]
