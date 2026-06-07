"""Literal expression evaluator for DMN decisions.

Supports literal expression execution with typed context at DMN 1.3 level.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..expression.evaluator import EvaluationContext
from ..expression.python_evaluator import PythonEvaluator
from .feel_engine import FEELEngine


@dataclass
class LiteralExpression:
    expression_id: str | None = None
    text: str = ""
    language: str = "FEEL"
    type_ref: str = "string"


class LiteralExpressionEvaluator:
    def __init__(self) -> None:
        self._python_evaluator = PythonEvaluator()
        self._feel_engine = FEELEngine()

    def evaluate(self, expression: str, context: dict[str, Any]) -> Any:
        if not expression or not expression.strip():
            return None

        text = expression.strip()

        if text.startswith('"') and text.endswith('"'):
            return text[1:-1]
        if text.startswith("'") and text.endswith("'"):
            return text[1:-1]

        if text == "true":
            return True
        if text == "false":
            return False

        if text == "null":
            return None

        try:
            return float(text) if "." in text else int(text)
        except ValueError:
            pass

        try:
            return self._feel_engine.evaluate(text, context)
        except Exception:
            pass

        try:
            return bool(self._python_evaluator.evaluate(text, EvaluationContext(variables=context)))
        except Exception:
            pass

        return text

    def evaluate_typed(self, expression: str, context: dict[str, Any], type_ref: str) -> Any:
        result = self.evaluate(expression, context)

        if result is None:
            return None

        type_coercions = {
            "string": str,
            "integer": int,
            "number": float,
            "double": float,
            "boolean": bool,
            "date": str,
            "time": str,
            "dateTime": str,
            "duration": str,
        }

        caster = type_coercions.get(type_ref)
        if caster is not None and not isinstance(result, caster):
            try:
                return caster(result)
            except (ValueError, TypeError):
                return result
        return result
