# Large Parser File Splits — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce three untested large parser files (bpmn 1441L, html 1831L) by extracting separable constants, utilities, and self-contained logic into focused modules. No behavior changes.

**Architecture:** Each extraction preserves the existing public API and import paths. Extracted modules use the sibling-package pattern (importable from the same directory). The parent file imports from the new modules and re-exports nothing new.

**Tech Stack:** Python 3.12, no new dependencies.

---

### Task 1: Extract bpmn constants → `bpmn_constants.py`

**Files:**
- Create: `engines/document/parsers/osdm_parsers/bpmn_constants.py`
- Modify: `engines/document/parsers/osdm_parsers/bpmn_xml_parser.py:60-112`

- [ ] **Step 1: Create `bpmn_constants.py`**

```python
# engines/document/parsers/osdm_parsers/bpmn_constants.py
"""BPMN 2.0 namespace constants and tag-to-class mapping tables."""

from __future__ import annotations

from ...models.osdm_models import (
    BusinessRuleTask,
    CallActivity,
    CancelEventDefinition,
    ChoreographyLoopType,
    CompensateEventDefinition,
    ComplexGateway,
    ConditionalEventDefinition,
    ErrorEventDefinition,
    EscalationEventDefinition,
    EventBasedGateway,
    ExclusiveGateway,
    GatewayDirection,
    InclusiveGateway,
    ItemKind,
    LinkEventDefinition,
    ManualTask,
    MessageEventDefinition,
    MultiInstanceBehavior,
    ParallelGateway,
    ProcessType,
    ReceiveTask,
    ScriptTask,
    SendTask,
    ServiceTask,
    SignalEventDefinition,
    StartEvent,
    EndEvent,
    IntermediateCatchEvent,
    IntermediateThrowEvent,
    BoundaryEvent,
    SubProcess,
    Task,
    TimerEventDefinition,
    TerminateEventDefinition,
    TransactionSubProcess,
    AdHocSubProcess,
    UserTask,
)

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
```

- [ ] **Step 2: Replace constants in `bpmn_xml_parser.py` with import**

Replace lines 60-112 (namespace constants and all `_TAG_MAP` dicts) with:

```python
from .bpmn_constants import (
    BPMN_NS, BPMN_DI_NS, DI_NS, DC_NS, NS,
    TASK_TAG_MAP, SUB_PROCESS_TAG_MAP, GATEWAY_TAG_MAP,
    EVENT_TAG_MAP, EVENT_DEFINITION_TAG_MAP,
)
```

Also remove the now-unused model imports from the long import block:
- Lines 24-55 kept but remove: `ChoreographyLoopType`, `GatewayDirection`, `ItemKind`, `MultiInstanceBehavior`, `ProcessType` (no longer needed at the top of the parser since they're only used in enum mappers and tag maps that moved)

Actually, let me be careful — some of these models are still used elsewhere in the file. Let me only remove what's truly unused after the extraction. The safest approach: remove only the imports that are ONLY used in the constants. Let me check each:

- `ChoreographyLoopType` — used in `_map_choreography_loop_type` (stays in parser)
- `GatewayDirection` — used in `_map_gateway_direction` (stays in parser)
- `ItemKind` — used in `_map_item_kind` (stays in parser)
- `MultiInstanceBehavior` — used in `_map_loop_behavior` (stays in parser)
- `ProcessType` — used in `_map_process_type` (stays in parser)

So none of the imported models can be dropped from the main parser — they're all still used in the enum mappers. The tag map model imports move to `bpmn_constants.py` but were imported from the shared `osdm_models` module so there's no duplication issue.

The only real change: replace the inline constant definitions with an import statement.

- [ ] **Step 3: Run tests to confirm no regression**

Run: `python -m pytest tests/ -k "bpmn" --asyncio-mode=auto -q`
Expected: No failures.

---

### Task 2: Extract bpmn reference resolver → `bpmn_reference_resolver.py`

**Files:**
- Create: `engines/document/parsers/osdm_parsers/bpmn_reference_resolver.py`
- Modify: `engines/document/parsers/osdm_parsers/bpmn_xml_parser.py:1037-1441`

- [ ] **Step 1: Create `bpmn_reference_resolver.py`**

```python
# engines/document/parsers/osdm_parsers/bpmn_reference_resolver.py
"""Two-pass reference resolution for BPMNDocument.

Maps all string cross-references (source_ref_id, target_ref_id, etc.)
to actual object references after the first pass of XML parsing.
"""

from __future__ import annotations

import logging
from typing import Optional, Dict, cast

from ...models.osdm_models import (
    Activity, Association, BaseElement, BoundaryEvent, BPMNDiagram,
    BPMNEdge, BPMNShape, ChoreographyActivity, ComplexGateway,
    CompensateEventDefinition, ConversationAssociation, ConversationLink,
    ConversationNode, CorrelationKey, CorrelationProperty,
    CorrelationSubscription, DataAssociation, DataElement,
    DataFlowElement, DataInput, DataObject, DataObjectReference,
    DataOutput, DataOutputAssociation, DataInputAssociation,
    DataStore, DataStoreReference, Error, ErrorEventDefinition,
    Escalation, EscalationEventDefinition, EventDefinition,
    ExclusiveGateway, FlowNode, Gateway, InclusiveGateway,
    InteractionNode, ItemDefinition, Lane, LinkEventDefinition,
    Message, MessageEventDefinition, MessageFlow,
    MessageFlowAssociation, MultiInstanceLoopCharacteristics,
    Operation, Participant, ParticipantAssociation,
    Process, Resource, ResourceRole, SequenceFlow,
    Signal, SignalEventDefinition,
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

    def get_obj(obj_id: str, elem_id: Optional[str] = None, ref_type: str = "") -> Optional[BaseElement]:
        obj = all_elements.get(obj_id)
        if obj is None:
            msg = f"Document '{doc_id}': Reference ID '{obj_id}' not found"
            if elem_id:
                msg += f" (referenced by element '{elem_id}', type '{ref_type}')"
            if strict:
                raise ValueError(msg)
            else:
                log.warning(msg)
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
                    log.warning(f"Document '{doc_id}': source_ref_id '{elem.source_ref_id}' on SequenceFlow '{elem_id}' resolved to non-FlowNode type {type(src)}")
            if hasattr(elem, "target_ref_id") and elem.target_ref_id:
                tgt = get_obj(elem.target_ref_id, elem_id, "target_ref")
                if tgt is not None and isinstance(tgt, FlowNode):
                    elem.target_ref = tgt
                elif tgt is not None:
                    log.warning(f"Document '{doc_id}': target_ref_id '{elem.target_ref_id}' on SequenceFlow '{elem_id}' resolved to non-FlowNode type {type(tgt)}")
        # MessageFlow
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
                    log.warning(f"Document '{doc_id}': message_ref_id '{elem.message_ref_id}' on MessageFlow '{elem_id}' resolved to non-Message type {type(msg)}")
        # DataObjectReference
        if isinstance(elem, DataObjectReference) and hasattr(elem, "data_object_id") and elem.data_object_id:
            obj = get_obj(elem.data_object_id, elem_id, "data_object")
            if obj is not None and isinstance(obj, DataObject):
                elem.data_object = obj
            elif obj is not None:
                log.warning(f"Document '{doc_id}': data_object_id '{elem.data_object_id}' on DataObjectReference '{elem_id}' resolved to non-DataObject type {type(obj)}")
        # DataStoreReference
        if isinstance(elem, DataStoreReference) and hasattr(elem, "data_store_id") and elem.data_store_id:
            obj = get_obj(elem.data_store_id, elem_id, "data_store")
            if obj is not None and isinstance(obj, DataStore):
                elem.data_store = obj
            elif obj is not None:
                log.warning(f"Document '{doc_id}': data_store_id '{elem.data_store_id}' on DataStoreReference '{elem_id}' resolved to non-DataStore type {type(obj)}")
        # DataInput / DataOutput / Property / ItemDefinition
        if hasattr(elem, "item_subject_ref_id") and elem.item_subject_ref_id and isinstance(elem, (DataInput, DataOutput, DataFlowElement, DataObject, DataStore, DataElement, Property)):
            obj = get_obj(elem.item_subject_ref_id, elem_id, "item_subject_ref")
            if obj is not None and isinstance(obj, ItemDefinition):
                elem.item_subject_ref = obj
            elif obj is not None:
                log.warning(f"Document '{doc_id}': item_subject_ref_id '{elem.item_subject_ref_id}' on {type(elem)} '{elem_id}' resolved to non-ItemDefinition type {type(obj)}")
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
                        log.warning(f"Document '{doc_id}': error_ref_id '{eid}' on Operation '{elem_id}' resolved to non-Error type {type(obj)}")
                elem.error_refs = resolved_errors
        # Lane
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
                        log.warning(f"Document '{doc_id}': flow_node_ref_id '{fid}' on Lane '{elem_id}' resolved to non-FlowNode type {type(obj)}")
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
                        log.warning(f"Document '{doc_id}': participant_ref_id '{pid}' on ChoreographyActivity '{elem_id}' resolved to non-Participant type {type(obj)}")
                elem.participant_refs = resolved_parts
            if hasattr(elem, "initiating_participant_ref_id") and elem.initiating_participant_ref_id:
                obj = get_obj(elem.initiating_participant_ref_id, elem_id, "initiating_participant_ref")
                if obj is not None and isinstance(obj, Participant):
                    elem.initiating_participant_ref = obj
                elif obj is not None:
                    log.warning(f"Document '{doc_id}': initiating_participant_ref_id '{elem.initiating_participant_ref_id}' on ChoreographyActivity '{elem_id}' resolved to non-Participant type {type(obj)}")
        # CorrelationKey
        if isinstance(elem, CorrelationKey) and hasattr(elem, "property_ref_ids"):
            resolved_props = []
            for pid in elem.property_ref_ids:
                obj = get_obj(pid, elem_id, "property_ref")
                if obj is not None and isinstance(obj, CorrelationProperty):
                    resolved_props.append(obj)
                elif obj is not None:
                    log.warning(f"Document '{doc_id}': property_ref_id '{pid}' on CorrelationKey '{elem_id}' resolved to non-CorrelationProperty type {type(obj)}")
            elem.property_refs = resolved_props
        # CorrelationSubscription
        if isinstance(elem, CorrelationSubscription) and hasattr(elem, "correlation_key_ref_id") and elem.correlation_key_ref_id:
            obj = get_obj(elem.correlation_key_ref_id, elem_id, "correlation_key_ref")
            if obj is not None and isinstance(obj, CorrelationKey):
                elem.correlation_key_ref = obj
            elif obj is not None:
                log.warning(f"Document '{doc_id}': correlation_key_ref_id '{elem.correlation_key_ref_id}' on CorrelationSubscription '{elem_id}' resolved to non-CorrelationKey type {type(obj)}")
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
                        log.warning(f"Document '{doc_id}': participant_ref_id '{pid}' on ConversationNode '{elem_id}' resolved to non-Participant type {type(obj)}")
                elem.participant_refs = resolved_parts
            if hasattr(elem, "message_flow_ref_ids"):
                resolved_mfs = []
                for mfid in elem.message_flow_ref_ids:
                    obj = get_obj(mfid, elem_id, "message_flow_ref")
                    if obj is not None and isinstance(obj, MessageFlow):
                        resolved_mfs.append(obj)
                    elif obj is not None:
                        log.warning(f"Document '{doc_id}': message_flow_ref_id '{mfid}' on ConversationNode '{elem_id}' resolved to non-MessageFlow type {type(obj)}")
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
                        log.warning(f"Document '{doc_id}': outer_conversation_node_ref_id '{oid}' on ConversationAssociation '{elem_id}' resolved to non-ConversationNode type {type(obj)}")
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
                log.warning(f"Document '{doc_id}': process_ref_id '{elem.process_ref_id}' on Participant '{elem_id}' resolved to non-Process type {type(obj)}")
        # BoundaryEvent
        if isinstance(elem, BoundaryEvent) and hasattr(elem, "attached_to_ref_id") and elem.attached_to_ref_id:
            obj = get_obj(elem.attached_to_ref_id, elem_id, "attached_to_ref")
            if obj is not None and isinstance(obj, Activity):
                elem.attached_to_ref = obj
            elif obj is not None:
                log.warning(f"Document '{doc_id}': attached_to_ref_id '{elem.attached_to_ref_id}' on BoundaryEvent '{elem_id}' resolved to non-Activity type {type(obj)}")
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
                        log.warning(f"Document '{doc_id}': source_id '{sid}' on LinkEventDefinition '{elem_id}' resolved to non-LinkEventDefinition type {type(obj)}")
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
                log.warning(f"Document '{doc_id}': element {elem_id} has model_element_id but is not a diagram element; ignoring")
```

- [ ] **Step 2: Replace `_resolve_references` in `bpmn_xml_parser.py`**

Replace the method body with a delegation:

```python
    def _resolve_references(self, doc, strict: bool, doc_id: str) -> None:
        from .bpmn_reference_resolver import resolve_references as _rr
        _rr(doc, strict, doc_id, self.logger)
```

- [ ] **Step 3: Run tests to confirm no regression**

Run: `python -m pytest tests/ -k "bpmn" --asyncio-mode=auto -q`
Expected: No failures.

---

### Task 3: Extract html constants → `html_parser_constants.py`

**Files:**
- Create: `engines/document/parsers/usdm_parsers/html/html_parser_constants.py`
- Modify: `engines/document/parsers/usdm_parsers/html/html_parser.py:39-173`

- [ ] **Step 1: Create `html_parser_constants.py`**

```python
# engines/document/parsers/usdm_parsers/html/html_parser_constants.py
"""Constants and lookup tables for the HTML parser."""

from __future__ import annotations

from ....models.base import ElementType


VOID_ELEMENTS = frozenset({
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
})

RAW_TEXT_ELEMENTS = frozenset({"script", "style"})

RCDATA_ELEMENTS = frozenset({"textarea", "title"})

ARIA_ROLE_MAP: dict[str, ElementType] = {
    "article": ElementType.SECTION,
    "banner": ElementType.HEADER,
    "complementary": ElementType.SECTION,
    "contentinfo": ElementType.FOOTER,
    "dialog": ElementType.SECTION,
    "document": ElementType.SECTION,
    "form": ElementType.FORM_FIELD,
    "img": ElementType.IMAGE,
    "list": ElementType.LIST,
    "listitem": ElementType.LIST_ITEM,
    "main": ElementType.SECTION,
    "navigation": ElementType.SECTION,
    "region": ElementType.SECTION,
    "search": ElementType.SECTION,
    "alert": ElementType.SECTION,
    "alertdialog": ElementType.SECTION,
    "application": ElementType.SECTION,
    "button": ElementType.FORM_FIELD,
    "checkbox": ElementType.FORM_FIELD,
    "columnheader": ElementType.TABLE,
    "combobox": ElementType.FORM_FIELD,
    "definition": ElementType.SECTION,
    "directory": ElementType.SECTION,
    "feed": ElementType.SECTION,
    "figure": ElementType.SECTION,
    "grid": ElementType.TABLE,
    "gridcell": ElementType.TABLE,
    "group": ElementType.SECTION,
    "heading": ElementType.HEADING,
    "link": ElementType.LINK,
    "listbox": ElementType.LIST,
    "log": ElementType.SECTION,
    "marquee": ElementType.SECTION,
    "math": ElementType.MATH,
    "menu": ElementType.SECTION,
    "menubar": ElementType.SECTION,
    "menuitem": ElementType.SECTION,
    "menuitemcheckbox": ElementType.FORM_FIELD,
    "menuitemradio": ElementType.FORM_FIELD,
    "none": ElementType.SECTION,
    "note": ElementType.SECTION,
    "option": ElementType.FORM_FIELD,
    "presentation": ElementType.SECTION,
    "progressbar": ElementType.FORM_FIELD,
    "radio": ElementType.FORM_FIELD,
    "radiogroup": ElementType.FORM_FIELD,
    "row": ElementType.TABLE,
    "rowgroup": ElementType.TABLE,
    "rowheader": ElementType.TABLE,
    "scrollbar": ElementType.FORM_FIELD,
    "searchbox": ElementType.FORM_FIELD,
    "separator": ElementType.DIVIDER,
    "slider": ElementType.FORM_FIELD,
    "spinbutton": ElementType.FORM_FIELD,
    "status": ElementType.SECTION,
    "switch": ElementType.FORM_FIELD,
    "tab": ElementType.SECTION,
    "tablist": ElementType.SECTION,
    "tabpanel": ElementType.SECTION,
    "term": ElementType.SECTION,
    "textbox": ElementType.FORM_FIELD,
    "timer": ElementType.SECTION,
    "toolbar": ElementType.FORM_FIELD,
    "tooltip": ElementType.SECTION,
    "tree": ElementType.SECTION,
    "treegrid": ElementType.TABLE,
    "treeitem": ElementType.SECTION,
}

ARIA_STATES_PROPERTIES = frozenset({
    "aria-label", "aria-labelledby", "aria-describedby",
    "aria-hidden", "aria-expanded", "aria-pressed", "aria-checked",
    "aria-selected", "aria-current", "aria-disabled", "aria-readonly",
    "aria-required", "aria-invalid", "aria-live", "aria-atomic",
    "aria-relevant", "aria-busy", "aria-dropeffect", "aria-grabbed",
    "aria-activedescendant", "aria-controls", "aria-flowto", "aria-owns",
    "aria-posinset", "aria-setsize", "aria-level",
    "aria-valuenow", "aria-valuemin", "aria-valuemax", "aria-valuetext",
    "aria-orientation", "aria-multiselectable", "aria-sort",
    "aria-colcount", "aria-colindex", "aria-colspan",
    "aria-rowcount", "aria-rowindex", "aria-rowspan",
    "aria-details", "aria-errormessage", "aria-keyshortcuts",
    "aria-roledescription",
})

SEMANTIC_SECTION_MAP: dict[str, str] = {
    "article": "article",
    "section": "section",
    "nav": "nav",
    "aside": "aside",
    "main": "main",
}

INLINE_STYLE_PROPERTY_MAP: dict[str, str] = {
    "font-family": "font",
    "font-size": "size",
    "font-weight": "weight",
    "font-style": "style",
    "color": "color",
    "background-color": "background",
    "text-align": "alignment",
    "text-decoration": "decoration",
    "text-transform": "transform",
    "line-height": "line_height",
    "letter-spacing": "letter_spacing",
    "word-spacing": "word_spacing",
    "text-indent": "text_indent",
    "vertical-align": "vertical_align",
    "white-space": "white_space",
    "list-style-type": "list_style",
}

SEMANTIC_HEADING = frozenset({"h1", "h2", "h3", "h4", "h5", "h6"})
SEMANTIC_INLINE_FORMAT = frozenset({
    "b", "strong", "i", "em", "u", "ins", "s", "del", "strike",
    "sub", "sup", "mark", "small", "big", "abbr", "cite", "code",
    "dfn", "kbd", "q", "samp", "var", "time", "data", "ruby", "rt",
    "rp", "bdi", "bdo", "wbr", "br", "font", "tt", "strike",
})

FORM_INPUT_TYPES = frozenset({
    "text", "password", "email", "tel", "url", "number", "range",
    "date", "time", "datetime-local", "color", "checkbox", "radio",
    "file", "hidden", "submit", "reset", "button", "image", "search",
})
```

- [ ] **Step 2: Create `html_parser_utils.py`**

```python
# engines/document/parsers/usdm_parsers/html/html_parser_utils.py
"""Utility functions for the HTML parser."""

from __future__ import annotations

import re
from typing import Any

from ....models.usdm_models import CharacterStyle

from .html_parser_constants import ARIA_STATES_PROPERTIES, INLINE_STYLE_PROPERTY_MAP


def parse_inline_style(style_str: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for declaration in style_str.split(";"):
        declaration = declaration.strip()
        if ":" not in declaration:
            continue
        prop, _, value = declaration.partition(":")
        prop = prop.strip().lower()
        value = value.strip()
        if not prop or not value:
            continue
        if prop in INLINE_STYLE_PROPERTY_MAP:
            key = INLINE_STYLE_PROPERTY_MAP[prop]
            result[key] = value
    return result


def parse_css_style_element(css_text: str) -> list[dict[str, Any]]:
    styles: list[dict[str, Any]] = []
    rule_pattern = re.compile(r'([^{]+)\{([^}]+)\}', re.DOTALL)
    for selector_match, body_match in rule_pattern.findall(css_text):
        selector = selector_match.strip()
        props = parse_inline_style(body_match)
        if props:
            styles.append({"selector": selector, "properties": props})
    return styles


def attrs_to_dict(attrs: list[tuple[str, str | None]]) -> dict[str, str]:
    result: dict[str, str] = {}
    for key, value in attrs:
        if value is not None:
            result[key] = value
    return result


def extract_aria(attrs: dict[str, str]) -> tuple[str | None, dict[str, str]]:
    role = attrs.get("role")
    aria_attrs: dict[str, str] = {}
    for key, value in attrs.items():
        if key in ARIA_STATES_PROPERTIES:
            aria_attrs[key] = value
    return role, aria_attrs


def extract_microdata(attrs: dict[str, str]) -> dict[str, str]:
    keys = ("itemscope", "itemtype", "itemprop", "itemid", "itemref")
    return {k: attrs[k] for k in keys if k in attrs}


def extract_rdfa(attrs: dict[str, str]) -> dict[str, str]:
    keys = ("vocab", "typeof", "property", "resource", "prefix", "content", "datatype", "rel", "rev")
    return {k: attrs[k] for k in keys if k in attrs}


def safe_int(value: str | None, default: int = 1) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def build_character_style_from_css(css_props: dict[str, Any]) -> CharacterStyle:
    kwargs: dict[str, Any] = {}
    if "font" in css_props:
        kwargs["font_family"] = css_props["font"]
    if "size" in css_props:
        try:
            kwargs["size"] = float(css_props["size"].replace("px", "").replace("pt", "").replace("em", ""))
        except (ValueError, TypeError):
            pass
    if "weight" in css_props:
        w = css_props["weight"]
        if w in ("bold", "bolder") or (w.isdigit() and int(w) >= 700):
            kwargs["bold"] = True
    if "style" in css_props:
        if "italic" in css_props["style"] or "oblique" in css_props["style"]:
            kwargs["italic"] = True
    if "decoration" in css_props:
        dec = css_props["decoration"]
        if "underline" in dec:
            kwargs["underline"] = True
        if "line-through" in dec:
            kwargs["strike"] = True
    if "color" in css_props:
        kwargs["color"] = css_props["color"]
    if "background" in css_props:
        kwargs["background"] = css_props["background"]
        kwargs["highlight"] = css_props["background"]
    if "transform" in css_props:
        t = css_props["transform"]
        if t == "uppercase":
            kwargs["all_caps"] = True
    if "alignment" in css_props:
        kwargs["alignment"] = css_props["alignment"]
    return CharacterStyle(name="inline", **kwargs) if kwargs else CharacterStyle(name="inline")
```

- [ ] **Step 3: Replace constants + functions in `html_parser.py`**

Replace lines 39-282 (constants definitions + module-level functions) with imports:

```python
from .html_parser_constants import (
    ARIA_ROLE_MAP, ARIA_STATES_PROPERTIES, FORM_INPUT_TYPES,
    INLINE_STYLE_PROPERTY_MAP, RAW_TEXT_ELEMENTS, RCDATA_ELEMENTS,
    SEMANTIC_HEADING, SEMANTIC_INLINE_FORMAT, SEMANTIC_SECTION_MAP,
    VOID_ELEMENTS,
)
from .html_parser_utils import (
    attrs_to_dict, build_character_style_from_css, extract_aria,
    extract_microdata, extract_rdfa, parse_css_style_element,
    parse_inline_style, safe_float, safe_int,
)
```

Then update all references in `HTMLDocumentParser` methods to call the new function names (e.g., `_parse_inline_style` → `parse_inline_style`).

- [ ] **Step 4: Run tests to confirm no regression**

Run: `python -m pytest tests/ -k "html" --asyncio-mode=auto -q`
Expected: No failures.
