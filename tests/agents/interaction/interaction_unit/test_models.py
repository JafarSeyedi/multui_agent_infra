# tests/agents/orchestration/unit/test_models.py
import pytest
from pydantic import ValidationError

from engines.agent.base_agents.base_agent import BaseAgent
from engines.agent.models import AgentOutput
from engines.interaction.interaction_models import InteractionRequest


def test_agent_definition_defaults_are_empty():
    agent = BaseAgent(agent_id="agent-1", agent_name="agent-1")
    assert agent.payload == {}
    assert agent.metadata == {}


def test_orchestration_request_builds_context_and_metadata():
    agent = BaseAgent(agent_id="agent-2", agent_name="agent-2")
    request = InteractionRequest(agents=[agent], context={"foo": "bar"}, metadata={"trace_id": "abc"})
    assert request.context["foo"] == "bar"
    assert request.metadata["trace_id"] == "abc"


def test_agent_result_can_be_truthy_with_correct_fields():
    result = AgentOutput(agent_id="t1", agent_name="agent-x", success=True, output={"value": 1})
    assert result.success is True
    assert result.output["value"] == 1


def test_orchestration_request_requires_agents():
    with pytest.raises(ValidationError):
        InteractionRequest()
