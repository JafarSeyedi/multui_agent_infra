# tests/agents/orchestration/interaction/performance/test_ensemble_strategy_performance.py
import time

import pytest
from agents.interaction.ensemble_strategy import EnsembleStrategy
from agents.interaction.interaction_models import InteractionRequest
from agents.base_agents.base_agent import BaseAgent

from tests.agents.interaction.interaction_unit.conftest import TestAgent


@pytest.mark.asyncio
async def test_ensemble_strategy_scales_with_many_voters(registry, message_bus):
    for idx in range(100):
        registry.register(TestAgent(f"voter_{idx}", lambda payload, idx=idx: {"final_answer": f"vote_{idx % 3}"}))

    agents = [
        BaseAgent(agent_id=f"vote_{idx}", agent_name=f"voter_{idx}", payload={})
        for idx in range(100)
    ]

    strategy = EnsembleStrategy(registry=registry, message_bus=message_bus)
    request = InteractionRequest(agents=agents, context={})

    start = time.perf_counter()
    result = await strategy.execute(request)
    duration = time.perf_counter() - start

    assert duration < 1.2
    assert len(result.results) == 100