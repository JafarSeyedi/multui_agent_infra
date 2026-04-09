# tests/agents/unit/test_agent_registry.py
import pytest

from agents.agent_registry import AgentRegistry
from agents.base_agent import BaseAgent
from agents.orchestration.models import OrchestrationRequest, OrchestrationResult


class SimpleInput(OrchestrationRequest):
    text: str


class SimpleOutput(OrchestrationResult):
    text: str


class SimpleAgent(BaseAgent):
    agent_name = "simple-agent"
    InputModel = SimpleInput
    OutputModel = SimpleOutput

    async def execute(self, input_model: SimpleInput) -> SimpleOutput:
        return SimpleOutput(text= input_model.text.upper(), results=[])


@pytest.fixture(autouse=True)
def disable_logging(monkeypatch):
    async def noop(*args, **kwargs):
        pass # intentionally empty

    monkeypatch.setattr("agents.base_agent.BaseAgent._log_execution", noop)


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
