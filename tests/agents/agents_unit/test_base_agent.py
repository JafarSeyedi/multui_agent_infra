# tests/agents/unit/test_base_agent.py
import pytest
from pydantic import BaseModel

from engines.agents.base_agents.base_agent import BaseAgent
from engines.agents.models import AgentInput, AgentOutput


class InputModel(AgentInput):
    value: int


class OutputModel(AgentOutput):
    doubled: int

class EchoAgent(BaseAgent[InputModel, OutputModel]):
    agent_name = "echo-agent"
    input_model_class = InputModel
    output_model_class = OutputModel
    
    async def execute(self, input_model: InputModel) -> OutputModel:
        return OutputModel(doubled=input_model.value * 2, agent_name=self.agent_name)


class FailingAgent(EchoAgent):
    async def execute(self, input_model: InputModel) -> OutputModel:
        raise RuntimeError("boom")


@pytest.mark.asyncio
async def test_run_validates_and_logs_success(monkeypatch):
    agent = EchoAgent()
    log_calls = []

    async def fake_log(self, *args, **kwargs):
        log_calls.append(kwargs)

    monkeypatch.setattr("engines.agents.base_agent.BaseAgent._log_execution", fake_log)

    result = await agent.run({"value": 3})

    assert result.doubled == 6
    assert log_calls
    assert log_calls[-1]["status"] == "success"


@pytest.mark.asyncio
async def test_run_logs_failure_and_raises(monkeypatch):
    agent = FailingAgent()
    log_calls = []

    async def fake_log(self, *args, **kwargs):
        log_calls.append(kwargs)

    monkeypatch.setattr("engines.agents.base_agent.BaseAgent._log_execution", fake_log)

    with pytest.raises(RuntimeError):
        await agent.run({"value": 1})

    assert log_calls
    assert log_calls[-1]["status"] == "failure"
    assert log_calls[-1]["error_message"] == "boom"


def test_run_sync_outside_event_loop(monkeypatch):
    agent = EchoAgent()

    async def fake_log(*args, **kwargs):
        pass # intentionally empty

    monkeypatch.setattr("engines.agents.base_agent.BaseAgent._log_execution", fake_log)

    result = agent.run_sync({"value": 5})
    assert result.doubled == 10


@pytest.mark.asyncio
async def test_run_sync_inside_running_loop_raises(monkeypatch):
    agent = EchoAgent()

    async def fake_log(*args, **kwargs):
        pass # intentionally empty

    monkeypatch.setattr("engines.agents.base_agent.BaseAgent._log_execution", fake_log)

    with pytest.raises(RuntimeError):
        agent.run_sync({"value": 2})
