"""BPMN sequence flow model and flow traversal helpers.

Supports condition evaluation, default flows, skip logic,
and execution graph semantics at BPMN 2.0 spec level.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, cast, overload

from ..expression.evaluator import EvaluationContext
from ..expression.python_evaluator import PythonEvaluator

from engines.orchestration.models.osdm_models import SequenceFlow

logger = logging.getLogger(__name__)


def _resolve_ref_id(ref: Any) -> str | None:
    if ref is None:
        return None
    if isinstance(ref, str):
        return ref
    return getattr(ref, "id", None)


def _extract_condition_text(condition_expression: Any) -> str | None:
    if condition_expression is None:
        return None
    if isinstance(condition_expression, str):
        return condition_expression if condition_expression else None
    body = getattr(condition_expression, "body", None)
    return body if body else None


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

    @overload
    def compute_next_nodes(
        self,
        flows: list[HandlerSequenceFlow],
        source_id: str,
        *,
        context: dict[str, Any] | None = ...,
        evaluate_conditions: bool = ...,
        skip_guarded: bool = ...,
    ) -> FlowTraversalResult: ...

    @overload
    def compute_next_nodes(
        self,
        flows: list[SequenceFlow],
        source_id: str,
        *,
        context: dict[str, Any] | None = ...,
        evaluate_conditions: bool = ...,
        skip_guarded: bool = ...,
    ) -> FlowTraversalResult: ...

    def compute_next_nodes(
        self,
        flows: list[HandlerSequenceFlow] | list[SequenceFlow],
        source_id: str,
        *,
        context: dict[str, Any] | None = None,
        evaluate_conditions: bool = True,
        skip_guarded: bool = False,
    ) -> FlowTraversalResult:
        context = context or {}
        if flows and isinstance(flows[0], HandlerSequenceFlow):
            return self._compute_next_nodes_handler(cast(list[HandlerSequenceFlow], flows), source_id, context=context, evaluate_conditions=evaluate_conditions, skip_guarded=skip_guarded)
        return self._compute_next_nodes(cast(list[SequenceFlow], flows), source_id, context=context, evaluate_conditions=evaluate_conditions, skip_guarded=skip_guarded)

    def _compute_next_nodes(
        self,
        flows: list[SequenceFlow],
        source_id: str,
        *,
        context: dict[str, Any],
        evaluate_conditions: bool,
        skip_guarded: bool,
    ) -> FlowTraversalResult:
        context = context or {}
        outgoing = self._collect_outgoing_osdm(flows, source_id)
        return self._select_targets(outgoing, source_id, context=context, evaluate_conditions=evaluate_conditions, skip_guarded=skip_guarded)

    def _compute_next_nodes_handler(
        self,
        flows: list[HandlerSequenceFlow],
        source_id: str,
        *,
        context: dict[str, Any],
        evaluate_conditions: bool,
        skip_guarded: bool,
    ) -> FlowTraversalResult:
        outgoing: list[HandlerSequenceFlow] = [
            f for f in flows if f.source_ref == source_id
        ]
        selected: list[str] = []
        conditions_evaluated: dict[str, bool] = {}
        default_used = False

        for flow in outgoing:
            condition = flow.condition_expression
            if not condition:
                selected.append(flow.target_ref)
                continue
            if evaluate_conditions:
                cond_result = self._evaluate_condition(condition, context)
                conditions_evaluated[f"{source_id}->{flow.target_ref}"] = cond_result
                if cond_result:
                    selected.append(flow.target_ref)
            elif skip_guarded:
                conditions_evaluated[f"{source_id}->{flow.target_ref}"] = False
            else:
                selected.append(flow.target_ref)

        return FlowTraversalResult(
            selected_targets=selected,
            default_used=default_used,
            skip_guarded=skip_guarded,
            conditions_evaluated=conditions_evaluated,
        )

    def _select_targets(
        self,
        outgoing: list[SequenceFlow],
        source_id: str,
        *,
        context: dict[str, Any],
        evaluate_conditions: bool,
        skip_guarded: bool,
    ) -> FlowTraversalResult:
        selected: list[str] = []
        conditions_evaluated: dict[str, bool] = {}
        default_used = False

        for flow in outgoing:
            target_id = _resolve_ref_id(flow.target_ref)
            if target_id is None:
                continue
            condition = _extract_condition_text(flow.condition_expression)
            if not condition:
                selected.append(target_id)
                continue
            if evaluate_conditions:
                cond_result = self._evaluate_condition(condition, context)
                conditions_evaluated[f"{source_id}->{target_id}"] = cond_result
                if cond_result:
                    selected.append(target_id)
            elif skip_guarded:
                conditions_evaluated[f"{source_id}->{target_id}"] = False
            else:
                selected.append(target_id)

        return FlowTraversalResult(
            selected_targets=selected,
            default_used=default_used,
            skip_guarded=skip_guarded,
            conditions_evaluated=conditions_evaluated,
        )

    def _collect_outgoing_osdm(
        self,
        flows: list[SequenceFlow],
        source_id: str,
    ) -> list[SequenceFlow]:
        result: list[SequenceFlow] = []
        for flow in flows:
            src = _resolve_ref_id(flow.source_ref)
            if src == source_id:
                result.append(flow)
        return result

    def _evaluate_condition(self, expression: str, context: dict[str, Any]) -> bool:
        if expression in {"true", "True", "1"}:
            return True
        if expression in {"false", "False", "0"}:
            return False
        try:
            return bool(self._evaluator.evaluate(expression, EvaluationContext(variables=context)))
        except Exception as exc:
            logger.debug("Sequence flow condition evaluation failed: %s", exc)
            return False


_backbone = SequenceFlowEngine()
compute_next_nodes = _backbone.compute_next_nodes


def find_default_flow(flows: list[HandlerSequenceFlow], source_id: str) -> str | None:
    for flow in flows:
        if flow.source_ref != source_id:
            continue
        if flow.is_default:
            if flow.target_ref:
                return flow.target_ref
    return None


def has_conditional_flows(flows: list[HandlerSequenceFlow], source_id: str) -> bool:
    for flow in flows:
        if flow.source_ref != source_id:
            continue
        if flow.condition_expression:
            return True
    return False
