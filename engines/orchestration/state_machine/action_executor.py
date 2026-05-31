"""Action executor for state machine entry/exit/transition actions.

Executes entry, exit, and transition actions with integration/runtime hooks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ...core.instance import ProcessInstance
from ...core.engine import OrchestrationEngine


@dataclass
class StateAction:
    action_id: str
    name: str | None = None
    action_type: str = "entry"
    expression: str | None = None
    target_variable: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)


class ActionExecutionError(RuntimeError):
    pass


class ActionExecutor:
    def __init__(self, orchestration_engine: OrchestrationEngine | None = None) -> None:
        self._engine = orchestration_engine
        self._actions: dict[str, StateAction] = {}

    def register(self, action: StateAction) -> None:
        self._actions[action.action_id] = action

    def execute_entry(self, state_id: str, instance: ProcessInstance) -> dict[str, Any]:
        results: dict[str, Any] = {}
        for action in self._actions.values():
            if action.action_type == "entry":
                result = self._execute_action(action, instance, state_id)
                results[action.action_id] = result
        return results

    def execute_exit(self, state_id: str, instance: ProcessInstance) -> dict[str, Any]:
        results: dict[str, Any] = {}
        for action in self._actions.values():
            if action.action_type == "exit":
                result = self._execute_action(action, instance, state_id)
                results[action.action_id] = result
        return results

    def execute_do(self, state_id: str, instance: ProcessInstance) -> dict[str, Any]:
        results: dict[str, Any] = {}
        for action in self._actions.values():
            if action.action_type == "do":
                result = self._execute_action(action, instance, state_id)
                results[action.action_id] = result
        return results

    def execute_transition_actions(
        self,
        transition_id: str,
        instance: ProcessInstance,
        actions: list[str],
    ) -> dict[str, Any]:
        results: dict[str, Any] = {}
        for action_id in actions:
            if action_id in self._actions:
                result = self._execute_action(self._actions[action_id], instance, transition_id)
                results[action_id] = result
            else:
                instance.set_variable(f"transition.{transition_id}.action.{action_id}", "executed")
                results[action_id] = {"status": "executed"}
        return results

    def _execute_action(
        self,
        action: StateAction,
        instance: ProcessInstance,
        state_id: str,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {"action_id": action.action_id, "type": action.action_type}

        if action.expression:
            from ...expression.evaluator import EvaluationContext
            from ...expression.python_evaluator import PythonEvaluator
            try:
                value = PythonEvaluator().evaluate(action.expression, EvaluationContext(variables=instance.get_all_variables()))
                result["result"] = value
                if action.target_variable:
                    instance.set_variable(action.target_variable, value)
                else:
                    instance.set_variable(f"state.{state_id}.{action.action_type}.{action.action_id}", value)
            except Exception as e:
                result["error"] = str(e)
                raise ActionExecutionError(f"Action {action.action_id} failed: {e}")

        return result
