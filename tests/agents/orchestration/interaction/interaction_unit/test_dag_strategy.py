# tests/agents/orchestration/interaction/unit/test_dag_strategy.py

import pytest
from agents.orchestration.interaction.dag_strategy import DAGStrategy
from agents.orchestration.models import OrchestrationRequest, TaskDefinition

from tests.agents.orchestration.interaction.interaction_unit.conftest import TestAgent


@pytest.mark.asyncio
async def test_dag_respects_dependencies_and_concurrent_tasks(registry, message_bus):
    registry.register(TestAgent("root", lambda payload: {"root": True}))
    registry.register(TestAgent("left", lambda payload: {"left": payload["context"]["root"]}))
    registry.register(TestAgent("right", lambda payload: {"right": payload["context"]["root"]}))
    registry.register(TestAgent("final", lambda payload: {"final": payload["context"]["left"] and payload["context"]["right"]}))

    tasks = [
        TaskDefinition(task_id="root", agent_name="root", payload={}, depends_on=[]),
        TaskDefinition(task_id="left", agent_name="left", payload={}, depends_on=["root"]),
        TaskDefinition(task_id="right", agent_name="right", payload={}, depends_on=["root"]),
        TaskDefinition(task_id="final", agent_name="final", payload={}, depends_on=["left", "right"]),
    ]

    strategy = DAGStrategy(registry=registry, message_bus=message_bus)
    result = await strategy.execute(OrchestrationRequest(tasks=tasks, context={}))

    assert result.success
    assert result.final_context["final"] is True
    assert len(result.results) == 4


@pytest.mark.asyncio
async def test_dag_detects_cycle(registry, message_bus):
    tasks = [
        TaskDefinition(task_id="a", agent_name="a", payload={}, depends_on=["b"]),
        TaskDefinition(task_id="b", agent_name="b", payload={}, depends_on=["a"]),
    ]

    strategy = DAGStrategy(registry=registry, message_bus=message_bus)

    with pytest.raises(ValueError):
        await strategy.execute(OrchestrationRequest(tasks=tasks, context={}))


@pytest.mark.asyncio
async def test_dag_fails_when_dependency_missing(registry, message_bus):
    registry.register(TestAgent("solo", lambda payload: {"solo": True}))
    tasks = [
        TaskDefinition(task_id="solo", agent_name="solo", payload={}, depends_on=["missing"]),
    ]

    strategy = DAGStrategy(registry=registry, message_bus=message_bus)

    with pytest.raises(ValueError):
        await strategy.execute(OrchestrationRequest(tasks=tasks, context={}))