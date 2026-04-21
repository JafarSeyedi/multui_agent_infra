# tests/agents/orchestration/interaction/unit/test_coordinator_strategy.py

import pytest
from engines.interaction.coordinator_strategy import CoordinatorStrategy
from engines.interaction.interaction_models import InteractionRequest
from engines.agents.base_agents.base_agent import BaseAgent

from tests.agents.interaction.interaction_unit.conftest import TestAgent, make_agent


@pytest.mark.asyncio
async def test_coordinator_strategy_runs_workers_and_aggregates(registry, message_bus):
    registry.register(TestAgent("worker_alpha", lambda payload: {"result": payload["input"] + "_done"}))
    registry.register(TestAgent("worker_beta", lambda payload: {"result": payload["input"] + "_ok"}))
    registry.register(TestAgent("validator", lambda payload: {"valid": True}))
    registry.register(TestAgent("aggregator", lambda payload: {"aggregated": sorted(payload["worker_results"], key=lambda r: r["agent_id"])}))

    request = InteractionRequest(
        agents=[
            BaseAgent(agent_id="alpha", agent_name="worker_alpha", payload={"input": "A"}),
            BaseAgent(agent_id="beta", agent_name="worker_beta", payload={"input": "B"}),
        ],
        context={"shared": True},
        metadata={},
    )

    strategy = CoordinatorStrategy(
        registry=registry,
        message_bus=message_bus,
        validation_agent="validator",
        aggregator_agent="aggregator",
    )

    result = await strategy.execute(request)

    assert result.success
    assert result.final_context["final_payload"]["aggregated"][0]["agent_id"] == "alpha"
    assert result.final_context["final_payload"]["aggregated"][1]["agent_id"] == "beta"
    assert any(evt["event"].startswith("broadcast") is False for evt in message_bus.published)


@pytest.mark.asyncio
async def test_coordinator_strategy_captures_worker_errors(registry, message_bus):
    async def failing_agent(payload):
        raise RuntimeError("boom")

    registry.register(TestAgent("failing_worker", failing_agent))
    registry.register(TestAgent("validator", lambda payload: {"valid": False}))

    request = InteractionRequest(
        agents=[make_agent("failing_worker", "fail-agent")],
        context={},
        metadata={},
    )

    strategy = CoordinatorStrategy(
        registry=registry,
        message_bus=message_bus,
        validation_agent="validator",
        aggregator_agent=None,
    )

    result = await strategy.execute(request)

    assert not all(r.success for r in result.results)
    assert any("boom" in (r.error or "") for r in result.results)
    assert "errors" in result.final_context