"""BPMN sequence flow model and flow traversal helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..expression.evaluator import EvaluationContext
from ..expression.python_evaluator import PythonEvaluator


@dataclass(frozen=True)
class SequenceFlow:
    source_ref: str
    target_ref: str
    condition_expression: str | None = None


def compute_next_nodes(flows: list[dict[str, Any]], source_id: str, *, context: dict[str, Any] | None = None) -> list[str]:
    result: list[str] = []
    for flow in flows:
        if flow.get("source") != source_id and flow.get("sourceRef") != source_id:
            continue
        condition = flow.get("condition") or flow.get("conditionExpression")
        target = flow.get("target") or flow.get("targetRef")
        if target is None:
            continue
        if not condition:
            result.append(str(target))
            continue
        if _evaluate_condition(condition, context or {}):
            result.append(str(target))
    return result


def _evaluate_condition(expression: str, context: dict[str, Any]) -> bool:
    if expression in {"true", "True", "1"}:
        return True
    if expression in {"false", "False", "0"}:
        return False
    try:
        return bool(PythonEvaluator().evaluate(expression, EvaluationContext(variables=context)))
    except Exception:
        return False
