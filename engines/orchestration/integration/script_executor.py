"""Script execution abstraction for BPMN task-like activities."""

from __future__ import annotations

from dataclasses import dataclass

from ..expression.python_evaluator import PythonEvaluator
from ..expression.javascript_evaluator import JavaScriptEvaluator
from ..expression.evaluator import EvaluationContext, EvaluationError


class ScriptExecutionError(RuntimeError):
    """Raised for script execution issues."""


@dataclass(frozen=True)
class ScriptExecutor:
    python_evaluator: PythonEvaluator | None = None
    javascript_evaluator: JavaScriptEvaluator | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "python_evaluator", self.python_evaluator or PythonEvaluator())
        object.__setattr__(self, "javascript_evaluator", self.javascript_evaluator or JavaScriptEvaluator())

    def execute(self, language: str, expression: str, context: dict[str, object]) -> object:
        evaluator = {
            "python": self.python_evaluator,
            "javascript": self.javascript_evaluator,
        }.get(language.lower())
        if evaluator is None:
            raise ScriptExecutionError(f"Unsupported language: {language}")
        try:
            return evaluator.evaluate(expression, EvaluationContext(variables=context))
        except EvaluationError as exc:
            raise ScriptExecutionError(str(exc)) from exc
