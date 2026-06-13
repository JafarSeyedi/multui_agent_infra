"""FEEL expression evaluator."""

from __future__ import annotations

from dataclasses import dataclass

from .evaluator import EvaluationContext, EvaluationError
from typing import Any


@dataclass(frozen=True)
class FEELExpressionEvaluator:
    """Minimal FEEL evaluator mapped to Python-compatible primitives."""

    def evaluate(self, expression: str, context: EvaluationContext) -> Any:
        normalized = expression.strip()
        if normalized.startswith("if") and " then " in normalized and " else " in normalized:
            # naive ternary conversion: if A then B else C
            payload = normalized[2:].strip()
            condition, rest = payload.split(" then ", 1)
            true_expr, false_expr = rest.split(" else ", 1)
            eval_code = f"({true_expr}) if ({condition}) else ({false_expr})"
            try:
                return eval(eval_code, {"__builtins__": {}}, dict(context.variables))
            except Exception as exc:
                raise EvaluationError(f"FEEL evaluation failed: {exc}") from exc

        if "=" in normalized and "==" not in normalized:
            normalized = normalized.replace("=", "==")

        try:
            return eval(normalized, {"__builtins__": {}}, dict(context.variables))
        except Exception as exc:
            raise EvaluationError(f"FEEL evaluation failed: {exc}") from exc
