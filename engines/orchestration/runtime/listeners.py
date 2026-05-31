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


class TaskListenerManager:
    def __init__(self) -> None:
        self._listeners: dict[str, list[TaskListener]] = {}
        self._invocation_log: list[ListenerInvocation] = []
        self._callbacks: dict[str, Callable[..., Any]] = {}

    def register_listener(
        self,
        task_definition_key: str,
        listener: TaskListener,
    ) -> None:
        if task_definition_key not in self._listeners:
            self._listeners[task_definition_key] = []
        self._listeners[task_definition_key].append(listener)
        self._listeners[task_definition_key].sort(key=lambda l: l.priority, reverse=True)

    def register_callback(
        self,
        listener_id: str,
        callback: Callable[..., Any],
    ) -> None:
        self._callbacks[listener_id] = callback

    async def fire_event(
        self,
        event_type: str,
        task_definition_key: str,
        instance_id: str,
        activity_id: str | None = None,
        task_id: str | None = None,
        variables: dict[str, Any] | None = None,
    ) -> list[ListenerInvocation]:
        invocations: list[ListenerInvocation] = []
        listeners = self._listeners.get(task_definition_key, [])

        for listener in listeners:
            if not listener.enabled:
                continue
            if listener.event_type != event_type:
                continue

            invocation = ListenerInvocation(
                listener_id=listener.listener_id,
                event_type=event_type,
                instance_id=instance_id,
                activity_id=activity_id,
                task_id=task_id,
                variables=variables or {},
            )

            try:
                await self._invoke_listener(listener, invocation)
                invocation.success = True
            except Exception as e:
                invocation.success = False
                invocation.error = str(e)
                logger.warning("Task listener %s failed: %s", listener.listener_id, e)

            invocations.append(invocation)
            self._invocation_log.append(invocation)

        return invocations

    async def _invoke_listener(self, listener: TaskListener, invocation: ListenerInvocation) -> Any:
        if listener.listener_id in self._callbacks:
            callback = self._callbacks[listener.listener_id]
            return await callback(invocation)

        if listener.expression:
            from ...expression.evaluator import EvaluationContext
            from ...expression.python_evaluator import PythonEvaluator
            context = dict(invocation.variables)
            context["eventType"] = invocation.event_type
            context["instanceId"] = invocation.instance_id
            context["activityId"] = invocation.activity_id
            return PythonEvaluator().evaluate(listener.expression, EvaluationContext(variables=context))

        if listener.script:
            from ...dmn.feel_engine import FEELEngine
            context = dict(invocation.variables)
            context["eventType"] = invocation.event_type
            return FEELEngine().evaluate(listener.script, context)

        if listener.class_name:
            logger.info("Java class listener not supported in Python runtime: %s", listener.class_name)

        return None

    def get_listeners(self, task_definition_key: str) -> list[TaskListener]:
        return list(self._listeners.get(task_definition_key, []))

    def get_invocation_log(
        self,
        instance_id: str | None = None,
        task_definition_key: str | None = None,
    ) -> list[ListenerInvocation]:
        results = self._invocation_log
        if instance_id:
            results = [i for i in results if i.instance_id == instance_id]
        return results

    def remove_listener(self, task_definition_key: str, listener_id: str) -> bool:
        listeners = self._listeners.get(task_definition_key, [])
        for i, listener in enumerate(listeners):
            if listener.listener_id == listener_id:
                listeners.pop(i)
                return True
        return False


class ExecutionListenerManager:
    def __init__(self) -> None:
        self._listeners: dict[str, list[ExecutionListener]] = {}
        self._invocation_log: list[ListenerInvocation] = []
        self._callbacks: dict[str, Callable[..., Any]] = {}

    def register_listener(
        self,
        activity_id: str,
        listener: ExecutionListener,
    ) -> None:
        if activity_id not in self._listeners:
            self._listeners[activity_id] = []
        self._listeners[activity_id].append(listener)
        self._listeners[activity_id].sort(key=lambda l: l.priority, reverse=True)

    def register_callback(
        self,
        listener_id: str,
        callback: Callable[..., Any],
    ) -> None:
        self._callbacks[listener_id] = callback

    async def fire_event(
        self,
        event_type: str,
        activity_id: str,
        instance_id: str,
        variables: dict[str, Any] | None = None,
    ) -> list[ListenerInvocation]:
        invocations: list[ListenerInvocation] = []
        listeners = self._listeners.get(activity_id, [])

        for listener in listeners:
            if not listener.enabled or listener.event_type != event_type:
                continue

            invocation = ListenerInvocation(
                listener_id=listener.listener_id,
                event_type=event_type,
                instance_id=instance_id,
                activity_id=activity_id,
                variables=variables or {},
            )

            try:
                await self._invoke_listener(listener, invocation)
                invocation.success = True
            except Exception as e:
                invocation.success = False
                invocation.error = str(e)
                logger.warning("Execution listener %s failed: %s", listener.listener_id, e)

            invocations.append(invocation)
            self._invocation_log.append(invocation)

        return invocations

    async def _invoke_listener(self, listener: ExecutionListener, invocation: ListenerInvocation) -> Any:
        if listener.listener_id in self._callbacks:
            callback = self._callbacks[listener.listener_id]
            return await callback(invocation)
        if listener.expression:
            from ...expression.evaluator import EvaluationContext
            from ...expression.python_evaluator import PythonEvaluator
            context = dict(invocation.variables)
            context["eventType"] = invocation.event_type
            return PythonEvaluator().evaluate(listener.expression, EvaluationContext(variables=context))
        if listener.script:
            from ...dmn.feel_engine import FEELEngine
            return FEELEngine().evaluate(listener.script, dict(invocation.variables))
        return None

    def get_listeners(self, activity_id: str) -> list[ExecutionListener]:
        return list(self._listeners.get(activity_id, []))

    def get_invocation_log(self, instance_id: str | None = None) -> list[ListenerInvocation]:
        if instance_id:
            return [i for i in self._invocation_log if i.instance_id == instance_id]
        return list(self._invocation_log)
