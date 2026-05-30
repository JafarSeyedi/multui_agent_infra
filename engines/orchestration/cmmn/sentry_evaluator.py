"""Evaluate CMMN sentries (entry/exit criteria)."""

from __future__ import annotations

from ..expression.evaluator import EvaluationContext
from ..expression.python_evaluator import PythonEvaluator


class SentryEvaluator:
    def is_active(self, task: dict, context: dict) -> bool:
        expression = task.get("sentry")
        if not expression:
            return True
        return bool(PythonEvaluator().evaluate(expression, EvaluationContext(variables=context)))

    def is_complete(self, task: dict, context: dict) -> bool:
        expression = task.get("completionCondition")
        if not expression:
            return False
        return bool(PythonEvaluator().evaluate(expression, EvaluationContext(variables=context)))
