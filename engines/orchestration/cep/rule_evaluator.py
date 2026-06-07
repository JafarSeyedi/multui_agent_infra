"""CEP rule evaluator with typed event/context data.

Evaluates CEP rules against typed event and context data at CEP level.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from ..expression.evaluator import EvaluationContext
from ..expression.python_evaluator import PythonEvaluator
from ..core.instance import ProcessInstance


logger = logging.getLogger(__name__)


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

        if condition.operator == "eq":
            return field_value == condition.comparison_value
        elif condition.operator == "neq":
            return field_value != condition.comparison_value
        elif condition.operator == "gt":
            try:
                return float(field_value or 0) > float(condition.comparison_value or 0)
            except (ValueError, TypeError):
                return False
        elif condition.operator == "gte":
            try:
                return float(field_value or 0) >= float(condition.comparison_value or 0)
            except (ValueError, TypeError):
                return False
        elif condition.operator == "lt":
            try:
                return float(field_value or 0) < float(condition.comparison_value or 0)
            except (ValueError, TypeError):
                return False
        elif condition.operator == "lte":
            try:
                return float(field_value or 0) <= float(condition.comparison_value or 0)
            except (ValueError, TypeError):
                return False
        elif condition.operator == "in":
            return field_value in condition.comparison_value if isinstance(condition.comparison_value, (list, tuple)) else False
        elif condition.operator == "not_in":
            return field_value not in condition.comparison_value if isinstance(condition.comparison_value, (list, tuple)) else True
        elif condition.operator == "exists":
            return field_value is not None
        elif condition.operator == "not_exists":
            return field_value is None
        elif condition.operator == "contains":
            return str(condition.comparison_value) in str(field_value) if field_value is not None else False

        return True
