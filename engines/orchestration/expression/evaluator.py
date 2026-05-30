"""Shared expression evaluator protocol."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class EvaluationContext:
    variables: dict[str, Any]


class Evaluator(Protocol):
    def evaluate(self, expression: str, context: EvaluationContext) -> Any:
        ...


class EvaluationError(RuntimeError):
    """Raised when expression evaluation fails."""
