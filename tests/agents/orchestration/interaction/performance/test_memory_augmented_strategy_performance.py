# tests/agents/orchestration/interaction/performance/test_memory_augmented_strategy_performance.py

import time

import pytest
from agents.orchestration.interaction.memory_augmented_strategy import MemoryAugmentedStrategy
from agents.orchestration.models import OrchestrationRequest, TaskDefinition

from .conftest import TestAgent


@pytest.mark.asyncio
async def test_memory_augmented_strategy_manages_large_memory(registry, message_bus):
    for idx in range(30):
        registry.register(TestAgent(f"agent_{idx}", lambda payload, idx=idx: {"value": idx}))

    tasks = [
        TaskDefinition(task_id=f"memory_{idx}", agent_name=f"agent_{idx}", payload={})
        for idx in range(30)
    ]

    strategy = MemoryAugmentedStrategy(registry=registry, message_bus=message_bus, max_memory_size=5)
    request = OrchestrationRequest(tasks=tasks, context={"long_term_memory": []})

    start = time.perf_counter()
    result = await strategy.execute(request)
    duration = time.perf_counter() - start

    assert duration < 1.3
    assert len(result.final_context["long_term_memory"]) <= 5
    