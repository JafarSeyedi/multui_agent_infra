# tests/agents/orchestration/unit/test_models.py
from typing import Any

import pytest
from pydantic import ValidationError

from agents.orchestration.models import TaskDefinition, OrchestrationRequest, TaskResult


def test_task_definition_defaults_are_empty():
    task = TaskDefinition(task_id="task-1", agent_name="agent-1")
    assert task.payload == {}
    assert task.depends_on == []
    assert task.metadata == {}
    assert task.condition is None
    assert task.max_iterations is None


def test_orchestration_request_builds_context_and_metadata():
    task = TaskDefinition(task_id="task-2", agent_name="agent-2")
    request = OrchestrationRequest(tasks=[task], context={"foo": "bar"}, metadata={"trace_id": "abc"})
    assert request.context["foo"] == "bar"
    assert request.metadata["trace_id"] == "abc"


def test_task_result_can_be_truthy_with_correct_fields():
    result = TaskResult(task_id="t1", agent_name="agent-x", success=True, output={"value": 1})
    assert result.success is True
    assert result.output["value"] == 1


def test_orchestration_request_requires_tasks():
    with pytest.raises(ValidationError):
        OrchestrationRequest()
