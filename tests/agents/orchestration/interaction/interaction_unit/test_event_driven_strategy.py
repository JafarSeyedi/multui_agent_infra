# tests/agents/orchestration/interaction/unit/test_event_driven_strategy.py

import pytest
from agents.orchestration.interaction.event_driven_strategy import EventDrivenStrategy
from agents.orchestration.models import OrchestrationRequest, TaskDefinition

from tests.agents.orchestration.interaction.interaction_unit.conftest import TestAgent


@pytest.mark.asyncio
async def test_event_driven_dispatches_and_emits(registry, message_bus):
    async def responder(payload):
        return {"emit_events": {"type": "next", "payload": {"value": payload["payload"].get("value", 0) + 1}}}

    registry.register(TestAgent("starter", lambda payload: {"emit_events": [{"type": "first", "payload": {"value": 1}}]}))
    registry.register(TestAgent("listener", responder))

    tasks = [
        TaskDefinition(task_id="starter", agent_name="starter", payload={}, on_events="start"),
        TaskDefinition(task_id="listener", agent_name="listener", payload={}, on_events="first"),
    ]

    strategy = EventDrivenStrategy(registry=registry, message_bus=message_bus)
    result = await strategy.execute(OrchestrationRequest(tasks=tasks, context={}, metadata={"initial_event": "start"}))

    assert result.success
    assert any(r.agent_name == "listener" for r in result.results)