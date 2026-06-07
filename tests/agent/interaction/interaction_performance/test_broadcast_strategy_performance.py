# tests/agents/orchestration/interaction/performance/test_broadcast_strategy_performance.py
import time

import pytest

from engines.agent.base_agents.base_agent import BaseAgent
from engines.interaction.broadcast_strategy import BroadcastStrategy
from engines.interaction.interaction_models import InteractionRequest
from tests.agent.interaction.interaction_unit.conftest import TestAgent


@pytest.mark.asyncio
async def test_broadcast_with_many_agents(registry, message_bus):
    for idx in range(70):
        registry.register(TestAgent(f"agent_{idx}", lambda payload, idx=idx: {"value": idx}))

    agents = [
        BaseAgent(agent_id=f"agent_{idx}", agent_name=f"agent_{idx}", payload={})
        for idx in range(70)
    ]

    strategy = BroadcastStrategy(registry=registry, message_bus=message_bus)
    request = InteractionRequest(agents=agents, metadata={"aggregator": "list"})

    start = time.perf_counter()
    result = await strategy.execute(request)
    duration = time.perf_counter() - start

    assert duration < 1.3
    assert len(result.results) == 70
    assert isinstance(result.final_context["broadcast_output"], list)
