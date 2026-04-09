# tests/agents/orchestration/interaction/performance/test_conditional_strategy_performance.py

import time

import pytest
from agents.orchestration.interaction.conditional_strategy import ConditionalStrategy
from agents.orchestration.models import OrchestrationRequest, TaskDefinition

from tests.agents.orchestration.interaction.interaction_unit.conftest import TestAgent


@pytest.mark.asyncio
async def test_conditional_chain_performance(registry, message_bus):
    steps = 25
    for idx in range(steps):
        registry.register(
            TestAgent(
                f"step_{idx}",
                lambda payload, idx=idx: {"route": f"step_{idx + 1}"} if idx + 1 < steps else {"route": None},
            )
        )

    tasks = [
        TaskDefinition(
            task_id=f"step_{idx}",
            agent_name=f"step_{idx}",
            payload={},
            routes={"default": f"step_{idx + 1}"},
        )
        for idx in range(steps)
    ]

    strategy = ConditionalStrategy(registry=registry, message_bus=message_bus)
    request = OrchestrationRequest(tasks=tasks, context={"start": True}, metadata={"start_task": "step_0"})

    start = time.perf_counter()
    result = await strategy.execute(request)
    duration = time.perf_counter() - start

    assert duration < 1.2
    assert len(result.results) == steps
