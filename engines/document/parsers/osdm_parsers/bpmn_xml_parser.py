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
from typing import Optional, Dict, Any, List, cast

from ...models.media_types import MEDIA_TYPES
from ...models.osdm_models import (
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

from ..base import ParseOptions
from .base_osdm_parser import BaseOSDMParser

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


class BPMNXMLParser(BaseOSDMParser):
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

        root_elements: Dict[str, RootElement] = {}
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

    # ── Process ────────────────────────────────────────────────────
    def _parse_process(self, elem: ET.Element) -> Process:
        proc_type_str = elem.get("processType", "None")
        proc_type = self._map_process_type(proc_type_str)
        proc = Process(
            id=elem.get("id", ""),
            name=elem.get("name"),
            process_type=proc_type,
            is_executable=elem.get("isExecutable", "false") == "true",
            is_closed=elem.get("isClosed", "false") == "true",
        )
        flow_elements: Dict[str, FlowElement] = {}
        for child in elem:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag in ("dataInput", "dataOutput", "dataAssociation", "messageFlow"):
                self._parse_process_level_element(proc, child, tag)
            else:
                flow = self._parse_flow_element(child)
                if flow:
                    flow_elements[flow.id] = flow
        proc.flow_elements = flow_elements

        for lane_set_elem in elem.findall("bpmn:laneSet", NS):
            ls = self._parse_lane_set(lane_set_elem)
            proc.lane_sets.append(ls)

        for art_elem in (elem.findall("bpmn:association", NS) +
                         elem.findall("bpmn:group", NS) +
                         elem.findall("bpmn:textAnnotation", NS)):
            art = self._parse_artifact(art_elem)
            if art:
                proc.artifacts.append(art)

        for prop_elem in elem.findall("bpmn:property", NS):
            prop = self._parse_property(prop_elem)
            proc.properties.append(prop)

        for cs_elem in elem.findall("bpmn:correlationSubscription", NS):
            cs = self._parse_correlation_subscription(cs_elem)
            proc.correlation_subscriptions.append(cs)

        aud = elem.find("bpmn:auditing", NS)
        if aud is not None:
            proc.auditing = self._parse_auditing(aud)
        mon = elem.find("bpmn:monitoring", NS)
        if mon is not None:
            proc.monitoring = Monitoring(id=mon.get("id", ""))

        io = elem.find("bpmn:ioSpecification", NS)
        if io is not None:
            proc.io_specification = self._parse_io_specification(io)

        return proc

    def _parse_process_level_element(self, proc: Process, elem: ET.Element, tag: str) -> None:
        """Parse elements that are not FlowElements (DataInput, DataOutput, DataAssociation, MessageFlow)."""
        if tag == "dataInput":
            di = self._parse_data_input(elem)
            proc.data_inputs.append(di)
        elif tag == "dataOutput":
            do = self._parse_data_output(elem)
            proc.data_outputs.append(do)
        elif tag == "dataAssociation":
            da = self._parse_data_association(elem)
            proc.data_associations.append(da)
        elif tag == "messageFlow":
            mf = self._parse_message_flow(elem)
            proc.message_flows.append(mf)

    def _parse_flow_element(self, elem: ET.Element) -> Optional[FlowElement]:
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if tag in TASK_TAG_MAP:
            cls = TASK_TAG_MAP[tag]
            return self._parse_task(elem, cls)
        elif tag in SUB_PROCESS_TAG_MAP:
            cls = SUB_PROCESS_TAG_MAP[tag]
            return self._parse_sub_process(elem, cls)
        elif tag in GATEWAY_TAG_MAP:
            cls = GATEWAY_TAG_MAP[tag]
            return self._parse_gateway(elem, cls)
        elif tag in EVENT_TAG_MAP:
            cls = EVENT_TAG_MAP[tag]
            return self._parse_event(elem, cls)
        elif tag == "sequenceFlow":
            return self._parse_sequence_flow(elem)
        elif tag == "dataObject":
            return self._parse_data_object(elem)
        elif tag == "dataObjectReference":
            return self._parse_data_object_reference(elem)
        elif tag == "dataStoreReference":
            return self._parse_data_store_reference(elem)
        return None

    def _parse_task(self, elem: ET.Element, cls: Any) -> Optional[Task]:
        task = cls(
            id=elem.get("id", ""),
            name=elem.get("name"),
        )
        self._parse_activity_common(elem, task)
        if isinstance(task, ServiceTask):
            task.implementation = None
            task.operation_ref = None
        elif isinstance(task, SendTask):
            task.message_ref = None
            task.operation_ref = None
            task.message_ref_id = elem.get("messageRef")
            task.operation_ref_id = elem.get("operationRef")
        elif isinstance(task, ReceiveTask):
            task.message_ref = None
            task.operation_ref = None
            task.message_ref_id = elem.get("messageRef")
            task.operation_ref_id = elem.get("operationRef")
            task.instantiate = elem.get("instantiate") == "true"
        elif isinstance(task, UserTask):
            task.implementation = "##unspecified"
            for rend_elem in elem.findall("bpmn:rendering", NS):
                rend = self._parse_rendering(rend_elem)
                task.rendering.append(rend)
        elif isinstance(task, ScriptTask):
            script_elem = elem.find("bpmn:script", NS)
            if script_elem is not None and script_elem.text:
                script_lang = script_elem.get("scriptFormat", "Python")
                lang_enum = self._map_enum(ScriptLanguage, script_lang, ScriptLanguage.PYTHON)
                task.script = Script(
                    id=elem.get("id", "") + "_script",
                    script_body=script_elem.text,
                    script_language=lang_enum,
                )
        elif isinstance(task, BusinessRuleTask):
            task.implementation = None
            impl_ref = elem.get("implementation")
            if impl_ref and impl_ref not in ("##unspecified", "##WebService"):
                self.logger.warning(f"BusinessRuleTask {task.id} references implementation '{impl_ref}' - not parsed")
        return task

    def _parse_activity_common(self, elem: ET.Element, activity: Activity) -> None:
        doc_elem = elem.find("bpmn:documentation", NS)
        if doc_elem is not None and doc_elem.text:
            activity.documentation = doc_elem.text
        loop = elem.find("bpmn:standardLoopCharacteristics", NS)
        if loop is not None:
            activity.loop_characteristics = self._parse_standard_loop(loop)
        multi = elem.find("bpmn:multiInstanceLoopCharacteristics", NS)
        if multi is not None:
            activity.loop_characteristics = self._parse_multi_instance_loop(multi)
        io = elem.find("bpmn:ioSpecification", NS)
        if io is not None:
            activity.io_specification = self._parse_io_specification(io)
        for rr in elem.findall("bpmn:resourceRole", NS):
            role = self._parse_resource_role(rr)
            activity.resources.append(role)
        for prop in elem.findall("bpmn:property", NS):
            activity.properties.append(self._parse_property(prop))
        for child in elem:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag == "dataInput":
                activity.data_inputs.append(self._parse_data_input(child))
            elif tag == "dataOutput":
                activity.data_outputs.append(self._parse_data_output(child))
            elif tag == "dataAssociation":
                da = self._parse_data_association(child)
                # distinguish between input/output association based on context?
                # For BPMN, dataAssociation inside an activity is generic, but we need to store it as either DataInputAssociation or DataOutputAssociation.
                # We'll store as DataAssociation and later convert if needed? The models require specific types.
                # Since it's ambiguous, we'll store as DataAssociation (which is a base) but the model has separate lists.
                # We'll add both? Simpler: ignore for now, as BPMN rarely uses generic DataAssociation at activity level without specific role.
                self.logger.debug(f"Ignoring generic DataAssociation {da.id} inside activity {activity.id}")
        # Also collect dataInputAssociation and dataOutputAssociation (not present in BPMN? Actually BPMN uses dataInputAssociation and dataOutputAssociation on events, not on activities)
        # For events, we handle separately in _parse_event.

    def _parse_sub_process(self, elem: ET.Element, cls: Any) -> SubProcess:
        sub = cls(
            id=elem.get("id", ""),
            name=elem.get("name"),
        )
        sub.triggered_by_event = elem.get("triggeredByEvent") == "true"
        if isinstance(sub, AdHocSubProcess):
            ordering_str = elem.get("ordering", "Parallel")
            sub.ordering = self._map_enum(AdHocOrdering, ordering_str, AdHocOrdering.PARALLEL)
            cond = elem.find("bpmn:completionCondition", NS)
            if cond is not None:
                sub.completion_condition = self._parse_expression(cond)
        if isinstance(sub, TransactionSubProcess):
            method_str = elem.get("transactionMethod", "##compensate")
            sub.method = self._map_enum(TransactionMethod, method_str, TransactionMethod.COMPENSATE)
        self._parse_activity_common(elem, sub)
        flow_elements: Dict[str, FlowElement] = {}
        for child in elem:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag in ("dataInput", "dataOutput", "dataAssociation", "messageFlow"):
                continue
            flow = self._parse_flow_element(child)
            if flow:
                flow_elements[flow.id] = flow
        sub.flow_elements = flow_elements
        for ls in elem.findall("bpmn:laneSet", NS):
            sub.lane_sets.append(self._parse_lane_set(ls))
        for art in (elem.findall("bpmn:association", NS) +
                    elem.findall("bpmn:group", NS) +
                    elem.findall("bpmn:textAnnotation", NS)):
            a = self._parse_artifact(art)
            if a:
                sub.artifacts.append(a)
        return sub

    def _parse_gateway(self, elem: ET.Element, cls: Any) -> Gateway:
        gateway_type_str = elem.get("gatewayType", "Exclusive")
        gateway_type = self._map_gateway_type(gateway_type_str)
        gw = cls(
            id=elem.get("id", ""),
            name=elem.get("name"),
            gateway_type=gateway_type,
            gateway_direction=self._map_gateway_direction(elem.get("gatewayDirection", "Unspecified")),
        )
        if isinstance(gw, (ExclusiveGateway, InclusiveGateway, ComplexGateway)):
            gw.default_sequence_flow_id = elem.get("default")
        if isinstance(gw, EventBasedGateway):
            event_type_str = elem.get("eventGatewayType", "Exclusive")
            gw.event_type = self._map_enum(EventBasedGatewayType, event_type_str, EventBasedGatewayType.EXCLUSIVE)
        if isinstance(gw, ComplexGateway):
            cond = elem.find("bpmn:activationCondition", NS)
            if cond is not None:
                gw.activation_condition = self._parse_expression(cond)
        return gw

    def _parse_event(self, elem: ET.Element, cls: Any) -> Event:
        ev = cls(
            id=elem.get("id", ""),
            name=elem.get("name"),
            event_type=elem.get("eventType", "Start"),
        )
        if isinstance(ev, CatchEvent):
            ev.parallel_multiple = elem.get("parallelMultiple") == "true"
        if isinstance(ev, BoundaryEvent):
            ev.attached_to_ref_id = elem.get("attachedToRef")
            ev.cancel_activity = elem.get("cancelActivity", "true") == "true"
        if isinstance(ev, StartEvent):
            ev.is_interrupting = elem.get("isInterrupting", "true") == "true"
        for ed_elem in elem.findall("bpmn:eventDefinition", NS):
            ed = self._parse_event_definition(ed_elem)
            if ed:
                ev.event_definitions.append(ed)
        for prop in elem.findall("bpmn:property", NS):
            ev.properties.append(self._parse_property(prop))
        if isinstance(ev, CatchEvent):
            for da_elem in elem.findall("bpmn:dataOutputAssociation", NS):
                da = self._parse_data_association(da_elem)
                # Convert to DataOutputAssociation (same fields, different type)
                doa = DataOutputAssociation(
                    id=da.id,
                    source_refs=da.source_refs,
                    target_ref=da.target_ref,
                    transformation=da.transformation,
                    assignments=da.assignments,
                    source_ref_ids=da.source_ref_ids,
                    target_ref_id=da.target_ref_id,
                )
                ev.data_output_associations.append(doa)
        if isinstance(ev, ThrowEvent):
            for da_elem in elem.findall("bpmn:dataInputAssociation", NS):
                da = self._parse_data_association(da_elem)
                dia = DataInputAssociation(
                    id=da.id,
                    source_refs=da.source_refs,
                    target_ref=da.target_ref,
                    transformation=da.transformation,
                    assignments=da.assignments,
                    source_ref_ids=da.source_ref_ids,
                    target_ref_id=da.target_ref_id,
                )
                ev.data_input_associations.append(dia)
        return ev

    def _parse_event_definition(self, elem: ET.Element) -> Optional[EventDefinition]:
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        cls = EVENT_DEFINITION_TAG_MAP.get(tag)
        if not cls:
            return None
        ed = cls(id=elem.get("id", ""))
        if isinstance(ed, MessageEventDefinition):
            ed.message_ref_id = elem.get("messageRef")
            ed.operation_ref_id = elem.get("operationRef")
        elif isinstance(ed, TimerEventDefinition):
            ed.time_date = self._parse_expression(elem.find("bpmn:timeDate", NS))
            ed.time_cycle = self._parse_expression(elem.find("bpmn:timeCycle", NS))
            ed.time_duration = self._parse_expression(elem.find("bpmn:timeDuration", NS))
        elif isinstance(ed, SignalEventDefinition):
            ed.signal_ref_id = elem.get("signalRef")
        elif isinstance(ed, ErrorEventDefinition):
            ed.error_ref_id = elem.get("errorRef")
        elif isinstance(ed, EscalationEventDefinition):
            ed.escalation_ref_id = elem.get("escalationRef")
        elif isinstance(ed, CompensateEventDefinition):
            ed.activity_ref_id = elem.get("activityRef")
            ed.wait_for_completion = elem.get("waitForCompletion", "true") == "true"
        elif isinstance(ed, ConditionalEventDefinition):
            cond = elem.find("bpmn:condition", NS)
            if cond is not None:
                ed.condition = self._parse_expression(cond)
        elif isinstance(ed, LinkEventDefinition):
            # Filter out None values from list comprehension
            ed.source_ids = [src_id for src in elem.findall("bpmn:source", NS) if (src_id := src.get("id")) is not None]
            target = elem.find("bpmn:target", NS)
            ed.target_id = target.get("id") if target is not None else None
        return ed

    def _parse_sequence_flow(self, elem: ET.Element) -> SequenceFlow:
        seq = SequenceFlow(
            id=elem.get("id", ""),
            name=elem.get("name"),
            source_ref=None,
            target_ref=None,
            is_immediate=elem.get("isImmediate", "true") == "true",
        )
        seq.source_ref_id = elem.get("sourceRef")
        seq.target_ref_id = elem.get("targetRef")
        cond = elem.find("bpmn:conditionExpression", NS)
        if cond is not None:
            seq.condition_expression = self._parse_expression(cond)
        return seq

    def _parse_data_object(self, elem: ET.Element) -> DataObject:
        obj = DataObject(
            id=elem.get("id", ""),
            name=elem.get("name"),
            is_collection=elem.get("isCollection") == "true",
            item_subject_ref=None,
        )
        obj.item_subject_ref_id = elem.get("itemSubjectRef")
        return obj

    def _parse_data_object_reference(self, elem: ET.Element) -> DataObjectReference:
        ref = DataObjectReference(
            id=elem.get("id", ""),
            name=elem.get("name"),
            data_object=None,
        )
        ref.data_object_id = elem.get("dataObjectRef")
        return ref

    def _parse_data_store(self, elem: ET.Element) -> DataStore:
        store = DataStore(
            id=elem.get("id", ""),
            name=elem.get("name"),
            is_unlimited=elem.get("isUnlimited", "true") == "true",
            capacity=int(elem.get("capacity", "0")),
            item_subject_ref=None,
        )
        store.item_subject_ref_id = elem.get("itemSubjectRef")
        return store

    def _parse_data_store_reference(self, elem: ET.Element) -> DataStoreReference:
        ref = DataStoreReference(
            id=elem.get("id", ""),
            name=elem.get("name"),
            data_store=None,
        )
        ref.data_store_id = elem.get("dataStoreRef")
        return ref

    def _parse_data_input(self, elem: ET.Element) -> DataInput:
        inp = DataInput(
            id=elem.get("id", ""),
            name=elem.get("name") or "",
            item_subject_ref=None,
            is_collection=elem.get("isCollection") == "true",
        )
        inp.item_subject_ref_id = elem.get("itemSubjectRef")
        return inp

    def _parse_data_output(self, elem: ET.Element) -> DataOutput:
        out = DataOutput(
            id=elem.get("id", ""),
            name=elem.get("name") or "",
            item_subject_ref=None,
            is_collection=elem.get("isCollection") == "true",
        )
        out.item_subject_ref_id = elem.get("itemSubjectRef")
        return out

    def _parse_data_association(self, elem: ET.Element) -> DataAssociation:
        da = DataAssociation(id=elem.get("id", ""))
        # Filter out None values from source list
        da.source_ref_ids = [src_id for src in elem.findall("bpmn:sourceRef", NS) if (src_id := src.get("id")) is not None]
        tgt = elem.find("bpmn:targetRef", NS)
        da.target_ref_id = tgt.get("id") if tgt is not None else None
        trans = elem.find("bpmn:transformation", NS)
        if trans is not None:
            da.transformation = self._parse_expression(trans)
        return da

    def _parse_message_flow(self, elem: ET.Element) -> MessageFlow:
        mf = MessageFlow(
            id=elem.get("id", ""),
            name=elem.get("name"),
            source_ref=None,
            target_ref=None,
            message_ref=None,
        )
        mf.source_ref_id = elem.get("sourceRef")
        mf.target_ref_id = elem.get("targetRef")
        mf.message_ref_id = elem.get("messageRef")
        return mf

    def _parse_lane_set(self, elem: ET.Element) -> LaneSet:
        ls = LaneSet(id=elem.get("id", ""), name=elem.get("name"))
        for lane_elem in elem.findall("bpmn:lane", NS):
            lane = self._parse_lane(lane_elem)
            ls.lanes.append(lane)
        return ls

    def _parse_lane(self, elem: ET.Element) -> Lane:
        lane = Lane(id=elem.get("id", ""), name=elem.get("name"))
        lane.partition_element_ref_id = elem.get("partitionElement")
        # Filter out None values
        lane.flow_node_ref_ids = [fn_id for fn in elem.findall("bpmn:flowNodeRef", NS) if (fn_id := fn.get("id")) is not None]
        child_ls = elem.find("bpmn:childLaneSet", NS)
        if child_ls is not None:
            lane.child_lane_set = self._parse_lane_set(child_ls)
        return lane

    def _parse_collaboration(self, elem: ET.Element) -> Collaboration:
        collab = Collaboration(
            id=elem.get("id", ""),
            name=elem.get("name"),
            is_closed=elem.get("isClosed", "false") == "true",
        )
        for p in elem.findall("bpmn:participant", NS):
            collab.participants.append(self._parse_participant(p))
        for mf in elem.findall("bpmn:messageFlow", NS):
            collab.message_flows.append(self._parse_message_flow(mf))
        for art in (elem.findall("bpmn:association", NS) +
                    elem.findall("bpmn:group", NS) +
                    elem.findall("bpmn:textAnnotation", NS)):
            a = self._parse_artifact(art)
            if a:
                collab.artifacts.append(a)
        for key in elem.findall("bpmn:correlationKey", NS):
            collab.correlation_keys.append(self._parse_correlation_key(key))
        for conv in (elem.findall("bpmn:conversation", NS) +
                     elem.findall("bpmn:callConversation", NS) +
                     elem.findall("bpmn:subConversation", NS)):
            collab.conversations.append(self._parse_conversation_node(conv))
        for ca in elem.findall("bpmn:conversationAssociation", NS):
            collab.conversation_associations.append(self._parse_conversation_association(ca))
        for cl in elem.findall("bpmn:conversationLink", NS):
            collab.conversation_links.append(self._parse_conversation_link(cl))
        for mfa in elem.findall("bpmn:messageFlowAssociation", NS):
            collab.message_flow_associations.append(self._parse_message_flow_association(mfa))
        for pa in elem.findall("bpmn:participantAssociation", NS):
            collab.participant_associations.append(self._parse_participant_association(pa))
        return collab

    def _parse_choreography(self, elem: ET.Element) -> Choreography:
        choreo = Choreography(
            id=elem.get("id", ""),
            name=elem.get("name"),
            is_closed=elem.get("isClosed", "false") == "true",
        )
        for child in elem:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag == "choreographyActivity":
                act = self._parse_choreography_activity(child)
                choreo.flow_elements[act.id] = act
            elif tag == "participant":
                choreo.participants.append(self._parse_participant(child))
            elif tag == "messageFlow":
                choreo.message_flows.append(self._parse_message_flow(child))
        return choreo

    def _parse_choreography_activity(self, elem: ET.Element) -> ChoreographyActivity:
        act = ChoreographyActivity(
            id=elem.get("id", ""),
            name=elem.get("name"),
        )
        # Filter out None
        act.participant_ref_ids = [pref_id for pref in elem.findall("bpmn:participantRef", NS) if (pref_id := pref.get("id")) is not None]
        act.initiating_participant_ref_id = elem.get("initiatingParticipantRef")
        loop_str = elem.get("loopType", "None")
        act.loop_type = self._map_choreography_loop_type(loop_str)
        return act

    def _parse_global_task(self, elem: ET.Element, cls: Any) -> GlobalTask:
        gt = cls(
            id=elem.get("id", ""),
            name=elem.get("name"),
        )
        io = elem.find("bpmn:ioSpecification", NS)
        if io is not None:
            gt.io_specification = self._parse_io_specification(io)
        return gt

    def _parse_expression(self, elem: Optional[ET.Element]) -> Optional[FormalExpression]:
        if elem is None:
            return None
        lang = elem.get("language")
        lang_enum = self._map_enum(ScriptLanguage, lang, ScriptLanguage.PYTHON) if lang else None
        body = elem.text or ""
        return FormalExpression(
            id=elem.get("id", ""),
            language=lang_enum,
            body=body,
        )

    def _parse_rendering(self, elem: ET.Element) -> Rendering:
        return Rendering(
            id=elem.get("id", ""),
            name=elem.get("name"),
        )

    def _parse_message(self, elem: ET.Element) -> Message:
        msg = Message(id=elem.get("id", ""), name=elem.get("name"))
        msg.item_ref_id = elem.get("itemRef")
        return msg

    def _parse_error(self, elem: ET.Element) -> Error:
        err = Error(id=elem.get("id", ""), name=elem.get("name"))
        err.error_code = elem.get("errorCode")
        return err

    def _parse_escalation(self, elem: ET.Element) -> Escalation:
        esc = Escalation(id=elem.get("id", ""), name=elem.get("name"))
        esc.escalation_code = elem.get("escalationCode")
        return esc

    def _parse_signal(self, elem: ET.Element) -> Signal:
        return Signal(id=elem.get("id", ""), name=elem.get("name"))

    def _parse_resource(self, elem: ET.Element) -> Resource:
        res = Resource(id=elem.get("id", ""), name=elem.get("name"))
        for rp in elem.findall("bpmn:resourceParameter", NS):
            res.resource_parameters.append(self._parse_resource_parameter(rp))
        return res

    def _parse_resource_parameter(self, elem: ET.Element) -> ResourceParameter:
        type_str = elem.get("type", "UserField")
        param_type = self._map_enum(ResourceParameterType, type_str, ResourceParameterType.USER_FIELD)
        return ResourceParameter(
            id=elem.get("id", ""),
            name=elem.get("name"),
            type=param_type,
            is_required=elem.get("isRequired", "false") == "true",
        )

    def _parse_resource_role(self, elem: ET.Element) -> ResourceRole:
        type_str = elem.get("type", "None")
        role_type = self._map_enum(ResourceRoleType, type_str, ResourceRoleType.NONE)
        role = ResourceRole(
            id=elem.get("id", ""),
            name=elem.get("name"),
            type=role_type,
            resource_ref=None,
        )
        role.resource_ref_id = elem.get("resourceRef")
        expr_elem = elem.find("bpmn:resourceAssignmentExpression", NS)
        if expr_elem is not None:
            role.resource_assignment_expression = self._parse_resource_assignment_expression(expr_elem)
        return role

    def _parse_interface(self, elem: ET.Element) -> Interface:
        iface = Interface(id=elem.get("id", ""), name=elem.get("name"))
        for op_elem in elem.findall("bpmn:operation", NS):
            op = self._parse_operation(op_elem)
            iface.operations[op.id] = op
        return iface

    def _parse_operation(self, elem: ET.Element) -> Operation:
        op = Operation(id=elem.get("id", ""), name=elem.get("name"))
        op.in_message_ref_id = elem.get("inMessageRef")
        op.out_message_ref_id = elem.get("outMessageRef")
        # Filter None
        op.error_ref_ids = [err_id for err in elem.findall("bpmn:errorRef", NS) if (err_id := err.get("id")) is not None]
        return op

    def _parse_item_definition(self, elem: ET.Element) -> ItemDefinition:
        kind_str = elem.get("itemKind", "Information")
        kind = self._map_item_kind(kind_str)
        return ItemDefinition(
            id=elem.get("id", ""),
            name=elem.get("name"),
            item_kind=kind,
            is_collection=elem.get("isCollection", "false") == "true",
        )

    def _parse_correlation_property(self, elem: ET.Element) -> CorrelationProperty:
        prop_type_str = elem.get("type", "key")
        prop_type = self._map_enum(CorrelationPropertyType, prop_type_str, CorrelationPropertyType.KEY)
        cp = CorrelationProperty(
            id=elem.get("id", ""),
            name=elem.get("name"),
            property_type=prop_type,
        )
        return cp

    def _parse_correlation_key(self, elem: ET.Element) -> CorrelationKey:
        key = CorrelationKey(id=elem.get("id", ""), name=elem.get("name"))
        # Filter None
        key.property_ref_ids = [pref_id for pref in elem.findall("bpmn:correlationPropertyRef", NS) if (pref_id := pref.get("id")) is not None]
        return key

    def _parse_correlation_subscription(self, elem: ET.Element) -> CorrelationSubscription:
        cs = CorrelationSubscription(id=elem.get("id", ""))
        cs.correlation_key_ref_id = elem.get("correlationKeyRef")
        return cs

    def _parse_io_specification(self, elem: ET.Element) -> InputOutputSpecification:
        ios = InputOutputSpecification(id=elem.get("id", ""), name=elem.get("name"))
        for di in elem.findall("bpmn:dataInput", NS):
            ios.data_inputs.append(self._parse_data_input(di))
        for do in elem.findall("bpmn:dataOutput", NS):
            ios.data_outputs.append(self._parse_data_output(do))
        return ios

    def _parse_standard_loop(self, elem: ET.Element) -> StandardLoopCharacteristics:
        loop = StandardLoopCharacteristics(id=elem.get("id", ""))
        loop.test_before = elem.get("testBefore", "false") == "true"
        loop_max = elem.get("loopMaximum")
        if loop_max is not None:
            loop.loop_maximum = int(loop_max)
        cond = elem.find("bpmn:loopCondition", NS)
        if cond is not None:
            loop.loop_condition = self._parse_expression(cond)
        return loop

    def _parse_multi_instance_loop(self, elem: ET.Element) -> MultiInstanceLoopCharacteristics:
        loop = MultiInstanceLoopCharacteristics(id=elem.get("id", ""))
        loop.is_sequential = elem.get("isSequential", "false") == "true"
        cond = elem.find("bpmn:completionCondition", NS)
        if cond is not None:
            loop.completion_condition = self._parse_expression(cond)
        card = elem.find("bpmn:loopCardinality", NS)
        if card is not None:
            loop.loop_cardinality = self._parse_expression(card)
        loop.loop_data_input_ref_id = elem.get("loopDataInputRef")
        loop.loop_data_output_ref_id = elem.get("loopDataOutputRef")
        behavior_str = elem.get("behavior", "All")
        loop.behavior = self._map_loop_behavior(behavior_str)
        return loop

    def _parse_auditing(self, elem: ET.Element) -> Auditing:
        aud = Auditing(id=elem.get("id", ""))
        aud.save_instances = elem.get("saveInstances", "false") == "true"
        aud.generate_trace_log = elem.get("generateTraceLog", "false") == "true"
        return aud

    def _parse_property(self, elem: ET.Element) -> Property:
        prop = Property(id=elem.get("id", ""), name=elem.get("name"))
        prop.item_subject_ref_id = elem.get("itemSubjectRef")
        return prop

    def _parse_artifact(self, elem: ET.Element) -> Optional[Artifact]:
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if tag == "association":
            assoc = Association(
                id=elem.get("id", ""),
                direction=self._map_association_direction(elem.get("associationDirection", "None")),
                source_ref=None,
                target_ref=None,
            )
            assoc.source_ref_id = elem.get("sourceRef")
            assoc.target_ref_id = elem.get("targetRef")
            return assoc
        elif tag == "textAnnotation":
            text_elem = elem.find("bpmn:text", NS)
            text = text_elem.text if text_elem is not None and text_elem.text is not None else ""
            return TextAnnotation(id=elem.get("id", ""), text=text)
        elif tag == "group":
            return Group(id=elem.get("id", ""))
        return None

    def _parse_participant(self, elem: ET.Element) -> Participant:
        part = Participant(id=elem.get("id", ""), name=elem.get("name"))
        part.process_ref_id = elem.get("processRef")
        mul = elem.find("bpmn:participantMultiplicity", NS)
        if mul is not None:
            part.participant_multiplicity = ParticipantMultiplicity(
                minimum=int(mul.get("minimum", "1")),
                maximum=int(mul.get("maximum", "0")),
            )
        return part

    def _parse_conversation_node(self, elem: ET.Element) -> ConversationNode:
        conv = ConversationNode(id=elem.get("id", ""), name=elem.get("name"))
        # Filter None
        conv.participant_ref_ids = [pref_id for pref in elem.findall("bpmn:participantRef", NS) if (pref_id := pref.get("id")) is not None]
        conv.message_flow_ref_ids = [mf_id for mf in elem.findall("bpmn:messageFlowRef", NS) if (mf_id := mf.get("id")) is not None]
        return conv

    def _parse_conversation_association(self, elem: ET.Element) -> ConversationAssociation:
        ca = ConversationAssociation(id=elem.get("id", ""))
        ca.inner_conversation_node_ref_id = elem.get("innerConversationNodeRef")
        # Filter None
        ca.outer_conversation_node_ref_ids = [outer_id for outer in elem.findall("bpmn:outerConversationNodeRef", NS) if (outer_id := outer.get("id")) is not None]
        return ca

    def _parse_conversation_link(self, elem: ET.Element) -> ConversationLink:
        link = ConversationLink(id=elem.get("id", ""))
        link.source_ref_id = elem.get("sourceRef")
        link.target_ref_id = elem.get("targetRef")
        return link

    def _parse_message_flow_association(self, elem: ET.Element) -> MessageFlowAssociation:
        mfa = MessageFlowAssociation(id=elem.get("id", ""))
        mfa.inner_message_flow_ref_id = elem.get("innerMessageFlowRef")
        mfa.outer_message_flow_ref_id = elem.get("outerMessageFlowRef")
        return mfa

    def _parse_participant_association(self, elem: ET.Element) -> ParticipantAssociation:
        pa = ParticipantAssociation(id=elem.get("id", ""))
        pa.inner_participant_ref_id = elem.get("innerParticipantRef")
        pa.outer_participant_ref_id = elem.get("outerParticipantRef")
        return pa

    def _parse_diagram(self, elem: ET.Element) -> BPMNDiagram:
        diagram = BPMNDiagram(
            id=elem.get("id", ""),
            name=elem.get("name"),
            model_element=None,
        )
        diagram.model_element_id = elem.get("bpmnElement")
        plane = elem.find("bpmndi:BPMNPlane", NS)
        if plane is not None:
            for shape in plane.findall("bpmndi:BPMNShape", NS):
                diagram.owned_elements.append(self._parse_bpmn_shape(shape))
            for edge in plane.findall("bpmndi:BPMNEdge", NS):
                diagram.owned_elements.append(self._parse_bpmn_edge(edge))
        return diagram

    def _parse_bpmn_shape(self, elem: ET.Element) -> BPMNShape:
        shape = BPMNShape(
            id=elem.get("id", ""),
            model_element=None,
            is_horizontal=elem.get("isHorizontal", "true") == "true",
            is_expanded=elem.get("isExpanded", "false") == "true",
            is_marker_visible=elem.get("isMarkerVisible", "false") == "true",
            is_message_visible=elem.get("isMessageVisible", "false") == "true",
        )
        shape.model_element_id = elem.get("bpmnElement")
        bounds = elem.find("dc:Bounds", NS)
        if bounds is not None:
            shape.bounds = Bounds(
                x=float(bounds.get("x", 0)),
                y=float(bounds.get("y", 0)),
                width=float(bounds.get("width", 0)),
                height=float(bounds.get("height", 0)),
            )
        label = elem.find("bpmndi:BPMNLabel", NS)
        if label is not None:
            shape.label = self._parse_bpmn_label(label)
        return shape

    def _parse_bpmn_edge(self, elem: ET.Element) -> BPMNEdge:
        edge = BPMNEdge(
            id=elem.get("id", ""),
            model_element=None,
        )
        edge.model_element_id = elem.get("bpmnElement")
        label = elem.find("bpmndi:BPMNLabel", NS)
        if label is not None:
            edge.label = self._parse_bpmn_label(label)
        return edge

    def _parse_bpmn_label(self, elem: ET.Element) -> BPMNLabel:
        text = elem.get("labelStyle", "")
        bounds = elem.find("dc:Bounds", NS)
        return BPMNLabel(
            text=text,
            bounds=Bounds(
                x=float(bounds.get("x", 0)) if bounds is not None else 0,
                y=float(bounds.get("y", 0)) if bounds is not None else 0,
                width=float(bounds.get("width", 0)) if bounds is not None else 0,
                height=float(bounds.get("height", 0)) if bounds is not None else 0,
            ),
            alignment=AlignmentKind.LEFT,
        )

    def _parse_resource_assignment_expression(self, elem: ET.Element) -> Optional[ResourceAssignmentExpression]:
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
        all_elements: Dict[str, BaseElement] = {}

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
        def get_obj(obj_id: str, elem_id: Optional[str] = None, ref_type: str = "") -> Optional[BaseElement]:
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
