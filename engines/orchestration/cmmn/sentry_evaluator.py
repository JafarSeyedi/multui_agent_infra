"""Evaluate CMMN sentries (entry/exit criteria).

Supports CMMN 1.1 sentry semantics with OnPart (PlanItemOnPart, CaseFileOnPart,
TimerOnPart, ExternalOnPart), IfPart, and full event-driven evaluation.
Sentries are re-evaluated whenever plan item state changes or case file items change.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from ...document.models.osdm_models import (
    Sentry,
    EntryCriterion,
    ExitCriterion,
    SentryExpression,
)
from ..expression.evaluator import EvaluationContext
from ..expression.python_evaluator import PythonEvaluator


logger = logging.getLogger(__name__)

# CMMN standard events per §5.4.4
CMMN_STANDARD_EVENTS = {
    "occur", "create", "enable", "disable", "manualStart", "resume", "suspend",
    "complete", "terminate", "fault", "close", "reactivate",
}
CMMN_CASEFILE_EVENTS = {
    "create", "update", "replace", "addChild", "removeChild", "delete",
}


@dataclass
class SentryRule:
    sentry_id: str | None = None
    name: str | None = None
    on_parts: list[dict[str, Any]] = field(default_factory=list)
    if_part: str | None = None
    references: list[str] = field(default_factory=list)
    is_entry_criterion: bool = True
    # Track which OnParts have been triggered for AND semantics
    triggered_on_parts: set[str] = field(default_factory=set)


@dataclass
class SentryEvaluationResult:
    satisfied: bool = False
    triggered_on_parts: list[str] = field(default_factory=list)
    evaluated_conditions: dict[str, bool] = field(default_factory=dict)


class SentryEvaluator:
    """CMMN 1.1 compliant sentry evaluator with event-driven semantics.

    Per CMMN §5.4.4, a sentry is satisfied when:
    1. ALL OnParts have been triggered (AND semantics) — each OnPart fires when
       its sourceRef plan item/case file item experiences the specified standardEvent
    2. AND the IfPart condition evaluates to true (if present)
    """

    def __init__(self) -> None:
        self._evaluator = PythonEvaluator()
        self._rules: dict[str, SentryRule] = {}
        # Track which events have fired: {source_ref: {event_name}}
        self._fired_events: dict[str, set[str]] = {}

    def register(self, sentry: dict[str, Any] | Sentry) -> None:
        if isinstance(sentry, dict):
            sentry_id = sentry.get("id", "")
            on_parts_raw = sentry.get("onParts", sentry.get("on", []))
            on_parts: list[dict[str, Any]] = on_parts_raw if isinstance(on_parts_raw, list) else []
            references_raw = sentry.get("planItemRefs", sentry.get("sentryRefs", []))
            references: list[str] = references_raw if isinstance(references_raw, list) else []
            rule = SentryRule(
                sentry_id=sentry_id,
                name=sentry.get("name"),
                on_parts=on_parts,
                if_part=sentry.get("ifPart") or sentry.get("condition"),
                references=references,
                is_entry_criterion=sentry.get("isEntryCriterion", True),
            )
        elif isinstance(sentry, Sentry):
            sentry_id = sentry.id
            on_parts = []
            for op in getattr(sentry, "on_parts", []) or []:
                on_parts.append({
                    "source_ref": getattr(getattr(op, "source_ref", None), "id", None),
                    "standard_event": getattr(op, "standard_event", None),
                    "type": type(op).__name__,
                    "case_file_event": getattr(op, "case_file_event", None),
                })
            if_part = None
            if getattr(sentry, "if_part", None):
                if_part = str(sentry.if_part)
            elif getattr(sentry, "names", None):
                sentry_expr = getattr(sentry, "names", None)
                if sentry_expr and hasattr(sentry_expr, "body"):
                    if_part = sentry_expr.body
            rule = SentryRule(
                sentry_id=sentry_id,
                name=getattr(sentry, "name", None),
                on_parts=on_parts,
                if_part=if_part,
                references=[r.id for r in getattr(sentry, "on_parts", []) or [] if hasattr(r, "source_ref") and hasattr(r.source_ref, "id")],
                is_entry_criterion=isinstance(sentry, EntryCriterion),
            )
        else:
            return
        if sentry_id:
            self._rules[sentry_id] = rule

    def register_osdm_sentry(self, sentry: Sentry) -> None:
        """Register from OSDM Sentry object."""
        self.register(sentry)

    def record_event(self, source_ref: str, event_name: str) -> list[str]:
        """Record that a plan item state change or case file event occurred.
        Returns list of sentry IDs that may now be newly satisfied."""
        if source_ref not in self._fired_events:
            self._fired_events[source_ref] = set()
        self._fired_events[source_ref].add(event_name)

        # Update triggered_on_parts for matching rules
        newly_satisfied = []
        for sentry_id, rule in self._rules.items():
            for on_part in rule.on_parts:
                part_source = on_part.get("source_ref")
                part_event = on_part.get("standard_event")
                if part_source == source_ref and part_event == event_name:
                    rule.triggered_on_parts.add(f"{source_ref}:{event_name}")
            # Check if rule is now fully satisfied
            if self._check_on_parts_and(rule) and self._evaluate_if_part(rule, {}):
                newly_satisfied.append(sentry_id)
        return newly_satisfied

    def evaluate_entry_criteria(self, criteria: list[dict[str, Any]] | list[Any], instance_or_context: Any) -> bool:
        if not criteria:
            return True
        context = self._extract_context(instance_or_context)
        if len(criteria) == 1:
            criterion = criteria[0]
            if isinstance(criterion, EntryCriterion) or isinstance(criterion, ExitCriterion):
                return self._evaluate_osdm_criterion(criterion, context)
            expression = criterion.get("condition") if isinstance(criterion, dict) else getattr(criterion, "condition", None)
            if expression:
                return bool(self._evaluator.evaluate(str(expression), EvaluationContext(variables=context)))
            return True
        return all(
            self._evaluate_single_criterion(c, context) for c in criteria
        )

    def evaluate_exit_criteria(self, criteria: list[dict[str, Any]] | list[Any], instance_or_context: Any) -> bool:
        """Evaluate exit criteria — CMMN §5.4.4."""
        if not criteria:
            return False  # No exit criteria means manual completion required
        return self.evaluate_entry_criteria(criteria, instance_or_context)

    def is_active(self, task: dict | Any, context: dict) -> bool:
        if isinstance(task, dict):
            sentry_ref = task.get("sentry") or (task.get("entryCriterionRefs", [None])[0] if task.get("entryCriterionRefs") else None)
            if sentry_ref:
                if isinstance(sentry_ref, str):
                    rule = self._rules.get(sentry_ref)
                    if rule:
                        return self._evaluate_rule(rule, context)
                elif isinstance(sentry_ref, dict):
                    expression = sentry_ref.get("condition") or sentry_ref.get("body")
                    if expression:
                        return bool(self._evaluator.evaluate(expression, EvaluationContext(variables=context)))
                    return True
                return False
            return True
        return True

    def is_complete(self, task: dict | Any, context: dict) -> bool:
        if isinstance(task, dict):
            expression = task.get("completionCondition") or task.get("exitCriterion")
            if not expression:
                return False
            return bool(self._evaluator.evaluate(expression, EvaluationContext(variables=context)))
        return False

    def check_sentry_satisfied(self, sentry_id: str, context: dict[str, Any] | None = None) -> bool:
        """Check if a specific sentry is satisfied given current triggered events."""
        rule = self._rules.get(sentry_id)
        if rule is None:
            return False
        ctx = context or {}
        return self._check_on_parts_and(rule) and self._evaluate_if_part(rule, ctx)

    def get_unsatisfied_sentries(self, context: dict[str, Any] | None = None) -> list[str]:
        """Return sentry IDs that are not yet satisfied."""
        ctx = context or {}
        return [sid for sid, rule in self._rules.items() if not self._evaluate_rule(rule, ctx)]

    def _evaluate_rule(self, rule: SentryRule, context: dict[str, Any]) -> bool:
        # CMMN §5.4.4: ALL OnParts must be triggered AND IfPart must be true
        if not self._check_on_parts_and(rule):
            return False
        return self._evaluate_if_part(rule, context)

    def _check_on_parts_and(self, rule: SentryRule) -> bool:
        """Check that ALL OnParts have been triggered (AND semantics)."""
        if not rule.on_parts:
            return True
        for on_part in rule.on_parts:
            source_ref = on_part.get("source_ref")
            standard_event = on_part.get("standard_event")
            if source_ref and standard_event:
                fired = self._fired_events.get(source_ref, set())
                if standard_event not in fired:
                    # Also check case_file_event for CaseFileOnPart
                    case_file_event = on_part.get("case_file_event")
                    if case_file_event is None or case_file_event not in fired:
                        return False
        return True

    def _evaluate_if_part(self, rule: SentryRule, context: dict[str, Any]) -> bool:
        """Evaluate IfPart condition. If absent, defaults to true (per CMMN §5.4.4)."""
        if not rule.if_part:
            return True
        return bool(self._evaluator.evaluate(rule.if_part, EvaluationContext(variables=context)))

    def _evaluate_single_criterion(self, criterion: dict[str, Any], context: dict[str, Any]) -> bool:
        expression = criterion.get("condition") or criterion.get("body")
        if not expression:
            return True
        return bool(self._evaluator.evaluate(expression, EvaluationContext(variables=context)))

    def _evaluate_osdm_criterion(self, criterion: Any, context: dict[str, Any]) -> bool:
        """Evaluate an OSDM EntryCriterion or ExitCriterion."""
        condition = getattr(criterion, "condition", None) or getattr(criterion, "names", None)
        if condition:
            expr = str(condition.body) if hasattr(condition, "body") else str(condition)
            return bool(self._evaluator.evaluate(expr, EvaluationContext(variables=context)))
        return True

    def _extract_context(self, instance_or_context: Any) -> dict[str, Any]:
        if isinstance(instance_or_context, dict):
            return instance_or_context
        if hasattr(instance_or_context, "get_all_variables"):
            return instance_or_context.get_all_variables()
        if hasattr(instance_or_context, "variables"):
            return dict(instance_or_context.variables)
        return {}

    def evaluate_all_sentries(self, context: dict[str, Any]) -> dict[str, bool]:
        results: dict[str, bool] = {}
        for sentry_id, rule in self._rules.items():
            results[sentry_id] = self._evaluate_rule(rule, context)
        return results

    def reset(self) -> None:
        """Reset all fired events and triggered on-parts (for testing)."""
        self._fired_events.clear()
        for rule in self._rules.values():
            rule.triggered_on_parts.clear()
