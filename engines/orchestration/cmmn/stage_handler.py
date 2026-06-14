"""Stage lifecycle management for CMMN.

Supports stage activation, completion, reentry, and nesting semantics.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ..core.instance import ProcessInstance
from ..core.event_bus import Event, EventType
from ..core.engine import OrchestrationEngine
from ..bpmn.models.bpmn_models import FormalExpression
from .models.cmmn_models import (
    PlanItem,
    Milestone,
    DiscretionaryItem,
    EntryCriterion,
    ExitCriterion,
    HumanTask,
    CaseTask,
    ProcessTask,
)


class StageState(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    TERMINATED = "terminated"
    FAILED = "failed"
    SUSPENDED = "suspended"
    AVAILABLE = "available"
    ENABLED = "enabled"


from enum import Enum


@dataclass
class Stage:
    stage_id: str
    name: str | None = None
    auto_complete: bool = True
    tasks: list[str] = field(default_factory=list)
    child_stages: list[str] = field(default_factory=list)
    entry_criteria: list[dict[str, Any]] = field(default_factory=list)
    exit_criteria: list[dict[str, Any]] = field(default_factory=list)
    state: StageState = StageState.AVAILABLE


class StageHandler:
    def __init__(self, orchestration_engine: OrchestrationEngine | None = None) -> None:
        self._engine = orchestration_engine
        self._stages: dict[str, Stage] = {}

    def register(self, stage: Stage) -> None:
        self._stages[stage.stage_id] = stage

    def get_stage(self, stage_id: str) -> Stage | None:
        return self._stages.get(stage_id)

    def activate(self, stage: Stage, instance: ProcessInstance | None = None) -> dict[str, Any]:
        stage.state = StageState.ACTIVE
        self._stages[stage.stage_id] = stage

        if instance:
            instance.set_variable(f"stage.{stage.stage_id}.state", StageState.ACTIVE.value)
            for task_id in stage.tasks:
                instance.set_variable(f"task.{task_id}.state", "enabled")

        if self._engine is not None:
            asyncio.ensure_future(self._engine.event_bus.publish(
                Event(
                    type=EventType.PROCESS_INSTANCE_STARTED,
                    data={"stage_id": stage.stage_id, "action": "activated"},
                )
            ))

        return {"stage_id": stage.stage_id, "status": "active", "tasks": stage.tasks}

    def complete(self, stage: Stage, instance: ProcessInstance | None = None) -> dict[str, Any]:
        stage.state = StageState.COMPLETED
        self._stages[stage.stage_id] = stage

        if instance:
            instance.set_variable(f"stage.{stage.stage_id}.state", StageState.COMPLETED.value)
            all_done = all(
                instance.get_variable(f"task.{t}.status") == "completed" for t in stage.tasks
            )
            instance.set_variable(f"stage.{stage.stage_id}.allTasksComplete", all_done)

        return {"stage_id": stage.stage_id, "status": "completed"}

    def reenter(self, stage: Stage, instance: ProcessInstance | None = None) -> dict[str, Any]:
        if stage.state == StageState.COMPLETED:
            stage.state = StageState.ACTIVE
            self._stages[stage.stage_id] = stage

            if instance:
                instance.set_variable(f"stage.{stage.stage_id}.state", StageState.ACTIVE.value)
                instance.set_variable(f"stage.{stage.stage_id}.reentered", True)

            return {"stage_id": stage.stage_id, "status": "reentered", "tasks": stage.tasks}

        return {"stage_id": stage.stage_id, "status": stage.state.value}

    def terminate(self, stage: Stage, instance: ProcessInstance | None = None) -> dict[str, Any]:
        stage.state = StageState.TERMINATED
        self._stages[stage.stage_id] = stage

        if instance:
            instance.set_variable(f"stage.{stage.stage_id}.state", StageState.TERMINATED.value)

        return {"stage_id": stage.stage_id, "status": "terminated"}

    def fail(self, stage: Stage, reason: str = "", instance: ProcessInstance | None = None) -> dict[str, Any]:
        stage.state = StageState.FAILED
        self._stages[stage.stage_id] = stage

        if instance:
            instance.set_variable(f"stage.{stage.stage_id}.state", StageState.FAILED.value)
            instance.set_variable(f"stage.{stage.stage_id}.failureReason", reason)

        return {"stage_id": stage.stage_id, "status": "failed", "reason": reason}

    def suspend(self, stage: Stage, instance: ProcessInstance | None = None) -> dict[str, Any]:
        stage.state = StageState.SUSPENDED
        self._stages[stage.stage_id] = stage

        if instance:
            instance.set_variable(f"stage.{stage.stage_id}.state", StageState.SUSPENDED.value)

        return {"stage_id": stage.stage_id, "status": "suspended"}

    def resume(self, stage: Stage, instance: ProcessInstance | None = None) -> dict[str, Any]:
        stage.state = StageState.ACTIVE
        self._stages[stage.stage_id] = stage

        if instance:
            instance.set_variable(f"stage.{stage.stage_id}.state", StageState.ACTIVE.value)

        return {"stage_id": stage.stage_id, "status": "active"}

    def is_auto_complete(self, stage: Stage, instance: ProcessInstance | None = None) -> bool:
        return stage.auto_complete

    def check_auto_complete(self, stage: Stage, instance: ProcessInstance) -> bool:
        if not stage.auto_complete:
            return False
        if stage.state != StageState.ACTIVE:
            return False

        all_completed = all(
            instance.get_variable(f"task.{t}.status") == "completed" for t in stage.tasks
        )
        return all_completed

    def get_execution_summary(self, stage: Stage, instance: ProcessInstance) -> dict[str, Any]:
        task_statuses: dict[str, str] = {}
        for task_id in stage.tasks:
            status = instance.get_variable(f"task.{task_id}.status")
            task_statuses[task_id] = status or "pending"

        completed_count = sum(1 for s in task_statuses.values() if s == "completed")
        total = len(task_statuses)

        return {
            "stage_id": stage.stage_id,
            "state": stage.state.value,
            "tasks_total": total,
            "tasks_completed": completed_count,
            "tasks_pending": total - completed_count,
            "task_statuses": task_statuses,
        }
