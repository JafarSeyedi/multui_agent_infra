"""Core BPMN process traversal and scheduling."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from ..core.correlation import CorrelationKeySet
from ..core.event_bus import Event, EventType
from ..core.context import ContextManager, ContextScope, ExecutionContext
from ..core.engine import OrchestrationEngine, ProcessDefinition
from ..core.instance import ProcessInstance
from ..core.token import Token, TokenState
from ..runtime.state_manager import StateManager
from .activity_handler import ActivityHandler, ActivityExecutionResult
from .sequence_flow import SequenceFlow, compute_next_nodes


@dataclass(frozen=True)
class ProcessModel:
    definition_id: str
    start_node: str | None
    activities: list[dict[str, Any]]
    flows: list[dict[str, Any]]


@dataclass(frozen=True)
class ProcessExecutionOutcome:
    completed: bool
    waiting: bool = False
    current_node: str | None = None


class BPMNProcessExecutor:
    """Evaluate a BPMN process dictionary and perform activity transitions."""

    def __init__(
        self,
        *,
        engine: object,
        orchestration_engine: OrchestrationEngine,
        state_manager: StateManager,
        context_manager: ContextManager,
    ) -> None:
        self._engine = engine
        self._orchestration_engine = orchestration_engine
        self._state_manager = state_manager
        self._context_manager = context_manager
        self._activity_handler = ActivityHandler(orchestration_engine=orchestration_engine)

    async def execute(self, instance: ProcessInstance, definition_payload: dict[str, Any]) -> ProcessExecutionOutcome:
        model = self._normalize_model(definition_payload)
        context = self._context_manager.get_context(instance.id)
        if context is None:
            context = self._context_manager.create_context(ContextScope.PROCESS, instance.id)

        if model.start_node is None:
            return ProcessExecutionOutcome(completed=True)

        token = self._ensure_runtime_token(instance, model.start_node)

        current = model.start_node
        visited: set[str] = set()
        guard_steps: int = 0

        while current and guard_steps < 200:
            guard_steps += 1
            if current in visited:
                break
            visited.add(current)
            activity = next((item for item in model.activities if item.get("id") == current), None)
            if not activity:
                break
            activity_id = str(activity.get("id", current))
            activity_type = str(activity.get("type", "task"))
            before_variables = instance.get_all_variables()

            instance.start_activity(activity_id, str(activity.get("name", activity_id)), activity_type)
            token.move_to(activity_id, activity_type)
            token.create_snapshot(before_variables)
            await self._orchestration_engine.token_manager.persist_token(token.token_id)
            await self._orchestration_engine.instance_manager.persist_instance(instance.id)
            await self._orchestration_engine.event_bus.publish(
                Event(
                    type=EventType.ACTIVITY_STARTED,
                    data={"instance_id": instance.id, "activity_id": activity_id, "activity_type": activity_type},
                )
            )

            execution_result = self._activity_handler.execute(instance, activity, context=context)
            if not execution_result.success:
                instance.fail_activity(activity_id, str(execution_result.error))
                await self._orchestration_engine.instance_manager.persist_instance(instance.id)
                raise RuntimeError(f"Activity failed: {execution_result.error}")

            await self._persist_new_variables(instance, before_variables)

            if execution_result.waiting:
                token.wait(f"{execution_result.wait_kind}:{execution_result.wait_name}")
                token.create_snapshot(instance.get_all_variables())
                await self._orchestration_engine.token_manager.persist_token(token.token_id)
                await self._register_wait(instance, activity_id, execution_result)
                await self._state_manager.set_persisted(
                    instance.id,
                    "waiting",
                    data={
                        "activity_id": activity_id,
                        "wait_kind": execution_result.wait_kind,
                        "wait_name": execution_result.wait_name,
                    },
                )
                await self._orchestration_engine.instance_manager.persist_instance(instance.id)
                return ProcessExecutionOutcome(completed=False, waiting=True, current_node=activity_id)

            instance.complete_activity(activity_id)
            token.create_snapshot(instance.get_all_variables())
            await self._orchestration_engine.token_manager.persist_token(token.token_id)
            await self._orchestration_engine.instance_manager.persist_instance(instance.id)
            await self._orchestration_engine.event_bus.publish(
                Event(
                    type=EventType.ACTIVITY_COMPLETED,
                    data={"instance_id": instance.id, "activity_id": activity_id, "activity_type": activity_type},
                )
            )

            next_nodes = compute_next_nodes(model.flows, current)
            if not next_nodes:
                token.complete()
                token.create_snapshot(instance.get_all_variables())
                await self._orchestration_engine.token_manager.persist_token(token.token_id)
                return ProcessExecutionOutcome(completed=True, current_node=activity_id)

            current = next_nodes[0]
            if not current:
                break

        if current and guard_steps >= 200:
            raise RuntimeError("BPMN process execution exceeded step limit")
        return ProcessExecutionOutcome(completed=False, current_node=current)

    def _normalize_model(self, payload: dict[str, Any]) -> ProcessModel:
        activities = list(payload.get("activities", []))
        flows = list(payload.get("flows", []))
        start_node = payload.get("start_event_id")
        if not start_node:
            for item in activities:
                if item.get("type", "").lower() in {"startEvent", "startevent", "start"}:
                    start_node = item.get("id")
                    break
        return ProcessModel(definition_id=str(payload.get("id", "process")), start_node=start_node, activities=activities, flows=flows)

    def _ensure_runtime_token(self, instance: ProcessInstance, start_node: str) -> Token:
        tokens = self._orchestration_engine.token_manager.get_instance_tokens(instance.id)
        for token in tokens:
            if token.state in {TokenState.ACTIVE, TokenState.WAITING}:
                return token
        return self._orchestration_engine.token_manager.create_token(instance.id, current_element_id=start_node)

    async def _persist_new_variables(self, instance: ProcessInstance, before_variables: dict[str, Any]) -> None:
        after_variables = instance.get_all_variables()
        for name, value in after_variables.items():
            if name in before_variables and before_variables[name] == value:
                continue
            await self._orchestration_engine.variable_manager.set_persisted(instance.id, instance.id, name, value)

    async def _register_wait(
        self,
        instance: ProcessInstance,
        activity_id: str,
        execution_result: ActivityExecutionResult,
    ) -> None:
        if execution_result.wait_kind == "message" and execution_result.wait_name:
            keys = CorrelationKeySet()
            for name, value in dict(execution_result.correlation_keys or {}).items():
                resolved = instance.get_variable(str(value), value) if isinstance(value, str) else value
                keys.add_key(str(name), str(resolved))
            await self._orchestration_engine.correlation_engine.subscribe_message_persisted(
                execution_result.wait_name,
                keys,
                instance.id,
                activity_id,
            )
            await self._orchestration_engine.event_bus.publish(
                Event(
                    type=EventType.MESSAGE_RECEIVED,
                    data={
                        "instance_id": instance.id,
                        "activity_id": activity_id,
                        "message_name": execution_result.wait_name,
                        "mode": "subscription_created",
                    },
                )
            )
        elif execution_result.wait_kind == "event" and execution_result.wait_name:
            await self._orchestration_engine.correlation_engine.subscribe_event_persisted(
                execution_result.wait_name,
                instance.id,
                activity_id,
            )
            await self._orchestration_engine.event_bus.publish(
                Event(
                    type=EventType.SIGNAL_CAUGHT,
                    data={
                        "instance_id": instance.id,
                        "activity_id": activity_id,
                        "event_name": execution_result.wait_name,
                        "mode": "subscription_created",
                    },
                )
            )
