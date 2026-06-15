# tests/agents/orchestration/interaction/interaction_unit/conftest.py
import inspect
from collections.abc import Callable
from typing import Any

import pytest

from engines.communication.buses.base_message_bus import HandlerType
from engines.communication.buses.base_message_bus import MessageBus
from engines.agent.interaction_models import AgentMessage


class TestAgent:
    def __init__(self, name: str, behavior: Callable[[dict[str, Any]], Any]) -> None:
        self.name = name
        self.behavior = behavior
        self.calls: list[dict[str, Any]] = []

    async def execute(self, payload: dict[str, Any]) -> Any:
        self.calls.append(payload)
        result = self.behavior(payload)
        if inspect.isawaitable(result):
            result = await result
        return result


class TestRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, TestAgent] = {}

    def register(self, agent: TestAgent) -> TestAgent:
        self._agents[agent.name] = agent
        return agent

    async def execute(self, agent_name: str, payload: dict[str, Any]) -> Any:
        agent = self._agents.get(agent_name)
        if agent is None:
            raise KeyError(f"Agent '{agent_name}' is not registered.")
        return await agent.execute(payload)


class DummyMessageBus1(MessageBus):
    def __init__(self) -> None:
        self.published: list[AgentMessage] = []

    async def publish(self, message: AgentMessage) -> None:
        self.published.append(message)
    async def subscribe(self, recipient: str, handler: HandlerType) -> None:
        pass
    async def unsubscribe(self, recipient: str, handler: HandlerType) -> None:
        pass


@pytest.fixture
def registry() -> TestRegistry:
    return TestRegistry()


@pytest.fixture
def message_bus() -> DummyMessageBus1:
    return DummyMessageBus1()


def make_agent(agent_name: str, agent_id: str) -> TestAgent:
    return TestAgent(agent_name, lambda payload: None)
