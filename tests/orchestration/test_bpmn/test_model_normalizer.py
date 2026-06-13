"""Tests for BpmnModelNormalizer and helper functions."""

from __future__ import annotations

import pytest

from engines.orchestration.bpmn.model_normalizer import (
    BpmnModelNormalizer,
    _activity_get,
    _activity_id,
    _activity_type_str,
    _dict_to_handler_flow,
)
from engines.document.models.osdm_models import (
    Activity,
    ActivityType,
    FlowNode,
    SequenceFlow,
    StartEvent,
)


class TestHelperFunctions:
    """_activity_get, _activity_type_str, _activity_id handle dict+object."""

    def test_activity_get_dict(self):
        d = {"id": "act-1", "type": "task"}
        assert _activity_get(d, "id") == "act-1"
        assert _activity_get(d, "type") == "task"
        assert _activity_get(d, "missing", "default") == "default"

    def test_activity_get_object(self):
        class Obj:
            id = "act-1"
            activity_type = ActivityType.TASK

        obj = Obj()
        assert _activity_get(obj, "id") == "act-1"
        assert _activity_get(obj, "activity_type") == ActivityType.TASK
        assert _activity_get(obj, "missing", "x") == "x"

    def test_activity_type_str_dict(self):
        assert _activity_type_str({"type": "task"}) == "task"
        assert _activity_type_str({"type": "StartEvent"}) == "startevent"
        assert _activity_type_str({}) == ""

    def test_activity_type_str_object_no_type(self):
        class Obj:
            pass
        assert _activity_type_str(Obj()) == ""

    def test_activity_type_str_object_with_activity_type(self):
        class Obj:
            activity_type = ActivityType.TASK
        assert _activity_type_str(Obj()) == "Task"

    def test_activity_type_str_object_with_type_attr(self):
        class Obj:
            type = "UserTask"
        assert _activity_type_str(Obj()) == "usertask"

    def test_activity_id_dict(self):
        assert _activity_id({"id": "act-1"}) == "act-1"
        assert _activity_id({}) == ""

    def test_activity_id_object(self):
        class Obj:
            id = "act-1"
        assert _activity_id(Obj()) == "act-1"

    def test_activity_id_none(self):
        class Obj:
            pass
        assert _activity_id(Obj()) == ""

    def test_dict_to_handler_flow_minimal(self):
        flow = _dict_to_handler_flow({"id": "f1"})
        assert flow.flow_id == "f1"
        assert flow.source_ref == ""
        assert flow.target_ref == ""

    def test_dict_to_handler_flow_full(self):
        flow = _dict_to_handler_flow({
            "id": "f1", "sourceRef": "a", "targetRef": "b",
            "conditionExpression": "x > 5", "isDefault": True,
        })
        assert flow.flow_id == "f1"
        assert flow.source_ref == "a"
        assert flow.target_ref == "b"
        assert flow.condition_expression == "x > 5"
        assert flow.is_default is True

    def test_dict_to_handler_flow_alternative_keys(self):
        flow = _dict_to_handler_flow({"id": "f1", "source": "a", "target": "b"})
        assert flow.source_ref == "a"
        assert flow.target_ref == "b"


class TestBpmnModelNormalizer:
    """BpmnModelNormalizer.normalize and normalize_osdm."""

    def test_normalize_minimal(self):
        payload = {"id": "proc-1"}
        model = BpmnModelNormalizer.normalize(payload)
        assert model.definition_id == "proc-1"
        assert model.start_node is None
        assert model.activities == []
        assert model.flows == []

    def test_normalize_with_start_event(self):
        payload = {
            "id": "proc-1",
            "start_event_id": "start-1",
            "activities": [{"id": "start-1", "type": "startEvent"}, {"id": "task-1", "type": "task"}],
            "flows": [{"id": "f1", "sourceRef": "start-1", "targetRef": "task-1"}],
        }
        model = BpmnModelNormalizer.normalize(payload)
        assert model.start_node == "start-1"
        assert len(model.activities) == 2
        assert len(model.flows) == 1

    def test_normalize_infers_start_from_activities(self):
        payload = {
            "id": "proc-1",
            "activities": [{"id": "a1", "type": "startEvent"}, {"id": "a2", "type": "task"}],
        }
        model = BpmnModelNormalizer.normalize(payload)
        assert model.start_node == "a1"

    def test_normalize_infers_start_from_flow_elements(self):
        payload = {
            "id": "proc-1",
            "flow_elements": {
                "start-1": StartEvent(id="start-1", name="Start"),
            },
        }
        model = BpmnModelNormalizer.normalize(payload)
        assert model.start_node == "start-1"

    def test_normalize_handles_handler_flows(self):
        from engines.orchestration.bpmn.sequence_flow import HandlerSequenceFlow
        payload = {
            "activities": [{"id": "a1"}],
            "flows": [HandlerSequenceFlow(flow_id="f1", source_ref="a1", target_ref="a2")],
        }
        model = BpmnModelNormalizer.normalize(payload)
        assert len(model.flows) == 1
        assert model.flows[0].flow_id == "f1"

    def test_normalize_osdm_minimal(self):
        result = BpmnModelNormalizer.normalize_osdm({}, "def-1")
        assert result.start_node_id is None

    def test_normalize_osdm_with_flow_node(self):
        node = FlowNode(id="n1", name="Node")
        flow = SequenceFlow(id="f1", source_ref=node, target_ref=node, name="Flow")
        flow.source_ref_id = "n1"
        flow.target_ref_id = "n2"
        result = BpmnModelNormalizer.normalize_osdm(
            {"flow_elements": {"n1": node, "f1": flow}}, "def-1",
        )
        assert result.get_node("n1") is node
        assert "n1" in result._flow_index

    def test_find_activity_by_id(self):
        payload = {
            "activities": [{"id": "a1", "type": "task"}, {"id": "a2", "type": "endEvent"}],
        }
        model = BpmnModelNormalizer.normalize(payload)
        found = BpmnModelNormalizer.find_activity(model, "a1")
        assert found is not None
        assert _activity_id(found) == "a1"

        not_found = BpmnModelNormalizer.find_activity(model, "nonexistent")
        assert not_found is None
