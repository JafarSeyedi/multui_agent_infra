from __future__ import annotations

import pytest

from engines.orchestration.multi_agent.plugins import BasePlugin, PluginRegistry


class LoggingPlugin(BasePlugin):
    def __init__(self) -> None:
        self.events: list[str] = []
        self.agent_override: object = None

    async def on_session_start(
        self, app_name: str, user_id: str, session_id: str,
    ) -> None:
        self.events.append(f"start:{app_name}:{user_id}:{session_id}")

    async def on_session_end(
        self, app_name: str, user_id: str, session_id: str,
    ) -> None:
        self.events.append(f"end:{app_name}:{user_id}:{session_id}")

    async def before_agent_execution(
        self, agent_name: str, input_data: object,
    ) -> object | None:
        self.events.append(f"before:{agent_name}")
        return self.agent_override

    async def after_agent_execution(
        self, agent_name: str, input_data: object, output_data: object,
    ) -> None:
        self.events.append(f"after:{agent_name}:{output_data!r}")


class TestPluginRegistry:

    @pytest.fixture
    def registry(self):
        return PluginRegistry()

    @pytest.fixture
    def plugin(self):
        return LoggingPlugin()

    def test_register_and_unregister(self, registry, plugin):
        registry.register(plugin)
        assert len(registry.plugins) == 1
        registry.unregister(plugin)
        assert len(registry.plugins) == 0

    def test_plugins_property_returns_copy(self, registry, plugin):
        registry.register(plugin)
        plugins = registry.plugins
        plugins.clear()
        assert len(registry.plugins) == 1

    async def test_fire_session_start(self, registry, plugin):
        registry.register(plugin)
        await registry.fire_session_start("app", "user", "sess")
        assert "start:app:user:sess" in plugin.events

    async def test_fire_session_end(self, registry, plugin):
        registry.register(plugin)
        await registry.fire_session_end("app", "user", "sess")
        assert "end:app:user:sess" in plugin.events

    async def test_fire_before_agent(self, registry, plugin):
        registry.register(plugin)
        result = await registry.fire_before_agent("agent1", "input")
        assert "before:agent1" in plugin.events
        assert result is None

    async def test_fire_before_agent_with_override(self, registry, plugin):
        plugin.agent_override = "OVERRIDE"
        registry.register(plugin)
        result = await registry.fire_before_agent("agent1", "input")
        assert result == "OVERRIDE"

    async def test_fire_after_agent(self, registry, plugin):
        registry.register(plugin)
        await registry.fire_after_agent("agent1", "input", "output")
        assert "after:agent1:" in plugin.events[0]

    async def test_multiple_plugins(self, registry):
        p1 = LoggingPlugin()
        p2 = LoggingPlugin()
        registry.register(p1)
        registry.register(p2)
        await registry.fire_session_start("app", "u", "s")
        assert len(p1.events) == 1
        assert len(p2.events) == 1

    async def test_before_agent_first_override_wins_and_shortcircuits(self, registry):
        p1 = LoggingPlugin()
        p2 = LoggingPlugin()
        p1.agent_override = "OVERRIDE1"
        registry.register(p1)
        registry.register(p2)
        result = await registry.fire_before_agent("a", "i")
        assert result == "OVERRIDE1"
        # First plugin ran
        assert "before:a" in p1.events
        # Second plugin was short-circuited — not called
        assert len(p2.events) == 0
