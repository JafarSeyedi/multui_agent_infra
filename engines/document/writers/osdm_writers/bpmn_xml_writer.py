# engines/document/writers/osdm_writers/bpmn_xml_writer.py
"""
BPMN 2.0 XML Writer – serialises an BPMNDocument into BPMN 2.0 XML.

Handles every BPMN element: processes, collaborations, choreographies,
events, gateways, tasks, data, resources, correlation, and diagrams.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, cast
from xml.etree.ElementTree import Element, SubElement, tostring

from ...models.msdm_models import MSDMDocument
from ...models.osdm_models import (
    Activity, AdHocSubProcess, Artifact, Association, Auditing,
    BaseElement, BaseOSDMDocument, BoundaryEvent, BPMNDiagram, BPMNDocument,
    BPMNEdge, BPMNLabel, BPMNShape, BusinessRuleTask, CallActivity,
    CallConversation, CatchEvent, Choreography, ChoreographyActivity,
    Collaboration, CompensateEventDefinition, ComplexGateway,
    ConditionalEventDefinition, ConversationAssociation, ConversationLink,
    ConversationNode, CorrelationKey, CorrelationSubscription, DataAssociation,
    DataInput, DataObject, DataObjectReference, DataOutput, DataStore,
    DataStoreReference, Error, ErrorEventDefinition, Escalation,
    EscalationEventDefinition, Event, EventBasedGateway, EventDefinition,
    ExclusiveGateway, FlowElement, FormalExpression, Gateway,
    GlobalBusinessRuleTask, GlobalManualTask, GlobalScriptTask, GlobalTask,
    GlobalUserTask, Group, InclusiveGateway, InputOutputSpecification,
    InteractionNode, Lane, LaneSet, LinkEventDefinition, LoopCharacteristics,
    ManualTask, Message, MessageEventDefinition, MessageFlow,
    MessageFlowAssociation, Monitoring, MultiInstanceLoopCharacteristics,
    Participant, ParticipantAssociation, Process, Property, ReceiveTask,
    Rendering, RenderingForm, Resource, ResourceRole, ScriptTask, SendTask,
    SequenceFlow, ServiceTask, Signal, SignalEventDefinition,
    StandardLoopCharacteristics, StartEvent, SubConversation, SubProcess, Task,
    TextAnnotation, ThrowEvent, TimerEventDefinition, TransactionSubProcess,
    UserTask,
)
from ...models.ssdm_models import SSDMDocument 
from ...models.tsdm_models import TSDMDocument
from .base_osdm_writer import BaseOSDMWriter, OSDMWriteOptions

# Namespaces
BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
BPMN_DI_NS = "http://www.omg.org/spec/BPMN/20100524/DI"
DI_NS = "http://www.omg.org/spec/DD/20100524/DI"
DC_NS = "http://www.omg.org/spec/DD/20100524/DC"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"


class BPMNXMLWriter(BaseOSDMWriter):
    """Serialises a BPMNDocument to BPMN 2.0 XML."""

    name = "bpmn_xml"
    supported_extensions = (".bpmn", ".bpmn2")

    def __init__(self, options: OSDMWriteOptions | None = None):
        super().__init__(options)
        self._id_map: dict[str, str] = {}
        self._next_internal_id = 0

    # Public API
    async def _write_design(self, base_document: BaseOSDMDocument) -> bytes:
        document = cast(BPMNDocument, base_document)

        root = Element(f"{{{BPMN_NS}}}definitions", {
            "xmlns": BPMN_NS,
            "xmlns:bpmndi": BPMN_DI_NS,
            "xmlns:di": DI_NS,
            "xmlns:dc": DC_NS,
            "xmlns:xsi": XSI_NS,
            "id": self._get_or_create_id(base_document),
            "name": base_document.title or "definitions",
        })

        if document.version:
            root.set("exporterVersion", document.version)

        # Optional imports and relationships (if present in the model)
        # These attributes may not exist; we check safely
        if hasattr(base_document, "imports"):
            for imp in base_document.imports:
                SubElement(root, f"{{{BPMN_NS}}}import", {
                    "importType": imp.import_type,
                    "location": imp.location,
                    "namespace": imp.namespace or "",
                })
        if hasattr(base_document, "relationships"):
            for rel in base_document.relationships:
                rel_elem = self._add_bpmn_element(root, "relationship", None,
                                                  type=rel.type, direction=rel.direction.value)
                for src in rel.sources:
                    SubElement(rel_elem, f"{{{BPMN_NS}}}source", {"id": src})
                for tgt in rel.targets:
                    SubElement(rel_elem, f"{{{BPMN_NS}}}target", {"id": tgt})

        # Top‑level elements
        for process in document.processes:
            self._write_process(root, process)
        for collaboration in document.collaborations:
            self._write_collaboration(root, collaboration)
        for choreography in document.choreographies:
            self._write_choreography(root, choreography)
        for global_task in document.global_tasks:
            self._write_global_task(root, global_task)

        # Core root elements (Messages, Errors, Signals, etc.)
        for re_obj in document.root_elements.values():
            self._write_root_element(root, re_obj)

        # Diagrams
        if self.osdm_options.include_diagrams:
            for diagram in base_document.diagrams:
                self._write_diagram(root, diagram)

        xml_bytes = tostring(root, encoding="unicode", method="xml")
        return xml_bytes.encode(getattr(self.options, "encoding", "utf-8") or "utf-8")

    def get_supported_media_types(self) -> list[str]:
        return ["application/xml"]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    # ID mapping – now accepts any object with an `id` attribute
    def _obj_id(self, obj: Any) -> str:
        if hasattr(obj, "id"):
            return obj.id
        return str(id(obj))

    def _add_bpmn_element(self, parent: Element, tag: str, obj: Any = None, **attrs) -> Element:
        """Create a BPMN element and set its id from obj if provided."""
        if obj is not None:
            attrs.setdefault("id", self._obj_id(obj))
        return SubElement(parent, f"{{{BPMN_NS}}}{tag}", attrs)

    # Process
    def _write_process(self, root: Element, process: Process) -> None:
        proc_elem = self._add_bpmn_element(root, "process", process,
                                           processType=process.process_type.value if process.process_type else None,
                                           isExecutable=str(process.is_executable).lower() if process.is_executable else None,
                                           isClosed=str(process.is_closed).lower() if process.is_closed else None)
        if process.name:
            proc_elem.set("name", process.name)
        self._write_auditing(proc_elem, process.auditing)
        self._write_monitoring(proc_elem, process.monitoring)

        for lane_set in process.lane_sets:
            self._write_lane_set(proc_elem, lane_set)
        for flow in process.flow_elements.values():
            self._write_flow_element(proc_elem, flow)
        for artifact in process.artifacts:
            self._write_artifact(proc_elem, artifact)
        for prop in process.properties:
            self._write_property(proc_elem, prop)
        for sub in process.correlation_subscriptions:
            self._write_correlation_subscription(proc_elem, sub)
        if process.io_specification:
            self._write_io_specification(proc_elem, process.io_specification)

    # Flow elements dispatch
    def _write_flow_element(self, parent: Element, flow: FlowElement) -> None:
        if isinstance(flow, Task):
            if isinstance(flow, ServiceTask):
                self._write_service_task(parent, flow)
            elif isinstance(flow, SendTask):
                self._write_send_task(parent, flow)
            elif isinstance(flow, ReceiveTask):
                self._write_receive_task(parent, flow)
            elif isinstance(flow, UserTask):
                self._write_user_task(parent, flow)
            elif isinstance(flow, ManualTask):
                self._write_manual_task(parent, flow)
            elif isinstance(flow, ScriptTask):
                self._write_script_task(parent, flow)
            elif isinstance(flow, BusinessRuleTask):
                self._write_business_rule_task(parent, flow)
            else:
                self._write_task(parent, flow)
        elif isinstance(flow, SubProcess):
            self._write_sub_process(parent, flow)
        elif isinstance(flow, CallActivity):
            self._write_call_activity(parent, flow)
        elif isinstance(flow, Gateway):
            self._write_gateway(parent, flow)
        elif isinstance(flow, Event):
            self._write_event(parent, flow)
        elif isinstance(flow, SequenceFlow):
            self._write_sequence_flow(parent, flow)
        elif isinstance(flow, DataObject):
            self._write_data_object(parent, flow)
        elif isinstance(flow, DataObjectReference):
            self._write_data_object_reference(parent, flow)
        elif isinstance(flow, DataStore):
            self._write_data_store(parent, flow)
        elif isinstance(flow, DataStoreReference):
            self._write_data_store_reference(parent, flow)
        elif isinstance(flow, DataInput):
            self._write_data_input(parent, flow)
        elif isinstance(flow, DataOutput):
            self._write_data_output(parent, flow)
        elif isinstance(flow, DataAssociation):
            self._write_data_association(parent, flow)
        elif isinstance(flow, Artifact):
            self._write_artifact(parent, flow)
        # else unknown – ignore

    # Task subtypes
    def _write_task(self, parent: Element, task: Task) -> None:
        elem = self._add_bpmn_element(parent, "task", task, name=task.name or "")
        self._write_activity_common(elem, task)

    def _write_service_task(self, parent: Element, task: ServiceTask) -> None:
        elem = self._add_bpmn_element(parent, "serviceTask", task, name=task.name or "")
        elem.set("implementation", task.implementation if isinstance(task.implementation, str) else "##unspecified")
        if task.operation_ref:
            elem.set("operationRef", self._obj_id(task.operation_ref))
        self._write_activity_common(elem, task)

    def _write_send_task(self, parent: Element, task: SendTask) -> None:
        elem = self._add_bpmn_element(parent, "sendTask", task, name=task.name or "")
        elem.set("implementation", task.implementation if isinstance(task.implementation, str) else "##unspecified")
        if task.message_ref:
            elem.set("messageRef", self._obj_id(task.message_ref))
        if task.operation_ref:
            elem.set("operationRef", self._obj_id(task.operation_ref))
        self._write_activity_common(elem, task)

    def _write_receive_task(self, parent: Element, task: ReceiveTask) -> None:
        elem = self._add_bpmn_element(parent, "receiveTask", task, name=task.name or "")
        elem.set("implementation", task.implementation if isinstance(task.implementation, str) else "##unspecified")
        if task.message_ref:
            elem.set("messageRef", self._obj_id(task.message_ref))
        if task.operation_ref:
            elem.set("operationRef", self._obj_id(task.operation_ref))
        if task.instantiate:
            elem.set("instantiate", "true")
        self._write_activity_common(elem, task)

    def _write_user_task(self, parent: Element, task: UserTask) -> None:
        elem = self._add_bpmn_element(parent, "userTask", task, name=task.name or "")
        elem.set("implementation", task.implementation if isinstance(task.implementation, str) else "##unspecified")
        for rendering in task.rendering:
            self._write_rendering(elem, rendering)
        self._write_activity_common(elem, task)

    def _write_manual_task(self, parent: Element, task: ManualTask) -> None:
        elem = self._add_bpmn_element(parent, "manualTask", task, name=task.name or "")
        self._write_activity_common(elem, task)

    def _write_script_task(self, parent: Element, task: ScriptTask) -> None:
        elem = self._add_bpmn_element(parent, "scriptTask", task, name=task.name or "")
        if task.script:
            script_elem = SubElement(elem, f"{{{BPMN_NS}}}script")
            script_elem.text = task.script.script_body
            if task.script.script_language:
                script_elem.set("scriptFormat", task.script.script_language.value)
        self._write_activity_common(elem, task)

    def _write_business_rule_task(self, parent: Element, task: BusinessRuleTask) -> None:
        elem = self._add_bpmn_element(parent, "businessRuleTask", task, name=task.name or "")
        if task.implementation:
            # TODO: map to DecisionService reference
            elem.set("implementation", "##unspecified")
        self._write_activity_common(elem, task)

    # Common activity content
    def _write_activity_common(self, elem: Element, activity: Activity) -> None:
        if activity.documentation:
            SubElement(elem, f"{{{BPMN_NS}}}documentation").text = activity.documentation
        if activity.loop_characteristics:
            self._write_loop_characteristics(elem, activity.loop_characteristics)
        if activity.io_specification:
            self._write_io_specification(elem, activity.io_specification)
        for res in activity.resources:
            self._write_resource_role(elem, res)
        for prop in activity.properties:
            self._write_property(elem, prop)

    # Sub‑Process / Call Activity
    def _write_sub_process(self, parent: Element, sub: SubProcess) -> None:
        elem = self._add_bpmn_element(parent, "subProcess", sub, name=sub.name or "")
        if sub.triggered_by_event:
            elem.set("triggeredByEvent", "true")
        if isinstance(sub, AdHocSubProcess):
            elem.set("adHoc", "true")
            if sub.ordering:
                elem.set("ordering", sub.ordering.value)
            if sub.completion_condition:
                self._write_expression(elem, "completionCondition", sub.completion_condition)
        if isinstance(sub, TransactionSubProcess) and sub.method:
            elem.set("transactionMethod", sub.method.value if hasattr(sub.method, 'value') else str(sub.method))
        self._write_activity_common(elem, sub)
        for flow in sub.flow_elements.values():
            self._write_flow_element(elem, flow)
        for lane_set in sub.lane_sets:
            self._write_lane_set(elem, lane_set)
        for artifact in sub.artifacts:
            self._write_artifact(elem, artifact)

    def _write_call_activity(self, parent: Element, call: CallActivity) -> None:
        elem = self._add_bpmn_element(parent, "callActivity", call, name=call.name or "")
        if call.called_element:
            elem.set("calledElement", self._obj_id(call.called_element))
        self._write_activity_common(elem, call)

    # Gateways
    def _write_gateway(self, parent: Element, gw: Gateway) -> None:
        gw_type = gw.gateway_type.value if gw.gateway_type else "Exclusive"
        tag_map = {
            "Exclusive": "exclusiveGateway",
            "Inclusive": "inclusiveGateway",
            "Parallel": "parallelGateway",
            "Complex": "complexGateway",
            "EventBased": "eventBasedGateway",
        }
        actual_tag = tag_map.get(gw_type, "exclusiveGateway")
        elem = self._add_bpmn_element(parent, actual_tag, gw, name=gw.name or "")
        if gw.gateway_direction:
            elem.set("gatewayDirection", gw.gateway_direction.value)
        if isinstance(gw, (ExclusiveGateway, InclusiveGateway, ComplexGateway)) and gw.default_sequence_flow:
            elem.set("default", self._obj_id(gw.default_sequence_flow))
        if isinstance(gw, EventBasedGateway) and gw.event_type:
            elem.set("eventGatewayType", gw.event_type.value)
        if isinstance(gw, ComplexGateway) and gw.activation_condition:
            self._write_expression(elem, "activationCondition", gw.activation_condition)

    # Events
    def _write_event(self, parent: Element, ev: Event) -> None:
        event_type = ev.event_type.value if ev.event_type else "Start"
        tag_map = {
            "Start": ("startEvent", True),
            "End": ("endEvent", False),
            "IntermediateCatch": ("intermediateCatchEvent", False),
            "IntermediateThrow": ("intermediateThrowEvent", False),
            "Boundary": ("boundaryEvent", False),
        }
        tag, is_catch = tag_map.get(event_type, ("event", False))
        elem = self._add_bpmn_element(parent, tag, ev, name=ev.name or "")
        if isinstance(ev, CatchEvent):
            if ev.parallel_multiple:
                elem.set("parallelMultiple", "true")
        if isinstance(ev, BoundaryEvent):
            if ev.attached_to_ref:
                elem.set("attachedToRef", self._obj_id(ev.attached_to_ref))
            if not ev.cancel_activity:
                elem.set("cancelActivity", "false")
        if isinstance(ev, StartEvent) and not ev.is_interrupting:
            elem.set("isInterrupting", "false")

        for ed in ev.event_definitions:
            self._write_event_definition(elem, ed)

        if isinstance(ev, CatchEvent):
            for out_da in ev.data_output_associations:
                self._write_data_association(elem, out_da)
        if isinstance(ev, ThrowEvent):
            for in_da in ev.data_input_associations:
                self._write_data_association(elem, in_da)

        for prop in ev.properties:
            self._write_property(elem, prop)

    def _write_event_definition(self, parent: Element, ed: EventDefinition) -> None:
        tag_map = {
            "Message": "messageEventDefinition",
            "Timer": "timerEventDefinition",
            "Signal": "signalEventDefinition",
            "Error": "errorEventDefinition",
            "Escalation": "escalationEventDefinition",
            "Compensation": "compensateEventDefinition",
            "Conditional": "conditionalEventDefinition",
            "Link": "linkEventDefinition",
            "Cancel": "cancelEventDefinition",
            "Terminate": "terminateEventDefinition",
        }
        actual_tag = tag_map.get(ed.type.value, "eventDefinition")
        elem = self._add_bpmn_element(parent, actual_tag, ed)

        if isinstance(ed, MessageEventDefinition):
            if ed.message_ref:
                elem.set("messageRef", self._obj_id(ed.message_ref))
            if ed.operation_ref:
                elem.set("operationRef", self._obj_id(ed.operation_ref))
        elif isinstance(ed, TimerEventDefinition):
            if ed.time_date:
                self._write_expression(elem, "timeDate", ed.time_date)
            if ed.time_cycle:
                self._write_expression(elem, "timeCycle", ed.time_cycle)
            if ed.time_duration:
                self._write_expression(elem, "timeDuration", ed.time_duration)
        elif isinstance(ed, SignalEventDefinition) and ed.signal_ref:
            elem.set("signalRef", self._obj_id(ed.signal_ref))
        elif isinstance(ed, ErrorEventDefinition) and ed.error_ref:
            elem.set("errorRef", self._obj_id(ed.error_ref))
        elif isinstance(ed, EscalationEventDefinition) and ed.escalation_ref:
            elem.set("escalationRef", self._obj_id(ed.escalation_ref))
        elif isinstance(ed, CompensateEventDefinition):
            if ed.activity_ref:
                elem.set("activityRef", self._obj_id(ed.activity_ref))
            if ed.wait_for_completion is not None:
                elem.set("waitForCompletion", str(ed.wait_for_completion).lower())
        elif isinstance(ed, ConditionalEventDefinition) and ed.condition:
            self._write_expression(elem, "condition", ed.condition)
        elif isinstance(ed, LinkEventDefinition):
            # ed.sources is a list of LinkEventDefinition objects; we need their ids.
            for src in ed.sources:
                src_elem = SubElement(elem, f"{{{BPMN_NS}}}source")
                src_elem.set("id", self._obj_id(src))
            if ed.target:
                tgt_elem = SubElement(elem, f"{{{BPMN_NS}}}target")
                tgt_elem.set("id", self._obj_id(ed.target))

    # Sequence Flow
    def _write_sequence_flow(self, parent: Element, flow: SequenceFlow) -> None:
        elem = self._add_bpmn_element(parent, "sequenceFlow", flow, name=flow.name or "")
        if flow.source_ref:
            elem.set("sourceRef", self._obj_id(flow.source_ref))
        if flow.target_ref:
            elem.set("targetRef", self._obj_id(flow.target_ref))
        if flow.condition_expression:
            self._write_expression(elem, "conditionExpression", flow.condition_expression)

    # Data objects / stores
    def _write_data_object(self, parent: Element, dobj: DataObject) -> None:
        elem = self._add_bpmn_element(parent, "dataObject", dobj, name=dobj.name or "")
        if dobj.item_subject_ref:
            elem.set("itemSubjectRef", self._obj_id(dobj.item_subject_ref))
        if dobj.is_collection:
            elem.set("isCollection", "true")

    def _write_data_object_reference(self, parent: Element, ref: DataObjectReference) -> None:
        elem = self._add_bpmn_element(parent, "dataObjectReference", ref, name=ref.name or "")
        if ref.data_object:
            elem.set("dataObjectRef", self._obj_id(ref.data_object))

    def _write_data_store(self, parent: Element, store: DataStore) -> None:
        elem = self._add_bpmn_element(parent, "dataStore", store, name=store.name or "")
        if store.item_subject_ref:
            elem.set("itemSubjectRef", self._obj_id(store.item_subject_ref))
        if store.is_unlimited:
            elem.set("isUnlimited", "true")
        if store.capacity:
            elem.set("capacity", str(store.capacity))

    def _write_data_store_reference(self, parent: Element, ref: DataStoreReference) -> None:
        elem = self._add_bpmn_element(parent, "dataStoreReference", ref)
        if ref.data_store:
            elem.set("dataStoreRef", self._obj_id(ref.data_store))

    # Data Associations (unified for both input and output)
    def _write_data_association(self, parent: Element, da: DataAssociation) -> None:
        elem = self._add_bpmn_element(parent, "dataAssociation", da)
        for src in da.source_refs:
            SubElement(elem, f"{{{BPMN_NS}}}sourceRef", {"id": self._obj_id(src)})
        if da.target_ref:
            SubElement(elem, f"{{{BPMN_NS}}}targetRef", {"id": self._obj_id(da.target_ref)})
        if da.transformation:
            self._write_expression(elem, "transformation", da.transformation)

    def _write_data_input(self, parent: Element, di: DataInput) -> None:
        elem = self._add_bpmn_element(parent, "dataInput", None, id=di.id, name=di.name or "")
        if di.item_subject_ref:
            elem.set("itemSubjectRef", self._obj_id(di.item_subject_ref))

    def _write_data_output(self, parent: Element, do: DataOutput) -> None:
        elem = self._add_bpmn_element(parent, "dataOutput", None, id=do.id, name=do.name or "")
        if do.item_subject_ref:
            elem.set("itemSubjectRef", self._obj_id(do.item_subject_ref))

    # Input/Output Specification
    def _write_io_specification(self, parent: Element, iospec: InputOutputSpecification) -> None:
        elem = self._add_bpmn_element(parent, "ioSpecification", iospec)
        for di in iospec.data_inputs:
            self._write_data_input(elem, di)
        for do in iospec.data_outputs:
            self._write_data_output(elem, do)
        for iset in iospec.input_sets:
            is_elem = self._add_bpmn_element(elem, "inputSet", iset, name=iset.name or "")
            for iref in iset.data_input_refs:
                SubElement(is_elem, f"{{{BPMN_NS}}}dataInputRefs", {"id": self._obj_id(iref.data_input) if iref.data_input else ""})
        for oset in iospec.output_sets:
            os_elem = self._add_bpmn_element(elem, "outputSet", oset, name=oset.name or "")
            for oref in oset.data_output_refs:
                SubElement(os_elem, f"{{{BPMN_NS}}}dataOutputRefs", {"id": self._obj_id(oref.data_output) if oref.data_output else ""})

    # Artifacts
    def _write_artifact(self, parent: Element, art: Artifact) -> None:
        if isinstance(art, Association):
            elem = self._add_bpmn_element(parent, "association", art, associationDirection=art.direction.value)
            if art.source_ref:
                elem.set("sourceRef", self._obj_id(art.source_ref))
            if art.target_ref:
                elem.set("targetRef", self._obj_id(art.target_ref))
        elif isinstance(art, TextAnnotation):
            elem = self._add_bpmn_element(parent, "textAnnotation", art)
            text_elem = SubElement(elem, f"{{{BPMN_NS}}}text")
            text_elem.text = art.text
        elif isinstance(art, Group):
            self._add_bpmn_element(parent, "group", art)

    # Properties
    def _write_property(self, parent: Element, prop: Property) -> None:
        elem = self._add_bpmn_element(parent, "property", prop, name=prop.name or "")
        if prop.item_subject_ref:
            elem.set("itemSubjectRef", self._obj_id(prop.item_subject_ref))

    # Resources
    def _write_resource_role(self, parent: Element, role: ResourceRole) -> None:
        elem = self._add_bpmn_element(parent, "resourceRole", role, name=role.name)
        if role.resource_ref:
            elem.set("resourceRef", self._obj_id(role.resource_ref))
        if role.resource_assignment_expression and role.resource_assignment_expression.expression:
            self._write_expression(elem, "resourceAssignmentExpression", role.resource_assignment_expression.expression)

    # Loop characteristics
    def _write_loop_characteristics(self, parent: Element, loop: LoopCharacteristics) -> None:
        if isinstance(loop, StandardLoopCharacteristics):
            elem = self._add_bpmn_element(parent, "standardLoopCharacteristics", loop)
            elem.set("testBefore", str(loop.test_before).lower())
            elem.set("loopMaximum", str(loop.loop_maximum))
            if loop.loop_condition:
                self._write_expression(elem, "loopCondition", loop.loop_condition)
        elif isinstance(loop, MultiInstanceLoopCharacteristics):
            elem = self._add_bpmn_element(parent, "multiInstanceLoopCharacteristics", loop)
            elem.set("isSequential", str(loop.is_sequential).lower())
            if loop.completion_condition:
                self._write_expression(elem, "completionCondition", loop.completion_condition)
            if loop.loop_cardinality:
                self._write_expression(elem, "loopCardinality", loop.loop_cardinality)
            if loop.loop_data_input_ref:
                elem.set("loopDataInputRef", self._obj_id(loop.loop_data_input_ref))
            if loop.input_data_item:
                elem.set("inputDataItem", self._obj_id(loop.input_data_item))
            if loop.output_data_item:
                elem.set("outputDataItem", self._obj_id(loop.output_data_item))
            if loop.behavior:
                elem.set("behavior", loop.behavior.value)
            for cbd in loop.complex_behavior_definition:
                self._write_complex_behavior_definition(elem, cbd)

    def _write_complex_behavior_definition(self, parent: Element, cbd) -> None:
        elem = self._add_bpmn_element(parent, "complexBehaviorDefinition", cbd)
        if cbd.condition:
            self._write_expression(elem, "condition", cbd.condition)
        if cbd.implicit_event:
            self._add_bpmn_element(elem, "implicitThrowEvent", cbd.implicit_event)

    # Auditing / Monitoring
    def _write_auditing(self, parent: Element, aud: Auditing | None) -> None:
        if aud is None:
            return
        elem = self._add_bpmn_element(parent, "auditing", aud)
        elem.set("saveInstances", str(aud.save_instances).lower())
        elem.set("generateTraceLog", str(aud.generate_trace_log).lower())
        if aud.log_condition and aud.log_condition.body:
            elem.set("logCondition", aud.log_condition.body)

    def _write_monitoring(self, parent: Element, mon: Monitoring | None) -> None:
        if mon is None:
            return
        self._add_bpmn_element(parent, "monitoring", mon)

    # Collaboration / Choreography
    def _write_collaboration(self, root: Element, collab: Collaboration) -> None:
        elem = self._add_bpmn_element(root, "collaboration", collab, name=collab.name or "")
        elem.set("isClosed", str(collab.is_closed).lower())
        for participant in collab.participants:
            self._write_participant(elem, participant)
        for msg_flow in collab.message_flows:
            self._write_message_flow(elem, msg_flow)
        for art in collab.artifacts:
            self._write_artifact(elem, art)
        for key in collab.correlation_keys:
            self._write_correlation_key(elem, key)
        for assoc in collab.conversation_associations:
            self._write_conversation_association(elem, assoc)
        for conv in collab.conversations:
            self._write_conversation_node(elem, conv)
        for link in collab.conversation_links:
            self._write_conversation_link(elem, link)
        for mfa in collab.message_flow_associations:
            self._write_message_flow_association(elem, mfa)
        for pa in collab.participant_associations:
            self._write_participant_association(elem, pa)

    def _write_choreography(self, root: Element, choreo: Choreography) -> None:
        elem = self._add_bpmn_element(root, "choreography", choreo, name=choreo.name or "")
        for flow in choreo.flow_elements.values():
            if isinstance(flow, ChoreographyActivity):
                self._write_choreography_activity(elem, flow)
        for participant in choreo.participants:
            self._write_participant(elem, participant)
        for msg_flow in choreo.message_flows:
            self._write_message_flow(elem, msg_flow)

    def _write_choreography_activity(self, parent: Element, act: ChoreographyActivity) -> None:
        elem = self._add_bpmn_element(parent, "choreographyActivity", act, name=act.name or "")
        for pref in act.participant_refs:
            SubElement(elem, f"{{{BPMN_NS}}}participantRef", {"id": self._obj_id(pref)})
        if act.initiating_participant_ref:
            elem.set("initiatingParticipantRef", self._obj_id(act.initiating_participant_ref))
        if act.loop_type:
            elem.set("loopType", act.loop_type.value)
        for key in act.correlation_keys:
            self._write_correlation_key(elem, key)

    # Participants
    def _write_participant(self, parent: Element, part: Participant) -> None:
        elem = self._add_bpmn_element(parent, "participant", part, name=part.name or "")
        if part.process_ref:
            elem.set("processRef", self._obj_id(part.process_ref))
        if part.participant_multiplicity:
            mul = part.participant_multiplicity
            SubElement(elem, f"{{{BPMN_NS}}}participantMultiplicity", {
                "minimum": str(mul.minimum),
                "maximum": str(mul.maximum) if mul.maximum > 0 else "*",
            })

    # Message Flow
    def _write_message_flow(self, parent: Element, mf: MessageFlow) -> None:
        elem = self._add_bpmn_element(parent, "messageFlow", mf, name=mf.name or "")
        if mf.source_ref:
            elem.set("sourceRef", self._obj_id(mf.source_ref))
        if mf.target_ref:
            elem.set("targetRef", self._obj_id(mf.target_ref))
        if mf.message_ref:
            elem.set("messageRef", self._obj_id(mf.message_ref))

    # Global tasks
    def _write_global_task(self, root: Element, gt: GlobalTask) -> None:
        tag = "globalTask"
        if isinstance(gt, GlobalUserTask):
            tag = "globalUserTask"
        elif isinstance(gt, GlobalScriptTask):
            tag = "globalScriptTask"
        elif isinstance(gt, GlobalManualTask):
            tag = "globalManualTask"
        elif isinstance(gt, GlobalBusinessRuleTask):
            tag = "globalBusinessRuleTask"
        elem = self._add_bpmn_element(root, tag, gt, name=gt.name or "")
        if gt.io_specification:
            self._write_io_specification(elem, gt.io_specification)

    # Root elements (single)
    def _write_root_element(self, root: Element, re_obj: Any) -> None:
        if isinstance(re_obj, Message):
            elem = self._add_bpmn_element(root, "message", re_obj, name=re_obj.name)
            if re_obj.item_ref:
                elem.set("itemRef", self._obj_id(re_obj.item_ref))
        elif isinstance(re_obj, Error):
            elem = self._add_bpmn_element(root, "error", re_obj, name=re_obj.name)
            if re_obj.error_code:
                elem.set("errorCode", re_obj.error_code)
        elif isinstance(re_obj, Escalation):
            elem = self._add_bpmn_element(root, "escalation", re_obj, name=re_obj.name)
            if re_obj.escalation_code:
                elem.set("escalationCode", re_obj.escalation_code)
        elif isinstance(re_obj, Signal):
            self._add_bpmn_element(root, "signal", re_obj, name=re_obj.name)
        elif isinstance(re_obj, Resource):
            self._add_bpmn_element(root, "resource", re_obj, name=re_obj.name)

    # Correlation
    def _write_correlation_subscription(self, parent: Element, sub: CorrelationSubscription) -> None:
        elem = self._add_bpmn_element(parent, "correlationSubscription", sub)
        if sub.correlation_key_ref:
            elem.set("correlationKeyRef", self._obj_id(sub.correlation_key_ref))
        for binding in sub.property_bindings:
            self._add_bpmn_element(elem, "correlationPropertyBinding", binding)

    def _write_correlation_key(self, parent: Element, key: CorrelationKey) -> None:
        elem = self._add_bpmn_element(parent, "correlationKey", key, name=key.name)
        for prop in key.property_refs:
            SubElement(elem, f"{{{BPMN_NS}}}correlationPropertyRef", {"id": self._obj_id(prop)})

    # Conversation elements
    def _write_conversation_node(self, parent: Element, node: ConversationNode) -> None:
        tag = "conversation"
        if isinstance(node, CallConversation):
            tag = "callConversation"
        elif isinstance(node, SubConversation):
            tag = "subConversation"
        elem = self._add_bpmn_element(parent, tag, node, name=node.name)
        for pref in node.participant_refs:
            SubElement(elem, f"{{{BPMN_NS}}}participantRef", {"id": self._obj_id(pref)})
        for mf_ref in node.message_flow_refs:
            SubElement(elem, f"{{{BPMN_NS}}}messageFlowRef", {"id": self._obj_id(mf_ref)})

    def _write_conversation_association(self, parent: Element, ca: ConversationAssociation) -> None:
        elem = self._add_bpmn_element(parent, "conversationAssociation", ca)
        if ca.inner_conversation_node_ref:
            elem.set("innerConversationNodeRef", self._obj_id(ca.inner_conversation_node_ref))
        for outer in ca.outer_conversation_node_refs:
            SubElement(elem, f"{{{BPMN_NS}}}outerConversationNodeRef", {"id": self._obj_id(outer)})

    def _write_conversation_link(self, parent: Element, link: ConversationLink) -> None:
        elem = self._add_bpmn_element(parent, "conversationLink", link)
        if link.source_ref:
            elem.set("sourceRef", self._obj_id(link.source_ref))
        if link.target_ref:
            elem.set("targetRef", self._obj_id(link.target_ref))

    def _write_message_flow_association(self, parent: Element, mfa: MessageFlowAssociation) -> None:
        elem = self._add_bpmn_element(parent, "messageFlowAssociation", mfa)
        if mfa.inner_message_flow_ref:
            elem.set("innerMessageFlowRef", self._obj_id(mfa.inner_message_flow_ref))
        if mfa.outer_message_flow_ref:
            elem.set("outerMessageFlowRef", self._obj_id(mfa.outer_message_flow_ref))

    def _write_participant_association(self, parent: Element, pa: ParticipantAssociation) -> None:
        elem = self._add_bpmn_element(parent, "participantAssociation", pa)
        if pa.inner_participant_ref:
            elem.set("innerParticipantRef", self._obj_id(pa.inner_participant_ref))
        if pa.outer_participant_ref:
            elem.set("outerParticipantRef", self._obj_id(pa.outer_participant_ref))

    # Lane sets
    def _write_lane_set(self, parent: Element, lane_set: LaneSet) -> None:
        elem = self._add_bpmn_element(parent, "laneSet", lane_set, name=lane_set.name)
        for lane in lane_set.lanes:
            self._write_lane(elem, lane)

    def _write_lane(self, parent: Element, lane: Lane) -> None:
        elem = self._add_bpmn_element(parent, "lane", lane, name=lane.name or "")
        if lane.partition_element_ref:
            elem.set("partitionElement", self._obj_id(lane.partition_element_ref))
        for flow_node in lane.flow_node_refs:
            SubElement(elem, f"{{{BPMN_NS}}}flowNodeRef", {"id": self._obj_id(flow_node)})
        if lane.child_lane_set:
            self._write_lane_set(elem, lane.child_lane_set)

    # Rendering
    def _write_rendering(self, parent: Element, rendering: Rendering) -> None:
        if isinstance(rendering, RenderingForm):
            elem = self._add_bpmn_element(parent, "rendering", rendering)
            elem.set("formId", rendering.form_id or "")
            elem.set("indexFormId", rendering.index_form_id or "")
            elem.set("associationFieldId", rendering.association_field_id or "")

    # Expressions
    def _write_expression(self, parent: Element, tag: str, expr: FormalExpression) -> None:
        elem = self._add_bpmn_element(parent, tag, expr)
        if expr.language:
            lang = expr.language.value if isinstance(expr.language, Enum) else str(expr.language)
            elem.set("language", lang)
        if expr.body:
            elem.text = expr.body

    # Diagrams
    def _write_diagram(self, root: Element, diagram: BPMNDiagram) -> None:
        diag_elem = self._add_bpmn_element(root, "bpmndi:BPMNDiagram", None, id=diagram.id, name=diagram.name)
        if diagram.model_element:
            plane = SubElement(diag_elem, f"{{{BPMN_DI_NS}}}BPMNPlane", {
                "bpmnElement": self._obj_id(diagram.model_element),
            })
            for shape in diagram.owned_elements:
                if isinstance(shape, BPMNShape):
                    self._write_bpmn_shape(plane, shape)
                elif isinstance(shape, BPMNEdge):
                    self._write_bpmn_edge(plane, shape)

    def _write_bpmn_shape(self, parent: Element, shape: BPMNShape) -> None:
        elem = SubElement(parent, f"{{{BPMN_DI_NS}}}BPMNShape", {
            "id": shape.id,
            "bpmnElement": self._obj_id(shape.model_element) if shape.model_element else "",
        })
        if shape.bounds:
            bounds = shape.bounds
            SubElement(elem, f"{{{DC_NS}}}Bounds", {
                "x": str(bounds.x), "y": str(bounds.y),
                "width": str(bounds.width), "height": str(bounds.height),
            })
        if shape.label:
            self._write_bpmn_label(elem, shape.label)

    def _write_bpmn_edge(self, parent: Element, edge: BPMNEdge) -> None:
        elem = SubElement(parent, f"{{{BPMN_DI_NS}}}BPMNEdge", {
            "id": edge.id,
            "bpmnElement": self._obj_id(edge.model_element) if edge.model_element else "",
        })
        # Waypoints omitted – can be added later
        if edge.label:
            self._write_bpmn_label(elem, edge.label)

    def _write_bpmn_label(self, parent: Element, label: BPMNLabel) -> None:
        # BPMNLabel has no 'id' attribute; we only set labelStyle and optionally bounds
        label_elem = SubElement(parent, f"{{{BPMN_DI_NS}}}BPMNLabel")
        if label.alignment:
            label_elem.set("labelStyle", label.alignment.value)
        # Optionally add bounds
        if label.bounds and (label.bounds.width != 0 or label.bounds.height != 0):
            SubElement(label_elem, f"{{{DC_NS}}}Bounds", {
                "x": str(label.bounds.x), "y": str(label.bounds.y),
                "width": str(label.bounds.width), "height": str(label.bounds.height),
            })

    # Utility ID mapping for any object with an id
    def _get_or_create_id(self, obj: Any) -> str:
        if hasattr(obj, "id"):
            return obj.id
        return str(id(obj))