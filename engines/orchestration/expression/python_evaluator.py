"""Python expression evaluator with restricted builtins."""

from __future__ import annotations

from dataclasses import dataclass

from .evaluator import EvaluationContext, EvaluationError


_SAFE_GLOBALS = {
    "__builtins__": {
        "True": True,
        "False": False,
        "None": None,
        "min": min,
        "max": max,
        "sum": sum,
        "len": len,
        "sorted": sorted,
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
    }
}


@dataclass(frozen=True)
class PythonEvaluator:
    """Evaluate Python expressions in a constrained namespace."""

    def evaluate(self, expression: str, context: EvaluationContext) -> object:
        try:
            return eval(expression, _SAFE_GLOBALS, dict(context.variables))
        except Exception as exc:  # pragma: no cover - boundary condition
            raise EvaluationError(f"Python evaluation failed: {exc}") from exc
