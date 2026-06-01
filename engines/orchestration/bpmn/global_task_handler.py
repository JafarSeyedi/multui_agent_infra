"""Global task execution helper for BPMN global tasks.

Supports global tasks/callable behavior and reuse across call activities.
Provides both OSDM-typed and backward-compatible dict-based interfaces.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from ...core.engine import OrchestrationEngine
from ...core.event_bus import Event, EventType

from ....document.models.osdm_models import (
    GlobalTask as OSDMGlobalTask,
    GlobalUserTask,
    GlobalScriptTask,
    GlobalManualTask,
    GlobalBusinessRuleTask,
)


@dataclass
class HandlerGlobalTask:
    task_id: str
    task_type: str = "task"
    payload: dict[str, Any] = field(default_factory=dict)
    name: str | None = None
    osdm_task: OSDMGlobalTask | None = None


@dataclass
class GlobalTaskExecutionResult:
    task_id: str
    success: bool = True
    status: str = "executed"
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class GlobalTaskHandler:
    def __init__(self, orchestration_engine: OrchestrationEngine | None = None) -> None:
        self._engine = orchestration_engine
        self._registry: dict[str, HandlerGlobalTask] = {}
        self._executors: dict[str, Callable[..., Any]] = {}
        self._execution_history: list[GlobalTaskExecutionResult] = []

    def register(self, task: HandlerGlobalTask) -> None:
        self._registry[task.task_id] = task

    def register_executor(self, task_id: str, executor: Callable[..., Any]) -> None:
        self._executors[task_id] = executor

    def get_task(self, task_id: str) -> HandlerGlobalTask | None:
        return self._registry.get(task_id)

    def get_all_tasks(self) -> list[HandlerGlobalTask]:
        return list(self._registry.values())

    def execute(self, task: HandlerGlobalTask, context: dict[str, Any] | None = None) -> GlobalTaskExecutionResult:
        context = context or {}
        task_id = task.task_id

        if task_id in self._executors:
            try:
                result = self._executors[task_id](task, context)
                exec_result = GlobalTaskExecutionResult(task_id=task_id, success=True, status="executed", output={"result": result} if not isinstance(result, dict) else result)
            except Exception as e:
                exec_result = GlobalTaskExecutionResult(task_id=task_id, success=False, status="failed", error=str(e))
        else:
            exec_result = GlobalTaskExecutionResult(
                task_id=task_id, success=True, status="executed",
                output={"task_id": task.task_id, "task_type": task.task_type, "status": "executed", "payload": task.payload},
            )

        self._execution_history.append(exec_result)

        if self._engine is not None:
            self._engine.event_bus.publish(
                Event(type=EventType.ACTIVITY_COMPLETED, data={"global_task": True, "task_id": task_id, "task_type": task.task_type, "success": exec_result.success})
            )

        return exec_result

    def resolve_for_call_activity(self, called_element: str, context: dict[str, Any] | None = None) -> GlobalTaskExecutionResult:
        task = self.get_task(called_element)
        if task is None:
            return GlobalTaskExecutionResult(task_id=called_element, success=False, status="not_found", error=f"Global task not found: {called_element}")
        return self.execute(task, context)

    def get_execution_history(self, task_id: str | None = None) -> list[GlobalTaskExecutionResult]:
        return [r for r in (self._execution_history if task_id is None else self._execution_history) if task_id is None or r.task_id == task_id]

    def clear_history(self, task_id: str | None = None) -> int:
        if task_id is None:
            count = len(self._execution_history)
            self._execution_history.clear()
            return count
        before = len(self._execution_history)
        self._execution_history = [r for r in self._execution_history if r.task_id != task_id]
        return before - len(self._execution_history)

    def register_osdm(self, task: OSDMGlobalTask) -> HandlerGlobalTask:
        """Register from OSDM GlobalTask, dispatching type-specific behavior."""
        task_type_str = self._resolve_global_task_type(task)
        handler_task = HandlerGlobalTask(
            task_id=task.id,
            task_type=task_type_str,
            name=task.name,
            osdm_task=task,
            payload={
                "resources": [r.id for r in task.resources] if task.resources else [],
                "supported_interface_refs": [iface.id for iface in task.supported_interface_refs] if task.supported_interface_refs else [],
                "io_specification": task.io_specification is not None,
                "io_binding_count": len(task.io_binding) if task.io_binding else 0,
                "global_task_subtype": task_type_str,
            },
        )
        self.register(handler_task)
        return handler_task

    def _resolve_global_task_type(self, task: OSDMGlobalTask) -> str:
        """Resolve specific global task subtype from OSDM class hierarchy."""
        if isinstance(task, GlobalBusinessRuleTask):
            return "businessRuleTask"
        if isinstance(task, GlobalScriptTask):
            return "scriptTask"
        if isinstance(task, GlobalManualTask):
            return "manualTask"
        if isinstance(task, GlobalUserTask):
            return "userTask"
        return task.task_type.value if hasattr(task.task_type, "value") else str(task.task_type)

    def execute_osdm(self, task: OSDMGlobalTask, context: dict[str, Any] | None = None) -> GlobalTaskExecutionResult:
        handler_task = self.register_osdm(task)
        result = self.execute(handler_task, context)
        result.output["osdm"] = True
        result.output["task_type"] = task.task_type.value if hasattr(task.task_type, "value") else str(task.task_type)
        result.output["resources"] = [r.id for r in task.resources] if task.resources else []
        result.output["supports"] = [iface.id for iface in task.supported_interface_refs] if task.supported_interface_refs else []
        return result
