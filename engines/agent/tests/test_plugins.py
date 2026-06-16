import pytest
from engines.agent.plugins import AgentPlugin, PluginRegistry


class DummyPlugin(AgentPlugin):
    def __init__(self, pid: str = "test-plugin"):
        self._pid = pid
        self.activated = False

    def plugin_id(self) -> str:
        return self._pid

    def plugin_type(self) -> str:
        return "AGENT"

    def activate(self, registry: PluginRegistry) -> None:
        self.activated = True

    def deactivate(self) -> None:
        self.activated = False


def test_register_and_get():
    registry = PluginRegistry()
    plugin = DummyPlugin()
    registry.register(plugin)
    assert registry.get("test-plugin") is plugin
    assert registry.list_plugins() == ["test-plugin"]


def test_unregister():
    registry = PluginRegistry()
    plugin = DummyPlugin()
    registry.register(plugin)
    registry.unregister("test-plugin")
    assert registry.get("test-plugin") is None
    assert plugin.activated is False


def test_duplicate_raises():
    registry = PluginRegistry()
    registry.register(DummyPlugin())
    with pytest.raises(ValueError, match="already registered"):
        registry.register(DummyPlugin())


def test_get_by_type():
    registry = PluginRegistry()
    registry.register(DummyPlugin("p1"))
    registry.register(DummyPlugin("p2"))
    assert len(registry.get_by_type("AGENT")) == 2
    assert len(registry.get_by_type("STRATEGY")) == 0


def test_activate_called_on_register():
    registry = PluginRegistry()
    plugin = DummyPlugin()
    assert plugin.activated is False
    registry.register(plugin)
    assert plugin.activated is True
