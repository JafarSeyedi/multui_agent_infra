"""BPMN sequence flow model and flow traversal helpers.

Supports condition evaluation, default flows, skip logic,
and execution graph semantics at BPMN 2.0 spec level.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..expression.evaluator import EvaluationContext
from ..expression.python_evaluator import PythonEvaluator

from ....document.models.osdm_models import (
    SequenceFlow as OSDMSequenceFlow,
)


@dataclass(frozen=True)
class HandlerSequenceFlow:
    flow_id: str
    source_ref: str
    target_ref: str
    condition_expression: str | None = None
    is_immediate: bool = True
    is_default: bool = False
    priority: int = 0


@dataclass
class FlowTraversalResult:
    selected_targets: list[str]
    default_used: bool = False
    skip_guarded: bool = False
    conditions_evaluated: dict[str, bool] = field(default_factory=dict)


class SequenceFlowEngine:
    def __init__(self) -> None:
        self._evaluator = PythonEvaluator()

    def compute_next_nodes(
        self,
        flows: list[dict[str, Any]],
        source_id: str,
        *,
        context: dict[str, Any] | None = None,
        evaluate_conditions: bool = True,
        skip_guarded: bool = False,
    ) -> FlowTraversalResult:
        context = context or {}
        outgoing = self._collect_outgoing(flows, source_id)
        selected: list[str] = []
        conditions_evaluated: dict[str, bool] = {}
        default_used = False

        for flow in outgoing:
            target = flow.get("target") or flow.get("targetRef") or flow.get("target_id")
            if target is None:
                continue
            target = str(target)
            condition = flow.get("condition") or flow.get("conditionExpression")
            is_default = flow.get("isDefault", flow.get("is_default", False))
            if is_default:
                continue
            if not condition:
                selected.append(target)
                continue
            if evaluate_conditions:
                cond_result = self._evaluate_condition(condition, context)
                conditions_evaluated[f"{source_id}->{target}"] = cond_result
                if cond_result:
                    selected.append(target)
            elif skip_guarded:
                conditions_evaluated[f"{source_id}->{target}"] = False
            else:
                selected.append(target)

        if not selected:
            for flow in outgoing:
                target = flow.get("target") or flow.get("targetRef") or flow.get("target_id")
                if target is None:
                    continue
                target = str(target)
                is_default = flow.get("isDefault", flow.get("is_default", False))
                if is_default:
                    selected.append(target)
                    default_used = True
                    break

        return FlowTraversalResult(
            selected_targets=selected,
            default_used=default_used,
            skip_guarded=skip_guarded,
            conditions_evaluated=conditions_evaluated,
        )

    def _collect_outgoing(self, flows: list[dict[str, Any]], source_id: str) -> list[dict[str, Any]]:
        return [f for f in flows if str(f.get("source") or f.get("sourceRef") or f.get("source_id", "")) == source_id]

    def _evaluate_condition(self, expression: str, context: dict[str, Any]) -> bool:
        if expression in {"true", "True", "1"}:
            return True
        if expression in {"false", "False", "0"}:
            return False
        try:
            return bool(self._evaluator.evaluate(expression, EvaluationContext(variables=context)))
        except Exception:
            return False


_backbone = SequenceFlowEngine()
compute_next_nodes = _backbone.compute_next_nodes


def find_default_flow(flows: list[dict[str, Any]], source_id: str) -> str | None:
    for flow in flows:
        if str(flow.get("source") or flow.get("sourceRef") or flow.get("source_id", "")) != source_id:
            continue
        if flow.get("isDefault", flow.get("is_default", False)):
            target = flow.get("target") or flow.get("targetRef") or flow.get("target_id")
            if target:
                return str(target)
    return None


def has_conditional_flows(flows: list[dict[str, Any]], source_id: str) -> bool:
    for flow in flows:
        if str(flow.get("source") or flow.get("sourceRef") or flow.get("source_id", "")) != source_id:
            continue
        if flow.get("condition") or flow.get("conditionExpression"):
            return True
    return False
