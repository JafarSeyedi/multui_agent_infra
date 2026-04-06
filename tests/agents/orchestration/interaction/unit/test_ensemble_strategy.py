# tests/agents/orchestration/interaction/unit/test_ensemble_strategy.py

import pytest
from agents.orchestration.interaction.ensemble_strategy import EnsembleStrategy
from agents.orchestration.models import OrchestrationRequest, TaskDefinition

from .conftest import TestAgent, make_task


@pytest.mark.asyncio
async def test_ensemble_strategy_default_vote(registry, message_bus):
    registry.register(TestAgent("agent_a", lambda payload: {"final_answer": "cat"}))
    registry.register(TestAgent("agent_b", lambda payload: {"final_answer": "dog"}))
    registry.register(TestAgent("agent_c", lambda payload: {"final_answer": "cat"}))

    request = OrchestrationRequest(
        tasks=[
            make_task("agent_a", "task_a", {}),
            make_task("agent_b", "task_b", {}),
            make_task("agent_c", "task_c", {}),
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

    request = OrchestrationRequest(
        tasks=[make_task("voter_one", "task1", {}), make_task("voter_two", "task2", {})],
        metadata={},
    )

    strategy = EnsembleStrategy(registry=registry, message_bus=message_bus, aggregator_agent="aggregator")
    result = await strategy.execute(request)

    assert result.final_context["ensemble_vote"] == {"merged": ["x", "y"]}
    assert len(result.results) == 2
