import pytest
from engines.observability.plugin import ObservabilityPlugin


def test_observability_plugin_identity():
    plugin = ObservabilityPlugin()
    assert plugin.plugin_id() == "observability"
    assert plugin.plugin_type() == "SKILL"
