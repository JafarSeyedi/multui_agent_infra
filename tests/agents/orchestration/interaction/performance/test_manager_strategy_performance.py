# tests/agents/orchestration/interaction/performance/test_manager_strategy_performance.py

import asyncio
import time

import pytest
from agents.orchestration.interaction.manager_strategy import ManagerStrategy
from agents.orchestration.models import OrchestrationRequest, TaskDefinition

from .conftest import TestAgent


@pytest.mark.asyncio
async def test_manager_strategy_handles_big_worker_batch(registry, message_bus):
    for idx in range(60):
        registry.register(TestAgent(f"worker_{idx}", lambda payload, idx=idx: {"value": idx}))

    tasks = [
        TaskDefinition(task_id=f"task_{idx}", agent_name=f"worker_{idx}", payload={"input": idx})
        for idx in range(60)
    ]

    request = OrchestrationRequest(tasks=tasks, context={})
    strategy = ManagerStrategy(registry=registry, message_bus=message_bus)

    start = time.perf_counter()
    result = await strategy.execute(request)
    duration = time.perf_counter() - start

    assert duration < 1.5
    assert len(result.results) == 60