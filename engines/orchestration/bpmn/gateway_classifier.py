"""Gateway classification and condition evaluation for BPMN execution."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

from engines.orchestration.models.osdm_models import (
    ExclusiveGateway, Gateway, InclusiveGateway, ParallelGateway,
    EventBasedGateway, ComplexGateway, SequenceFlow,
)
from .model_normalizer import _activity_id, _activity_type_str
from .process_model import TypedProcessModel

_GATEWAY_CLASSIFIER_MAP: dict[type, str] = {
    ExclusiveGateway: "exclusive",
    InclusiveGateway: "inclusive",
    ParallelGateway: "parallel",
    EventBasedGateway: "event",
    ComplexGateway: "complex",
}


class BpmnGatewayClassifier:
    """Gateway type detection, classification, and condition evaluation."""

    @staticmethod
    def is_gateway_typed(node_id: str, typed_model: TypedProcessModel) -> bool:
        node = typed_model.get_node(node_id)
        return isinstance(node, Gateway) if node is not None else False

    @staticmethod
    def classify_gateway_typed(node_id: str, typed_model: TypedProcessModel) -> str:
        node = typed_model.get_node(node_id)
        if node is None:
            return "none"
        return _GATEWAY_CLASSIFIER_MAP.get(type(node), "none")

    @staticmethod
    def is_converging_gateway_typed(node_id: str, typed_model: TypedProcessModel) -> bool:
        return BpmnGatewayClassifier.classify_gateway_typed(node_id, typed_model) in ("inclusive", "complex")

    @staticmethod
    def find_fork_for_converging(
        node_id: str, typed_model: TypedProcessModel,
    ) -> str | None:
        node = typed_model.get_node(node_id)
        if node is None:
            return None
        incoming: list[SequenceFlow] = []
        for src, flows in typed_model._flow_index.items():
            for f in flows:
                if f.target_ref_id == node_id:
                    incoming.append(f)
        for flow in incoming:
            source = typed_model.get_node(flow.source_ref_id or "")
            if source and BpmnGatewayClassifier.classify_gateway_typed(
                flow.source_ref_id or "", typed_model,
            ) in ("inclusive", "parallel"):
                return flow.source_ref_id
        for flow in incoming:
            source = typed_model.get_node(flow.source_ref_id or "")
            if source and BpmnGatewayClassifier.classify_gateway_typed(
                flow.source_ref_id or "", typed_model,
            ) in ("inclusive", "parallel"):
                source2 = typed_model.get_node(getattr(source, "source_ref_id", ""))
                if source2 and BpmnGatewayClassifier.classify_gateway_typed(
                    getattr(source, "source_ref_id", ""), typed_model,
                ) in ("inclusive", "parallel"):
                    return getattr(source, "source_ref_id", "")
        return None

    @staticmethod
    def get_flow_source(flow_id: str, model: Any, typed_model: TypedProcessModel) -> str | None:
        if typed_model._flow_index:
            for _src, flows in typed_model._flow_index.items():
                for flow in flows:
                    if flow.id == flow_id:
                        return flow.source_ref_id
        for f in model.flows:
            if f.flow_id == flow_id:
                return f.source_ref
        return None

    @staticmethod
    def evaluate_gateway_split_typed(
        incoming_node: str, typed_model: TypedProcessModel, instance: Any,
    ) -> list[str]:
        from ..expression.evaluator import EvaluationContext
        from ..expression.python_evaluator import PythonEvaluator

        outgoing = typed_model.get_outgoing_flows(incoming_node)
        if not outgoing:
            return []
        first_unconditional: str | None = None
        matched: list[str] = []
        for flow in outgoing:
            if flow.condition_expression:
                evaluator = PythonEvaluator()
                try:
                    context = EvaluationContext(variables=instance.get_all_variables())
                    body = getattr(flow.condition_expression, "body", None) or str(flow.condition_expression)
                    if evaluator.evaluate(str(body), context):
                        matched.append(flow.target_ref_id or "")
                except Exception as exc:
                    logger.debug("Condition evaluation skipped for flow %s: %s", getattr(flow, "id", "?"), exc)
                    continue
            elif first_unconditional is None:
                first_unconditional = flow.target_ref_id or ""
        if matched:
            return matched
        if first_unconditional:
            return [first_unconditional]
        return [outgoing[0].target_ref_id or ""] if outgoing else []

    @staticmethod
    def find_flow_to_target_typed(
        source_id: str, target_id: str, typed_model: TypedProcessModel,
    ) -> SequenceFlow | None:
        outgoing = typed_model.get_outgoing_flows(source_id)
        for flow in outgoing:
            if flow.target_ref_id == target_id or _activity_id(flow.target_ref) == target_id:
                return flow
        return None

    @staticmethod
    def extract_flow_condition(flow: SequenceFlow | None) -> str | None:
        if flow is None or not flow.condition_expression:
            return None
        body = getattr(flow.condition_expression, "body", None)
        return str(body) if body else str(flow.condition_expression)


