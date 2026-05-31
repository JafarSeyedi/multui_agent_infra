"""Execution loop for state machine definitions.

Supports hierarchy, parallel regions, history, pseudostates,
and event/action semantics at UML state diagram level.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ...core.instance import ProcessInstance
from ...core.engine import OrchestrationEngine
from .transition_handler import TransitionHandler
from .history_manager import StateMachineHistory


logger = logging.getLogger(__name__)


class StateKind(str, Enum):
    SIMPLE = "simple"
    COMPOSITE = "composite"
    SUBMACHINE = "submachine"
    FINAL = "final"


class PseudoStateKind(str, Enum):
    INITIAL = "initial"
    CHOICE = "choice"
    JUNCTION = "junction"
    FORK = "fork"
    JOIN = "join"
    SHALLOW_HISTORY = "shallowHistory"
    DEEP_HISTORY = "deepHistory"
    TERMINATE = "terminate"
    ENTRY_POINT = "entryPoint"
    EXIT_POINT = "exitPoint"


@dataclass
class StateContext:
    state_id: str
    name: str | None = None
    kind: str = StateKind.SIMPLE.value
    parent: str | None = None
    children: list[str] = field(default_factory=list)
    entry_actions: list[str] = field(default_factory=list)
    exit_actions: list[str] = field(default_factory=list)
    do_actions: list[str] = field(default_factory=list)
    is_active: bool = False
    is_final: bool = False
    region_id: str | None = None


@dataclass
class RegionContext:
    region_id: str
    states: list[str] = field(default_factory=list)
    initial_state: str | None = None
    current_state: str | None = None
    is_orthogonal: bool = False


@dataclass
class StateMachineModel:
    states: list[dict[str, Any]] = field(default_factory=list)
    transitions: list[dict[str, Any]] = field(default_factory=list)
    initial_state: str | None = None
    regions: list[dict[str, Any]] = field(default_factory=list)
    pseudostates: list[dict[str, Any]] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)
    context: dict[str, StateContext] = field(default_factory=dict)
    region_context: dict[str, RegionContext] = field(default_factory=dict)


class StateMachineExecutor:
    """Execute a state machine definition with full UML semantics."""

    def __init__(
        self,
        orchestration_engine: OrchestrationEngine | None = None,
        transition_handler: TransitionHandler | None = None,
    ) -> None:
        self.orchestration_engine = orchestration_engine
        self.transition_handler = transition_handler or TransitionHandler()
        self.history_manager = StateMachineHistory()
        self._models: dict[str, StateMachineModel] = {}

    async def execute(self, instance: ProcessInstance, definition: dict[str, Any]) -> None:
        model = self._normalize_model(definition)
        self._models[instance.id] = model

        current_state_id = model.initial_state
        if not current_state_id:
            if model.states:
                for s in model.states:
                    if s.get("kind", "").lower() == PseudoStateKind.INITIAL.value:
                        current_state_id = s.get("target") or s.get("transitions", [{}])[0].get("target")
                        break
                if not current_state_id:
                    current_state_id = model.states[0].get("id") if model.states else None

        if not current_state_id:
            logger.warning("No initial state found for state machine instance %s", instance.id)
            instance.complete()
            return

        steps = 0
        max_steps = definition.get("_max_steps", 200)

        while steps < max_steps:
            steps += 1
            instance.current_activity_id = str(current_state_id)

            state_ctx = model.context.get(current_state_id)
            if state_ctx is None:
                state_def = next((s for s in model.states if s.get("id") == current_state_id), None)
                if state_def is None:
                    break
                state_ctx = StateContext(
                    state_id=current_state_id,
                    name=state_def.get("name"),
                    kind=state_def.get("kind", StateKind.SIMPLE.value),
                )
                model.context[current_state_id] = state_ctx

            if not state_ctx.is_active and state_ctx.entry_actions:
                await self._execute_actions(instance, state_ctx.entry_actions, "entry", current_state_id)

            if state_ctx.is_active and state_ctx.do_actions:
                await self._execute_actions(instance, state_ctx.do_actions, "do", current_state_id)

            state_ctx.is_active = True
            instance.set_variable(f"state.{current_state_id}.active", True)

            if self.orchestration_engine is not None:
                self.orchestration_engine.event_bus.publish(
                    type=EventType.ACTIVITY_STARTED,
                    data={
                        "instance_id": instance.id,
                        "state_id": current_state_id,
                        "engine_type": "state_machine",
                    },
                )

            transition = self.transition_handler.resolve(
                current_state_id,
                model.transitions,
                instance.get_all_variables(),
            )

            if not transition:
                if state_ctx.kind == StateKind.FINAL.value or current_state_id.endswith("Final"):
                    state_ctx.is_final = True
                    if state_ctx.exit_actions:
                        await self._execute_actions(instance, state_ctx.exit_actions, "exit", current_state_id)
                    state_ctx.is_active = False
                    instance.set_variable(f"state.{current_state_id}.active", False)
                    break
                if state_ctx.kind == StateKind.SIMPLE.value:
                    pass
                break

            target_id = transition.get("target")
            if not target_id:
                break

            guard = transition.get("guard")
            if guard:
                if not self._evaluate_guard(guard, instance.get_all_variables()):
                    continue

            if state_ctx.exit_actions:
                await self._execute_actions(instance, state_ctx.exit_actions, "exit", current_state_id)

            transition_actions = transition.get("actions", [])
            if transition_actions:
                await self._execute_actions(instance, transition_actions, "transition", current_state_id)

            state_ctx.is_active = False
            instance.set_variable(f"state.{current_state_id}.active", False)

            target_ctx = model.context.get(target_id)
            if target_ctx and target_ctx.kind == PseudoStateKind.TERMINATE.value:
                instance.complete()
                return

            self.history_manager.push(instance.id, current_state_id, target_id, transition.get("trigger"))
            current_state_id = target_id

        if steps >= max_steps:
            raise RuntimeError(f"State machine execution exceeded step limit for instance {instance.id}")

        final_ctx = model.context.get(current_state_id)
        if final_ctx and final_ctx.kind != StateKind.FINAL.value:
            if final_ctx.do_actions:
                await self._execute_actions(instance, final_ctx.do_actions, "do", final_ctx.state_id)

        instance.complete()

    def _normalize_model(self, definition: dict[str, Any]) -> StateMachineModel:
        model = StateMachineModel()
        model.states = definition.get("states", definition.get("elements", []))
        model.transitions = definition.get("transitions", [])
        model.regions = definition.get("regions", [])
        model.pseudostates = definition.get("pseudostates", [])
        model.events = definition.get("events", [])

        model.initial_state = definition.get("initial_state") or definition.get("initialState")

        for state_def in model.states:
            state_id = state_def.get("id", "")
            ctx = StateContext(
                state_id=state_id,
                name=state_def.get("name"),
                kind=state_def.get("kind", StateKind.SIMPLE.value),
                entry_actions=state_def.get("entry", state_def.get("entryActions", [])),
                exit_actions=state_def.get("exit", state_def.get("exitActions", [])),
                do_actions=state_def.get("doActivity", state_def.get("do", [])),
            )
            model.context[state_id] = ctx

        for region_def in model.regions:
            region_id = region_def.get("id", f"region_{len(model.region_context)}")
            region_ctx = RegionContext(
                region_id=region_id,
                states=region_def.get("states", []),
                initial_state=region_def.get("initialState"),
                is_orthogonal=region_def.get("orthogonal", False),
            )
            model.region_context[region_id] = region_ctx

        if not model.initial_state:
            for pseudo in model.pseudostates:
                if pseudo.get("kind", "").lower() == PseudoStateKind.INITIAL.value:
                    target = pseudo.get("transitions", [{}])
                    if isinstance(target, list) and target:
                        model.initial_state = target[0].get("target")
                    break

        return model

    async def _execute_actions(
        self,
        instance: ProcessInstance,
        actions: list[str],
        action_type: str,
        state_id: str,
    ) -> None:
        for action in actions:
            if isinstance(action, str):
                instance.set_variable(f"state.{state_id}.{action_type}", action)
            elif isinstance(action, dict):
                action_name = action.get("name", action.get("id", "unknown"))
                instance.set_variable(f"state.{state_id}.{action_type}.{action_name}", action)

    def _evaluate_guard(self, guard: str, context: dict[str, Any]) -> bool:
        if guard in {"true", "True", "1"}:
            return True
        if guard in {"false", "False", "0"}:
            return False
        try:
            from ...expression.evaluator import EvaluationContext
            from ...expression.python_evaluator import PythonEvaluator
            result = PythonEvaluator().evaluate(guard, EvaluationContext(variables=context))
            return bool(result)
        except Exception:
            return False

    def get_history(self, instance_id: str) -> list[dict[str, Any]]:
        return self.history_manager.get_history(instance_id)

    def get_current_state(self, instance_id: str) -> str | None:
        model = self._models.get(instance_id)
        if model is None:
            return None
        for state_id, ctx in model.context.items():
            if ctx.is_active:
                return state_id
        return None
