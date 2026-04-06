# tests/agents/orchestration/interaction/performance/test_dag_strategy_performance.py

import time

import pytest
from agents.orchestration.interaction.dag_strategy import DAGStrategy
from agents.orchestration.models import OrchestrationRequest, TaskDefinition

from .conftest import TestAgent


@pytest.mark.asyncio
async def test_dag_performance_with_broad_layers(registry, message_bus):
    num_layers = 4
    per_layer = 8
    for layer in range(num_layers):
        for idx in range(per_layer):
            registry.register(
                TestAgent(
                    f"task_{layer}_{idx}",
                    lambda payload, layer=layer, idx=idx: {f"value_{layer}_{idx}": layer + idx},
                )
            )

    tasks = []
    for layer in range(num_layers):
        for idx in range(per_layer):
            depends_on = []
            if layer > 0:
                depends_on = [f"task_{layer - 1}_{prev_idx}" for prev_idx in range(per_layer)]
            tasks.append(
                TaskDefinition(
                    task_id=f"task_{layer}_{idx}",
                    agent_name=f"task_{layer}_{idx}",
                    payload={},
                    depends_on=depends_on,
                )
            )

    strategy = DAGStrategy(registry=registry, message_bus=message_bus)
    request = OrchestrationRequest(tasks=tasks, context={})

    start = time.perf_counter()
    result = await strategy.execute(request)
    duration = time.perf_counter() - start

    assert duration < 2.0
    assert result.success
    assert len(result.results) == num_layers * per_layer