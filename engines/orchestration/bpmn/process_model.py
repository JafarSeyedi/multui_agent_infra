"""BPMN process model with OSDM-typed elements.

Provides typed traversal of process definitions using OSDM model classes
instead of raw dictionaries.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from .models.bpmn_models import (
    Process,
    FlowElement,
    FlowNode,
    Activity,
    ActivityType,
    Task,
    Event,
    CatchEvent,
    ThrowEvent,
    StartEvent,
    EndEvent,
    IntermediateCatchEvent,
    IntermediateThrowEvent,
    BoundaryEvent,
    Gateway,
    ExclusiveGateway,
    InclusiveGateway,
    ParallelGateway,
    EventBasedGateway,
    ComplexGateway,
    SequenceFlow,
    Participant,
    Lane,
    LaneSet,
    MessageFlow,
    DataObject,
    DataObjectReference,
    DataStoreReference,
    DataAssociation,
    DataInputAssociation,
    DataOutputAssociation,
    Message,
    Signal,
    Error,
    Escalation,
    CorrelationKey,
    CorrelationSubscription,
    InputOutputSpecification,
    LoopCharacteristics,
    StandardLoopCharacteristics,
    MultiInstanceLoopCharacteristics,
    EventType,
    EventDefinitionType,
    GatewayType,
    SubProcess,
    AdHocSubProcess,
    TransactionSubProcess,
    ServiceTask,
    UserTask,
    ManualTask,
    ScriptTask,
    BusinessRuleTask,
    SendTask,
    ReceiveTask,
    CallActivity,
    GlobalTask,
    ChoreographyTask,
    ChoreographyLoopType,
    ConversationLink,
    Conversation,
    Collaboration,
)

logger = logging.getLogger(__name__)


@dataclass
class TypedProcessModel:
    """OSDM-typed process model for traversal."""
    definition_id: str
    start_node_id: str | None = None
    process: Process | None = None
    _node_index: dict[str, FlowNode] = field(default_factory=dict)
    _raw_node_index: dict[str, dict[str, Any]] = field(default_factory=dict)
    _flow_index: dict[str, list[SequenceFlow]] = field(default_factory=dict)
    _boundary_events: dict[str, list[BoundaryEvent]] = field(default_factory=dict)

    @classmethod
    def from_osdm_process(cls, process: Process) -> TypedProcessModel:
        model = cls(definition_id=process.id, process=process)
        model._build_index()
        model._find_start_node()
        return model

    @classmethod
    def from_definition_xml(cls, definition_xml: dict[str, Any], definition_id: str) -> TypedProcessModel:
        model = cls(definition_id=definition_id)
        model._build_from_dict(definition_xml)
        return model

    def _build_index(self) -> None:
        if self.process and self.process.flow_elements:
            for element_id, element in self.process.flow_elements.items():
                if isinstance(element, FlowNode):
                    self._node_index[element_id] = element
                    if isinstance(element, BoundaryEvent):
                        attached = element.attached_to_ref
                        if attached:
                            attached_id = attached.id if isinstance(attached, Activity) else str(attached)
                            if attached_id not in self._boundary_events:
                                self._boundary_events[attached_id] = []
                            self._boundary_events[attached_id].append(element)

    def _find_start_node(self) -> None:
        if self.process and self.process.flow_elements:
            for element_id, element in self.process.flow_elements.items():
                if isinstance(element, StartEvent):
                    self.start_node_id = element_id
                    break

    def _build_from_dict(self, definition_xml: dict[str, Any]) -> None:
        elements = definition_xml.get("flow_elements", definition_xml.get("elements", {}))
        for element_id, element_data in elements.items():
            if isinstance(element_data, dict):
                self._raw_node_index[element_id] = element_data
        self.start_node_id = definition_xml.get("start_event_id")
        if not self.start_node_id:
            for element_id, element_data in elements.items():
                if isinstance(element_data, dict):
                    etype = str(element_data.get("type", "")).lower()
                    if "start" in etype or etype == "":
                        if etype.startswith("start") or "StartEvent" in str(element_data.get("__class__", "")):
                            self.start_node_id = element_id
                            break

    def get_node(self, node_id: str) -> FlowNode | dict[str, Any] | None:
        node: FlowNode | dict[str, Any] | None = self._node_index.get(node_id)
        if node is None:
            node = self._raw_node_index.get(node_id)
        if node is None:
            logger.warning("Node not found: %s", node_id)
        return node

    def get_outgoing_flows(self, node_id: str) -> list[SequenceFlow]:
        return self._flow_index.get(node_id, [])

    def get_outgoing_targets(self, node_id: str) -> list[str]:
        result: list[str] = []
        for f in self.get_outgoing_flows(node_id):
            if f.target_ref:
                result.append(f.target_ref.id if isinstance(f.target_ref, FlowNode) else str(f.target_ref))
        return result

    def get_boundary_events(self, activity_id: str) -> list[BoundaryEvent]:
        return self._boundary_events.get(activity_id, [])

    def get_all_activities(self) -> list[Activity]:
        result = []
        for node in self._node_index.values():
            if isinstance(node, Activity):
                result.append(node)
        return result

    def get_all_events(self) -> list[Event]:
        result = []
        for node in self._node_index.values():
            if isinstance(node, Event):
                result.append(node)
        return result

    def get_all_gateways(self) -> list[Gateway]:
        result = []
        for node in self._node_index.values():
            if isinstance(node, Gateway):
                result.append(node)
        return result

    def get_start_event(self) -> StartEvent | None:
        if self.start_node_id:
            node = self.get_node(self.start_node_id)
            if isinstance(node, StartEvent):
                return node
        return None

    def get_activity_type(self, node_id: str) -> str | None:
        node = self.get_node(node_id)
        if isinstance(node, ActivityType):
            return None
        if isinstance(node, Activity):
            return getattr(node, 'activity_type', None)
        return None

    def get_loop_characteristics(self, node_id: str) -> LoopCharacteristics | None:
        node = self.get_node(node_id)
        if isinstance(node, Activity):
            return getattr(node, 'loop_characteristics', None)
        return None

    def get_io_specification(self, node_id: str) -> InputOutputSpecification | None:
        node = self.get_node(node_id)
        if isinstance(node, Activity):
            return getattr(node, 'io_specification', None)
        return None

    def get_participants(self) -> list[Participant]:
        if self.process:
            collab = getattr(self.process, 'definitional_collaboration_ref', None)
            if collab and hasattr(collab, 'participants'):
                return list(collab.participants.values()) if isinstance(collab.participants, dict) else list(collab.participants)
        return []

    def get_lane_sets(self) -> list[LaneSet]:
        if self.process:
            return list(self.process.lane_sets) if self.process.lane_sets else []
        return []

    def iter_flow_elements(self) -> list[tuple[str, FlowElement]]:
        if self.process and self.process.flow_elements:
            return list(self.process.flow_elements.items())
        return []


def classify_node(node: FlowNode | Any) -> str:
    """Classify a flow node into a handler-friendly type string."""
    if isinstance(node, ExclusiveGateway):
        return "exclusiveGateway"
    if isinstance(node, InclusiveGateway):
        return "inclusiveGateway"
    if isinstance(node, ParallelGateway):
        return "parallelGateway"
    if isinstance(node, EventBasedGateway):
        return "eventBasedGateway"
    if isinstance(node, ComplexGateway):
        return "complexGateway"
    if isinstance(node, StartEvent):
        return "startEvent"
    if isinstance(node, EndEvent):
        return "endEvent"
    if isinstance(node, BoundaryEvent):
        return "boundaryEvent"
    if isinstance(node, IntermediateCatchEvent):
        return "intermediateCatch"
    if isinstance(node, IntermediateThrowEvent):
        return "intermediateThrow"
    if isinstance(node, ServiceTask):
        return "serviceTask"
    if isinstance(node, UserTask):
        return "userTask"
    if isinstance(node, ManualTask):
        return "manualTask"
    if isinstance(node, ScriptTask):
        return "scriptTask"
    if isinstance(node, BusinessRuleTask):
        return "businessRuleTask"
    if isinstance(node, SendTask):
        return "sendTask"
    if isinstance(node, ReceiveTask):
        return "receiveTask"
    if isinstance(node, CallActivity):
        return "callActivity"
    if isinstance(node, AdHocSubProcess):
        return "adHocSubProcess"
    if isinstance(node, SubProcess):
        return "subProcess"
    if isinstance(node, Task):
        return "task"
    if isinstance(node, Activity):
        return "activity"
    if isinstance(node, Event):
        return "event"
    if isinstance(node, Gateway):
        return "gateway"
    if isinstance(node, FlowNode):
        return "flowNode"
    return "unknown"
