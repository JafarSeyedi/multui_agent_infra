"""Guard evaluator for state machine transitions.

Supports expression languages and contextual data access.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..expression.evaluator import EvaluationContext
from ..expression.python_evaluator import PythonEvaluator


@dataclass
class GuardCondition:
    expression: str
    guard_id: str | None = None
    description: str | None = None
    language: str | None = None


class GuardEvaluator:
    def __init__(self) -> None:
        self._evaluator = PythonEvaluator()
        self._conditions: dict[str, GuardCondition] = {}

    def register(self, condition: GuardCondition) -> None:
        key = condition.guard_id or condition.expression
        self._conditions[key] = condition

    def evaluate(self, expression: str, context: dict[str, Any]) -> bool:
        if expression in {"true", "True", "1"}:
            return True
        if expression in {"false", "False", "0"}:
            return False
        try:
            result = self._evaluator.evaluate(expression, EvaluationContext(variables=context))
            return bool(result)
        except Exception:
            return False

    def evaluate_guard(self, guard_id: str, context: dict[str, Any]) -> bool:
        condition = self._conditions.get(guard_id)
        if condition is None:
            return False
        return self.evaluate(condition.expression, context)

    def evaluate_all(self, context: dict[str, Any]) -> dict[str, bool]:
        results: dict[str, bool] = {}
        for key, condition in self._conditions.items():
            results[key] = self.evaluate(condition.expression, context)
        return results
