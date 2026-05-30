"""BPMN gateway decision support."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..expression.evaluator import EvaluationContext
from ..expression.python_evaluator import PythonEvaluator


@dataclass(frozen=True)
class GatewayDecision:
    gateway_id: str
    next_targets: list[str]


class GatewayHandler:
    def __init__(self) -> None:
        self._evaluator = PythonEvaluator()

    def choose(self, *, gateway: dict[str, Any], context: dict[str, Any]) -> GatewayDecision:
        gateway_id = str(gateway.get("id", ""))
        branches = gateway.get("branches", [])
        next_targets: list[str] = []

        for branch in branches:
            expr = branch.get("condition") or "true"
            if bool(self._evaluator.evaluate(expr, EvaluationContext(variables=context))):
                target = branch.get("target")
                if target:
                    next_targets.append(str(target))
        if not next_targets:
            fallback = gateway.get("default")
            if fallback:
                next_targets.append(str(fallback))
        return GatewayDecision(gateway_id=gateway_id, next_targets=next_targets)
