# tests/agents/orchestration/interaction/unit/test_broadcast_strategy.py

import pytest
from agents.orchestration.interaction.broadcast_strategy import BroadcastStrategy
from agents.orchestration.models import OrchestrationRequest, TaskDefinition

from .conftest import TestAgent


@pytest.mark.asyncio
async def test_broadcast_merge_mode(registry, message_bus):
    registry.register(TestAgent("agent_one", lambda payload: {"value": 1}))
    registry.register(TestAgent("agent_two", lambda payload: {"value": 2}))

    tasks = [
        TaskDefinition(task_id="a1", agent_name="agent_one", payload={}),
        TaskDefinition(task_id="a2", agent_name="agent_two", payload={}),
    ]

    request = OrchestrationRequest(tasks=tasks, metadata={"aggregator": "merge"})
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

    tasks = [
        TaskDefinition(task_id="t1", agent_name="text_agent", payload={}),
        TaskDefinition(task_id="t2", agent_name="numeric_agent", payload={}),
    ]

    request = OrchestrationRequest(tasks=tasks, metadata={"aggregator": "vote"})
    strategy = BroadcastStrategy(registry=registry, message_bus=message_bus)

    result = await strategy.execute(request)

    assert result.final_context["broadcast_output"] == "blue"
    assert any(r.agent_name == "numeric_agent" and r.success for r in result.results)