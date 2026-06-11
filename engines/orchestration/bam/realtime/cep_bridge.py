from __future__ import annotations

from typing import Any


class CepBridge:
    def __init__(self) -> None:
        self._rules: dict[str, dict[str, Any]] = {}

    def register_rule(self, rule_id: str, condition: dict[str, Any]) -> None:
        self._rules[rule_id] = condition

    def evaluate(
        self,
        metric_id: str,
        value: float,
    ) -> dict[str, Any] | None:
        for rule_id, condition in self._rules.items():
            if condition.get("metric") != metric_id:
                continue
            operator = condition.get("operator", "gt")
            threshold = condition.get("value", 0)
            if self._compare(value, operator, threshold):
                return {
                    "rule_id": rule_id,
                    "metric": metric_id,
                    "value": value,
                    "threshold": threshold,
                }
        return None

    def evaluate_batch(
        self,
        metrics: dict[str, float],
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for metric_id, value in metrics.items():
            result = self.evaluate(metric_id, value)
            if result:
                results.append(result)
        return results

    def remove_rule(self, rule_id: str) -> None:
        self._rules.pop(rule_id, None)

    def _compare(self, value: float, operator: str, threshold: float) -> bool:
        operators = {
            "gt": lambda v, t: v > t,
            "gte": lambda v, t: v >= t,
            "lt": lambda v, t: v < t,
            "lte": lambda v, t: v <= t,
            "eq": lambda v, t: v == t,
            "neq": lambda v, t: v != t,
        }
        op_func = operators.get(operator)
        if op_func is None:
            return False
        return op_func(value, threshold)
