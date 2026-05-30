"""Literal expression evaluator for DMN decision outputs."""

from __future__ import annotations

from ..expression.evaluator import EvaluationContext
from ..expression.python_evaluator import PythonEvaluator


class LiteralExpressionEvaluator:
    def evaluate(self, expression: str, context: dict[str, object]) -> object:
        return PythonEvaluator().evaluate(expression, EvaluationContext(variables=context))
