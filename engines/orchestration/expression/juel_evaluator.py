"""JUEL evaluator implementation placeholder using Python compatibility semantics."""

from __future__ import annotations

from dataclasses import dataclass

from .context_builder import ExpressionContext
from .evaluator import EvaluationContext, EvaluationError
from .python_evaluator import PythonEvaluator


@dataclass(frozen=True)
class JuelExpressionEvaluator:
    """Fallback evaluator that maps JUEL to Python-like syntax minimally."""

    def __post_init__(self) -> None:
        self._python = PythonEvaluator()

    def evaluate(self, expression: str, context: EvaluationContext) -> object:
        normalized = expression.replace("&&", "and").replace("||", "or")
        return self._python.evaluate(normalized, context)
