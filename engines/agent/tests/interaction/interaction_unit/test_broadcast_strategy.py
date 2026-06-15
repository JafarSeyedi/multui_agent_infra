# tests/agents/orchestration/interaction/unit/test_broadcast_strategy.py
import pytest

from engines.agent.base_agents.base_agent import BaseAgent
from engines.interaction.broadcast_strategy import BroadcastStrategy
from engines.interaction.interaction_models import InteractionRequest
from .conftest import TestAgent


@pytest.mark.asyncio
async def test_broadcast_merge_mode(registry, message_bus):
    registry.register(TestAgent("agent_one", lambda payload: {"value": 1}))
    registry.register(TestAgent("agent_two", lambda payload: {"value": 2}))

    agents = [
        BaseAgent(agent_id="a1", agent_name="agent_one", payload={}),
        BaseAgent(agent_id="a2", agent_name="agent_two", payload={}),
    ]

    request = InteractionRequest(agents=agents, metadata={"aggregator": "merge"})
    strategy = BroadcastStrategy(registry=registry, message_bus=message_bus)

    result = await strategy.execute(request)

    assert result.success
    assert result.final_context["broadcast_output"]["agent_one"]["value"] == 1
    assert result.final_context["broadcast_output"]["agent_two"]["value"] == 2
    assert len(result.results) == 2


@pytest.mark.asyncio
async def test_broadcast_vote_mode_ignores_non_string(registry, message_bus):
    registry.register(TestAgent("text_agent", lambda payload: "blue"))
    registry.register(TestAgent("numeric_agent", lambda payload: {"value": 5}))

    agents = [
        BaseAgent(agent_id="t1", agent_name="text_agent", payload={}),
        BaseAgent(agent_id="t2", agent_name="numeric_agent", payload={}),
    ]

    request = InteractionRequest(agents=agents, metadata={"aggregator": "vote"})
    strategy = BroadcastStrategy(registry=registry, message_bus=message_bus)

    result = await strategy.execute(request)

    assert result.final_context["broadcast_output"] == "blue"
    assert any(r.agent_name == "numeric_agent" and r.success for r in result.results)
