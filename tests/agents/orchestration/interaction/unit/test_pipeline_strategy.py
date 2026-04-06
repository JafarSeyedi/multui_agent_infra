# tests/agents/orchestration/interaction/unit/test_pipeline_strategy.py

import pytest
from agents.orchestration.interaction.pipeline_strategy import PipelineStrategy
from agents.orchestration.models import OrchestrationRequest, TaskDefinition

from .conftest import TestAgent, make_task


@pytest.mark.asyncio
async def test_pipeline_runs_linear_tasks_and_updates_context(registry, message_bus):
    registry.register(TestAgent("step_alpha", lambda payload: {"alpha": payload["context"].get("alpha_pre", 0) + 1}))
    registry.register(TestAgent("step_beta", lambda payload: {"beta": payload["context"]["alpha"] * 2}))

    request = OrchestrationRequest(
        tasks=[
            make_task("step_alpha", "alpha", {"alpha_pre": 5}),
            make_task("step_beta", "beta", {}),
        ],
        context={"alpha_pre": 5},
    )

    strategy = PipelineStrategy(registry=registry, message_bus=message_bus)
    result = await strategy.execute(request)

    assert result.success
    assert result.final_context["alpha"] == 6
    assert result.final_context["beta"] == 12
    assert len(result.results) == 2
    assert all(r.success for r in result.results)


@pytest.mark.asyncio
async def test_pipeline_stops_on_failure_and_reports_error(registry, message_bus):
    registry.register(TestAgent("ok_agent", lambda payload: {"value": "ok"}))
    async def failing(payload):
        raise RuntimeError("boom")
    registry.register(TestAgent("fail_agent", failing))

    request = OrchestrationRequest(
        tasks=[
            make_task("ok_agent", "task_ok", {}),
            make_task("fail_agent", "task_fail", {}),
            make_task("ok_agent", "task_should_not_run", {}),
        ],
        context={},
    )

    strategy = PipelineStrategy(registry=registry, message_bus=message_bus)
    result = await strategy.execute(request)

    assert not result.success
    assert len(result.results) == 2
    assert result.results[-1].task_id == "task_fail"
    assert "boom" in (result.results[-1].error or "")
    assert "task_should_not_run" not in [r.task_id for r in result.results]


@pytest.mark.asyncio
async def test_pipeline_handles_missing_agent(registry, message_bus):
    request = OrchestrationRequest(
        tasks=[make_task("missing_agent", "task_missing", {})],
        context={},
    )

    strategy = PipelineStrategy(registry=registry, message_bus=message_bus)
    result = await strategy.execute(request)

    assert not result.success
    assert result.results[0].error
    assert "not found" in result.results[0].error