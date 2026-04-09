# tests/agents/orchestration/interaction/unit/test_memory_augmented_strategy.py

import pytest
from agents.orchestration.interaction.memory_augmented_strategy import MemoryAugmentedStrategy
from agents.orchestration.models import OrchestrationRequest

from .conftest import TestAgent, make_task


@pytest.mark.asyncio
async def test_memory_augmented_strategy_updates_memory_and_prioritizes(registry, message_bus):
    registry.register(TestAgent("alpha", lambda payload: {"value": "alpha"}))
    registry.register(TestAgent("beta", lambda payload: {"value": "beta"}))
    registry.register(TestAgent("gamma", lambda payload: {"value": "gamma"}))

    request = OrchestrationRequest(
        tasks=[
            make_task("alpha", "task_alpha", {}),
            make_task("beta", "task_beta", {}),
            make_task("gamma", "task_gamma", {}),
        ],
        context={"long_term_memory": [{"agent": "gamma", "output": {"value": "old"}}]},
        metadata={},
    )

    strategy = MemoryAugmentedStrategy(registry=registry, message_bus=message_bus, max_memory_size=2)
    result = await strategy.execute(request)

    memory = result.final_context["long_term_memory"]
    assert len(memory) <= 2
    assert memory[-1]["agent"] == "gamma"
    assert result.results[0].agent_name == "gamma"  # اولویت یافته به‌دلیل حافظه


@pytest.mark.asyncio
async def test_memory_augmented_strategy_handles_agent_errors_without_crash(registry, message_bus):
    async def fallible(payload):
        raise RuntimeError("network")

    registry.register(TestAgent("faulty", fallible))
    request = OrchestrationRequest(
        tasks=[make_task("faulty", "bad_task", {})],
        context={},
    )

    strategy = MemoryAugmentedStrategy(registry=registry, message_bus=message_bus, max_memory_size=1)
    result = await strategy.execute(request)

    assert not result.success
    assert any(r.error for r in result.results)
