# tests/agents/orchestration/interaction/unit/test_debate_strategy.py
import pytest

from engines.agent.base_agents.base_agent import BaseAgent
from engines.interaction.debate_strategy import DebateStrategy
from engines.interaction.interaction_models import InteractionRequest
from .conftest import TestAgent


@pytest.mark.asyncio
async def test_debate_finishes_when_critic_approves(registry, message_bus):
    registry.register(TestAgent("proposer", lambda payload: "proposal"))
    registry.register(TestAgent("critic", lambda payload: {"approved": True}))

    agents = [
        BaseAgent(agent_id="proposer", agent_name="proposer", payload={}),
        BaseAgent(agent_id="critic", agent_name="critic", payload={}),
    ]

    strategy = DebateStrategy(registry=registry, message_bus=message_bus)
    result = await strategy.execute(InteractionRequest(agents=agents, context={}, metadata={"max_rounds": 3}))

    assert result.success
    assert any(r.agent_name == "critic" for r in result.results)
    assert result.final_context["final_answer"] == "proposal"


@pytest.mark.asyncio
async def test_debate_handles_critic_exception(registry, message_bus):
    registry.register(TestAgent("proposer", lambda payload: "proposal"))

    async def critic_fail(payload):
        raise RuntimeError("critic fail")

    registry.register(TestAgent("critic", critic_fail))

    agents = [
        BaseAgent(agent_id="proposer", agent_name="proposer", payload={}),
        BaseAgent(agent_id="critic", agent_name="critic", payload={}),
    ]

    strategy = DebateStrategy(registry=registry, message_bus=message_bus)
    result = await strategy.execute(InteractionRequest(agents=agents, context={}, metadata={"max_rounds": 2}))

    assert result.success
    assert any(r.error for r in result.results if r.agent_name == "critic")
