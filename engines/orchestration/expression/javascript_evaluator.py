"""JavaScript expression evaluator."""

from __future__ import annotations

try:
    import js2py  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    js2py = None

from dataclasses import dataclass

from .evaluator import EvaluationContext, EvaluationError


@dataclass(frozen=True)
class JavaScriptEvaluator:
    """Evaluate JavaScript expressions when runtime supports it."""

    def evaluate(self, expression: str, context: EvaluationContext) -> object:
        if js2py is None:
            raise EvaluationError(
                "JavaScript evaluation unavailable: install `js2py` or avoid JS expressions"
            )
        try:
            js_ctx = js2py.EvalJs()
            for key, value in context.variables.items():
                setattr(js_ctx, key, value)
            return js_ctx.eval(expression)
        except Exception as exc:  # pragma: no cover - dependency boundary
            raise EvaluationError(f"JavaScript evaluation failed: {exc}") from exc
