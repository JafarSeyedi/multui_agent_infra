"""Mixin for BPMN flow element parsers — tasks, gateways, events, data, sequence flows."""

# mypy: disable-error-code="attr-defined"

from __future__ import annotations

from typing import Any
from xml.etree import ElementTree as ET

from engines.orchestration.models.osdm_models import (
    Activity, AdHocOrdering, AdHocSubProcess, BoundaryEvent,
    BusinessRuleTask, CatchEvent, ComplexGateway,
    CompensateEventDefinition, ConditionalEventDefinition,
    DataAssociation, DataInput, DataInputAssociation, DataObject,
    DataObjectReference, DataOutput, DataOutputAssociation,
    DataStore, DataStoreReference, ErrorEventDefinition,
    EscalationEventDefinition, Event, EventBasedGateway,
    EventBasedGatewayType, EventDefinition, ExclusiveGateway,
    FlowElement, Gateway, InclusiveGateway,
    LinkEventDefinition, MessageEventDefinition,
    MessageFlow, Monitoring,
    MultiInstanceBehavior, MultiInstanceLoopCharacteristics,
    ParallelGateway, Process, ReceiveTask, Script, ScriptLanguage,
    ScriptTask, SendTask, SequenceFlow, ServiceTask,
    SignalEventDefinition, StandardLoopCharacteristics, StartEvent,
    SubProcess, Task, ThrowEvent, TimerEventDefinition,
    TransactionMethod, TransactionSubProcess, UserTask,
)
from .bpmn_constants import (
    EVENT_DEFINITION_TAG_MAP, EVENT_TAG_MAP, GATEWAY_TAG_MAP,
    SUB_PROCESS_TAG_MAP, TASK_TAG_MAP, NS,
)


class BPMNFlowParser:
    """Mixin providing BPMN flow element parsing methods.

    Expects ``self`` to provide: ``logger``, ``_map_enum()``,
    ``_map_gateway_type()``, ``_map_process_type()``,
    ``_map_association_direction()``, ``_map_item_kind()``,
    ``_map_loop_behavior()``, ``_map_choreography_loop_type()``.
    """

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
        flow_elements: dict[str, FlowElement] = {}
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

    def _parse_flow_element(self, elem: ET.Element) -> FlowElement | None:
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

    def _parse_task(self, elem: ET.Element, cls: Any) -> Task | None:
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
                self.logger.debug(f"Ignoring generic DataAssociation {da.id} inside activity {activity.id}")

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
        flow_elements: dict[str, FlowElement] = {}
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

    def _parse_event_definition(self, elem: ET.Element) -> EventDefinition | None:
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
