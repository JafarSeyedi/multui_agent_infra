"""CEP rule evaluator with typed event/context data.

Evaluates CEP rules against typed event and context data at CEP level.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any
from collections.abc import Callable

from ..expression.evaluator import EvaluationContext
from ..expression.python_evaluator import PythonEvaluator
from ..core.instance import ProcessInstance


logger = logging.getLogger(__name__)


def _op_eq(field_value: Any, comp_value: Any) -> bool:
    return field_value == comp_value


def _op_neq(field_value: Any, comp_value: Any) -> bool:
    return field_value != comp_value


def _op_gt(field_value: Any, comp_value: Any) -> bool:
    try:
        return float(field_value or 0) > float(comp_value or 0)
    except (ValueError, TypeError):
        return False


def _op_gte(field_value: Any, comp_value: Any) -> bool:
    try:
        return float(field_value or 0) >= float(comp_value or 0)
    except (ValueError, TypeError):
        return False


def _op_lt(field_value: Any, comp_value: Any) -> bool:
    try:
        return float(field_value or 0) < float(comp_value or 0)
    except (ValueError, TypeError):
        return False


def _op_lte(field_value: Any, comp_value: Any) -> bool:
    try:
        return float(field_value or 0) <= float(comp_value or 0)
    except (ValueError, TypeError):
        return False


def _op_in(field_value: Any, comp_value: Any) -> bool:
    return field_value in comp_value if isinstance(comp_value, (list, tuple)) else False


def _op_not_in(field_value: Any, comp_value: Any) -> bool:
    return field_value not in comp_value if isinstance(comp_value, (list, tuple)) else True


def _op_exists(field_value: Any, comp_value: Any) -> bool:
    return field_value is not None


def _op_not_exists(field_value: Any, comp_value: Any) -> bool:
    return field_value is None


def _op_contains(field_value: Any, comp_value: Any) -> bool:
    return str(comp_value) in str(field_value) if field_value is not None else False


_OPERATOR_HANDLERS: dict[str, Callable[[Any, Any], bool]] = {
    "eq": _op_eq,
    "neq": _op_neq,
    "gt": _op_gt,
    "gte": _op_gte,
    "lt": _op_lt,
    "lte": _op_lte,
    "in": _op_in,
    "not_in": _op_not_in,
    "exists": _op_exists,
    "not_exists": _op_not_exists,
    "contains": _op_contains,
}


def _evaluate_operator(operator: str, field_value: Any, comp_value: Any) -> bool:
    handler = _OPERATOR_HANDLERS.get(operator)
    if handler is not None:
        return handler(field_value, comp_value)
    return True


@dataclass
class CEPRuleCondition:
    expression: str = ""
    target_field: str | None = None
    operator: str = "eq"
    comparison_value: Any = None


@dataclass
class CEPRule:
    rule_id: str = ""
    name: str | None = None
    conditions: list[CEPRuleCondition] = field(default_factory=list)
    action: str | None = None
    output_variable: str | None = None
    priority: int = 0
    enabled: bool = True


class RuleEvaluator:
    def __init__(self) -> None:
        self._evaluator = PythonEvaluator()
        self._rules: dict[str, CEPRule] = {}

    def register(self, rule: CEPRule) -> None:
        self._rules[rule.rule_id] = rule

    def get_rule(self, rule_id: str) -> CEPRule | None:
        return self._rules.get(rule_id)

    async def evaluate(
        self,
        rule_data: dict[str, Any],
        context: dict[str, Any],
        instance: ProcessInstance | None = None,
    ) -> Any:
        rule = self._normalize_rule(rule_data)

        if not rule.enabled:
            return None

        if not self._evaluate_conditions(rule.conditions, context):
            return None

        if rule.output_variable is None:
            rule.output_variable = rule.name or rule.rule_id

        result: dict[str, Any] = {
            "rule_id": rule.rule_id,
            "triggered": True,
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        }

        if instance:
            instance.set_variable(f"rule.{rule.output_variable}", result)

        if rule.action:
            try:
                action_result = self._evaluator.evaluate(
                    rule.action, EvaluationContext(variables=context)
                )
                result["action_result"] = action_result
            except Exception as e:
                logger.warning("Rule %s action failed: %s", rule.rule_id, e)
                result["action_error"] = str(e)

        return result

    def evaluate_batch(
        self,
        rule_data: dict[str, Any],
        events: list[dict[str, Any]],
    ) -> list[str]:
        rule = self._normalize_rule(rule_data)
        triggered: list[str] = []

        if not rule.enabled:
            return triggered

        for event in events:
            if self._evaluate_conditions(rule.conditions, event):
                triggered.append(event.get("id", ""))

        return triggered

    def _normalize_rule(self, data: dict[str, Any]) -> CEPRule:
        conditions: list[CEPRuleCondition] = []
        for cond_data in data.get("conditions", []):
            condition = CEPRuleCondition(
                expression=cond_data.get("expression", cond_data.get("text", "")),
                target_field=cond_data.get("field") or cond_data.get("target"),
                operator=cond_data.get("operator", "eq"),
                comparison_value=cond_data.get("value") or cond_data.get("comparisonValue"),
            )
            conditions.append(condition)

        return CEPRule(
            rule_id=data.get("id", data.get("name", "")),
            name=data.get("name"),
            conditions=conditions,
            action=data.get("action"),
            output_variable=data.get("outputVariable"),
            priority=data.get("priority", 0),
            enabled=data.get("enabled", True),
        )

    def _evaluate_conditions(
        self,
        conditions: list[CEPRuleCondition],
        context: dict[str, Any],
    ) -> bool:
        if not conditions:
            return True

        for condition in conditions:
            if not self._evaluate_single_condition(condition, context):
                return False
        return True

    def _evaluate_single_condition(
        self,
        condition: CEPRuleCondition,
        context: dict[str, Any],
    ) -> bool:
        field_value = None
        if condition.target_field:
            field_value = context.get(condition.target_field)
        elif condition.expression:
            try:
                field_value = self._evaluator.evaluate(
                    condition.expression, EvaluationContext(variables=context)
                )
            except Exception:
                return False

        return _evaluate_operator(condition.operator, field_value, condition.comparison_value)
