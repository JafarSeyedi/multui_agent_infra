"""Guard condition evaluation for state transitions."""

from __future__ import annotations

from ..expression.evaluator import EvaluationContext
from ..expression.python_evaluator import PythonEvaluator


class GuardEvaluator:
    def evaluate(self, expression: str, context: dict) -> bool:
        try:
            return bool(PythonEvaluator().evaluate(expression, EvaluationContext(variables=context)))
        except Exception:
            return False
