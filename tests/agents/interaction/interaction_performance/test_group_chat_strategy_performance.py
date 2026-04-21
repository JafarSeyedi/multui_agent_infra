# tests/agents/orchestration/interaction/performance/test_group_chat_strategy_performance.py

import time

import pytest
from engines.interaction.group_chat_strategy import GroupChatStrategy
from engines.interaction.interaction_models import InteractionRequest
from engines.agents.base_agents.base_agent import BaseAgent

from tests.agents.interaction.interaction_unit.conftest import TestAgent


@pytest.mark.asyncio
async def test_group_chat_handles_long_history(registry, message_bus):
    for idx in range(6):
        registry.register(TestAgent(f"agent_{idx}", lambda payload, idx=idx: {"message": f"msg_{idx}"}))

    agents = [BaseAgent(agent_id=f"agent_{idx}", agent_name=f"agent_{idx}", payload={}) for idx in range(6)]

    strategy = GroupChatStrategy(registry=registry, message_bus=message_bus, storage=None, default_max_rounds=12)
    request = InteractionRequest(agents=agents, context={}, metadata={"max_rounds": 12})

    start = time.perf_counter()
    result = await strategy.execute(request)
    duration = time.perf_counter() - start

    assert duration < 2.0
    assert len(result.final_context["messages"]) <= 12
