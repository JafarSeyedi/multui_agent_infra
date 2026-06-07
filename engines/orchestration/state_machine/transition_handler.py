"""Transition handler for state machine.

Implements trigger matching, guard evaluation, priority/order,
and target resolution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Transition:
    transition_id: str | None = None
    source: str = ""
    target: str = ""
    trigger: str | None = None
    guard: str | None = None
    priority: int = 0
    actions: list[str] = field(default_factory=list)
    kind: str = "external"


@dataclass
class TriggerMatch:
    transition: Transition
    matched: bool = False
    priority: int = 0


class TransitionHandler:
    def __init__(self) -> None:
        self._transitions: list[Transition] = []

    def register(self, transition: Transition) -> None:
        self._transitions.append(transition)

    def resolve(
        self,
        current_state: str,
        transitions: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> dict[str, Any] | None:
        outgoing = self._get_outgoing_transitions(current_state, transitions)

        if not outgoing:
            return None

        candidates: list[TriggerMatch] = []

        for transition in outgoing:
            guard = transition.get("guard")
            if guard:
                if not self._evaluate_guard(guard, context):
                    continue

            trigger = transition.get("trigger")
            if trigger:
                if not self._matches_trigger(trigger, context):
                    continue

            priority = transition.get("priority", 0)
            candidates.append(TriggerMatch(
                transition=Transition(
                    transition_id=transition.get("id"),
                    source=transition.get("source", current_state),
                    target=transition.get("target", ""),
                    trigger=trigger,
                    guard=guard,
                    priority=priority,
                    actions=transition.get("actions", []),
                    kind=transition.get("kind", "external"),
                ),
                matched=True,
                priority=priority,
            ))

        if not candidates:
            unconditional = [
                t for t in outgoing if not t.get("guard") and not t.get("trigger")
            ]
            if unconditional:
                best_unconditional: dict[str, Any] = max(unconditional, key=lambda t: t.get("priority", 0))
                return best_unconditional
            return None

        best_candidate: TriggerMatch = max(candidates, key=lambda c: c.priority)
        return {
            "id": best_candidate.transition.transition_id,
            "source": current_state,
            "target": best_candidate.transition.target,
            "trigger": best_candidate.transition.trigger,
            "actions": best_candidate.transition.actions,
            "kind": best_candidate.transition.kind,
        }

    def _get_outgoing_transitions(
        self,
        current_state: str,
        transitions: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        outgoing: list[dict[str, Any]] = []
        for t in transitions:
            source = t.get("source", t.get("sourceRef", ""))
            if source == current_state:
                outgoing.append(t)
        return outgoing

    def _matches_trigger(self, trigger: str, context: dict[str, Any]) -> bool:
        trigger_value = context.get(f"trigger.{trigger}")
        if trigger_value is not None:
            return bool(trigger_value)
        event_value = context.get(f"event.{trigger}")
        if event_value is not None:
            return bool(event_value)
        return False

    def _evaluate_guard(self, guard: str, context: dict[str, Any]) -> bool:
        if guard in {"true", "True", "1"}:
            return True
        if guard in {"false", "False", "0"}:
            return False
        try:
            from ..expression.evaluator import EvaluationContext
            from ..expression.python_evaluator import PythonEvaluator
            result = PythonEvaluator().evaluate(guard, EvaluationContext(variables=context))
            return bool(result)
        except Exception:
            return False

    def get_available_transitions(
        self,
        current_state: str,
        transitions: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        outgoing = self._get_outgoing_transitions(current_state, transitions)
        for t in outgoing:
            guard = t.get("guard")
            if guard and not self._evaluate_guard(guard, context):
                continue
            trigger = t.get("trigger")
            if trigger and not self._matches_trigger(trigger, context):
                continue
            result.append(t)
        return result
