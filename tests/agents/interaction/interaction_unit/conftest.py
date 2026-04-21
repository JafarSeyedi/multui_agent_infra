# tests/agents/orchestration/interaction/interaction_unit/conftest.py

import inspect
from typing import Any, Callable, Dict, List

import pytest
from engines.interaction.interaction_models import AgentMessage
from engines.agents.base_agents.base_agent import BaseAgent
from engines.buses.base_message_bus import MessageBus, HandlerType


class TestAgent:
    def __init__(self, name: str, behavior: Callable[[Dict[str, Any]], Any]) -> None:
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
    def __init__(self) -> None:
        self._agents: Dict[str, TestAgent] = {}

    def register(self, agent: TestAgent) -> TestAgent:
        self._agents[agent.name] = agent
        return agent

    async def execute(self, agent_name: str, payload: Dict[str, Any]) -> Any:
        agent = self._agents.get(agent_name)
        if agent is None:
            raise KeyError(f"Agent '{agent_name}' is not registered.")
        return await agent.execute(payload)


class DummyMessageBus1(MessageBus):
    def __init__(self) -> None:
        self.published: List[AgentMessage] = []

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


def make_agent(agent_name: str, agent_id: str) -> BaseAgent:
    return BaseAgent(agent_id=agent_id, agent_name=agent_name)