"""CMMN case executor with stage/task/milestone orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..core.instance import ProcessInstance
from .sentry_evaluator import SentryEvaluator


@dataclass(frozen=True)
class CaseExecutionError(RuntimeError):
    """Raised when a case cannot continue."""


class CaseExecutor:
    """Run a case definition represented as dictionaries."""

    def __init__(self) -> None:
        self.sentry_evaluator = SentryEvaluator()

    def execute(self, instance: ProcessInstance, definition: dict[str, Any]) -> None:
        tasks = definition.get("tasks", [])
        case_file = definition.get("case_file", {})
        if not isinstance(tasks, list):
            raise CaseExecutionError("CMMN definition tasks must be an array")

        for task in tasks:
            if self.sentry_evaluator.is_active(task, case_file):
                instance.set_variable(f"task.{task.get('id')}", task.get("name", task.get("id")))

        if tasks:
            instance.complete()

    def plan(self, definition: dict[str, Any]) -> list[str]:
        return [str(item.get("id")) for item in definition.get("tasks", [])]
