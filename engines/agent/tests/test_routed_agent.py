from __future__ import annotations

import pytest

from engines.agent.base_agents.base_agent import BaseAgent
from engines.agent.base_agents.routed_agent import ErrorContext, RoutedAgent
from engines.agent.callbacks import CallbackContext
from engines.agent.models import AgentInput, AgentOutput


class EchoAgent(BaseAgent[AgentInput, AgentOutput]):
    input_model_class = AgentInput
    output_model_class = AgentOutput

    def __init__(self, agent_id: str, agent_name: str, **kwargs):
        super().__init__(agent_id=agent_id, agent_name=agent_name, **kwargs)

    async def execute(self, input_model: AgentInput) -> AgentOutput:
        return AgentOutput(
            agent_name=self.agent_name,
            message=f"from {self.agent_name}: {input_model.message}",
        )


class FailAgent(EchoAgent):
    async def execute(self, input_model: AgentInput) -> AgentOutput:
        raise ValueError(f"{self.agent_name} failed")


class TestRoutedAgent:

    @pytest.fixture
    def agents(self):
        weather = EchoAgent(agent_id="w1", agent_name="weather")
        greet = EchoAgent(agent_id="g1", agent_name="greeter")
        calc = EchoAgent(agent_id="c1", agent_name="calculator")
        return {"weather": weather, "greeter": greet, "calculator": calc}

    async def test_router_selects_correct_agent(self, agents):
        async def router(ctx, available):
            return "weather"

        routed = RoutedAgent(agent_id="r1", agent_name="root", agents=agents, router=router)
        result = await routed.run(AgentInput(agent_name="root", message="what's the weather?"))
        assert result.message == "from weather: what's the weather?"

    async def test_router_selects_different_agents(self, agents):
        async def router(ctx, available):
            return "greeter"

        routed = RoutedAgent(agent_id="r1", agent_name="root", agents=agents, router=router)
        result = await routed.run(AgentInput(agent_name="root", message="hello"))
        assert result.message == "from greeter: hello"

    async def test_router_returns_none_no_agent_selected(self, agents):
        async def router(ctx, available):
            return None

        routed = RoutedAgent(agent_id="r1", agent_name="root", agents=agents, router=router)
        result = await routed.run(AgentInput(agent_name="root", message="hello"))
        assert result.message == "No agent could handle the request"

    async def test_failover_to_fallback(self, agents):
        agents["weather"] = FailAgent(agent_id="w1", agent_name="weather")

        async def router(ctx, available, error_ctx=None):
            if error_ctx and error_ctx.failed_keys:
                return "greeter"
            return "weather"

        routed = RoutedAgent(agent_id="r1", agent_name="root", agents=agents, router=router)
        result = await routed.run(AgentInput(agent_name="root", message="hi"))
        assert result.message == "from greeter: hi"

    async def test_failover_raises_when_no_fallback(self, agents):
        agents["weather"] = FailAgent(agent_id="w1", agent_name="weather")
        agents["greeter"] = FailAgent(agent_id="g1", agent_name="greeter")

        async def router(ctx, available, error_ctx=None):
            if error_ctx and error_ctx.failed_keys:
                return None
            return "weather"

        routed = RoutedAgent(agent_id="r1", agent_name="root", agents=agents, router=router)
        with pytest.raises(Exception):
            await routed.run(AgentInput(agent_name="root", message="hi"))

    async def test_failed_key_cannot_be_re_selected(self, agents):
        agents["weather"] = FailAgent(agent_id="w1", agent_name="weather")

        async def router(ctx, available, error_ctx=None):
            if error_ctx and error_ctx.failed_keys:
                return "weather"
            return "weather"

        routed = RoutedAgent(agent_id="r1", agent_name="root", agents=agents, router=router)
        with pytest.raises(Exception):
            await routed.run(AgentInput(agent_name="root", message="hi"))

    async def test_router_receives_error_context(self, agents):
        agents["weather"] = FailAgent(agent_id="w1", agent_name="weather")

        captured = []

        async def router(ctx, available, error_ctx=None):
            if error_ctx:
                captured.append(error_ctx)
                return "greeter"
            return "weather"

        routed = RoutedAgent(agent_id="r1", agent_name="root", agents=agents, router=router)
        await routed.run(AgentInput(agent_name="root", message="hi"))
        assert len(captured) == 1
        assert "weather" in captured[0].failed_keys
        assert captured[0].last_error is not None

    async def test_sync_router_string_key(self, agents):
        def router(ctx, available):
            return "calculator"

        routed = RoutedAgent(agent_id="r1", agent_name="root", agents=agents, router=router)
        result = await routed.run(AgentInput(agent_name="root", message="2+2"))
        assert "calculator" in result.message
