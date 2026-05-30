"""Evaluate CEP rules from simple boolean expressions."""

from __future__ import annotations

from dataclasses import dataclass

from ..expression.evaluator import EvaluationContext
from ..expression.python_evaluator import PythonEvaluator


@dataclass(frozen=True)
class Rule:
    name: str
    when: str


class RuleEvaluator:
    def evaluate(self, rule: Rule, payload: dict) -> bool:
        return bool(PythonEvaluator().evaluate(rule.when, EvaluationContext(variables=payload)))
