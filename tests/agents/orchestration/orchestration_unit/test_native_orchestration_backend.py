# tests/agents/orchestration/unit/test_native_orchestration_backend.py
from types import SimpleNamespace

import pytest

from agents.orchestration.backends.native_backend import NativeOrchestrationBackend
# from agents.orchestration.backends.autogen_backend import AutoGenOrchestrationBackend  # for Shared helpers if needed


class DummyOutput:
    def __init__(self, payload):
        self._payload = payload

    def model_dump(self):
        return self._payload


class DummyRegistry:
    def __init__(self, fail_on=None):
        self.calls = []
        self.fail_on = fail_on

    async def execute(self, agent_name, payload):
        self.calls.append((agent_name, payload))
        if agent_name == self.fail_on:
            raise RuntimeError("agent failure")
        return DummyOutput({"agent": agent_name, "input": payload})


class DummyMessageBus:
    def __init__(self):
        self.published = []

    async def publish(self, message):
        self.published.append(message)


def make_task(agent_name, input_payload=None, task_id=None, description=None):
    return SimpleNamespace(
        agent_name=agent_name,
        input_payload=input_payload or {},
        task_id=task_id or agent_name,
        description=description,
    )


def make_request(
    scenario="pipeline",
    tasks=None,
    shared_context=None,
    workflow_id="workflow-1",
    max_rounds=1,
    selected_agent=None,
):
    return SimpleNamespace(
        workflow_id=workflow_id,
        scenario=scenario,
        tasks=tasks or [],
        shared_context=shared_context or {},
        max_rounds=max_rounds,
        selected_agent=selected_agent,
    )


@pytest.mark.asyncio
async def test_pipeline_strategy_updates_context_and_returns_success():
    registry = DummyRegistry()
    bus = DummyMessageBus()
    backend = NativeOrchestrationBackend(registry=registry, message_bus=bus)

    tasks = [
        make_task("alpha", {"value": 1}, task_id="alpha-1"),
        make_task("beta", {"value": 2}, task_id="beta-1"),
    ]
    request = make_request(scenario="pipeline", tasks=tasks, shared_context={"foo": "bar"})

    result = await backend.execute(request)

    assert result.status == "success"
    assert len(result.executions) == 2
    assert result.shared_context["task:alpha"]["agent"] == "alpha"
    assert result.shared_context["task:beta"]["agent"] == "beta"
    assert bus.published
    assert registry.calls[0][0] == "alpha"


@pytest.mark.asyncio
async def test_round_robin_propagates_output_between_agents():
    registry = DummyRegistry()
    backend = NativeOrchestrationBackend(registry=registry, message_bus=None)

    tasks = [
        make_task("loop1", {"value": 10}),
        make_task("loop2", {"value": 20}),
    ]
    request = make_request(scenario="round_robin", tasks=tasks, max_rounds=2)

    result = await backend.execute(request)

    assert result.status == "success"
    assert result.shared_context["round_index"] == 1
    assert "last_output:loop2" in result.shared_context
    assert len(result.steps) == 4  # 2 tasks × 2 rounds


@pytest.mark.asyncio
async def test_selector_defaults_when_no_selected_agent():
    registry = DummyRegistry()
    backend = NativeOrchestrationBackend(registry=registry, message_bus=None)

    tasks = [make_task("solo", {"value": 123})]
    request = make_request(scenario="selector", tasks=tasks, selected_agent=None)

    result = await backend.execute(request)

    assert result.status == "success"
    assert result.notes, "Should register the note about missing selector"
    assert result.shared_context["task:solo"]["agent"] == "solo"


@pytest.mark.asyncio
async def test_task_failure_marks_step_and_aggregates_failure_status():
    registry = DummyRegistry(fail_on="failing-agent")
    backend = NativeOrchestrationBackend(registry=registry, message_bus=None)

    tasks = [
        make_task("failing-agent", {"value": 1}),
        make_task("next-agent", {"value": 2}),
    ]
    request = make_request(scenario="pipeline", tasks=tasks)

    result = await backend.execute(request)

    assert result.status == "failure"
    assert any(exec.status == "failure" for exec in result.executions)
    assert result.steps[0].status == "failed"