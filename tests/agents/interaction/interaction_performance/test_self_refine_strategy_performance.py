# tests/agents/orchestration/interaction/performance/test_self_refine_strategy_performance.py

import time

import pytest
from engines.interaction.self_refine_strategy import SelfRefineStrategy
from engines.interaction.interaction_models import InteractionRequest

from tests.agents.interaction.interaction_unit.conftest import TestAgent


@pytest.mark.asyncio
async def test_self_refine_iteration_performance(registry, message_bus):
    registry.register(TestAgent("generator", lambda payload: "draft"))
    registry.register(TestAgent("critic", lambda payload: {"score": 0.0}))
    registry.register(TestAgent("refiner", lambda payload: "still refining"))

    request = InteractionRequest(
        context={},
        metadata={
            "generator_agent": "generator",
            "critic_agent": "critic",
            "refiner_agent": "refiner",
            "max_refinements": 5,
            "quality_threshold": 1.0,
        },
    )

    strategy = SelfRefineStrategy(registry=registry, message_bus=message_bus)

    start = time.perf_counter()
    result = await strategy.execute(request)
    duration = time.perf_counter() - start

    assert duration < 1.4
    assert result.metadata["iterations"] == 5
