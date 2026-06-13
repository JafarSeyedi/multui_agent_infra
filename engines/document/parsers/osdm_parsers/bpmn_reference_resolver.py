# engines/document/parsers/osdm_parsers/bpmn_reference_resolver.py
"""Two-pass reference resolution for BPMNDocument.

Maps all string cross-references (source_ref_id, target_ref_id, etc.)
to actual object references after the first pass of XML parsing.
"""

from __future__ import annotations

import logging
from typing import Optional, Dict, cast

from ...models.osdm_models import (
    Activity,
    Association,
    BaseElement,
    BoundaryEvent,
    BPMNDiagram,
    BPMNEdge,
    BPMNShape,
    ChoreographyActivity,
    ComplexGateway,
    CompensateEventDefinition,
    ConversationAssociation,
    ConversationLink,
    ConversationNode,
    CorrelationKey,
    CorrelationProperty,
    CorrelationSubscription,
    DataAssociation,
    DataElement,
    DataFlowElement,
    DataInput,
    DataObject,
    DataObjectReference,
    DataOutput,
    DataStore,
    DataStoreReference,
    Error,
    ErrorEventDefinition,
    Escalation,
    EscalationEventDefinition,
    ExclusiveGateway,
    FlowNode,
    InclusiveGateway,
    InteractionNode,
    ItemDefinition,
    Lane,
    LinkEventDefinition,
    Message,
    MessageEventDefinition,
    MessageFlow,
    MessageFlowAssociation,
    MultiInstanceLoopCharacteristics,
    Operation,
    Participant,
    ParticipantAssociation,
    Process,
    Property,
    Resource,
    ResourceRole,
    SequenceFlow,
    Signal,
    SignalEventDefinition,
)


logger = logging.getLogger(__name__)


def resolve_references(doc, strict: bool, doc_id: str, log: logging.Logger) -> None:
    """Resolve all string cross-references in a BPMNDocument to object references.

    Args:
        doc: The parsed BPMNDocument.
        strict: If True, raise ValueError on missing reference.
        doc_id: Document identifier for logging.
        log: Logger instance for warnings.
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

    for root_elem in doc.root_elements.values():
        collect(root_elem)

    for proc in doc.processes:
        collect(proc)
    for collab in doc.collaborations:
        collect(collab)
    for choreo in doc.choreographies:
        collect(choreo)
    for gt in doc.global_tasks:
        collect(gt)

    def get_obj(
        obj_id: str, elem_id: Optional[str] = None, ref_type: str = ""
    ) -> Optional[BaseElement]:
        obj = all_elements.get(obj_id)
        if obj is None:
            msg = f"Document '{doc_id}': Reference ID '{obj_id}' not found"
            if elem_id:
                msg += f" (referenced by element '{elem_id}', type '{ref_type}')"
            if strict:
                raise ValueError(msg)
            log.warning(msg)
        return obj

    for elem in list(all_elements.values()):
        elem_id = elem.id

        if isinstance(elem, SequenceFlow):
            if hasattr(elem, "source_ref_id") and elem.source_ref_id:
                src = get_obj(elem.source_ref_id, elem_id, "source_ref")
                if src is not None and isinstance(src, FlowNode):
                    elem.source_ref = src
                elif src is not None:
                    log.warning(
                        f"Document '{doc_id}': source_ref_id '{elem.source_ref_id}'"
                        f" on SequenceFlow '{elem_id}' resolved to non-FlowNode type {type(src)}"
                    )
            if hasattr(elem, "target_ref_id") and elem.target_ref_id:
                tgt = get_obj(elem.target_ref_id, elem_id, "target_ref")
                if tgt is not None and isinstance(tgt, FlowNode):
                    elem.target_ref = tgt
                elif tgt is not None:
                    log.warning(
                        f"Document '{doc_id}': target_ref_id '{elem.target_ref_id}'"
                        f" on SequenceFlow '{elem_id}' resolved to non-FlowNode type {type(tgt)}"
                    )

        if isinstance(elem, MessageFlow):
            if hasattr(elem, "source_ref_id") and elem.source_ref_id:
                src = get_obj(elem.source_ref_id, elem_id, "source_ref")
                if src is not None:
                    elem.source_ref = cast(InteractionNode, src)
            if hasattr(elem, "target_ref_id") and elem.target_ref_id:
                tgt = get_obj(elem.target_ref_id, elem_id, "target_ref")
                if tgt is not None:
                    elem.target_ref = cast(InteractionNode, tgt)
            if hasattr(elem, "message_ref_id") and elem.message_ref_id:
                msg = get_obj(elem.message_ref_id, elem_id, "message_ref")
                if msg is not None and isinstance(msg, Message):
                    elem.message_ref = msg
                elif msg is not None:
                    log.warning(
                        f"Document '{doc_id}': message_ref_id '{elem.message_ref_id}'"
                        f" on MessageFlow '{elem_id}' resolved to non-Message type {type(msg)}"
                    )

        if isinstance(elem, DataObjectReference) and hasattr(elem, "data_object_id") and elem.data_object_id:
            obj = get_obj(elem.data_object_id, elem_id, "data_object")
            if obj is not None and isinstance(obj, DataObject):
                elem.data_object = obj
            elif obj is not None:
                log.warning(
                    f"Document '{doc_id}': data_object_id '{elem.data_object_id}'"
                    f" on DataObjectReference '{elem_id}' resolved to non-DataObject type {type(obj)}"
                )

        if isinstance(elem, DataStoreReference) and hasattr(elem, "data_store_id") and elem.data_store_id:
            obj = get_obj(elem.data_store_id, elem_id, "data_store")
            if obj is not None and isinstance(obj, DataStore):
                elem.data_store = obj
            elif obj is not None:
                log.warning(
                    f"Document '{doc_id}': data_store_id '{elem.data_store_id}'"
                    f" on DataStoreReference '{elem_id}' resolved to non-DataStore type {type(obj)}"
                )

        if hasattr(elem, "item_subject_ref_id") and elem.item_subject_ref_id and isinstance(elem, (DataInput, DataOutput, DataFlowElement, DataObject, DataStore, DataElement, Property)):
            obj = get_obj(elem.item_subject_ref_id, elem_id, "item_subject_ref")
            if obj is not None and isinstance(obj, ItemDefinition):
                elem.item_subject_ref = obj
            elif obj is not None:
                log.warning(
                    f"Document '{doc_id}': item_subject_ref_id '{elem.item_subject_ref_id}'"
                    f" on {type(elem)} '{elem_id}' resolved to non-ItemDefinition type {type(obj)}"
                )

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
                        log.warning(
                            f"Document '{doc_id}': error_ref_id '{eid}'"
                            f" on Operation '{elem_id}' resolved to non-Error type {type(obj)}"
                        )
                elem.error_refs = resolved_errors

        if isinstance(elem, Lane):
            if hasattr(elem, "partition_element_ref_id") and elem.partition_element_ref_id:
                obj = get_obj(elem.partition_element_ref_id, elem_id, "partition_element_ref")
                if obj is not None:
                    elem.partition_element_ref = obj
            if hasattr(elem, "flow_node_ref_ids"):
                resolved_nodes = []
                for fid in elem.flow_node_ref_ids:
                    obj = get_obj(fid, elem_id, "flow_node_ref")
                    if obj is not None and isinstance(obj, FlowNode):
                        resolved_nodes.append(obj)
                    elif obj is not None:
                        log.warning(
                            f"Document '{doc_id}': flow_node_ref_id '{fid}'"
                            f" on Lane '{elem_id}' resolved to non-FlowNode type {type(obj)}"
                        )
                elem.flow_node_refs = resolved_nodes

        if isinstance(elem, ChoreographyActivity):
            if hasattr(elem, "participant_ref_ids"):
                resolved_parts = []
                for pid in elem.participant_ref_ids:
                    obj = get_obj(pid, elem_id, "participant_ref")
                    if obj is not None and isinstance(obj, Participant):
                        resolved_parts.append(obj)
                    elif obj is not None:
                        log.warning(
                            f"Document '{doc_id}': participant_ref_id '{pid}'"
                            f" on ChoreographyActivity '{elem_id}' resolved to non-Participant type {type(obj)}"
                        )
                elem.participant_refs = resolved_parts
            if hasattr(elem, "initiating_participant_ref_id") and elem.initiating_participant_ref_id:
                obj = get_obj(elem.initiating_participant_ref_id, elem_id, "initiating_participant_ref")
                if obj is not None and isinstance(obj, Participant):
                    elem.initiating_participant_ref = obj
                elif obj is not None:
                    log.warning(
                        f"Document '{doc_id}': initiating_participant_ref_id '{elem.initiating_participant_ref_id}'"
                        f" on ChoreographyActivity '{elem_id}' resolved to non-Participant type {type(obj)}"
                    )

        if isinstance(elem, CorrelationKey) and hasattr(elem, "property_ref_ids"):
            resolved_props = []
            for pid in elem.property_ref_ids:
                obj = get_obj(pid, elem_id, "property_ref")
                if obj is not None and isinstance(obj, CorrelationProperty):
                    resolved_props.append(obj)
                elif obj is not None:
                    log.warning(
                        f"Document '{doc_id}': property_ref_id '{pid}'"
                        f" on CorrelationKey '{elem_id}' resolved to non-CorrelationProperty type {type(obj)}"
                    )
            elem.property_refs = resolved_props

        if isinstance(elem, CorrelationSubscription) and hasattr(elem, "correlation_key_ref_id") and elem.correlation_key_ref_id:
            obj = get_obj(elem.correlation_key_ref_id, elem_id, "correlation_key_ref")
            if obj is not None and isinstance(obj, CorrelationKey):
                elem.correlation_key_ref = obj
            elif obj is not None:
                log.warning(
                    f"Document '{doc_id}': correlation_key_ref_id '{elem.correlation_key_ref_id}'"
                    f" on CorrelationSubscription '{elem_id}' resolved to non-CorrelationKey type {type(obj)}"
                )

        if isinstance(elem, Association):
            if hasattr(elem, "source_ref_id") and elem.source_ref_id:
                obj = get_obj(elem.source_ref_id, elem_id, "source_ref")
                if obj is not None:
                    elem.source_ref = obj
            if hasattr(elem, "target_ref_id") and elem.target_ref_id:
                obj = get_obj(elem.target_ref_id, elem_id, "target_ref")
                if obj is not None:
                    elem.target_ref = obj

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

        if isinstance(elem, ConversationNode):
            if hasattr(elem, "participant_ref_ids"):
                resolved_parts = []
                for pid in elem.participant_ref_ids:
                    obj = get_obj(pid, elem_id, "participant_ref")
                    if obj is not None and isinstance(obj, Participant):
                        resolved_parts.append(obj)
                    elif obj is not None:
                        log.warning(
                            f"Document '{doc_id}': participant_ref_id '{pid}'"
                            f" on ConversationNode '{elem_id}' resolved to non-Participant type {type(obj)}"
                        )
                elem.participant_refs = resolved_parts
            if hasattr(elem, "message_flow_ref_ids"):
                resolved_mfs = []
                for mfid in elem.message_flow_ref_ids:
                    obj = get_obj(mfid, elem_id, "message_flow_ref")
                    if obj is not None and isinstance(obj, MessageFlow):
                        resolved_mfs.append(obj)
                    elif obj is not None:
                        log.warning(
                            f"Document '{doc_id}': message_flow_ref_id '{mfid}'"
                            f" on ConversationNode '{elem_id}' resolved to non-MessageFlow type {type(obj)}"
                        )
                elem.message_flow_refs = resolved_mfs

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
                        log.warning(
                            f"Document '{doc_id}': outer_conversation_node_ref_id '{oid}'"
                            f" on ConversationAssociation '{elem_id}' resolved to non-ConversationNode type {type(obj)}"
                        )
                elem.outer_conversation_node_refs = resolved_outer

        if isinstance(elem, ConversationLink):
            if hasattr(elem, "source_ref_id") and elem.source_ref_id:
                obj = get_obj(elem.source_ref_id, elem_id, "source_ref")
                if obj is not None:
                    elem.source_ref = cast(InteractionNode, obj)
            if hasattr(elem, "target_ref_id") and elem.target_ref_id:
                obj = get_obj(elem.target_ref_id, elem_id, "target_ref")
                if obj is not None:
                    elem.target_ref = cast(InteractionNode, obj)

        if isinstance(elem, MessageFlowAssociation):
            if hasattr(elem, "inner_message_flow_ref_id") and elem.inner_message_flow_ref_id:
                obj = get_obj(elem.inner_message_flow_ref_id, elem_id, "inner_message_flow_ref")
                if obj is not None and isinstance(obj, MessageFlow):
                    elem.inner_message_flow_ref = obj
            if hasattr(elem, "outer_message_flow_ref_id") and elem.outer_message_flow_ref_id:
                obj = get_obj(elem.outer_message_flow_ref_id, elem_id, "outer_message_flow_ref")
                if obj is not None and isinstance(obj, MessageFlow):
                    elem.outer_message_flow_ref = obj

        if isinstance(elem, ParticipantAssociation):
            if hasattr(elem, "inner_participant_ref_id") and elem.inner_participant_ref_id:
                obj = get_obj(elem.inner_participant_ref_id, elem_id, "inner_participant_ref")
                if obj is not None and isinstance(obj, Participant):
                    elem.inner_participant_ref = obj
            if hasattr(elem, "outer_participant_ref_id") and elem.outer_participant_ref_id:
                obj = get_obj(elem.outer_participant_ref_id, elem_id, "outer_participant_ref")
                if obj is not None and isinstance(obj, Participant):
                    elem.outer_participant_ref = obj

        if isinstance(elem, Participant) and hasattr(elem, "process_ref_id") and elem.process_ref_id:
            obj = get_obj(elem.process_ref_id, elem_id, "process_ref")
            if obj is not None and isinstance(obj, Process):
                elem.process_ref = obj
            elif obj is not None:
                log.warning(
                    f"Document '{doc_id}': process_ref_id '{elem.process_ref_id}'"
                    f" on Participant '{elem_id}' resolved to non-Process type {type(obj)}"
                )

        if isinstance(elem, BoundaryEvent) and hasattr(elem, "attached_to_ref_id") and elem.attached_to_ref_id:
            obj = get_obj(elem.attached_to_ref_id, elem_id, "attached_to_ref")
            if obj is not None and isinstance(obj, Activity):
                elem.attached_to_ref = obj
            elif obj is not None:
                log.warning(
                    f"Document '{doc_id}': attached_to_ref_id '{elem.attached_to_ref_id}'"
                    f" on BoundaryEvent '{elem_id}' resolved to non-Activity type {type(obj)}"
                )

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
                        log.warning(
                            f"Document '{doc_id}': source_id '{sid}'"
                            f" on LinkEventDefinition '{elem_id}' resolved to non-LinkEventDefinition type {type(obj)}"
                        )
                elem.sources = resolved_sources
            if hasattr(elem, "target_id") and elem.target_id:
                obj = get_obj(elem.target_id, elem_id, "target")
                if obj is not None and isinstance(obj, LinkEventDefinition):
                    elem.target = obj

        if isinstance(elem, ResourceRole) and hasattr(elem, "resource_ref_id") and elem.resource_ref_id:
            obj = get_obj(elem.resource_ref_id, elem_id, "resource_ref")
            if obj is not None and isinstance(obj, Resource):
                elem.resource_ref = obj

        if isinstance(elem, MultiInstanceLoopCharacteristics):
            if hasattr(elem, "loop_data_input_ref_id") and elem.loop_data_input_ref_id:
                obj = get_obj(elem.loop_data_input_ref_id, elem_id, "loop_data_input_ref")
                if obj is not None and isinstance(obj, DataInput):
                    elem.loop_data_input_ref = obj
            if hasattr(elem, "loop_data_output_ref_id") and elem.loop_data_output_ref_id:
                obj = get_obj(elem.loop_data_output_ref_id, elem_id, "loop_data_output_ref")
                if obj is not None and isinstance(obj, DataOutput):
                    elem.loop_data_output_ref = obj

        if hasattr(elem, "default_sequence_flow_id") and elem.default_sequence_flow_id:
            if isinstance(elem, (ExclusiveGateway, InclusiveGateway, ComplexGateway)):
                obj = get_obj(elem.default_sequence_flow_id, elem_id, "default_sequence_flow")
                if obj is not None and isinstance(obj, SequenceFlow):
                    elem.default_sequence_flow = obj

        if hasattr(elem, "model_element_id") and elem.model_element_id:
            if isinstance(elem, (BPMNDiagram, BPMNShape, BPMNEdge)):
                obj = get_obj(elem.model_element_id, elem_id, "model_element")
                if obj is not None:
                    elem.model_element = obj
            else:
                log.warning(
                    f"Document '{doc_id}': element {elem_id} has model_element_id"
                    f" but is not a diagram element; ignoring"
                )
