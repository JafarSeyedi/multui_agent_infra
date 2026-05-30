"""High-level DMN decision execution."""

from __future__ import annotations

from dataclasses import dataclass

from .decision_table_evaluator import DecisionTableEvaluator
from .literal_expression_eval import LiteralExpressionEvaluator


@dataclass(frozen=True)
class DecisionExecutionError(RuntimeError):
    """Raised when a decision cannot be executed."""


class DecisionExecutor:
    def __init__(self) -> None:
        self.table_evaluator = DecisionTableEvaluator()
        self.literal_evaluator = LiteralExpressionEvaluator()

    def evaluate(self, decision: dict, context: dict) -> object:
        if "table" in decision:
            return self.table_evaluator.evaluate(decision["table"], context)
        if "expression" in decision:
            return self.literal_evaluator.evaluate(decision["expression"], context)
        if "decisions" in decision and decision["decisions"]:
            first = decision["decisions"][0]
            return self.evaluate(first, context)
        raise DecisionExecutionError("DMN payload has no executable branch")
