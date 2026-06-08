# tests/agents/orchestration/interaction/performance/test_coordinator_strategy_performance.py
import time

import pytest

from engines.agent.base_agents.base_agent import BaseAgent
from engines.interaction.coordinator_strategy import CoordinatorStrategy
from engines.interaction.interaction_models import InteractionRequest
from tests.agents.interaction.interaction_unit.conftest import TestAgent


@pytest.mark.asyncio
async def test_coordinator_strategy_handles_big_worker_batch(registry, message_bus):
    for idx in range(60):
        registry.register(TestAgent(f"worker_{idx}", lambda payload, idx=idx: {"value": idx}))

    agents = [
        BaseAgent(agent_id=f"agent_{idx}", agent_name=f"worker_{idx}", payload={"input": idx})
        for idx in range(60)
    ]

    request = InteractionRequest(agents=agents, context={})
    strategy = CoordinatorStrategy(registry=registry, message_bus=message_bus)

    start = time.perf_counter()
    result = await strategy.execute(request)
    duration = time.perf_counter() - start

    assert duration < 1.5
    assert len(result.results) == 60
