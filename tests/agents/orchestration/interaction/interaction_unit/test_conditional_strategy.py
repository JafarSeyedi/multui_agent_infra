# tests/agents/orchestration/interaction/unit/test_conditional_strategy.py

import pytest
from agents.orchestration.interaction.conditional_strategy import ConditionalStrategy
from agents.orchestration.models import OrchestrationRequest, TaskDefinition

from .conftest import TestAgent


@pytest.mark.asyncio
async def test_conditional_routes_based_on_output(registry, message_bus):
    registry.register(TestAgent("step_a", lambda payload: {"val": "next", "route": "b"}))
    registry.register(TestAgent("step_b", lambda payload: {"completed": True}))
    registry.register(TestAgent("step_default", lambda payload: {"completed": False}))

    tasks = [
        TaskDefinition(task_id="a", agent_name="step_a", payload={}, routes={"next": "b", "default": "c"}),
        TaskDefinition(task_id="b", agent_name="step_b", payload={}),
        TaskDefinition(task_id="c", agent_name="step_default", payload={}),
    ]

    strategy = ConditionalStrategy(registry=registry, message_bus=message_bus)
    result = await strategy.execute(OrchestrationRequest(tasks=tasks, context={}, metadata={"start_task": "a"}))

    assert result.success
    assert len(result.results) == 2
    assert any(r.agent_name == "step_b" for r in result.results)


@pytest.mark.asyncio
async def test_conditional_detects_cycle(registry, message_bus):
    registry.register(TestAgent("loop", lambda payload: {"route": "loop"}))
    tasks = [
        TaskDefinition(task_id="loop", agent_name="loop", payload={}, routes={"loop": "loop"}),
    ]

    strategy = ConditionalStrategy(registry=registry, message_bus=message_bus)
    with pytest.raises(RuntimeError):
        await strategy.execute(OrchestrationRequest(tasks=tasks, context={}))
        