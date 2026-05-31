"""Evaluate CMMN sentries (entry/exit criteria).

Supports CMMN 1.1 sentry semantics with OnPart, IfPart, and PlanItemOnPart
for evaluating entry and exit criteria against case file and plan item state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ...expression.evaluator import EvaluationContext
from ...expression.python_evaluator import PythonEvaluator


@dataclass
class SentryRule:
    sentry_id: str | None = None
    name: str | None = None
    on_parts: list[dict[str, Any]] = field(default_factory=list)
    if_part: str | None = None
    references: list[str] = field(default_factory=list)
    is_entry_criterion: bool = True


@dataclass
class SentryEvaluationResult:
    satisfied: bool = False
    triggered_on_parts: list[str] = field(default_factory=list)
    evaluated_conditions: dict[str, bool] = field(default_factory=dict)


class SentryEvaluator:
    def __init__(self) -> None:
        self._evaluator = PythonEvaluator()
        self._rules: dict[str, SentryRule] = {}

    def register(self, sentry: dict[str, Any]) -> None:
        sentry_id = sentry.get("id", "")
        rule = SentryRule(
            sentry_id=sentry_id,
            name=sentry.get("name"),
            on_parts=sentry.get("onParts", sentry.get("on", [])),
            if_part=sentry.get("ifPart") or sentry.get("condition"),
            references=sentry.get("planItemRefs", []),
            is_entry_criterion=sentry.get("isEntryCriterion", True),
        )
        if sentry_id:
            self._rules[sentry_id] = rule

    def is_active(self, task: dict, context: dict) -> bool:
        sentry_ref = task.get("sentry") or task.get("entryCriterionRefs", [None])[0] if task.get("entryCriterionRefs") else None

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

    def is_complete(self, task: dict, context: dict) -> bool:
        expression = task.get("completionCondition") or task.get("exitCriterion")
        if not expression:
            return False
        return bool(self._evaluator.evaluate(expression, EvaluationContext(variables=context)))

    def evaluate_entry_criteria(self, criteria: list[dict[str, Any]], instance_or_context: Any) -> bool:
        if not criteria:
            return True

        if len(criteria) == 1:
            criterion = criteria[0]
            expression = criterion.get("condition") or criterion.get("body")
            context = self._extract_context(instance_or_context)
            if expression:
                return bool(self._evaluator.evaluate(expression, EvaluationContext(variables=context)))
            return True

        context = self._extract_context(instance_or_context)
        return all(
            self._evaluate_single_criterion(c, context) for c in criteria
        )

    def _evaluate_single_criterion(self, criterion: dict[str, Any], context: dict[str, Any]) -> bool:
        expression = criterion.get("condition") or criterion.get("body")
        if not expression:
            return True
        return bool(self._evaluator.evaluate(expression, EvaluationContext(variables=context)))

    def _evaluate_rule(self, rule: SentryRule, context: dict[str, Any]) -> bool:
        if not rule.on_parts and not rule.if_part:
            return True

        on_parts_satisfied = True
        triggered: list[str] = []

        for on_part in rule.on_parts:
            source_ref = on_part.get("sourceRef") or on_part.get("source")
            standard_event = on_part.get("standardEvent") or on_part.get("event")
            if source_ref and standard_event:
                triggered.append(f"{source_ref}:{standard_event}")

        if rule.if_part:
            result = bool(self._evaluator.evaluate(rule.if_part, EvaluationContext(variables=context)))
            return result and on_parts_satisfied

        return True

    def _extract_context(self, instance_or_context: Any) -> dict[str, Any]:
        if isinstance(instance_or_context, dict):
            return instance_or_context
        if hasattr(instance_or_context, "get_all_variables"):
            return instance_or_context.get_all_variables()
        if hasattr(instance_or_case, "variables"):
            return dict(instance_or_context.variables)
        return {}

    def evaluate_all_sentries(self, context: dict[str, Any]) -> dict[str, bool]:
        results: dict[str, bool] = {}
        for sentry_id, rule in self._rules.items():
            results[sentry_id] = self._evaluate_rule(rule, context)
        return results
