# tests/agents/orchestration/interaction/performance/test_pipeline_strategy_performance.py

import time

import pytest
from agents.orchestration.interaction.pipeline_strategy import PipelineStrategy
from agents.orchestration.models import OrchestrationRequest, TaskDefinition

from tests.agents.orchestration.interaction.interaction_unit.conftest import TestAgent


@pytest.mark.asyncio
async def test_pipeline_scaling_with_many_serial_tasks(registry, message_bus):
    for idx in range(80):
        registry.register(TestAgent(f"step_{idx}", lambda payload, idx=idx: {f"value_{idx}": idx}))

    tasks = [
        TaskDefinition(task_id=f"task_{idx}", agent_name=f"step_{idx}", payload={})
        for idx in range(80)
    ]
    request = OrchestrationRequest(tasks=tasks, context={})
    strategy = PipelineStrategy(registry=registry, message_bus=message_bus)

    start = time.perf_counter()
    result = await strategy.execute(request)
    duration = time.perf_counter() - start

    assert duration < 1.4
    assert len(result.results) == 80
    assert result.success
    