# tests/agents/orchestration/interaction/unit/conftest.py

import inspect
from typing import Any, Callable, Dict, List

import pytest
from agents.orchestration.models import TaskDefinition
from agents.buses.base import MessageBus


class TestAgent:
    def __init__(self, name: str, behavior: Callable[[Dict[str, Any]], Any]):
        self.name = name
        self.behavior = behavior
        self.calls: List[Dict[str, Any]] = []

    async def execute(self, payload: Dict[str, Any]) -> Any:
        self.calls.append(payload)
        result = self.behavior(payload)
        if inspect.isawaitable(result):
            result = await result
        return result


class TestRegistry:
    def __init__(self):
        self._agents: Dict[str, TestAgent] = {}

    def register(self, agent: TestAgent) -> TestAgent:
        self._agents[agent.name] = agent
        return agent

    async def execute(self, agent_name: str, payload: Dict[str, Any]) -> Any:
        agent = self._agents.get(agent_name)
        if agent is None:
            raise KeyError(f"Agent '{agent_name}' is not registered.")
        return await agent.execute(payload)


class DummyMessageBus(MessageBus):
    def __init__(self):
        self.published: List[Dict[str, Any]] = []

    async def publish(self, message: Dict[str, Any]) -> None:
        self.published.append(message)


@pytest.fixture
def registry() -> TestRegistry:
    return TestRegistry()


@pytest.fixture
def message_bus() -> DummyMessageBus:
    return DummyMessageBus()


def make_task(agent_name: str, task_id: str, payload: Dict[str, Any]) -> TaskDefinition:
    return TaskDefinition(task_id=task_id, agent_name=agent_name, payload=payload)