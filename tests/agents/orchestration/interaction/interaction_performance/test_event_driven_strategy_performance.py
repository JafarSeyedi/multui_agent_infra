# tests/agents/orchestration/interaction/performance/test_event_driven_strategy_performance.py
import time

import pytest
from agents.orchestration.interaction.event_driven_strategy import EventDrivenStrategy
from agents.orchestration.models import OrchestrationRequest, TaskDefinition

from .conftest_performance import TestAgent


@pytest.mark.asyncio
async def test_event_driven_high_volume(registry, message_bus):
    def make_agent(name):
        async def responder(payload):
            return {"emit_events": [{"type": name, "payload": {"value": 1}}]}
        return TestAgent(name, responder)

    registry.register(TestAgent("bootstrap", lambda payload: {"emit_events": [{"type": "fanout", "payload": {"value": 0}}]}))
    registry.register(make_agent("fanout"))

    tasks = [
        TaskDefinition(task_id="bootstrap", agent_name="bootstrap", payload={}, on_events="start"),
        TaskDefinition(task_id="fanout", agent_name="fanout", payload={}, on_events="fanout"),
    ]

    strategy = EventDrivenStrategy(registry=registry, message_bus=message_bus)
    request = OrchestrationRequest(tasks=tasks, context={}, metadata={"initial_event": "start", "max_iterations": 30})

    start = time.perf_counter()
    result = await strategy.execute(request)
    duration = time.perf_counter() - start

    assert duration < 1.4
    assert result.success
    assert result.results