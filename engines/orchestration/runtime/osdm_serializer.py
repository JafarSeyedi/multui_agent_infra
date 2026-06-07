"""OSDM serialization and deserialization for runtime objects.

Converts between runtime state and OSDM document types for persistence
and interchange.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from ...document.models.media_types import MEDIA_TYPES
from ...document.models.osdm_models import (
    BPMNDocument,
    CMMNDocument,
    StateMachineDocument,
    DMNDocument,
    CEPDocument,
    Process,
    ProcessType,
    EventType,
    EventDefinitionType,
    GatewayType,
    LoopType,
    MultiInstanceBehavior,
    TransactionMethod,
    SequenceFlow,
    StartEvent,
    EndEvent,
    IntermediateCatchEvent,
    IntermediateThrowEvent,
    BoundaryEvent,
    ExclusiveGateway,
    InclusiveGateway,
    ParallelGateway,
    EventBasedGateway,
    ComplexGateway,
    Task,
    ServiceTask,
    UserTask,
    ManualTask,
    ScriptTask,
    BusinessRuleTask,
    SendTask,
    ReceiveTask,
    CallActivity,
    SubProcess,
    TransactionSubProcess,
    AdHocSubProcess,
    StandardLoopCharacteristics,
    MultiInstanceLoopCharacteristics,
    Message,
    Signal,
    Error,
    Escalation,
    DataObject,
    DataObjectReference,
    DataStoreReference,
    DataAssociation,
    DataInputAssociation,
    DataOutputAssociation,
    DataState,
    InputOutputSpecification,
    InputSet,
    OutputSet,
    DataInput,
    DataOutput,
    FormalExpression,
    CorrelationKey,
    CorrelationProperty,
    CorrelationSubscription,
    CorrelationPropertyBinding,
    Participant,
    Lane,
    LaneSet,
    MessageFlow,
    Association,
    Group,
    TextAnnotation,
    Auditing,
    Monitoring,
    Interface,
    Operation,
    EndPoint,
    Resource,
    ResourceParameter,
    ResourceRole,
    HumanPerformer,
    Performer,
    PotentialOwner,
    Category,
    CategoryValue,
    Artifact,
    FlowElement,
    FlowNode,
    Activity,
    ActivityType,
    TaskType,
    SubProcessType,
    GatewayDirection,
    AssociationDirection,
    EventBasedGatewayType,
    TimerEventType,
    ItemKind,
    CallActivityType,
    ChoreographyLoopType,
    ChoreographyTask,
    Choreography,
    ConversationLink,
    Conversation,
    ConversationNode,
    ConversationAssociation,
    PlanItem,
    DiscretionaryItem,
    CaseFileItem,
    CaseTask,
    ProcessTask,
    HumanTask,
    EntryCriterion,
    ExitCriterion,
    Stage,
    Milestone,
    EventListener,
    Sentry,
    SentryExpression,
    ApplicabilityRule,
    InformationRequirement,
    KnowledgeRequirement,
    AuthorityRequirement,
    DecisionService,
    Decision,
    BusinessKnowledgeModel,
    InputData,
    KnowledgeSource,
    DecisionTable,
    State,
    StateNode,
    Transition,
    StateTransition,
    StateInvoke,
    StateMachineRegion,
    StateMachineModel,
    PseudoState,
    PseudoStateKind,
    Place,
    PnTransition,
    Arc,
    EventStream,
    CEPRule,
    CEPOperator,
    InteractionProtocol,
    InteractionModel,
    Extension,
    ExtensionDefinition,
    ExtensionAttributeValue,
    Bounds,
    DiagramElement,
    Edge,
    Shape,
    BPMNDiagram,
    BPMNPlane,
    BPMNShape,
    BPMNEdge,
    BPMNLabel,
    ItemDefinition,
    Rendering,
    RenderingForm,
    ComplexBehaviorDefinition,
    ErrorHandlingConfig,
    RetryConfig,
    TimeoutConfig,
    ErrorHandlingOperator,
    CloudResourceBinding,
    BaseOSDMDocument,
)


logger = logging.getLogger(__name__)


@dataclass
class SerializationContext:
    document_id: str = ""
    document_type: str = ""
    include_diagram: bool = False
    include_metadata: bool = True
    include_history: bool = False
    include_variables: bool = True
    include_tokens: bool = True
    include_incidents: bool = False
    include_audit_log: bool = False


@dataclass
class SerializationResult:
    document: BaseOSDMDocument | None = None
    format: str = ""
    content: str = ""
    content_type: str = ""
    size_bytes: int = 0
    errors: list[str] = field(default_factory=list)


class OsdmSerializer:
    """Serializes runtime state to OSDM documents."""

    def serialize_bpmn_process(
        self,
        process_data: dict[str, Any],
        context: SerializationContext | None = None,
    ) -> SerializationResult:
        ctx = context or SerializationContext()
        try:
            process = self._dict_to_process(process_data)
            doc = BPMNDocument(
                title=process.name or process.id,
                document_id=ctx.document_id or process.id,
                processes=[process],
                media_type=MEDIA_TYPES["bpmn_xml"],
            )
            return SerializationResult(
                document=doc,
                format="osdm",
                content_type="application/json",
            )
        except Exception as e:
            logger.error("BPMN serialization failed: %s", e)
            return SerializationResult(errors=[str(e)])

    def serialize_cmmn_case(
        self,
        case_data: dict[str, Any],
        context: SerializationContext | None = None,
    ) -> SerializationResult:
        ctx = context or SerializationContext()
        try:
            doc = CMMNDocument(
                title=case_data.get("name", "Case"),
                document_id=ctx.document_id or case_data.get("id", ""),
                media_type=MEDIA_TYPES["cmmn_xml"],
            )
            return SerializationResult(document=doc, format="osdm", content_type="application/json")
        except Exception as e:
            logger.error("CMMN serialization failed: %s", e)
            return SerializationResult(errors=[str(e)])

    def serialize_state_machine(
        self,
        sm_data: dict[str, Any],
        context: SerializationContext | None = None,
    ) -> SerializationResult:
        ctx = context or SerializationContext()
        try:
            doc = StateMachineDocument(
                title=sm_data.get("name", "StateMachine"),
                document_id=ctx.document_id or sm_data.get("id", ""),
                media_type=MEDIA_TYPES["uml_state_machine_xml"],
            )
            return SerializationResult(document=doc, format="osdm", content_type="application/json")
        except Exception as e:
            logger.error("State machine serialization failed: %s", e)
            return SerializationResult(errors=[str(e)])

    def serialize_dmn_decision(
        self,
        dmn_data: dict[str, Any],
        context: SerializationContext | None = None,
    ) -> SerializationResult:
        ctx = context or SerializationContext()
        try:
            doc = DMNDocument(
                title=dmn_data.get("name", "Decision"),
                document_id=ctx.document_id or dmn_data.get("id", ""),
                media_type=MEDIA_TYPES["dmn_xml"],
            )
            return SerializationResult(document=doc, format="osdm", content_type="application/json")
        except Exception as e:
            logger.error("DMN serialization failed: %s", e)
            return SerializationResult(errors=[str(e)])

    def _dict_to_process(self, data: dict[str, Any]) -> Process:
        process = Process(
            id=data.get("id", ""),
            name=data.get("name", ""),
            process_type=ProcessType(data.get("process_type", "None")),
            is_executable=data.get("is_executable", True),
            is_closed=data.get("is_closed", False),
        )
        flow_elements = data.get("flow_elements", data.get("elements", {}))
        if flow_elements:
            process.flow_elements = {}
            for eid, edata in flow_elements.items():
                if isinstance(edata, dict):
                    element = self._dict_to_flow_element(edata)
                    if element:
                        process.flow_elements[eid] = element
        lane_sets = data.get("lane_sets", [])
        if lane_sets:
            process.lane_sets = []
            for ls_data in lane_sets:
                lanes = []
                for l_data in ls_data.get("lanes", []):
                    lanes.append(Lane(
                        id=l_data.get("id", ""),
                        name=l_data.get("name"),
                        flow_node_refs=l_data.get("flow_node_refs", []),
                    ))
                process.lane_sets.append(LaneSet(
                    id=ls_data.get("id", ""),
                    lanes=lanes,
                ))
        return process

    def _dict_to_flow_element(self, data: dict[str, Any]) -> FlowElement | None:
        etype = str(data.get("type", "")).lower()
        eid = data.get("id", "")
        name = data.get("name", "")
        if "startevent" in etype:
            return StartEvent(id=eid, name=name)
        elif "endevent" in etype:
            return EndEvent(id=eid, name=name)
        elif "intermediatecatch" in etype:
            return IntermediateCatchEvent(id=eid, name=name)
        elif "intermediatethrow" in etype:
            return IntermediateThrowEvent(id=eid, name=name)
        elif "boundary" in etype:
            return BoundaryEvent(
                id=eid, name=name,
                attached_to_ref=data.get("payload", {}).get("attachedToRef"),
                cancel_activity=data.get("payload", {}).get("cancelActivity", True),
            )
        elif "exclusivegateway" in etype:
            return ExclusiveGateway(id=eid, name=name)
        elif "inclusivegateway" in etype:
            return InclusiveGateway(id=eid, name=name)
        elif "parallelgateway" in etype:
            return ParallelGateway(id=eid, name=name)
        elif "eventbasedgateway" in etype:
            return EventBasedGateway(id=eid, name=name)
        elif "complexgateway" in etype:
            return ComplexGateway(id=eid, name=name)
        elif "servicetask" in etype:
            return ServiceTask(id=eid, name=name)
        elif "usertask" in etype:
            return UserTask(id=eid, name=name)
        elif "manualtask" in etype:
            return ManualTask(id=eid, name=name)
        elif "scripttask" in etype:
            return ScriptTask(id=eid, name=name)
        elif "businessruletask" in etype:
            return BusinessRuleTask(id=eid, name=name)
        elif "sendtask" in etype:
            return SendTask(id=eid, name=name)
        elif "receivetask" in etype:
            return ReceiveTask(id=eid, name=name)
        elif "callactivity" in etype:
            return CallActivity(id=eid, name=name)
        elif "subprocess" in etype:
            sp_type = SubProcessType.EMBEDDED
            payload = data.get("payload", {})
            sp_type_str = payload.get("subProcessType", "embedded").lower()
            for spt in SubProcessType:
                if spt.value.lower() == sp_type_str:
                    sp_type = spt
                    break
            if "transaction" in etype:
                return TransactionSubProcess(id=eid, name=name, method=TransactionMethod.COMPENSATE)
            elif "adhoc" in etype:
                return AdHocSubProcess(id=eid, name=name)
            return SubProcess(id=eid, name=name, sub_process_type=sp_type)
        elif "task" in etype:
            return Task(id=eid, name=name)
        elif "sequenceflow" in etype:
            return SequenceFlow(
                id=eid,
                source_ref=data.get("source", data.get("sourceRef", "")),
                target_ref=data.get("target", data.get("targetRef", "")),
                condition_expression=data.get("condition", data.get("conditionExpression")),
            )
        else:
            return FlowElement(id=eid, name=name)


class OsdmDeserializer:
    """Deserializes OSDM documents to runtime state."""

    def deserialize_bpmn_document(self, document: BPMNDocument) -> dict[str, Any]:
        result: dict[str, Any] = {
            "id": document.document_id,
            "type": "bpmn",
            "processes": [],
        }
        for process in document.processes:
            proc_data = self._process_to_dict(process)
            result["processes"].append(proc_data)
        return result

    def _process_to_dict(self, process: Process) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": process.id,
            "name": process.name or "",
            "process_type": process.process_type.value if process.process_type else "None",
            "is_executable": process.is_executable,
            "is_closed": process.is_closed,
            "flow_elements": {},
        }
        if process.flow_elements:
            for eid, element in process.flow_elements.items():
                data["flow_elements"][eid] = self._flow_element_to_dict(element)
        return data

    def _flow_element_to_dict(self, element: FlowElement) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": element.id,
            "name": getattr(element, "name", "") or "",
            "type": element.__class__.__name__,
        }
        if isinstance(element, SequenceFlow):
            data["source"] = element.source_ref
            data["target"] = element.target_ref
            if element.condition_expression:
                data["condition"] = element.condition_expression
        if isinstance(element, BoundaryEvent):
            data["payload"] = {
                "attachedToRef": element.attached_to_ref,
                "cancelActivity": getattr(element, "cancel_activity", True),
            }
        if isinstance(element, SubProcess):
            data["payload"] = {
                "subProcessType": element.sub_process_type.value if hasattr(element, "sub_process_type") else "embedded",
            }
        return data
