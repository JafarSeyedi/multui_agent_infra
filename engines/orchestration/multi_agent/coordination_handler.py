"""Task coordination across multiple agents."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CoordinationTask:
    task_id: str
    assignees: list[str]


class CoordinationHandler:
    def coordinate(self, instance_id: str, plan: list[CoordinationTask] | list[dict[str, object]]) -> list[str]:
        return [self._task_id(task) for task in plan]

    def _task_id(self, task: CoordinationTask | dict[str, object]) -> str:
        if isinstance(task, CoordinationTask):
            return task.task_id
        return str(task.get("task_id"))
