# tests/agents/unit/test_agent_registry.py
import pytest

from engines.agents.agent_registry import AgentRegistry
from engines.agents.base_agents.base_agent import BaseAgent
from engines.agents.models import AgentInput
from engines.agents.models import AgentOutput


class SimpleInput(AgentInput):
    text: str


class SimpleOutput(AgentOutput):
    text: str


class SimpleAgent(BaseAgent):
    agent_name = "simple-agent"
    InputModel = SimpleInput
    OutputModel = SimpleOutput

    async def execute(self, input_model: SimpleInput) -> SimpleOutput:
        return SimpleOutput(text= input_model.text.upper(), agent_name=self.agent_name)


@pytest.fixture(autouse=True)
def disable_logging(monkeypatch):
    async def noop(*args, **kwargs):
        pass # intentionally empty

    monkeypatch.setattr("engines.agents.base_agent.BaseAgent._log_execution", noop)


@pytest.mark.asyncio
async def test_register_populates_shared_dependencies():
    registry = AgentRegistry(llm="llm-instance", vector_db="vec-db", storage="storage-adapter")
    agent = SimpleAgent(llm=None, vector_db=None, storage=None)
    registry.register(agent)

    assert agent.llm == "llm-instance"
    assert agent.vector_db == "vec-db"
    assert agent.storage == "storage-adapter"


@pytest.mark.asyncio
async def test_run_returns_agent_output():
    registry = AgentRegistry()
    agent = SimpleAgent()
    registry.register(agent)

    result = await registry.run("simple-agent", {"text": "hello"})
    assert result.text == "HELLO"


@pytest.mark.asyncio
async def test_run_missing_agent_raises():
    registry = AgentRegistry()
    with pytest.raises(KeyError):
        await registry.run("missing", {})
