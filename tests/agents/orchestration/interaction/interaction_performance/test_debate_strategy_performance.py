# tests/agents/orchestration/interaction/performance/test_debate_strategy_performance.py

import time

import pytest
from agents.orchestration.interaction.debate_strategy import DebateStrategy
from agents.orchestration.models import OrchestrationRequest, TaskDefinition

from tests.agents.orchestration.interaction.interaction_unit.conftest import TestAgent


@pytest.mark.asyncio
async def test_debate_rounds_up_to_max(registry, message_bus):
    registry.register(TestAgent("proposer", lambda payload: "p"))
    registry.register(TestAgent("critic", lambda payload: {"approved": False}))

    tasks = [
        TaskDefinition(task_id="proposer", agent_name="proposer", payload={}),
        TaskDefinition(task_id="critic", agent_name="critic", payload={}),
    ]

    strategy = DebateStrategy(registry=registry, message_bus=message_bus)
    request = OrchestrationRequest(tasks=tasks, context={}, metadata={"max_rounds": 8})

    start = time.perf_counter()
    result = await strategy.execute(request)
    duration = time.perf_counter() - start

    assert duration < 1.5
    assert len(result.results) == 16  # 8 proposer + 8 critic rounds