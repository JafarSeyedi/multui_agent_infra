from __future__ import annotations

from typing import Any

import pytest

from engines.agent.models import AgentInput, AgentOutput
from engines.orchestration.multi_agent.plugins import BasePlugin, PluginRegistry
from engines.session.service import InMemorySessionService


class FakeAgent:
    def __init__(self):
        self.last_input: AgentInput | None = None

    async def run(self, input_data: AgentInput) -> AgentOutput:
        self.last_input = input_data
        return AgentOutput(
            agent_name="fake_agent",
            message=f"echo: {input_data.message}",
        )


class TrackingPlugin(BasePlugin):
    def __init__(self):
        self.starts: list[tuple[str, str, str]] = []
        self.ends: list[tuple[str, str, str]] = []
        self.befores: list[str] = []
        self.afters: list[str] = []

    async def on_session_start(
        self, app_name: str, user_id: str, session_id: str,
    ) -> None:
        self.starts.append((app_name, user_id, session_id))

    async def on_session_end(
        self, app_name: str, user_id: str, session_id: str,
    ) -> None:
        self.ends.append((app_name, user_id, session_id))

    async def before_agent_execution(
        self, agent_name: str, input_data: object,
    ) -> object | None:
        self.befores.append(agent_name)
        return None

    async def after_agent_execution(
        self, agent_name: str, input_data: object, output_data: object,
    ) -> None:
        self.afters.append(agent_name)


class TestRunnerWithPlugins:

    @pytest.fixture
    def plugin(self):
        return TrackingPlugin()

    @pytest.fixture
    def runner(self, plugin):
        from engines.orchestration.multi_agent.runner import Runner
        plugins = PluginRegistry()
        plugins.register(plugin)
        return Runner(
            agent=FakeAgent(),
            app_name="test_app",
            session_service=InMemorySessionService(),
            plugins=plugins,
        )

    async def test_session_start_fired(self, runner, plugin):
        async for _ in runner.run_async("user1", "sess1", "hello"):
            pass
        assert len(plugin.starts) == 1
        assert plugin.starts[0] == ("test_app", "user1", "sess1")

    async def test_session_end_fired(self, runner, plugin):
        async for _ in runner.run_async("user1", "sess1", "hello"):
            pass
        assert len(plugin.ends) == 1
        assert plugin.ends[0] == ("test_app", "user1", "sess1")

    async def test_before_agent_fired(self, runner, plugin):
        async for _ in runner.run_async("user1", "sess1", "hello"):
            pass
        assert "runner" in plugin.befores

    async def test_after_agent_fired(self, runner, plugin):
        async for _ in runner.run_async("user1", "sess1", "hello"):
            pass
        assert "runner" in plugin.afters

    async def test_plugin_order(self, runner, plugin):
        async for _ in runner.run_async("user1", "sess1", "msg"):
            pass
        # start -> before -> after -> end
        assert len(plugin.starts) == 1
        assert len(plugin.befores) == 1
        assert len(plugin.afters) == 1
        assert len(plugin.ends) == 1
