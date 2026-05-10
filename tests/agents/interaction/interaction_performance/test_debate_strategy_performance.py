# tests/agents/orchestration/interaction/performance/test_debate_strategy_performance.py
import time

import pytest

from engines.agents.base_agents.base_agent import BaseAgent
from engines.interaction.debate_strategy import DebateStrategy
from engines.interaction.interaction_models import InteractionRequest
from tests.agents.interaction.interaction_unit.conftest import TestAgent


@pytest.mark.asyncio
async def test_debate_rounds_up_to_max(registry, message_bus):
    registry.register(TestAgent("proposer", lambda payload: "p"))
    registry.register(TestAgent("critic", lambda payload: {"approved": False}))

    agents = [
        BaseAgent(agent_id="proposer", agent_name="proposer", payload={}),
        BaseAgent(agent_id="critic", agent_name="critic", payload={}),
    ]

    strategy = DebateStrategy(registry=registry, message_bus=message_bus)
    request = InteractionRequest(agents=agents, context={}, metadata={"max_rounds": 8})

    start = time.perf_counter()
    result = await strategy.execute(request)
    duration = time.perf_counter() - start

    assert duration < 1.5
    assert len(result.results) == 16  # 8 proposer + 8 critic rounds
