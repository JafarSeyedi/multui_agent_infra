"""Task and execution listeners for orchestration runtime.

Supports lifecycle hooks on tasks and executions per Camunda/Flowable patterns.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable


logger = logging.getLogger(__name__)


class TaskListenerEventType(str, Enum):
    CREATE = "create"
    ASSIGNMENT = "assignment"
    COMPLETE = "complete"
    DELETE = "delete"
    UPDATE = "update"
    TIMEOUT = "timeout"


class ExecutionListenerEventType(str, Enum):
    START = "start"
    END = "end"
    TAKE = "take"


class ListenerType(str, Enum):
    JAVA_CLASS = "javaClass"
    EXPRESSION = "expression"
    DELEGATE_EXPRESSION = "delegateExpression"
    SCRIPT = "script"


@dataclass
class TaskListener:
    listener_id: str
    event_type: str
    listener_type: str = ListenerType.EXPRESSION
    expression: str | None = None
    class_name: str | None = None
    delegate_expression: str | None = None
    script: str | None = None
    script_format: str = "FEEL"
    fields: dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    enabled: bool = True


@dataclass
class ExecutionListener:
    listener_id: str
    event_type: str
    listener_type: str = ListenerType.EXPRESSION
    expression: str | None = None
    class_name: str | None = None
    delegate_expression: str | None = None
    script: str | None = None
    script_format: str = "FEEL"
    fields: dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    enabled: bool = True


@dataclass
class ListenerInvocation:
    listener_id: str
    event_type: str
    instance_id: str
    activity_id: str | None = None
    task_id: str | None = None
    variables: dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""
    success: bool = True
    error: str | None = None

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()


class _BaseListenerManager:
    """Shared base for listener managers using Observer-like notification."""

    def __init__(self) -> None:
        self._listeners: dict[str, list[Any]] = {}
        self._invocation_log: list[ListenerInvocation] = []
        self._callbacks: dict[str, Callable[..., Any]] = {}

    def register_listener(self, key: str, listener: Any) -> None:
        if key not in self._listeners:
            self._listeners[key] = []
        self._listeners[key].append(listener)
        self._listeners[key].sort(key=lambda ls: ls.priority, reverse=True)

    def register_callback(self, listener_id: str, callback: Callable[..., Any]) -> None:
        self._callbacks[listener_id] = callback

    def _build_invocation(self, event_type: str, instance_id: str, key: str,
                          variables: dict[str, Any] | None,
                          listener: Any) -> ListenerInvocation:
        return ListenerInvocation(
            listener_id=listener.listener_id,
            event_type=event_type,
            instance_id=instance_id,
            activity_id=key,
            variables=variables or {},
        )

    async def _fire(self, event_type: str, key: str, instance_id: str,
                    variables: dict[str, Any] | None,
                    listener_type_label: str) -> list[ListenerInvocation]:
        invocations: list[ListenerInvocation] = []
        listeners = self._listeners.get(key, [])

        for listener in listeners:
            if not listener.enabled or listener.event_type != event_type:
                continue

            invocation = self._build_invocation(event_type, instance_id, key, variables, listener)

            try:
                await self._invoke_listener(listener, invocation)
                invocation.success = True
            except Exception as e:
                invocation.success = False
                invocation.error = str(e)
                logger.warning("%s listener %s failed: %s", listener_type_label, listener.listener_id, e)

            invocations.append(invocation)
            self._invocation_log.append(invocation)

        return invocations

    async def _invoke_listener(self, listener: Any, invocation: ListenerInvocation) -> Any:
        if listener.listener_id in self._callbacks:
            callback = self._callbacks[listener.listener_id]
            return await callback(invocation)
        if listener.expression:
            from ..expression.evaluator import EvaluationContext
            from ..expression.python_evaluator import PythonEvaluator
            context = dict(invocation.variables)
            context["eventType"] = invocation.event_type
            context["instanceId"] = invocation.instance_id
            context["activityId"] = invocation.activity_id
            return PythonEvaluator().evaluate(listener.expression, EvaluationContext(variables=context))
        if listener.script:
            from ..dmn.feel_engine import FEELEngine
            fe_ctx = dict(invocation.variables)
            fe_ctx["eventType"] = invocation.event_type
            return FEELEngine().evaluate(listener.script, fe_ctx)
        if listener.class_name:
            logger.info("Java class listener not supported in Python runtime: %s", listener.class_name)
        return None

    def get_listeners(self, key: str) -> list[Any]:
        return list(self._listeners.get(key, []))

    def get_invocation_log(self, instance_id: str | None = None) -> list[ListenerInvocation]:
        if instance_id:
            return [i for i in self._invocation_log if i.instance_id == instance_id]
        return list(self._invocation_log)

    def remove_listener(self, key: str, listener_id: str) -> bool:
        listeners = self._listeners.get(key, [])
        for i, listener in enumerate(listeners):
            if listener.listener_id == listener_id:
                listeners.pop(i)
                return True
        return False


class TaskListenerManager(_BaseListenerManager):
    """Manages task-level lifecycle listeners (Observer pattern)."""

    async def fire_event(
        self,
        event_type: str,
        task_definition_key: str,
        instance_id: str,
        activity_id: str | None = None,
        task_id: str | None = None,
        variables: dict[str, Any] | None = None,
    ) -> list[ListenerInvocation]:
        return await self._fire(event_type, task_definition_key, instance_id, variables, "Task")


class ExecutionListenerManager(_BaseListenerManager):
    """Manages execution-level lifecycle listeners (Observer pattern)."""

    async def fire_event(
        self,
        event_type: str,
        activity_id: str,
        instance_id: str,
        variables: dict[str, Any] | None = None,
    ) -> list[ListenerInvocation]:
        return await self._fire(event_type, activity_id, instance_id, variables, "Execution")
