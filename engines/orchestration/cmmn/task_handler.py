"""CMMN task execution strategies.

Supports HumanTask, ProcessTask, CaseTask, DecisionTask semantics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ...core.instance import ProcessInstance
from ...core.engine import OrchestrationEngine


class CMMNTaskState(str, Enum):
    AVAILABLE = "available"
    ENABLED = "enabled"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"
    SUSPENDED = "suspended"


class CMMNTaskBlocking(str, Enum):
    BLOCKING = "Blocking"
    NON_BLOCKING = "NonBlocking"


@dataclass
class CMMNTask:
    task_id: str
    task_type: str = "task"
    payload: dict[str, Any] = field(default_factory=dict)
    name: str | None = None
    is_blocking: str = CMMNTaskBlocking.BLOCKING.value
    state: str = CMMNTaskState.AVAILABLE.value
    required_rule: str = "optional"
    repetition_rule: str = "none"
    activation_rule: str = "manual"
    entry_criteria: list[dict[str, Any]] = field(default_factory=list)
    exit_criteria: list[dict[str, Any]] = field(default_factory=list)
    inputs: list[dict[str, Any]] = field(default_factory=list)
    outputs: list[dict[str, Any]] = field(default_factory=list)
    io_specification: dict[str, Any] = field(default_factory=dict)


@dataclass
class HumanTaskConfig:
    assignee: str | None = None
    candidate_users: list[str] = field(default_factory=list)
    candidate_groups: list[str] = field(default_factory=list)
    form_key: str | None = None
    priority: str = "medium"
    due_date: str | None = None
    follow_up_date: str | None = None


@dataclass
class ProcessTaskConfig:
    called_element: str | None = None
    io_mapping: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class CaseTaskConfig:
    case_ref: str | None = None
    io_mapping: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class DecisionTaskConfig:
    called_decision: str | None = None
    result_variable: str | None = None
    mapping: list[dict[str, Any]] = field(default_factory=list)


class CMMNTaskHandler:
    def __init__(self, orchestration_engine: OrchestrationEngine | None = None) -> None:
        self._engine = orchestration_engine
        self._tasks: dict[str, CMMNTask] = {}
        self._human_tasks: dict[str, HumanTaskConfig] = {}
        self._process_tasks: dict[str, ProcessTaskConfig] = {}
        self._case_tasks: dict[str, CaseTaskConfig] = {}
        self._decision_tasks: dict[str, DecisionTaskConfig] = {}

    def register(self, task: CMMNTask) -> None:
        self._tasks[task.task_id] = task

    def get_task(self, task_id: str) -> CMMNTask | None:
        return self._tasks.get(task_id)

    def execute(self, task: CMMNTask, instance: ProcessInstance | None = None) -> dict[str, Any]:
        task_type = task.task_type
        result: dict[str, Any] = {"task_id": task.task_id, "type": task_type, "status": "done"}

        if instance:
            instance.set_variable(f"task.{task.task_id}.state", CMMNTaskState.COMPLETED.value)

        if task_type == "HumanTask":
            result.update(self._execute_human_task(task))
        elif task_type == "ProcessTask":
            result.update(self._execute_process_task(task))
        elif task_type == "CaseTask":
            result.update(self._execute_case_task(task))
        elif task_type == "DecisionTask":
            result.update(self._execute_decision_task(task))
        else:
            result["output"] = task.payload
            if instance:
                instance.set_variable(f"task.{task.task_id}.output", task.payload)

        if instance:
            instance.set_variable(f"task.{task.task_id}.output", result)

        return result

    def _execute_human_task(self, task: CMMNTask) -> dict[str, Any]:
        config = self._human_tasks.get(task.task_id, HumanTaskConfig(
            assignee=task.payload.get("assignee"),
            candidate_users=task.payload.get("candidateUsers", []),
            candidate_groups=task.payload.get("candidateGroups", []),
            form_key=task.payload.get("formKey"),
            priority=task.payload.get("priority", "medium"),
            due_date=task.payload.get("dueDate"),
        ))
        return {"type": "HumanTask", "assignee": config.assignee, "claimed": False}

    def _execute_process_task(self, task: CMMNTask) -> dict[str, Any]:
        called_element = task.payload.get("calledElement", task.payload.get("called_element"))
        return {"type": "ProcessTask", "calledElement": called_element}

    def _execute_case_task(self, task: CMMNTask) -> dict[str, Any]:
        case_ref = task.payload.get("caseRef")
        return {"type": "CaseTask", "caseRef": case_ref}

    def _execute_decision_task(self, task: CMMNTask) -> dict[str, Any]:
        called_decision = task.payload.get("calledDecision")
        result_variable = task.payload.get("resultVariable", f"task.{task.task_id}.result")
        return {"type": "DecisionTask", "calledDecision": called_decision, "resultVariable": result_variable}

    def register_human_task(self, task_id: str, config: HumanTaskConfig) -> None:
        self._human_tasks[task_id] = config

    def register_process_task(self, task_id: str, config: ProcessTaskConfig) -> None:
        self._process_tasks[task_id] = config

    def register_case_task(self, task_id: str, config: CaseTaskConfig) -> None:
        self._case_tasks[task_id] = config

    def register_decision_task(self, task_id: str, config: DecisionTaskConfig) -> None:
        self._decision_tasks[task_id] = config

    def claim_task(self, task_id: str, user: str, instance: ProcessInstance) -> bool:
        task = self._tasks.get(task_id)
        if task is None:
            return False
        task.state = CMMNTaskState.ACTIVE.value
        instance.set_variable(f"task.{task_id}.claimant", user)
        instance.set_variable(f"task.{task_id}.state", CMMNTaskState.ACTIVE.value)
        return True

    def release_task(self, task_id: str, instance: ProcessInstance) -> bool:
        task = self._tasks.get(task_id)
        if task is None:
            return False
        task.state = CMMNTaskState.ENABLED.value
        instance.set_variable(f"task.{task_id}.claimant", None)
        instance.set_variable(f"task.{task_id}.state", CMMNTaskState.ENABLED.value)
        return True

    def is_blocking(self, task_id: str) -> bool:
        task = self._tasks.get(task_id)
        if task is None:
            return True
        return task.is_blocking == CMMNTaskBlocking.BLOCKING.value
