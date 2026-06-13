"""Tests for BpmnGatewayClassifier."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from engines.orchestration.bpmn.gateway_classifier import BpmnGatewayClassifier
from engines.orchestration.bpmn.process_model import TypedProcessModel
from engines.document.models.osdm_models import (
    ExclusiveGateway,
    InclusiveGateway,
    ParallelGateway,
    EventBasedGateway,
    ComplexGateway,
    SequenceFlow,
    FlowNode,
)


class TestGatewayClassification:
    """classify_gateway_typed and is_gateway_typed."""

    def test_classify_none_for_missing_node(self):
        tm = TypedProcessModel(definition_id="test")
        assert BpmnGatewayClassifier.classify_gateway_typed("nope", tm) == "none"

    def test_classify_exclusive(self):
        tm = TypedProcessModel(definition_id="test")
        tm._node_index["gw-1"] = ExclusiveGateway(id="gw-1")
        assert BpmnGatewayClassifier.classify_gateway_typed("gw-1", tm) == "exclusive"

    def test_classify_inclusive(self):
        tm = TypedProcessModel(definition_id="test")
        tm._node_index["gw-1"] = InclusiveGateway(id="gw-1")
        assert BpmnGatewayClassifier.classify_gateway_typed("gw-1", tm) == "inclusive"

    def test_classify_parallel(self):
        tm = TypedProcessModel(definition_id="test")
        tm._node_index["gw-1"] = ParallelGateway(id="gw-1")
        assert BpmnGatewayClassifier.classify_gateway_typed("gw-1", tm) == "parallel"

    def test_classify_event_based(self):
        tm = TypedProcessModel(definition_id="test")
        tm._node_index["gw-1"] = EventBasedGateway(id="gw-1")
        assert BpmnGatewayClassifier.classify_gateway_typed("gw-1", tm) == "event"

    def test_classify_complex(self):
        tm = TypedProcessModel(definition_id="test")
        tm._node_index["gw-1"] = ComplexGateway(id="gw-1")
        assert BpmnGatewayClassifier.classify_gateway_typed("gw-1", tm) == "complex"

    def test_is_gateway_typed_true(self):
        tm = TypedProcessModel(definition_id="test")
        tm._node_index["gw-1"] = ExclusiveGateway(id="gw-1")
        assert BpmnGatewayClassifier.is_gateway_typed("gw-1", tm) is True

    def test_is_gateway_typed_false_for_non_gateway(self):
        tm = TypedProcessModel(definition_id="test")
        tm._node_index["n1"] = FlowNode(id="n1")
        assert BpmnGatewayClassifier.is_gateway_typed("n1", tm) is False

    def test_is_gateway_typed_false_for_missing(self):
        tm = TypedProcessModel(definition_id="test")
        assert BpmnGatewayClassifier.is_gateway_typed("nope", tm) is False

    def test_is_converging_gateway(self):
        tm = TypedProcessModel(definition_id="test")
        tm._node_index["gw-1"] = InclusiveGateway(id="gw-1")
        assert BpmnGatewayClassifier.is_converging_gateway_typed("gw-1", tm) is True

        tm._node_index["gw-2"] = ParallelGateway(id="gw-2")
        assert BpmnGatewayClassifier.is_converging_gateway_typed("gw-2", tm) is False


class TestFlowOperations:
    """get_flow_source, find_flow_to_target, extract_flow_condition."""

    def test_get_flow_source_from_model(self):
        tm = TypedProcessModel(definition_id="test")
        tm._node_index["a1"] = FlowNode(id="a1")
        flow = SequenceFlow(id="f1", source_ref=tm._node_index["a1"],
                            target_ref=tm._node_index["a1"], name="f1")
        flow.source_ref_id = "a1"
        flow.target_ref_id = "b1"
        tm._flow_index["a1"] = [flow]

        model = MagicMock()
        model.flows = []
        assert BpmnGatewayClassifier.get_flow_source("f1", model, tm) == "a1"

    def test_get_flow_source_from_model_fallback(self):
        tm = TypedProcessModel(definition_id="test")
        model = MagicMock()
        model.flows = [MagicMock(flow_id="f1", source_ref="a1")]
        assert BpmnGatewayClassifier.get_flow_source("f1", model, tm) == "a1"

    def test_find_flow_to_target(self):
        tm = TypedProcessModel(definition_id="test")
        flow = SequenceFlow(id="f1", source_ref=FlowNode(id="a1"),
                            target_ref=FlowNode(id="b1"), name="f1")
        flow.source_ref_id = "a1"
        flow.target_ref_id = "b1"
        tm._flow_index["a1"] = [flow]

        found = BpmnGatewayClassifier.find_flow_to_target_typed("a1", "b1", tm)
        assert found is flow

    def test_find_flow_to_target_not_found(self):
        tm = TypedProcessModel(definition_id="test")
        assert BpmnGatewayClassifier.find_flow_to_target_typed("a", "b", tm) is None

    def test_extract_flow_condition_none(self):
        assert BpmnGatewayClassifier.extract_flow_condition(None) is None

    def test_extract_flow_condition_present(self):
        flow = MagicMock(spec=SequenceFlow)
        flow.condition_expression = MagicMock()
        flow.condition_expression.body = "x > 5"
        assert BpmnGatewayClassifier.extract_flow_condition(flow) == "x > 5"


class TestFindForkForConverging:
    """find_fork_for_converging traces back to parallel/inclusive fork."""

    def test_returns_none_when_node_missing(self):
        tm = TypedProcessModel(definition_id="test")
        assert BpmnGatewayClassifier.find_fork_for_converging("nope", tm) is None

    def test_returns_fork_id_when_found(self):
        tm = TypedProcessModel(definition_id="test")
        fork = ParallelGateway(id="fork-1")
        conv = InclusiveGateway(id="conv-1")
        tm._node_index["fork-1"] = fork
        tm._node_index["conv-1"] = conv
        flow = SequenceFlow(id="f1", source_ref=fork, target_ref=conv, name="f1")
        flow.source_ref_id = "fork-1"
        flow.target_ref_id = "conv-1"
        tm._flow_index["fork-1"] = [flow]

        result = BpmnGatewayClassifier.find_fork_for_converging("conv-1", tm)
        assert result == "fork-1"
