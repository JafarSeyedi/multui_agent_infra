"""Process model normalization — converts payloads into ProcessModel/TypedProcessModel."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .process_executor import ProcessModel
from ..._types import RawData, VariableValue

from .models.bpmn_models import ActivityType, FlowNode, SequenceFlow, StartEvent
from .process_model import TypedProcessModel
from .sequence_flow import HandlerSequenceFlow


def _dict_to_handler_flow(d: RawData) -> HandlerSequenceFlow:
    return HandlerSequenceFlow(
        flow_id=str(d.get("id", "")),
        source_ref=str(d.get("source") or d.get("sourceRef") or d.get("source_id") or ""),
        target_ref=str(d.get("target") or d.get("targetRef") or d.get("target_id") or ""),
        condition_expression=str(d.get("condition") or d.get("conditionExpression") or "") or None,
        is_default=bool(d.get("isDefault", d.get("is_default", False))),
    )


def _activity_get(activity: Any, key: str, default: Any = None) -> Any:
    if isinstance(activity, dict):
        return activity.get(key, default)
    return getattr(activity, key, default)


def _activity_type_str(activity: Any) -> str:
    if isinstance(activity, dict):
        return str(activity.get("type", "")).lower()
    if hasattr(activity, "activity_type") and activity.activity_type is not None:
        at = activity.activity_type
        return at.value if isinstance(at, ActivityType) else str(at)
    if hasattr(activity, "type"):
        return str(activity.type).lower()
    return ""


def _activity_id(activity: Any) -> str:
    if isinstance(activity, dict):
        return activity.get("id", "")
    return str(getattr(activity, "id", ""))


class BpmnModelNormalizer:
    """Normalizes definition payloads into ProcessModel and TypedProcessModel."""

    @staticmethod
    def normalize(payload: RawData) -> ProcessModel:
        from .process_executor import ProcessModel
        activities = list(payload.get("activities", []))
        raw_flows = list(payload.get("flows", []))
        typed_flows: list[HandlerSequenceFlow] = []
        for f in raw_flows:
            if hasattr(f, "flow_id"):
                typed_flows.append(f)
            elif isinstance(f, dict):
                typed_flows.append(_dict_to_handler_flow(f))
        start_node = payload.get("start_event_id")
        if not start_node:
            for item in activities:
                item_type = _activity_type_str(item)
                if item_type.lower() in {"startevent", "start"}:
                    start_node = _activity_id(item)
                    break
        if not start_node:
            flow_elements = payload.get("flow_elements", payload.get("elements", {}))
            if isinstance(flow_elements, dict):
                for eid, elem in flow_elements.items():
                    if isinstance(elem, StartEvent):
                        start_node = eid
                        break
                    if isinstance(elem, dict) and str(elem.get("type", "")).lower() in {"startevent", "start"}:
                        start_node = eid
                        break
        return ProcessModel(
            definition_id=str(payload.get("id", "process")),
            start_node=start_node, activities=activities, flows=typed_flows,
        )

    @staticmethod
    def normalize_osdm(definition_xml: RawData, definition_id: str) -> TypedProcessModel:
        typed_model = TypedProcessModel(definition_id=definition_id)
        flow_elements = definition_xml.get("flow_elements", definition_xml.get("elements", {}))
        if isinstance(flow_elements, dict):
            for element_id, element in flow_elements.items():
                if isinstance(element, FlowNode):
                    typed_model._node_index[element_id] = element
                    if isinstance(element, SequenceFlow):
                        typed_model._flow_index.setdefault(element.source_ref_id or "", []).append(element)
                elif isinstance(element, SequenceFlow):
                    typed_model._flow_index.setdefault(element.source_ref_id or "", []).append(element)
        if hasattr(typed_model, "process") and typed_model.process is None:
            processes = definition_xml.get("processes", definition_xml.get("Process", []))
            if processes and isinstance(processes, list):
                typed_model.process = processes[0]
        typed_model.start_node_id = definition_xml.get("start_event_id")
        return typed_model

    @staticmethod
    def find_activity(model: Any, activity_id: str) -> Any | None:
        for item in getattr(model, "activities", []):
            if _activity_id(item) == activity_id:
                return item
        return None
