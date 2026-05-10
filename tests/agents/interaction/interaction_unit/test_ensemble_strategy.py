# tests/agents/orchestration/interaction/unit/test_ensemble_strategy.py
import pytest

from engines.interaction.ensemble_strategy import EnsembleStrategy
from engines.interaction.interaction_models import InteractionRequest
from tests.agents.interaction.interaction_unit.conftest import make_agent
from tests.agents.interaction.interaction_unit.conftest import TestAgent


@pytest.mark.asyncio
async def test_ensemble_strategy_default_vote(registry, message_bus):
    registry.register(TestAgent("agent_a", lambda payload: {"final_answer": "cat"}))
    registry.register(TestAgent("agent_b", lambda payload: {"final_answer": "dog"}))
    registry.register(TestAgent("agent_c", lambda payload: {"final_answer": "cat"}))

    request = InteractionRequest(
        agents=[
            make_agent("agent_a", "agent_a"),
            make_agent("agent_b", "agent_b"),
            make_agent("agent_c", "agent_c"),
        ],
    )

    strategy = EnsembleStrategy(registry=registry, message_bus=message_bus)
    result = await strategy.execute(request)

    assert result.final_context["ensemble_vote"] == "cat"
    assert result.success
    assert len(result.results) == 3


@pytest.mark.asyncio
async def test_ensemble_strategy_with_custom_aggregator(registry, message_bus):
    registry.register(TestAgent("voter_one", lambda payload: {"final_answer": "x"}))
    registry.register(TestAgent("voter_two", lambda payload: {"final_answer": "y"}))
    registry.register(TestAgent("aggregator", lambda payload: {"merged": payload["votes"]}))

    request = InteractionRequest(
        agents=[make_agent("voter_one", "agent1"), make_agent("voter_two", "agent2")],
        metadata={},
    )

    strategy = EnsembleStrategy(registry=registry, message_bus=message_bus, aggregator_agent="aggregator")
    result = await strategy.execute(request)

    assert result.final_context["ensemble_vote"] == {"merged": ["x", "y"]}
    assert len(result.results) == 2
