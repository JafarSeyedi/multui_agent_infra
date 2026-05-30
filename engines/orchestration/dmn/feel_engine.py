"""DMN FEEL language runtime."""

from __future__ import annotations

from dataclasses import dataclass

from ..expression.evaluator import EvaluationContext
from ..expression.feel_evaluator import FEELExpressionEvaluator


@dataclass(frozen=True)
class FEELEngine:
    evaluator: FEELExpressionEvaluator = FEELExpressionEvaluator()

    def evaluate(self, expression: str, context: dict[str, object]) -> object:
        return self.evaluator.evaluate(expression, EvaluationContext(variables=context))
