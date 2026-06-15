# tests/agents/orchestration/interaction/unit/test_self_refine_strategy.py
import pytest

from engines.interaction.interaction_models import InteractionRequest
from engines.interaction.self_refine_strategy import SelfRefineStrategy
from .conftest import TestAgent


@pytest.mark.asyncio
async def test_self_refine_converges_before_max(registry, message_bus):
    registry.register(TestAgent("generator", lambda payload: "draft"))
    registry.register(TestAgent("critic", lambda payload: {"score": 0.95}))
    registry.register(TestAgent("refiner", lambda payload: f"refined-{payload['answer']}"))

    request = InteractionRequest(
        context={},
        metadata={"generator_agent": "generator", "critic_agent": "critic", "refiner_agent": "refiner", "quality_threshold": 0.8},
    )

    strategy = SelfRefineStrategy(registry=registry, message_bus=message_bus)
    result = await strategy.execute(request)

    assert result.success
    assert result.final_context["final_answer"] == "draft"
    assert any(r.agent_name == "critic" for r in result.results)


@pytest.mark.asyncio
async def test_self_refine_handles_refinement_loop(registry, message_bus):
    registry.register(TestAgent("generator", lambda payload: "draft"))
    registry.register(TestAgent("critic", lambda payload: {"score": 0.0}))
    registry.register(TestAgent("refiner", lambda payload: f"iteration-{payload['answer']}"))

    request = InteractionRequest(
        context={},
        metadata={
            "generator_agent": "generator",
            "critic_agent": "critic",
            "refiner_agent": "refiner",
            "quality_threshold": 1.1,
            "max_refinements": 2,
        },
    )

    strategy = SelfRefineStrategy(registry=registry, message_bus=message_bus)
    result = await strategy.execute(request)

    assert result.success
    assert result.metadata["iterations"] == 2
    assert result.metadata["converged_round"] is None
