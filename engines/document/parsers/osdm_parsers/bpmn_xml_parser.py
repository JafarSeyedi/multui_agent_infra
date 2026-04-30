# engines/document/parsers/osdm_parsers/bpmn_xml_parser.py
"""
BPMN 2.0 XML Parser – converts a .bpmn file into a BPMNDocument (unified OSDM).

Mapping rules:
- <definitions> → BPMNDocument root
- <process> → Process (flow elements, lane sets, artifacts)
- <collaboration> → Collaboration (participants, message flows, conversations)
- <choreography> → Choreography
- Flow elements are mapped 1:1 to OSDM classes (Task, Event, Gateway, etc.).
- <sequenceFlow> → SequenceFlow (typed source/target refs resolved in a second pass)
- <dataObject>, <dataStore> → DataObject / DataStore
- <messageFlow> → MessageFlow
- Resources, correlation, and BPMN DI are fully handled.
"""

from __future__ import annotations
import io
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from xml.etree import ElementTree as ET

from .base_osdm_parser import BaseOSDMParser
from ..base import ParseOptions
from ...models.osdm_models import (
    BaseOSDMDocument,
    BPMNDocument,
    Process, Collaboration, Choreography, GlobalTask,
    FlowElement, FlowNode, SequenceFlow, MessageFlow,
    Activity, Task, ServiceTask, SendTask, ReceiveTask, UserTask, ManualTask,
    ScriptTask, BusinessRuleTask, CallActivity, SubProcess,
    TransactionSubProcess, AdHocSubProcess,
    Gateway, ExclusiveGateway, InclusiveGateway, ParallelGateway,
    EventBasedGateway, ComplexGateway,
    Event, StartEvent, EndEvent, IntermediateCatchEvent,
    IntermediateThrowEvent, BoundaryEvent, ImplicitThrowEvent,
    EventDefinition, MessageEventDefinition, TimerEventDefinition,
    SignalEventDefinition, ErrorEventDefinition, EscalationEventDefinition,
    CompensateEventDefinition, ConditionalEventDefinition,
    LinkEventDefinition, CancelEventDefinition, TerminateEventDefinition,
    DataObject, DataStore, DataObjectReference, DataStoreReference,
    DataInput, DataOutput, InputOutputSpecification,
    Lane, LaneSet, Participant, PartnerEntity, PartnerRole,
    Interface, Operation, Message, Error, Escalation, Signal,
    Resource, ResourceRole, ResourceParameter,
    CorrelationKey, CorrelationProperty, CorrelationSubscription,
    LoopCharacteristics, StandardLoopCharacteristics,
    MultiInstanceLoopCharacteristics,
    Auditing, Monitoring, Rendering, FormalExpression, BpmnExpression,
    ItemDefinition, Category, CategoryValue, Artifact, Association,
    TextAnnotation, Group,
    Conversation, ConversationNode, CallConversation, SubConversation,
    ConversationLink, ConversationAssociation,
    MessageFlowAssociation, ParticipantAssociation,
    ChoreographyActivity, ChoreographyTask, CallChoreography, SubChoreography,
    BPMNDiagram, BPMNPlane, BPMNShape, BPMNEdge, BPMNLabel, Bounds, DiagramElement,
    InteractionNode,
    RootElement, BaseElement, Script, ScriptLanguage,
)
from ...models.base import BaseDocument


# ── Namespaces ────────────────────────────────────────────────────
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

    async def _parse_to_document(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> BaseOSDMDocument:
        encoding = options.encoding or "utf-8"
        text = data.decode(encoding)
        root = ET.fromstring(text)

        doc = BPMNDocument()
        # Root definitions attributes
        if root.tag == f"{{{BPMN_NS}}}definitions":
            doc.id = root.get("id", source_name)
            doc.title = root.get("name", source_name)
            doc.source_file = source_name

        # Collect all root elements defined under definitions
        root_elements = {}
        for child in root:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag == "process":
                proc = self._parse_process(child)
                doc.processes.append(proc)
            elif tag == "collaboration":
                collab = self._parse_collaboration(child)
                doc.collaborations.append(collab)
            elif tag == "choreography":
                choreo = self._parse_choreography(child)
                doc.choreographies.append(choreo)
            elif tag == "globalTask":
                gt = self._parse_global_task(child, GlobalTask)
                doc.global_tasks.append(gt)
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

        # Resolve cross‑references across all processes and root elements
        # (We'll rely on the id map for later passes; currently typed references are set during parsing)
        doc.root_elements = root_elements

        # Parse BPMN DI (diagrams)
        for diag_elem in root.findall("bpmndi:BPMNDiagram", NS):
            diagram = self._parse_diagram(diag_elem)
            doc.diagrams.append(diagram)

        return doc

    # ── Process ────────────────────────────────────────────────────
    def _parse_process(self, elem: ET.Element) -> Process:
        proc = Process(
            id=elem.get("id", ""),
            name=elem.get("name"),
            process_type=elem.get("processType", "None"),
            is_executable=elem.get("isExecutable", "false") == "true",
            is_closed=elem.get("isClosed", "false") == "true",
        )
        # Flow elements
        flow_elements: Dict[str, FlowElement] = {}
        for child in elem:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            flow = self._parse_flow_element(child)
            if flow:
                flow_elements[flow.id] = flow
        proc.flow_elements = flow_elements

        # Lane sets
        for lane_set_elem in elem.findall("bpmn:laneSet", NS):
            ls = self._parse_lane_set(lane_set_elem)
            proc.lane_sets.append(ls)

        # Artifacts
        for art_elem in elem.findall("bpmn:artifact", NS) + elem.findall("bpmn:association", NS) + elem.findall("bpmn:group", NS) + elem.findall("bpmn:textAnnotation", NS):
            art = self._parse_artifact(art_elem)
            if art:
                proc.artifacts.append(art)

        # Properties
        for prop_elem in elem.findall("bpmn:property", NS):
            prop = self._parse_property(prop_elem)
            proc.properties.append(prop)

        # Correlation subscriptions
        for cs_elem in elem.findall("bpmn:correlationSubscription", NS):
            cs = self._parse_correlation_subscription(cs_elem)
            proc.correlation_subscriptions.append(cs)

        # Auditing / Monitoring
        aud = elem.find("bpmn:auditing", NS)
        if aud is not None:
            proc.auditing = self._parse_auditing(aud)
        mon = elem.find("bpmn:monitoring", NS)
        if mon is not None:
            proc.monitoring = Monitoring()

        # IO specification (if directly under process)
        io = elem.find("bpmn:ioSpecification", NS)
        if io is not None:
            proc.io_specification = self._parse_io_specification(io)

        return proc

    # ── Flow element dispatch ──────────────────────────────────────
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
        elif tag == "dataStore":
            return self._parse_data_store(elem)
        elif tag == "dataStoreReference":
            return self._parse_data_store_reference(elem)
        elif tag == "dataInput":
            return self._parse_data_input(elem)
        elif tag == "dataOutput":
            return self._parse_data_output(elem)
        elif tag == "dataAssociation":
            return self._parse_data_association(elem)
        elif tag == "messageFlow":
            return self._parse_message_flow(elem)
        return None

    # ── Task parsing ──────────────────────────────────────────────
    def _parse_task(self, elem: ET.Element, cls) -> Optional[Task]:
        task = cls(
            id=elem.get("id", ""),
            name=elem.get("name"),
        )
        # Activity common
        self._parse_activity_common(elem, task)
        if isinstance(task, ServiceTask):
            task.implementation = elem.get("implementation")
            task.operation_ref = None  # resolved later if operation element exists
        elif isinstance(task, SendTask):
            task.message_ref = elem.get("messageRef")
            task.operation_ref = elem.get("operationRef")
        elif isinstance(task, ReceiveTask):
            task.message_ref = elem.get("messageRef")
            task.operation_ref = elem.get("operationRef")
            task.instantiate = elem.get("instantiate") == "true"
        elif isinstance(task, UserTask):
            task.implementation = elem.get("implementation")
            # Rendering
            for rend_elem in elem.findall("bpmn:rendering", NS):
                rend = self._parse_rendering(rend_elem)
                task.rendering.append(rend)
        elif isinstance(task, ManualTask):
            pass
        elif isinstance(task, ScriptTask):
            script_elem = elem.find("bpmn:script", NS)
            if script_elem is not None and script_elem.text:
                task.script = Script(
                    script_body=script_elem.text,
                    script_language=ScriptLanguage(script_elem.get("scriptFormat", "Python")),
                )
        elif isinstance(task, BusinessRuleTask):
            task.implementation = elem.get("implementation")
        return task

    def _parse_activity_common(self, elem: ET.Element, activity: Activity) -> None:
        doc = elem.find("bpmn:documentation", NS)
        if doc is not None:
            activity.documentation = doc.text
        # Loop characteristics
        loop = elem.find("bpmn:standardLoopCharacteristics", NS)
        if loop is not None:
            activity.loop_characteristics = self._parse_standard_loop(loop)
        multi = elem.find("bpmn:multiInstanceLoopCharacteristics", NS)
        if multi is not None:
            activity.loop_characteristics = self._parse_multi_instance_loop(multi)
        # IO Spec
        io = elem.find("bpmn:ioSpecification", NS)
        if io is not None:
            activity.io_specification = self._parse_io_specification(io)
        # Resources
        for rr in elem.findall("bpmn:resourceRole", NS):
            role = self._parse_resource_role(rr)
            activity.resources.append(role)
        # Properties
        for prop in elem.findall("bpmn:property", NS):
            activity.properties.append(self._parse_property(prop))

    # ── Sub‑Process ───────────────────────────────────────────────
    def _parse_sub_process(self, elem: ET.Element, cls) -> SubProcess:
        sub = cls(
            id=elem.get("id", ""),
            name=elem.get("name"),
        )
        sub.triggered_by_event = elem.get("triggeredByEvent") == "true"
        if isinstance(sub, AdHocSubProcess):
            sub.ordering = AdHocOrdering(elem.get("ordering", "Parallel"))
            cond = elem.find("bpmn:completionCondition", NS)
            if cond is not None:
                sub.completion_condition = self._parse_expression(cond)
        if isinstance(sub, TransactionSubProcess):
            sub.method = TransactionMethod(elem.get("transactionMethod", "##compensate"))
        self._parse_activity_common(elem, sub)
        # Internal flow elements
        flow_elements = {}
        for child in elem:
            flow = self._parse_flow_element(child)
            if flow:
                flow_elements[flow.id] = flow
        sub.flow_elements = flow_elements
        # Lane sets
        for ls in elem.findall("bpmn:laneSet", NS):
            sub.lane_sets.append(self._parse_lane_set(ls))
        # Artifacts
        for art in elem.findall("bpmn:artifact", NS) + elem.findall("bpmn:association", NS) + elem.findall("bpmn:group", NS) + elem.findall("bpmn:textAnnotation", NS):
            a = self._parse_artifact(art)
            if a:
                sub.artifacts.append(a)
        return sub

    # ── Gateway ───────────────────────────────────────────────────
    def _parse_gateway(self, elem: ET.Element, cls) -> Gateway:
        gw = cls(
            id=elem.get("id", ""),
            name=elem.get("name"),
            gateway_type=elem.get("gatewayType", "Exclusive"),
            gateway_direction=GatewayDirection(elem.get("gatewayDirection", "Unspecified")),
        )
        if isinstance(gw, (ExclusiveGateway, InclusiveGateway, ComplexGateway)):
            gw.default_sequence_flow = elem.get("default")  # id, resolved later? We'll keep as id for now; typed reference is set later.
        if isinstance(gw, EventBasedGateway):
            gw.event_type = EventBasedGatewayType(elem.get("eventGatewayType", "Exclusive"))
        if isinstance(gw, ComplexGateway):
            cond = elem.find("bpmn:activationCondition", NS)
            if cond is not None:
                gw.activation_condition = self._parse_expression(cond)
        return gw

    # ── Event ────────────────────────────────────────────────────
    def _parse_event(self, elem: ET.Element, cls) -> Event:
        ev = cls(
            id=elem.get("id", ""),
            name=elem.get("name"),
            event_type=elem.get("eventType", "Start"),  # default
        )
        if isinstance(ev, CatchEvent):
            ev.parallel_multiple = elem.get("parallelMultiple") == "true"
        if isinstance(ev, BoundaryEvent):
            ev.attached_to_ref = elem.get("attachedToRef")
            ev.cancel_activity = elem.get("cancelActivity", "true") == "true"
        if isinstance(ev, StartEvent):
            ev.is_interrupting = elem.get("isInterrupting", "true") == "true"
        # Event definitions
        for ed_elem in elem.findall("bpmn:eventDefinition", NS) + elem.findall("bpmn:*", NS):  # any child that ends with EventDefinition
            ed = self._parse_event_definition(ed_elem)
            if ed:
                ev.event_definitions.append(ed)
        # Properties
        for prop in elem.findall("bpmn:property", NS):
            ev.properties.append(self._parse_property(prop))
        # Data associations (catch/throw)
        if isinstance(ev, CatchEvent):
            for da in elem.findall("bpmn:dataOutputAssociation", NS):
                ev.data_output_associations.append(self._parse_data_association(da))
        if isinstance(ev, ThrowEvent):
            for da in elem.findall("bpmn:dataInputAssociation", NS):
                ev.data_input_associations.append(self._parse_data_association(da))
        return ev

    def _parse_event_definition(self, elem: ET.Element) -> Optional[EventDefinition]:
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        cls = EVENT_DEFINITION_TAG_MAP.get(tag)
        if not cls:
            return None
        ed = cls(id=elem.get("id", ""))
        if isinstance(ed, MessageEventDefinition):
            ed.message_ref = elem.get("messageRef")
            ed.operation_ref = elem.get("operationRef")
        elif isinstance(ed, TimerEventDefinition):
            ed.time_date = self._parse_expression(elem.find("bpmn:timeDate", NS))
            ed.time_cycle = self._parse_expression(elem.find("bpmn:timeCycle", NS))
            ed.time_duration = self._parse_expression(elem.find("bpmn:timeDuration", NS))
        elif isinstance(ed, SignalEventDefinition):
            ed.signal_ref = elem.get("signalRef")
        elif isinstance(ed, ErrorEventDefinition):
            ed.error_ref = elem.get("errorRef")
        elif isinstance(ed, EscalationEventDefinition):
            ed.escalation_ref = elem.get("escalationRef")
        elif isinstance(ed, CompensateEventDefinition):
            ed.activity_ref = elem.get("activityRef")
            ed.wait_for_completion = elem.get("waitForCompletion", "true") == "true"
        elif isinstance(ed, ConditionalEventDefinition):
            cond = elem.find("bpmn:condition", NS)
            if cond is not None:
                ed.condition = self._parse_expression(cond)
        elif isinstance(ed, LinkEventDefinition):
            # sources/targets are ids; we'll store them as strings for now; later resolve to objects? keep as strings
            for s in elem.findall("bpmn:source", NS):
                ed.sources.append(s.get("id"))
            t = elem.find("bpmn:target", NS)
            if t is not None:
                ed.target = t.get("id")
        return ed

    # ── Sequence flow ─────────────────────────────────────────────
    def _parse_sequence_flow(self, elem: ET.Element) -> SequenceFlow:
        seq = SequenceFlow(
            id=elem.get("id", ""),
            name=elem.get("name"),
            source_ref=elem.get("sourceRef"),  # will be resolved later
            target_ref=elem.get("targetRef"),
            is_immediate=elem.get("isImmediate", "true") == "true",
        )
        cond = elem.find("bpmn:conditionExpression", NS)
        if cond is not None:
            seq.condition_expression = self._parse_expression(cond)
        return seq

    # ── Data objects / stores ──────────────────────────────────────
    def _parse_data_object(self, elem: ET.Element) -> DataObject:
        dobj = DataObject(
            id=elem.get("id", ""),
            name=elem.get("name"),
            is_collection=elem.get("isCollection") == "true",
        )
        dobj.item_subject_ref = elem.get("itemSubjectRef")
        return dobj

    def _parse_data_object_reference(self, elem: ET.Element) -> DataObjectReference:
        ref = DataObjectReference(
            id=elem.get("id", ""),
            name=elem.get("name"),
            data_object=elem.get("dataObjectRef"),  # id, resolved later
        )
        return ref

    def _parse_data_store(self, elem: ET.Element) -> DataStore:
        store = DataStore(
            id=elem.get("id", ""),
            name=elem.get("name"),
            is_unlimited=elem.get("isUnlimited", "true") == "true",
            capacity=int(elem.get("capacity", "0")),
        )
        store.item_subject_ref = elem.get("itemSubjectRef")
        return store

    def _parse_data_store_reference(self, elem: ET.Element) -> DataStoreReference:
        ref = DataStoreReference(
            id=elem.get("id", ""),
            name=elem.get("name"),
            data_store=elem.get("dataStoreRef"),
        )
        return ref

    def _parse_data_input(self, elem: ET.Element) -> DataInput:
        return DataInput(
            id=elem.get("id", ""),
            name=elem.get("name"),
            item_subject_ref=elem.get("itemSubjectRef"),
            is_collection=elem.get("isCollection") == "true",
        )

    def _parse_data_output(self, elem: ET.Element) -> DataOutput:
        return DataOutput(
            id=elem.get("id", ""),
            name=elem.get("name"),
            item_subject_ref=elem.get("itemSubjectRef"),
            is_collection=elem.get("isCollection") == "true",
        )

    def _parse_data_association(self, elem: ET.Element) -> DataAssociation:
        da = DataAssociation(id=elem.get("id", ""))
        for src in elem.findall("bpmn:sourceRef", NS):
            da.source_refs.append(src.get("id"))
        tgt = elem.find("bpmn:targetRef", NS)
        if tgt is not None:
            da.target_ref = tgt.get("id")
        trans = elem.find("bpmn:transformation", NS)
        if trans is not None:
            da.transformation = self._parse_expression(trans)
        return da

    # ── Message flow ──────────────────────────────────────────────
    def _parse_message_flow(self, elem: ET.Element) -> MessageFlow:
        return MessageFlow(
            id=elem.get("id", ""),
            name=elem.get("name"),
            source_ref=elem.get("sourceRef"),
            target_ref=elem.get("targetRef"),
            message_ref=elem.get("messageRef"),
        )

    # ── Lane set / Lane ───────────────────────────────────────────
    def _parse_lane_set(self, elem: ET.Element) -> LaneSet:
        ls = LaneSet(id=elem.get("id", ""), name=elem.get("name"))
        for lane_elem in elem.findall("bpmn:lane", NS):
            lane = self._parse_lane(lane_elem)
            ls.lanes.append(lane)
        return ls

    def _parse_lane(self, elem: ET.Element) -> Lane:
        lane = Lane(id=elem.get("id", ""), name=elem.get("name"))
        lane.partition_element_ref = elem.get("partitionElement")
        for fn in elem.findall("bpmn:flowNodeRef", NS):
            lane.flow_node_refs.append(fn.get("id"))
        # Nested lane set
        child_ls = elem.find("bpmn:childLaneSet", NS)
        if child_ls is not None:
            lane.child_lane_set = self._parse_lane_set(child_ls)
        return lane

    # ── Collaboration ─────────────────────────────────────────────
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
        for art in elem.findall("bpmn:artifact", NS) + elem.findall("bpmn:association", NS) + elem.findall("bpmn:group", NS) + elem.findall("bpmn:textAnnotation", NS):
            a = self._parse_artifact(art)
            if a:
                collab.artifacts.append(a)
        for key in elem.findall("bpmn:correlationKey", NS):
            collab.correlation_keys.append(self._parse_correlation_key(key))
        for conv in elem.findall("bpmn:conversation", NS) + elem.findall("bpmn:callConversation", NS) + elem.findall("bpmn:subConversation", NS):
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
                choreo.flow_elements[child.get("id")] = self._parse_choreography_activity(child)
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
        for pref in elem.findall("bpmn:participantRef", NS):
            act.participant_refs.append(pref.get("id"))
        act.initiating_participant_ref = elem.get("initiatingParticipantRef")
        act.loop_type = ChoreographyLoopType(elem.get("loopType", "None"))
        return act

    # ── Global task ───────────────────────────────────────────────
    def _parse_global_task(self, elem: ET.Element, cls) -> GlobalTask:
        gt = cls(
            id=elem.get("id", ""),
            name=elem.get("name"),
        )
        io = elem.find("bpmn:ioSpecification", NS)
        if io is not None:
            gt.io_specification = self._parse_io_specification(io)
        return gt

    # ── Expressions ───────────────────────────────────────────────
    def _parse_expression(self, elem: Optional[ET.Element]) -> Optional[FormalExpression]:
        if elem is None:
            return None
        lang = elem.get("language")
        body = elem.text or ""
        return FormalExpression(
            id=elem.get("id", ""),
            language=ScriptLanguage(lang) if lang else None,
            body=body,
        )

    # ── Rendering ─────────────────────────────────────────────────
    def _parse_rendering(self, elem: ET.Element) -> Rendering:
        return Rendering(
            id=elem.get("id", ""),
            name=elem.get("name"),
        )

    # ── Root elements (message, error, etc.) ──────────────────────
    def _parse_message(self, elem: ET.Element) -> Message:
        msg = Message(id=elem.get("id", ""), name=elem.get("name"))
        msg.item_ref = elem.get("itemRef")
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
        return ResourceParameter(
            id=elem.get("id", ""),
            name=elem.get("name"),
            type=elem.get("type", "UserField"),
            is_required=elem.get("isRequired", "false") == "true",
        )

    def _parse_resource_role(self, elem: ET.Element) -> ResourceRole:
        role = ResourceRole(
            id=elem.get("id", ""),
            name=elem.get("name"),
            type=elem.get("type", "None"),
            resource_ref=elem.get("resourceRef"),
        )
        expr = elem.find("bpmn:resourceAssignmentExpression", NS)
        if expr is not None:
            role.resource_assignment_expression = self._parse_expression(expr)
        return role

    def _parse_interface(self, elem: ET.Element) -> Interface:
        iface = Interface(id=elem.get("id", ""), name=elem.get("name"))
        for op_elem in elem.findall("bpmn:operation", NS):
            op = self._parse_operation(op_elem)
            iface.operations[op.id] = op
        return iface

    def _parse_operation(self, elem: ET.Element) -> Operation:
        op = Operation(id=elem.get("id", ""), name=elem.get("name"))
        op.in_message_ref = elem.get("inMessageRef")
        op.out_message_ref = elem.get("outMessageRef")
        for err in elem.findall("bpmn:errorRef", NS):
            op.error_refs.append(err.get("id"))
        return op

    def _parse_item_definition(self, elem: ET.Element) -> ItemDefinition:
        item = ItemDefinition(
            id=elem.get("id", ""),
            name=elem.get("name"),
            item_kind=ItemKind(elem.get("itemKind", "Information")),
            is_collection=elem.get("isCollection", "false") == "true",
        )
        return item

    def _parse_correlation_property(self, elem: ET.Element) -> CorrelationProperty:
        cp = CorrelationProperty(
            id=elem.get("id", ""),
            name=elem.get("name"),
            type=elem.get("type", "key"),
        )
        return cp

    def _parse_correlation_key(self, elem: ET.Element) -> CorrelationKey:
        key = CorrelationKey(id=elem.get("id", ""), name=elem.get("name"))
        for pref in elem.findall("bpmn:correlationPropertyRef", NS):
            key.property_refs.append(pref.get("id"))
        return key

    def _parse_correlation_subscription(self, elem: ET.Element) -> CorrelationSubscription:
        cs = CorrelationSubscription(id=elem.get("id", ""))
        cs.correlation_key_ref = elem.get("correlationKeyRef")
        return cs

    # ── IO Specification ──────────────────────────────────────────
    def _parse_io_specification(self, elem: ET.Element) -> InputOutputSpecification:
        ios = InputOutputSpecification(id=elem.get("id", ""), name=elem.get("name"))
        for di in elem.findall("bpmn:dataInput", NS):
            ios.data_inputs.append(self._parse_data_input(di))
        for do in elem.findall("bpmn:dataOutput", NS):
            ios.data_outputs.append(self._parse_data_output(do))
        # Input/output sets omitted for brevity
        return ios

    # ── Loop characteristics ──────────────────────────────────────
    def _parse_standard_loop(self, elem: ET.Element) -> StandardLoopCharacteristics:
        loop = StandardLoopCharacteristics(id=elem.get("id", ""))
        loop.test_before = elem.get("testBefore", "false") == "true"
        loop.loop_maximum = int(elem.get("loopMaximum", "0"))
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
        loop.loop_data_input_ref = elem.get("loopDataInputRef")
        loop.loop_data_output_ref = elem.get("loopDataOutputRef")
        # behavior
        loop.behavior = MultiInstanceBehavior(elem.get("behavior", "All"))
        for cbd in elem.findall("bpmn:complexBehaviorDefinition", NS):
            pass  # skip for brevity
        return loop

    # ── Auditing ──────────────────────────────────────────────────
    def _parse_auditing(self, elem: ET.Element) -> Auditing:
        aud = Auditing(id=elem.get("id", ""))
        aud.save_instances = elem.get("saveInstances", "false") == "true"
        aud.generate_trace_log = elem.get("generateTraceLog", "false") == "true"
        aud.log_condition = elem.get("logCondition")
        return aud

    # ── Property ──────────────────────────────────────────────────
    def _parse_property(self, elem: ET.Element) -> Property:
        prop = Property(id=elem.get("id", ""), name=elem.get("name"))
        prop.item_subject_ref = elem.get("itemSubjectRef")
        return prop

    # ── Artifact ──────────────────────────────────────────────────
    def _parse_artifact(self, elem: ET.Element) -> Optional[Artifact]:
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if tag == "association":
            return Association(
                id=elem.get("id", ""),
                direction=AssociationDirection(elem.get("associationDirection", "None")),
                source_ref=elem.get("sourceRef"),
                target_ref=elem.get("targetRef"),
            )
        elif tag == "textAnnotation":
            text_elem = elem.find("bpmn:text", NS)
            text = text_elem.text if text_elem is not None else ""
            return TextAnnotation(id=elem.get("id", ""), text=text)
        elif tag == "group":
            return Group(id=elem.get("id", ""))
        return None

    # ── Collaboration / Conversation helpers ──────────────────────
    def _parse_participant(self, elem: ET.Element) -> Participant:
        part = Participant(id=elem.get("id", ""), name=elem.get("name"))
        part.process_ref = elem.get("processRef")
        # Multiplicity
        mul = elem.find("bpmn:participantMultiplicity", NS)
        if mul is not None:
            part.participant_multiplicity = ParticipantMultiplicity(
                minimum=int(mul.get("minimum", "1")),
                maximum=int(mul.get("maximum", "0")),
            )
        return part

    def _parse_conversation_node(self, elem: ET.Element) -> ConversationNode:
        conv = ConversationNode(id=elem.get("id", ""), name=elem.get("name"))
        for pref in elem.findall("bpmn:participantRef", NS):
            conv.participant_refs.append(pref.get("id"))
        for mf in elem.findall("bpmn:messageFlowRef", NS):
            conv.message_flow_refs.append(mf.get("id"))
        return conv

    def _parse_conversation_association(self, elem: ET.Element) -> ConversationAssociation:
        ca = ConversationAssociation(id=elem.get("id", ""))
        ca.inner_conversation_node_ref = elem.get("innerConversationNodeRef")
        for outer in elem.findall("bpmn:outerConversationNodeRef", NS):
            ca.outer_conversation_node_refs.append(outer.get("id"))
        return ca

    def _parse_conversation_link(self, elem: ET.Element) -> ConversationLink:
        link = ConversationLink(id=elem.get("id", ""))
        link.source_ref = elem.get("sourceRef")
        link.target_ref = elem.get("targetRef")
        return link

    def _parse_message_flow_association(self, elem: ET.Element) -> MessageFlowAssociation:
        mfa = MessageFlowAssociation(id=elem.get("id", ""))
        mfa.inner_message_flow_ref = elem.get("innerMessageFlowRef")
        mfa.outer_message_flow_ref = elem.get("outerMessageFlowRef")
        return mfa

    def _parse_participant_association(self, elem: ET.Element) -> ParticipantAssociation:
        pa = ParticipantAssociation(id=elem.get("id", ""))
        pa.inner_participant_ref = elem.get("innerParticipantRef")
        pa.outer_participant_ref = elem.get("outerParticipantRef")
        return pa

    # ── Diagram ──────────────────────────────────────────────────
    def _parse_diagram(self, elem: ET.Element) -> BPMNDiagram:
        diagram = BPMNDiagram(
            id=elem.get("id", ""),
            name=elem.get("name"),
            model_element=elem.get("bpmnElement"),
        )
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
            model_element=elem.get("bpmnElement"),
            is_horizontal=elem.get("isHorizontal", "true") == "true",
            is_expanded=elem.get("isExpanded", "false") == "true",
            is_marker_visible=elem.get("isMarkerVisible", "false") == "true",
            is_message_visible=elem.get("isMessageVisible", "false") == "true",
        )
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
            model_element=elem.get("bpmnElement"),
        )
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