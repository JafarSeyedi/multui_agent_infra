# tests/agents/orchestration/performance/test_native_orchestration_backend_performance.py
import time
from types import SimpleNamespace

import pytest

from engines.interaction.backends.native_backend import NativeOrchestrationBackend


class DummyOutput:
    def __init__(self, payload):
        self._payload = payload

    def model_dump(self):
        return self._payload


class SimpleRegistry:
    async def execute(self, agent_name, payload):
        return DummyOutput({"agent": agent_name})


def make_task(agent_name):
    return SimpleNamespace(
        agent_name=agent_name,
        input_payload={"value": agent_name},
        task_id=agent_name,
        description="perf",
    )


def make_request(scenario, tasks):
    return SimpleNamespace(
        workflow_id="perf-workflow",
        scenario=scenario,
        tasks=tasks,
        shared_context={},
        max_rounds=len(tasks),
        selected_agent=None,
    )

