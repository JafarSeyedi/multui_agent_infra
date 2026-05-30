"""Activity handling for BPMN tasks, sub-processes, and call activities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..core.context import ExecutionContext
from ..core.engine import OrchestrationEngine
from ..core.instance import ProcessInstance


@dataclass(frozen=True)
class ActivityExecutionResult:
    success: bool
    output: dict[str, Any] | None = None
    error: Exception | None = None
    waiting: bool = False
    wait_kind: str | None = None
    wait_name: str | None = None
    correlation_keys: dict[str, Any] | None = None


class ActivityHandler:
    def __init__(self, orchestration_engine: OrchestrationEngine) -> None:
        self._orchestration_engine = orchestration_engine

    def execute(self, instance: ProcessInstance, activity: dict[str, Any], *, context: ExecutionContext) -> ActivityExecutionResult:
        activity_id = str(activity.get("id"))
        activity_type = str(activity.get("type", "task"))
        instance.current_activity_id = activity_id
        payload = dict(activity.get("payload", {}))

        try:
            if activity_type in {"task", "serviceTask", "usertask", "scriptTask"}:
                instance.set_variable(f"{activity_id}.output", payload)
            elif activity_type in {"subProcess", "callActivity"}:
                instance.set_variable(f"{activity_id}.children", payload.get("children", []))
            elif activity_type in {"boundaryEvent", "intermediateCatch", "intermediateThrow"}:
                message_name = payload.get("message_name")
                event_name = payload.get("event_name")
                if message_name:
                    return ActivityExecutionResult(
                        success=True,
                        output=payload,
                        waiting=True,
                        wait_kind="message",
                        wait_name=str(message_name),
                        correlation_keys=dict(payload.get("correlation_keys") or {}),
                    )
                if event_name:
                    return ActivityExecutionResult(
                        success=True,
                        output=payload,
                        waiting=True,
                        wait_kind="event",
                        wait_name=str(event_name),
                    )
            else:
                instance.set_variable(f"{activity_id}.raw", payload)
            return ActivityExecutionResult(success=True, output=payload)
        except Exception as exc:  # pragma: no cover - defensive
            return ActivityExecutionResult(success=False, error=exc)
