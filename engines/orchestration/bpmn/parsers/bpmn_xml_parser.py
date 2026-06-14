# engines/document/parsers/osdm_parsers/bpmn_xml_parser.py
"""
BPMN 2.0 XML Parser – converts a .bpmn file into a BPMNDocument (unified OSDM).

This parser follows the BPMN 2.0 XML specification and maps all BPMN elements
to the OSDM model classes. It uses a two-pass approach:
1. Parse all elements and store temporary string IDs for cross-references.
2. Resolve all references to actual object instances.

DataInput, DataOutput, DataAssociation, and MessageFlow are stored in dedicated
lists on Process and Activity rather than in the main flow_elements dictionary.

Logging and strict mode are configurable via ParseOptions.custom:
- custom['strict']: bool (default False) – if True, missing references raise ValueError.
- custom['log_level']: str (default "WARNING") – one of "DEBUG", "INFO", "WARNING", "ERROR".
"""
from __future__ import annotations

import logging
from xml.etree import ElementTree as ET
from typing import Any, cast

from engines.document.models.media_types import MEDIA_TYPES
from ..models.bpmn_models import (
    Activity, AdHocOrdering, AdHocSubProcess, AlignmentKind, Artifact,
    Association, AssociationDirection, Auditing, BaseOSDMDocument,
    BoundaryEvent, Bounds, BPMNDiagram, BPMNDocument, BPMNEdge, BPMNLabel,
    BPMNShape, BusinessRuleTask, CallActivity, CatchEvent,
    CancelEventDefinition, Choreography, ChoreographyActivity,
    Collaboration, CompensateEventDefinition, ComplexGateway,
    ConditionalEventDefinition, ConversationAssociation, ConversationLink,
    ConversationNode, ChoreographyLoopType, CorrelationKey,
    CorrelationProperty, CorrelationPropertyType,
    CorrelationSubscription, DataAssociation, 
    DataFlowElement, DataElement, DataInput, DataObject,
    DataObjectReference, DataOutput, DataOutputAssociation,
    DataInputAssociation, DataStore, DataStoreReference, EndEvent, Error,
    ErrorEventDefinition, Escalation, EscalationEventDefinition, Event,
    EventBasedGateway, EventBasedGatewayType, EventDefinition, ExclusiveGateway,
    FlowNode, FlowElement, FormalExpression, Gateway, GatewayDirection,
    GlobalTask, Group, InclusiveGateway, InputOutputSpecification, Interface,
    InteractionNode, IntermediateCatchEvent, IntermediateThrowEvent, ItemDefinition, 
    ItemKind, Lane, LaneSet, LinkEventDefinition, ManualTask, Message,
    MessageEventDefinition, MessageFlow, MessageFlowAssociation, Monitoring,
    MultiInstanceBehavior, MultiInstanceLoopCharacteristics, Operation,
    ParallelGateway, Participant, ParticipantAssociation,
    ParticipantMultiplicity, Process, ProcessType, Property, ReceiveTask,
    Rendering, Resource, ResourceParameter, ResourceParameterType,
    ResourceRole, ResourceRoleType, Script, ScriptLanguage, ScriptTask,
    SendTask, SequenceFlow, ServiceTask, Signal, SignalEventDefinition,
    StandardLoopCharacteristics, StartEvent, SubProcess, Task,
    TerminateEventDefinition, TextAnnotation, ThrowEvent, TimerEventDefinition,
    TransactionMethod, TransactionSubProcess, UserTask,
    ResourceAssignmentExpression, RootElement, BaseElement
)

from engines.document.parsers.base import ParseOptions
from ...models.parsers.base_osdm_parser import BaseOSDMParser
from .bpmn_collaboration import BPMNCollaborationParser
from .bpmn_diagram import BPMNDiagramParser
from .bpmn_flow_parser import BPMNFlowParser
from .bpmn_root_element import BPMNRootElementParser

# Namespaces
BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
BPMN_DI_NS = "http://www.omg.org/spec/BPMN/20100524/DI"
DI_NS = "http://www.omg.org/spec/DD/20100524/DI"
DC_NS = "http://www.omg.org/spec/DD/20100524/DC"
NS = {"bpmn": BPMN_NS, "bpmndi": BPMN_DI_NS, "di": DI_NS, "dc": DC_NS}

TASK_TAG_MAP = {
    "task": Task,
    "serviceTask": ServiceTask,
    "sendTask": SendTask,
    "receiveTask": ReceiveTask,
    "userTask": UserTask,
    "manualTask": ManualTask,
    "scriptTask": ScriptTask,
    "businessRuleTask": BusinessRuleTask,
    "callActivity": CallActivity,
}

SUB_PROCESS_TAG_MAP = {
    "subProcess": SubProcess,
    "transaction": TransactionSubProcess,
    "adHocSubProcess": AdHocSubProcess,
}

GATEWAY_TAG_MAP = {
    "exclusiveGateway": ExclusiveGateway,
    "inclusiveGateway": InclusiveGateway,
    "parallelGateway": ParallelGateway,
    "eventBasedGateway": EventBasedGateway,
    "complexGateway": ComplexGateway,
}

EVENT_TAG_MAP = {
    "startEvent": StartEvent,
    "endEvent": EndEvent,
    "intermediateCatchEvent": IntermediateCatchEvent,
    "intermediateThrowEvent": IntermediateThrowEvent,
    "boundaryEvent": BoundaryEvent,
}

EVENT_DEFINITION_TAG_MAP = {
    "messageEventDefinition": MessageEventDefinition,
    "timerEventDefinition": TimerEventDefinition,
    "signalEventDefinition": SignalEventDefinition,
    "errorEventDefinition": ErrorEventDefinition,
    "escalationEventDefinition": EscalationEventDefinition,
    "compensateEventDefinition": CompensateEventDefinition,
    "conditionalEventDefinition": ConditionalEventDefinition,
    "linkEventDefinition": LinkEventDefinition,
    "cancelEventDefinition": CancelEventDefinition,
    "terminateEventDefinition": TerminateEventDefinition,
}


class BPMNXMLParser(
    BaseOSDMParser,
    BPMNFlowParser,
    BPMNCollaborationParser,
    BPMNRootElementParser,
    BPMNDiagramParser,
):
    """Parser for BPMN 2.0 XML files (.bpmn, .bpmn2)."""

    name = "bpmn_xml"
    supported_extensions = (".bpmn", ".bpmn2")

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        # Will be configured per parse call

    # ── Enum mapping helpers ──────────────────────────────────────
    @staticmethod
    def _map_enum(cls, value: str, default: Any) -> Any:
        """Safely map string to enum member, return default if not found."""
        try:
            return cls(value)
        except ValueError:
            return default

    @staticmethod
    def _map_gateway_type(value: str) -> str:
        mapping = {"Exclusive": "Exclusive", "Inclusive": "Inclusive",
                   "Parallel": "Parallel", "Complex": "Complex", "EventBased": "EventBased"}
        return mapping.get(value, "Exclusive")

    @staticmethod
    def _map_gateway_direction(value: str) -> GatewayDirection:
        return BPMNXMLParser._map_enum(GatewayDirection, value, GatewayDirection.UNSPECIFIED)

    @staticmethod
    def _map_process_type(value: str) -> ProcessType:
        mapping = {"None": ProcessType.NONE, "Public": ProcessType.PUBLIC, "Private": ProcessType.PRIVATE}
        return mapping.get(value, ProcessType.NONE)

    @staticmethod
    def _map_association_direction(value: str) -> AssociationDirection:
        return BPMNXMLParser._map_enum(AssociationDirection, value, AssociationDirection.NONE)

    @staticmethod
    def _map_item_kind(value: str) -> ItemKind:
        return BPMNXMLParser._map_enum(ItemKind, value, ItemKind.INFORMATION)

    @staticmethod
    def _map_loop_behavior(value: str) -> MultiInstanceBehavior:
        return BPMNXMLParser._map_enum(MultiInstanceBehavior, value, MultiInstanceBehavior.ALL)

    @staticmethod
    def _map_choreography_loop_type(value: str) -> ChoreographyLoopType:
        return BPMNXMLParser._map_enum(ChoreographyLoopType, value, ChoreographyLoopType.NONE)

    # ── Parsing ──────────────────────────────────────────────────
    async def _parse_to_document(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> BaseOSDMDocument:
        # Configure logging based on options.custom
        custom = options.custom or {}
        log_level = custom.get("log_level", "WARNING").upper()
        self.logger.setLevel(getattr(logging, log_level, logging.WARNING))

        strict = custom.get("strict", False)
        doc_id = source_name  # will be overwritten by real ID later

        encoding = options.encoding or "utf-8"
        text = data.decode(encoding)
        root = ET.fromstring(text)

        doc_id = root.get("id", source_name)
        doc_title = root.get("name", source_name)
        doc = BPMNDocument(
            document_id=doc_id,
            title=doc_title,
            media_type=MEDIA_TYPES["bpmn_xml"]
        )
        doc.source_file = source_name

        root_elements: dict[str, RootElement] = {}
        for child in root:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag == "process":
                proc = self._parse_process(child)
                doc.processes.append(proc)
                root_elements[proc.id] = proc
            elif tag == "collaboration":
                collab = self._parse_collaboration(child)
                doc.collaborations.append(collab)
                root_elements[collab.id] = collab
            elif tag == "choreography":
                choreo = self._parse_choreography(child)
                doc.choreographies.append(choreo)
                root_elements[choreo.id] = choreo
            elif tag == "globalTask":
                gt = self._parse_global_task(child, GlobalTask)
                doc.global_tasks.append(gt)
                root_elements[gt.id] = gt
            elif tag == "message":
                msg = self._parse_message(child)
                root_elements[msg.id] = msg
            elif tag == "error":
                err = self._parse_error(child)
                root_elements[err.id] = err
            elif tag == "escalation":
                esc = self._parse_escalation(child)
                root_elements[esc.id] = esc
            elif tag == "signal":
                sig = self._parse_signal(child)
                root_elements[sig.id] = sig
            elif tag == "resource":
                res = self._parse_resource(child)
                root_elements[res.id] = res
            elif tag == "interface":
                iface = self._parse_interface(child)
                root_elements[iface.id] = iface
            elif tag == "itemDefinition":
                item = self._parse_item_definition(child)
                root_elements[item.id] = item
            elif tag == "correlationProperty":
                cp = self._parse_correlation_property(child)
                root_elements[cp.id] = cp
            elif tag == "dataStore":
                ds = self._parse_data_store(child)
                root_elements[ds.id] = ds

        doc.root_elements = root_elements

        # Parse BPMN DI
        for diag_elem in root.findall("bpmndi:BPMNDiagram", NS):
            diagram = self._parse_diagram(diag_elem)
            doc.diagrams.append(diagram)

        # Resolve all cross-references with strict mode and logging
        self._resolve_references(doc, strict=strict, doc_id=doc_id)

        return doc

    def _parse_resource_assignment_expression(self, elem: ET.Element) -> ResourceAssignmentExpression | None:
        expr = elem.find("bpmn:formalExpression", NS)
        if expr is None:
            return None
        formal_expr = self._parse_expression(expr)
        if formal_expr is None:
            return None
        return ResourceAssignmentExpression(
            id=elem.get("id", ""),
            expression=formal_expr,
        )

    # ── Reference resolution (with strict mode and structured logging) ──
    def _resolve_references(self, doc: BPMNDocument, strict: bool, doc_id: str) -> None:
        """
        Resolve all string cross‑references to actual object references.

        Args:
            doc: The parsed BPMNDocument.
            strict: If True, raise ValueError on missing reference.
            doc_id: Document identifier for logging.
        """
        all_elements: dict[str, BaseElement] = {}

        def collect(root: BaseElement) -> None:
            all_elements[root.id] = root
            if hasattr(root, "flow_elements") and root.flow_elements:
                for fe in root.flow_elements.values():
                    collect(fe)
            if hasattr(root, "lane_sets"):
                for ls in root.lane_sets:
                    collect(ls)
                    for lane in ls.lanes:
                        collect(lane)
                        if lane.child_lane_set:
                            collect(lane.child_lane_set)
            if hasattr(root, "artifacts"):
                for art in root.artifacts:
                    if art:
                        collect(art)
            if hasattr(root, "properties"):
                for prop in root.properties:
                    collect(prop)
            if hasattr(root, "correlation_subscriptions"):
                for cs in root.correlation_subscriptions:
                    collect(cs)
            if hasattr(root, "io_specification") and root.io_specification:
                collect(root.io_specification)
            if hasattr(root, "loop_characteristics") and root.loop_characteristics:
                collect(root.loop_characteristics)
            if hasattr(root, "monitoring") and root.monitoring:
                collect(root.monitoring)
            if hasattr(root, "participants"):
                for p in root.participants:
                    collect(p)
            if hasattr(root, "message_flows"):
                for mf in root.message_flows:
                    collect(mf)
            if hasattr(root, "correlation_keys"):
                for ck in root.correlation_keys:
                    collect(ck)
            if hasattr(root, "conversations"):
                for conv in root.conversations:
                    collect(conv)
            if hasattr(root, "conversation_associations"):
                for ca in root.conversation_associations:
                    collect(ca)
            if hasattr(root, "conversation_links"):
                for cl in root.conversation_links:
                    collect(cl)
            if hasattr(root, "message_flow_associations"):
                for mfa in root.message_flow_associations:
                    collect(mfa)
            if hasattr(root, "participant_associations"):
                for pa in root.participant_associations:
                    collect(pa)
            if hasattr(root, "choreographies"):
                for ch in root.choreographies:
                    collect(ch)
            if hasattr(root, "global_tasks"):
                for gt in root.global_tasks:
                    collect(gt)
            if hasattr(root, "resources"):
                for r in root.resources:
                    collect(r)
            if hasattr(root, "interfaces"):
                for i in root.interfaces:
                    collect(i)
            if hasattr(root, "data_inputs"):
                for di in root.data_inputs:
                    collect(di)
            if hasattr(root, "data_outputs"):
                for do in root.data_outputs:
                    collect(do)
            if hasattr(root, "data_associations"):
                for da in root.data_associations:
                    collect(da)

        # Collect all root elements
        for root_elem in doc.root_elements.values():
            collect(root_elem)

        # Collect all processes and their contents
        for proc in doc.processes:
            collect(proc)
        for collab in doc.collaborations:
            collect(collab)
        for choreo in doc.choreographies:
            collect(choreo)
        for gt in doc.global_tasks:
            collect(gt)

        # Helper to get object by ID with strict mode and logging
        def get_obj(obj_id: str, elem_id: str | None = None, ref_type: str = "") -> BaseElement | None:
            obj = all_elements.get(obj_id)
            if obj is None:
                msg = f"Document '{doc_id}': Reference ID '{obj_id}' not found"
                if elem_id:
                    msg += f" (referenced by element '{elem_id}', type '{ref_type}')"
                if strict:
                    raise ValueError(msg)
                else:
                    self.logger.warning(msg)
            return obj

        for elem in all_elements.values():
            elem_id = elem.id
            # SequenceFlow
            if isinstance(elem, SequenceFlow):
                if hasattr(elem, "source_ref_id") and elem.source_ref_id:
                    src = get_obj(elem.source_ref_id, elem_id, "source_ref")
                    if src is not None and isinstance(src, FlowNode):
                        elem.source_ref = src
                    elif src is not None:
                        self.logger.warning(f"Document '{doc_id}': source_ref_id '{elem.source_ref_id}' on SequenceFlow '{elem_id}' resolved to non-FlowNode type {type(src)}")
                if hasattr(elem, "target_ref_id") and elem.target_ref_id:
                    tgt = get_obj(elem.target_ref_id, elem_id, "target_ref")
                    if tgt is not None and isinstance(tgt, FlowNode):
                        elem.target_ref = tgt
                    elif tgt is not None:
                        self.logger.warning(f"Document '{doc_id}': target_ref_id '{elem.target_ref_id}' on SequenceFlow '{elem_id}' resolved to non-FlowNode type {type(tgt)}")
            # MessageFlow
            if isinstance(elem, MessageFlow):
                if hasattr(elem, "source_ref_id") and elem.source_ref_id:
                    src = get_obj(elem.source_ref_id, elem_id, "source_ref")
                    if src is not None:
                        elem.source_ref = cast(InteractionNode, src)  # InteractionNode is a union type; cast for mypy
                if hasattr(elem, "target_ref_id") and elem.target_ref_id:
                    tgt = get_obj(elem.target_ref_id, elem_id, "target_ref")
                    if tgt is not None:
                        elem.target_ref = cast(InteractionNode, tgt)
                if hasattr(elem, "message_ref_id") and elem.message_ref_id:
                    msg = get_obj(elem.message_ref_id, elem_id, "message_ref")
                    if msg is not None and isinstance(msg, Message):
                        elem.message_ref = msg
                    elif msg is not None:
                        self.logger.warning(f"Document '{doc_id}': message_ref_id '{elem.message_ref_id}' on MessageFlow '{elem_id}' resolved to non-Message type {type(msg)}")
            # DataObjectReference
            if isinstance(elem, DataObjectReference) and hasattr(elem, "data_object_id") and elem.data_object_id:
                obj = get_obj(elem.data_object_id, elem_id, "data_object")
                if obj is not None and isinstance(obj, DataObject):
                    elem.data_object = obj
                elif obj is not None:
                    self.logger.warning(f"Document '{doc_id}': data_object_id '{elem.data_object_id}' on DataObjectReference '{elem_id}' resolved to non-DataObject type {type(obj)}")
            # DataStoreReference
            if isinstance(elem, DataStoreReference) and hasattr(elem, "data_store_id") and elem.data_store_id:
                obj = get_obj(elem.data_store_id, elem_id, "data_store")
                if obj is not None and isinstance(obj, DataStore):
                    elem.data_store = obj
                elif obj is not None:
                    self.logger.warning(f"Document '{doc_id}': data_store_id '{elem.data_store_id}' on DataStoreReference '{elem_id}' resolved to non-DataStore type {type(obj)}")
            # DataInput / DataOutput / Property / ItemDefinition
            if hasattr(elem, "item_subject_ref_id") and elem.item_subject_ref_id and isinstance(elem,(DataInput, DataOutput, DataFlowElement, DataObject, DataStore, DataElement, Property)):
                obj = get_obj(elem.item_subject_ref_id, elem_id, "item_subject_ref")
                if obj is not None and isinstance(obj, ItemDefinition):
                    elem.item_subject_ref = obj
                elif obj is not None:
                    self.logger.warning(f"Document '{doc_id}': item_subject_ref_id '{elem.item_subject_ref_id}' on {type(elem)} '{elem_id}' resolved to non-ItemDefinition type {type(obj)}")
            # Operation
            if isinstance(elem, Operation):
                if hasattr(elem, "in_message_ref_id") and elem.in_message_ref_id:
                    obj = get_obj(elem.in_message_ref_id, elem_id, "in_message_ref")
                    if obj is not None and isinstance(obj, Message):
                        elem.in_message_ref = obj
                if hasattr(elem, "out_message_ref_id") and elem.out_message_ref_id:
                    obj = get_obj(elem.out_message_ref_id, elem_id, "out_message_ref")
                    if obj is not None and isinstance(obj, Message):
                        elem.out_message_ref = obj
                if hasattr(elem, "error_ref_ids"):
                    resolved_errors = []
                    for eid in elem.error_ref_ids:
                        obj = get_obj(eid, elem_id, "error_ref")
                        if obj is not None and isinstance(obj, Error):
                            resolved_errors.append(obj)
                        elif obj is not None:
                            self.logger.warning(f"Document '{doc_id}': error_ref_id '{eid}' on Operation '{elem_id}' resolved to non-Error type {type(obj)}")
                    elem.error_refs = resolved_errors
            # Lane
            if isinstance(elem, Lane):
                if hasattr(elem, "partition_element_ref_id") and elem.partition_element_ref_id:
                    obj = get_obj(elem.partition_element_ref_id, elem_id, "partition_element_ref")
                    if obj is not None:
                        elem.partition_element_ref = obj  # BaseElement, any type allowed
                if hasattr(elem, "flow_node_ref_ids"):
                    resolved_nodes = []
                    for fid in elem.flow_node_ref_ids:
                        obj = get_obj(fid, elem_id, "flow_node_ref")
                        if obj is not None and isinstance(obj, FlowNode):
                            resolved_nodes.append(obj)
                        elif obj is not None:
                            self.logger.warning(f"Document '{doc_id}': flow_node_ref_id '{fid}' on Lane '{elem_id}' resolved to non-FlowNode type {type(obj)}")
                    elem.flow_node_refs = resolved_nodes
            # ChoreographyActivity
            if isinstance(elem, ChoreographyActivity):
                if hasattr(elem, "participant_ref_ids"):
                    resolved_parts = []
                    for pid in elem.participant_ref_ids:
                        obj = get_obj(pid, elem_id, "participant_ref")
                        if obj is not None and isinstance(obj, Participant):
                            resolved_parts.append(obj)
                        elif obj is not None:
                            self.logger.warning(f"Document '{doc_id}': participant_ref_id '{pid}' on ChoreographyActivity '{elem_id}' resolved to non-Participant type {type(obj)}")
                    elem.participant_refs = resolved_parts
                if hasattr(elem, "initiating_participant_ref_id") and elem.initiating_participant_ref_id:
                    obj = get_obj(elem.initiating_participant_ref_id, elem_id, "initiating_participant_ref")
                    if obj is not None and isinstance(obj, Participant):
                        elem.initiating_participant_ref = obj
                    elif obj is not None:
                        self.logger.warning(f"Document '{doc_id}': initiating_participant_ref_id '{elem.initiating_participant_ref_id}' on ChoreographyActivity '{elem_id}' resolved to non-Participant type {type(obj)}")
            # CorrelationKey
            if isinstance(elem, CorrelationKey) and hasattr(elem, "property_ref_ids"):
                resolved_props = []
                for pid in elem.property_ref_ids:
                    obj = get_obj(pid, elem_id, "property_ref")
                    if obj is not None and isinstance(obj, CorrelationProperty):
                        resolved_props.append(obj)
                    elif obj is not None:
                        self.logger.warning(f"Document '{doc_id}': property_ref_id '{pid}' on CorrelationKey '{elem_id}' resolved to non-CorrelationProperty type {type(obj)}")
                elem.property_refs = resolved_props
            # CorrelationSubscription
            if isinstance(elem, CorrelationSubscription) and hasattr(elem, "correlation_key_ref_id") and elem.correlation_key_ref_id:
                obj = get_obj(elem.correlation_key_ref_id, elem_id, "correlation_key_ref")
                if obj is not None and isinstance(obj, CorrelationKey):
                    elem.correlation_key_ref = obj
                elif obj is not None:
                    self.logger.warning(f"Document '{doc_id}': correlation_key_ref_id '{elem.correlation_key_ref_id}' on CorrelationSubscription '{elem_id}' resolved to non-CorrelationKey type {type(obj)}")
            # Association
            if isinstance(elem, Association):
                if hasattr(elem, "source_ref_id") and elem.source_ref_id:
                    obj = get_obj(elem.source_ref_id, elem_id, "source_ref")
                    if obj is not None:
                        elem.source_ref = obj
                if hasattr(elem, "target_ref_id") and elem.target_ref_id:
                    obj = get_obj(elem.target_ref_id, elem_id, "target_ref")
                    if obj is not None:
                        elem.target_ref = obj
            # DataAssociation
            if isinstance(elem, DataAssociation):
                if hasattr(elem, "source_ref_ids"):
                    resolved_srcs = []
                    for sid in elem.source_ref_ids:
                        obj = get_obj(sid, elem_id, "source_ref")
                        if obj is not None:
                            resolved_srcs.append(obj)
                    elem.source_refs = resolved_srcs
                if hasattr(elem, "target_ref_id") and elem.target_ref_id:
                    obj = get_obj(elem.target_ref_id, elem_id, "target_ref")
                    if obj is not None:
                        elem.target_ref = obj
            # ConversationNode
            if isinstance(elem, ConversationNode):
                if hasattr(elem, "participant_ref_ids"):
                    resolved_parts = []
                    for pid in elem.participant_ref_ids:
                        obj = get_obj(pid, elem_id, "participant_ref")
                        if obj is not None and isinstance(obj, Participant):
                            resolved_parts.append(obj)
                        elif obj is not None:
                            self.logger.warning(f"Document '{doc_id}': participant_ref_id '{pid}' on ConversationNode '{elem_id}' resolved to non-Participant type {type(obj)}")
                    elem.participant_refs = resolved_parts
                if hasattr(elem, "message_flow_ref_ids"):
                    resolved_mfs = []
                    for mfid in elem.message_flow_ref_ids:
                        obj = get_obj(mfid, elem_id, "message_flow_ref")
                        if obj is not None and isinstance(obj, MessageFlow):
                            resolved_mfs.append(obj)
                        elif obj is not None:
                            self.logger.warning(f"Document '{doc_id}': message_flow_ref_id '{mfid}' on ConversationNode '{elem_id}' resolved to non-MessageFlow type {type(obj)}")
                    elem.message_flow_refs = resolved_mfs
            # ConversationAssociation
            if isinstance(elem, ConversationAssociation):
                if hasattr(elem, "inner_conversation_node_ref_id") and elem.inner_conversation_node_ref_id:
                    obj = get_obj(elem.inner_conversation_node_ref_id, elem_id, "inner_conversation_node_ref")
                    if obj is not None and isinstance(obj, ConversationNode):
                        elem.inner_conversation_node_ref = obj
                if hasattr(elem, "outer_conversation_node_ref_ids"):
                    resolved_outer = []
                    for oid in elem.outer_conversation_node_ref_ids:
                        obj = get_obj(oid, elem_id, "outer_conversation_node_ref")
                        if obj is not None and isinstance(obj, ConversationNode):
                            resolved_outer.append(obj)
                        elif obj is not None:
                            self.logger.warning(f"Document '{doc_id}': outer_conversation_node_ref_id '{oid}' on ConversationAssociation '{elem_id}' resolved to non-ConversationNode type {type(obj)}")
                    elem.outer_conversation_node_refs = resolved_outer
            # ConversationLink
            if isinstance(elem, ConversationLink):
                if hasattr(elem, "source_ref_id") and elem.source_ref_id:
                    obj = get_obj(elem.source_ref_id, elem_id, "source_ref")
                    if obj is not None:
                        elem.source_ref = cast(InteractionNode, obj)
                if hasattr(elem, "target_ref_id") and elem.target_ref_id:
                    obj = get_obj(elem.target_ref_id, elem_id, "target_ref")
                    if obj is not None:
                        elem.target_ref = cast(InteractionNode, obj)
            # MessageFlowAssociation
            if isinstance(elem, MessageFlowAssociation):
                if hasattr(elem, "inner_message_flow_ref_id") and elem.inner_message_flow_ref_id:
                    obj = get_obj(elem.inner_message_flow_ref_id, elem_id, "inner_message_flow_ref")
                    if obj is not None and isinstance(obj, MessageFlow):
                        elem.inner_message_flow_ref = obj
                if hasattr(elem, "outer_message_flow_ref_id") and elem.outer_message_flow_ref_id:
                    obj = get_obj(elem.outer_message_flow_ref_id, elem_id, "outer_message_flow_ref")
                    if obj is not None and isinstance(obj, MessageFlow):
                        elem.outer_message_flow_ref = obj
            # ParticipantAssociation
            if isinstance(elem, ParticipantAssociation):
                if hasattr(elem, "inner_participant_ref_id") and elem.inner_participant_ref_id:
                    obj = get_obj(elem.inner_participant_ref_id, elem_id, "inner_participant_ref")
                    if obj is not None and isinstance(obj, Participant):
                        elem.inner_participant_ref = obj
                if hasattr(elem, "outer_participant_ref_id") and elem.outer_participant_ref_id:
                    obj = get_obj(elem.outer_participant_ref_id, elem_id, "outer_participant_ref")
                    if obj is not None and isinstance(obj, Participant):
                        elem.outer_participant_ref = obj
            # Participant
            if isinstance(elem, Participant) and hasattr(elem, "process_ref_id") and elem.process_ref_id:
                obj = get_obj(elem.process_ref_id, elem_id, "process_ref")
                if obj is not None and isinstance(obj, Process):
                    elem.process_ref = obj
                elif obj is not None:
                    self.logger.warning(f"Document '{doc_id}': process_ref_id '{elem.process_ref_id}' on Participant '{elem_id}' resolved to non-Process type {type(obj)}")
            # BoundaryEvent
            if isinstance(elem, BoundaryEvent) and hasattr(elem, "attached_to_ref_id") and elem.attached_to_ref_id:
                obj = get_obj(elem.attached_to_ref_id, elem_id, "attached_to_ref")
                if obj is not None and isinstance(obj, Activity):
                    elem.attached_to_ref = obj
                elif obj is not None:
                    self.logger.warning(f"Document '{doc_id}': attached_to_ref_id '{elem.attached_to_ref_id}' on BoundaryEvent '{elem_id}' resolved to non-Activity type {type(obj)}")
            # EventDefinition
            if isinstance(elem, MessageEventDefinition):
                if hasattr(elem, "message_ref_id") and elem.message_ref_id:
                    obj = get_obj(elem.message_ref_id, elem_id, "message_ref")
                    if obj is not None and isinstance(obj, Message):
                        elem.message_ref = obj
                if hasattr(elem, "operation_ref_id") and elem.operation_ref_id:
                    obj = get_obj(elem.operation_ref_id, elem_id, "operation_ref")
                    if obj is not None and isinstance(obj, Operation):
                        elem.operation_ref = obj
            if isinstance(elem, SignalEventDefinition) and hasattr(elem, "signal_ref_id") and elem.signal_ref_id:
                obj = get_obj(elem.signal_ref_id, elem_id, "signal_ref")
                if obj is not None and isinstance(obj, Signal):
                    elem.signal_ref = obj
            if isinstance(elem, ErrorEventDefinition) and hasattr(elem, "error_ref_id") and elem.error_ref_id:
                obj = get_obj(elem.error_ref_id, elem_id, "error_ref")
                if obj is not None and isinstance(obj, Error):
                    elem.error_ref = obj
            if isinstance(elem, EscalationEventDefinition) and hasattr(elem, "escalation_ref_id") and elem.escalation_ref_id:
                obj = get_obj(elem.escalation_ref_id, elem_id, "escalation_ref")
                if obj is not None and isinstance(obj, Escalation):
                    elem.escalation_ref = obj
            if isinstance(elem, CompensateEventDefinition) and hasattr(elem, "activity_ref_id") and elem.activity_ref_id:
                obj = get_obj(elem.activity_ref_id, elem_id, "activity_ref")
                if obj is not None and isinstance(obj, Activity):
                    elem.activity_ref = obj
            if isinstance(elem, LinkEventDefinition):
                if hasattr(elem, "source_ids"):
                    resolved_sources = []
                    for sid in elem.source_ids:
                        obj = get_obj(sid, elem_id, "source")
                        if obj is not None and isinstance(obj, LinkEventDefinition):
                            resolved_sources.append(obj)
                        elif obj is not None:
                            self.logger.warning(f"Document '{doc_id}': source_id '{sid}' on LinkEventDefinition '{elem_id}' resolved to non-LinkEventDefinition type {type(obj)}")
                    elem.sources = resolved_sources
                if hasattr(elem, "target_id") and elem.target_id:
                    obj = get_obj(elem.target_id, elem_id, "target")
                    if obj is not None and isinstance(obj, LinkEventDefinition):
                        elem.target = obj
            # ResourceRole
            if isinstance(elem, ResourceRole) and hasattr(elem, "resource_ref_id") and elem.resource_ref_id:
                obj = get_obj(elem.resource_ref_id, elem_id, "resource_ref")
                if obj is not None and isinstance(obj, Resource):
                    elem.resource_ref = obj
            # MultiInstanceLoopCharacteristics
            if isinstance(elem, MultiInstanceLoopCharacteristics):
                if hasattr(elem, "loop_data_input_ref_id") and elem.loop_data_input_ref_id:
                    obj = get_obj(elem.loop_data_input_ref_id, elem_id, "loop_data_input_ref")
                    if obj is not None and isinstance(obj, DataInput):
                        elem.loop_data_input_ref = obj
                if hasattr(elem, "loop_data_output_ref_id") and elem.loop_data_output_ref_id:
                    obj = get_obj(elem.loop_data_output_ref_id, elem_id, "loop_data_output_ref")
                    if obj is not None and isinstance(obj, DataOutput):
                        elem.loop_data_output_ref = obj
            # Gateway with default_sequence_flow
            if hasattr(elem, "default_sequence_flow_id") and elem.default_sequence_flow_id:
                if isinstance(elem, (ExclusiveGateway, InclusiveGateway, ComplexGateway)):
                    obj = get_obj(elem.default_sequence_flow_id, elem_id, "default_sequence_flow")
                    if obj is not None and isinstance(obj, SequenceFlow):
                        elem.default_sequence_flow = obj
            # BPMNDiagram, BPMNShape, BPMNEdge model_element
            if hasattr(elem, "model_element_id") and elem.model_element_id:
                if isinstance(elem, (BPMNDiagram, BPMNShape, BPMNEdge)):
                    obj = get_obj(elem.model_element_id, elem_id, "model_element")
                    if obj is not None:
                        elem.model_element = obj
                else:
                    self.logger.warning(f"Document '{doc_id}': element {elem_id} has model_element_id but is not a diagram element; ignoring")
