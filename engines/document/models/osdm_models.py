# engines/document/models/osdm_models.py
"""
OSDM – Orchestration Standard Definition Model (Unified, Type‑Safe)
========================================================================
A single, declarative model covering workflows, state machines,
cases, decisions, event processing, and multi‑agent interactions.
Every reference is a typed object; no raw string IDs are used for
navigation within the loaded model.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from .models.base import BaseDocument
from .media_types import DocumentStandard, DocumentFormat
from .msdm_models import MSDMDocument
from .ssdm_models import SSDM_DOCUMENT
from .tsdm_models import TSDMDocument   # added missing import

# ═══════════════════════════════════════════════════════════════
# New Enums for previously untyped fields
# ═══════════════════════════════════════════════════════════════
class YAWLJoinType(str, Enum):
    XOR = "xor"
    AND = "and"
    OR = "or"
    NONE = "none"

class YAWLSplitType(str, Enum):
    XOR = "xor"
    AND = "and"
    OR = "or"
    NONE = "none"
       
class ParticipantBandKind(str, Enum):
    TOP_INITIATING = "top_initiating"
    MIDDLE_INITIATING = "middle_initiating"
    BOTTOM_INITIATING = "bottom_initiating"
    TOP_NON_INITIATING = "top_non_initiating"
    MIDDLE_NON_INITIATING = "middle_non_initiating"
    BOTTOM_NON_INITIATING = "bottom_non_initiating"

class MessageVisibleKind(str, Enum):
    INITIATING = "initiating"
    NON_INITIATING = "non_initiating"

class AlignmentKind(str, Enum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"

class TransactionMethod(str, Enum):
    COMPENSATE = "##compensate"
    STORE = "##store"
    IMAGE = "##image"
    WS_ATOMIC_TRANSACTION = "http://schemas.xmlsoap.org/ws/2004/10/wsat"
    WS_BUSINESS_ACTIVITY = "http://docs.oasis-open.org/ws-tx/wsba/2006/06/AtomicOutcome"

class TimerCalculationType(str, Enum):
    ISO8601 = "Iso8601"
    NUMBER = "Number"
    PROPERTY = "Property"
    FORMULA = "Formula"

class TimeReference(str, Enum):
    PROPERTY = "Property"
    PROCESS_START_TIME = "ProcessStartTime"
    ACTIVITY_START_TIME = "ActivityStartTime"
    EVENT_START_TIME = "EventStartTime"

class DurationResolution(str, Enum):
    SECOND = "Second"
    MINUTE = "Minute"
    HOUR = "Hour"
    DAY = "Day"

class EscapeType(str, Enum):
    pass   # placeholder if needed

class CorrelationPropertyType(str, Enum):
    KEY = "key"
    VALUE = "value"

class CaseFileMultiplicity(str, Enum):
    ZERO_OR_ONE = "0..1"
    EXACTLY_ONE = "1"
    ZERO_OR_MORE = "0..*"
    ONE_OR_MORE = "1..*"

class EventListenerType(str, Enum):
    USER = "user"
    TIMER = "timer"
    SIGNAL = "signal"
    MESSAGE = "message"
    ESCALATION = "escalation"
    ERROR = "error"
    CANCEL = "cancel"
    COMPENSATION = "compensation"
    CONDITIONAL = "conditional"
    LINK = "link"

class SentryExpression(BaseElement):
    """Formal expression for an onPart or ifPart of a Sentry."""
    language: Optional[ScriptLanguage] = None
    body: str = ""

class DecisionTable(BaseElement):
    """Structured decision table with rows (maps of input/output columns)."""
    columns: List[str] = field(default_factory=list)
    rows: List[Dict[str, str]] = field(default_factory=list)

class ActionList(BaseElement):
    """List of action identifiers, each potentially a reference to a TSDM tool or script."""
    actions: List[Union[str, Script]] = field(default_factory=list)

# ── Original Enums (unchanged, included for completeness) ────────
class ActivityType(str, Enum):
    TASK = "Task"
    SUB_PROCESS = "SubProcess"
    CALL_ACTIVITY = "CallActivity"

class TaskType(str, Enum):
    NONE = "None"
    SERVICE = "Service"
    USER = "User"
    MANUAL = "Manual"
    SCRIPT = "Script"
    BUSINESS_RULE = "BusinessRule"
    SEND = "Send"
    RECEIVE = "Receive"

class SubProcessType(str, Enum):
    EMBEDDED = "Embedded"
    EVENT = "Event"
    TRANSACTION = "Transaction"
    AD_HOC = "AdHoc"

class GatewayType(str, Enum):
    EXCLUSIVE = "Exclusive"
    INCLUSIVE = "Inclusive"
    PARALLEL = "Parallel"
    COMPLEX = "Complex"
    EVENT_BASED = "EventBased"

class EventType(str, Enum):
    START = "Start"
    END = "End"
    INTERMEDIATE_CATCH = "IntermediateCatch"
    INTERMEDIATE_THROW = "IntermediateThrow"
    BOUNDARY = "Boundary"

class LoopType(str, Enum):
    NONE = "None"
    STANDARD = "Standard"
    MULTI_INSTANCE = "MultiInstance"

class MultiInstanceBehavior(str, Enum):
    NONE = "None"
    ONE = "One"
    ALL = "All"
    COMPLEX = "Complex"

class AdHocOrdering(str, Enum):
    PARALLEL = "Parallel"
    SEQUENTIAL = "Sequential"

class ScriptLanguage(str, Enum):
    JS = "JS"
    PYTHON = "Python"

class CallActivityType(str, Enum):
    PROCESS = "Process"
    GLOBAL_TASK = "GlobalTask"

class ProcessType(str, Enum):
    NONE = "None"
    PUBLIC = "Public"
    PRIVATE = "Private"

class GatewayDirection(str, Enum):
    UNSPECIFIED = "Unspecified"
    CONVERGING = "Converging"
    DIVERGING = "Diverging"
    MIXED = "Mixed"

class AssociationDirection(str, Enum):
    NONE = "None"
    ONE = "One"
    BOTH = "Both"

class EventBasedGatewayType(str, Enum):
    EXCLUSIVE = "Exclusive"
    PARALLEL = "Parallel"

class ItemKind(str, Enum):
    INFORMATION = "Information"
    PHYSICAL = "Physical"

class TimerEventType(str, Enum):
    DATE = "dateTime"
    CYCLE = "timeCycle"
    DURATION = "timeDuration"

class RelationshipDirection(str, Enum):
    NONE = "None"
    FORWARD = "Forward"
    BACKWARD = "Backward"
    BOTH = "Both"

class CEPOperator(str, Enum):
    AND = "and"
    OR = "or"
    NOT = "not"
    SEQUENCE = "sequence"
    WINDOW = "window"
    THRESHOLD = "threshold"
    ABSENCE = "absence"

class WorkflowStateType(str, Enum):
    OPERATION = "operation"
    EVENT = "event"
    SWITCH = "switch"
    DELAY = "delay"
    PARALLEL = "parallel"
    FOREACH = "forEach"
    INJECT = "inject"
    CALLBACK = "callback"
    SUBFLOW = "subFlow"

class ResourceParameterType(str, Enum):
    USER_FIELD = "UserField"
    ENTITY_FIELD = "EntityField"
    CLAIM = "Claim"
    ROLE = "Role"

class ResourceRoleType(str, Enum):
    NONE = "None"
    FIRST_LEVEL_POTENTIAL_OWNER = "FirstLevelPotentialOwner"
    DELEGATE_POTENTIAL_OWNER = "DelegatePotentialOwner"
    SUPERVISOR_POTENTIAL_OWNER = "SupervisorPotentialOwner"
    PHYSICAL_PERFORMER = "PhysicalPerformerResource"
    AUTHORIZED_USER = "AuthorizedUser"
    CONFIRMER = "Confirmer"
    COSTING_RESOURCE = "CostingResource"
    CAPACITY_CONSTRAINT_RESOURCE = "CapacityConstraintResource"
    PROCESS_MANAGER = "ProcessManagerResource"
    NOTIFICATION_RESOURCE = "NotificationResource"

class PotentialOwnerType(str, Enum):
    FIRST_LEVEL = "FirstLevelPotentialOwner"
    DELEGATE = "DelegatePotentialOwner"
    SUPERVISOR = "SupervisorPotentialOwner"

class InteractionNodeType(str, Enum):
    EVENT = "event"
    TASK = "task"
    PARTICIPANT = "participant"
    UNDEFINED = "undefined"

class EventDefinitionType(str, Enum):
    NONE = "None"
    MESSAGE = "Message"
    TIMER = "Timer"
    SIGNAL = "Signal"
    ERROR = "Error"
    ESCALATION = "Escalation"
    COMPENSATION = "Compensation"
    CONDITIONAL = "Conditional"
    LINK = "Link"
    CANCEL = "Cancel"
    TERMINATE = "Terminate"
    MULTIPLE = "Multiple"

class ChoreographyLoopType(str, Enum):
    NONE = "None"
    STANDARD = "Standard"
    MULTI_INSTANCE_SEQUENTIAL = "MultiInstanceSequential"
    MULTI_INSTANCE_PARALLEL = "MultiInstanceParallel"

class DecisionLogicType(str, Enum):
    DECISION_TABLE = "decisionTable"
    INVOCATION = "invocation"
    LITERAL_EXPRESSION = "literalExpression"
    CONTEXT = "context"
    RELATION = "relation"
    FUNCTION_DEFINITION = "functionDefinition"

class PseudoStateKind(str, Enum):
    INITIAL = "initial"
    DEEP_HISTORY = "deepHistory"
    SHALLOW_HISTORY = "shallowHistory"
    JOIN = "join"
    FORK = "fork"
    JUNCTION = "junction"
    CHOICE = "choice"
    ENTRY_POINT = "entryPoint"
    EXIT_POINT = "exitPoint"
    TERMINATE = "terminate"

class InteractionStrategy(str, Enum):
    BROADCAST = "broadcast"
    DEBATE = "debate"
    COORDINATOR = "coordinator"
    ENSEMBLE = "ensemble"
    ROUND_ROBIN = "round_robin"
    SELF_REFINE = "self_refine"
    GROUP_CHAT = "group_chat"

# ═══════════════════════════════════════════════════════════════
# Base elements (unchanged)
# ═══════════════════════════════════════════════════════════════
@dataclass
class BaseElement:
    id: str
    name: Optional[str] = None
    documentation: Optional[str] = None

@dataclass
class RootElement(BaseElement):
    pass

@dataclass
class StateNode(BaseElement):
    incoming_transitions: List[Transition] = field(default_factory=list)
    outgoing_transitions: List[Transition] = field(default_factory=list)

@dataclass
class Transition(BaseElement):
    source: Optional[StateNode] = None
    target: Optional[StateNode] = None
    condition: Optional[FormalExpression] = None
    action: Optional[Script] = None           # was str

# ── Extension definitions ────────────────────────────────────────
@dataclass
class ExtensionAttributeDefinition:
    name: str
    extension_type: str
    is_reference: bool = False

@dataclass
class ExtensionDefinition:
    name: str
    extension_attribute_definitions: List[ExtensionAttributeDefinition] = field(default_factory=list)

@dataclass
class ExtensionAttributeValue:
    extension_attribute_definition: Optional[ExtensionAttributeDefinition] = None
    value: Optional[str] = None
    value_ref: Optional[str] = None

@dataclass
class Extension:
    definition: Optional[ExtensionDefinition] = None
    must_understand: bool = False

# ── Diagram interchange ──────────────────────────────────────────
@dataclass
class Bounds:
    x: float = 0
    y: float = 0
    width: float = 0
    height: float = 0

@dataclass
class DiagramElement(BaseElement):
    owning_element: Optional[DiagramElement] = None
    model_element: Optional[BaseElement] = None

@dataclass
class Edge(DiagramElement):
    source: Optional[DiagramElement] = None
    target: Optional[DiagramElement] = None

@dataclass
class Shape(DiagramElement):
    bounds: Bounds = field(default_factory=Bounds)

@dataclass
class BPMNDiagram:
    id: str
    name: Optional[str] = None
    bounds: Bounds = field(default_factory=Bounds)
    model_element: Optional[RootElement] = None
    owned_elements: List[DiagramElement] = field(default_factory=list)

@dataclass
class BPMNPlane(DiagramElement):
    bpmn_element: Optional[BaseElement] = None

@dataclass
class BPMNShape(Shape):
    label: Optional[BPMNLabel] = None
    is_horizontal: bool = True
    is_expanded: bool = False
    is_marker_visible: bool = False
    is_message_visible: bool = False
    participant_band_kind: ParticipantBandKind = ParticipantBandKind.TOP_INITIATING   # enum, not str
    choreography_activity_shape: Optional[BPMNShape] = None

@dataclass
class BPMNEdge(Edge):
    label: Optional[BPMNLabel] = None
    message_visible_kind: MessageVisibleKind = MessageVisibleKind.NON_INITIATING   # enum

@dataclass
class BPMNLabel:
    text: str
    bounds: Bounds = field(default_factory=Bounds)
    alignment: AlignmentKind = AlignmentKind.LEFT    # enum

# ═══════════════════════════════════════════════════════════════
# Expressions
# ═══════════════════════════════════════════════════════════════
@dataclass
class BpmnExpression(BaseElement):
    pass

@dataclass
class FormalExpression(BpmnExpression):
    language: Optional[ScriptLanguage] = None
    body: Optional[str] = None
    evaluates_to_type_ref: Optional[ItemDefinition] = None

# ── Item Definition ──────────────────────────────────────────────
@dataclass
class ItemDefinition(RootElement):
    item_kind: ItemKind = ItemKind.INFORMATION
    structure_ref: Optional[MSDMDocument] = None
    import_ref: Optional[str] = None
    is_collection: bool = False

# ── Resources ────────────────────────────────────────────────────
@dataclass
class Resource(RootElement):
    resource_parameters: List[ResourceParameter] = field(default_factory=list)

@dataclass
class ResourceParameter(BaseElement):
    type: ResourceParameterType = ResourceParameterType.USER_FIELD
    is_required: bool = False

@dataclass
class ResourceAssignmentExpression(BaseElement):
    expression: Optional[FormalExpression] = None

@dataclass
class ResourceParameterBinding(BaseElement):
    parameter_ref: Optional[ResourceParameter] = None
    expression: Optional[FormalExpression] = None

@dataclass
class ResourceRole(BaseElement):
    type: ResourceRoleType = ResourceRoleType.NONE
    resource_ref: Optional[Resource] = None
    resource_assignment_expression: Optional[ResourceAssignmentExpression] = None
    resource_parameter_bindings: List[ResourceParameterBinding] = field(default_factory=list)

@dataclass
class HumanPerformer(ResourceRole):
    pass

@dataclass
class Performer(HumanPerformer):
    pass

@dataclass
class PotentialOwner(HumanPerformer):
    potential_owner_type: PotentialOwnerType = PotentialOwnerType.FIRST_LEVEL

# ── Flow Elements ────────────────────────────────────────────────
@dataclass
class FlowElement(BaseElement):
    category_values: List[CategoryValue] = field(default_factory=list)
    auditing: Optional[Auditing] = None
    monitoring: Optional[Monitoring] = None

@dataclass
class FlowNode(FlowElement):
    incoming: List[SequenceFlow] = field(default_factory=list)
    outgoing: List[SequenceFlow] = field(default_factory=list)
    input_state_id: Optional[int] = None
    output_state_id: Optional[int] = None

@dataclass
class Activity(FlowNode):
    activity_type: ActivityType = ActivityType.TASK
    loop_characteristics: Optional[LoopCharacteristics] = None
    io_specification: Optional[InputOutputSpecification] = None
    resources: List[ResourceRole] = field(default_factory=list)
    properties: List[Property] = field(default_factory=list)

@dataclass
class Task(Activity):
    task_type: TaskType = TaskType.NONE
    priority_level: Optional[float] = None
    priority_level_property: Optional[Property] = None    # was str

@dataclass
class ServiceTask(Task):
    implementation: Optional[SSDM_DOCUMENT] = None        # ssdm reference
    operation_ref: Optional[Operation] = None

@dataclass
class SendTask(Task):
    implementation: Optional[SSDM_DOCUMENT] = None
    message_ref: Optional[Message] = None
    operation_ref: Optional[Operation] = None

@dataclass
class ReceiveTask(Task):
    implementation: Optional[SSDM_DOCUMENT] = None
    message_ref: Optional[Message] = None
    operation_ref: Optional[Operation] = None
    instantiate: bool = False

@dataclass
class UserTask(Task):
    implementation: str = "##unspecified"   # placeholder for UISDMDocument
    rendering: List[Rendering] = field(default_factory=list)
    work_distribution_policy: Optional[Any] = None

@dataclass
class ManualTask(Task):
    control_by_system: bool = False

@dataclass
class Script(BaseElement):
    script_body: str
    script_language: ScriptLanguage = ScriptLanguage.PYTHON

@dataclass
class ScriptTask(Task):
    script: Optional[Script] = None

@dataclass
class BusinessRuleTask(Task):
    implementation: DecisionService         # reference to decision service

@dataclass
class CallActivity(Activity):
    called_element: Optional[Union[Process, GlobalTask]] = None
    call_activity_type: CallActivityType = CallActivityType.PROCESS
    io_binding: List[InputOutputBinding] = field(default_factory=list)

@dataclass
class SubProcess(Activity):
    sub_process_type: SubProcessType = SubProcessType.EMBEDDED
    flow_elements: Dict[str, FlowElement] = field(default_factory=dict)
    lane_sets: List[LaneSet] = field(default_factory=list)
    artifacts: List[Artifact] = field(default_factory=list)
    triggered_by_event: bool = False

@dataclass
class TransactionSubProcess(SubProcess):
    method: TransactionMethod = TransactionMethod.COMPENSATE   # enum

@dataclass
class AdHocSubProcess(SubProcess):
    ordering: AdHocOrdering = AdHocOrdering.PARALLEL
    completion_condition: Optional[FormalExpression] = None
    cancel_remaining_instances: bool = True

@dataclass
class GlobalTask(RootElement):
    task_type: TaskType = TaskType.NONE
    resources: List[ResourceRole] = field(default_factory=list)
    io_specification: Optional[InputOutputSpecification] = None
    io_binding: List[InputOutputBinding] = field(default_factory=list)
    supported_interface_refs: List[Interface] = field(default_factory=list)

@dataclass
class GlobalUserTask(GlobalTask):
    implementation: str = "##unspecified"
    rendering: List[Rendering] = field(default_factory=list)
    work_distribution_policy: Optional[Any] = None

@dataclass
class GlobalScriptTask(GlobalTask):
    script: Optional[Script] = None

@dataclass
class GlobalManualTask(GlobalTask):
    control_by_system: bool = False

@dataclass
class GlobalBusinessRuleTask(GlobalTask):
    implementation: DecisionService

@dataclass
class Rendering(BaseElement):
    pass

@dataclass
class RenderingForm(Rendering):
    form_id: Optional[str] = None
    index_form_id: Optional[str] = None
    association_field_id: Optional[str] = None

# ── Loop Characteristics ─────────────────────────────────────────
@dataclass
class LoopCharacteristics(BaseElement):
    loop_type: LoopType = LoopType.NONE

@dataclass
class StandardLoopCharacteristics(LoopCharacteristics):
    test_before: bool = False
    loop_maximum: int = 0
    loop_condition: Optional[FormalExpression] = None

@dataclass
class MultiInstanceLoopCharacteristics(LoopCharacteristics):
    is_sequential: bool = False
    completion_condition: Optional[FormalExpression] = None
    loop_cardinality: Optional[FormalExpression] = None
    loop_data_input_ref: Optional[DataInput] = None
    loop_data_output_ref: Optional[DataOutput] = None
    input_data_item: Optional[DataInput] = None
    output_data_item: Optional[DataOutput] = None
    behavior: MultiInstanceBehavior = MultiInstanceBehavior.ALL
    complex_behavior_definition: List[ComplexBehaviorDefinition] = field(default_factory=list)
    one_behavior_event_ref: Optional[EventDefinition] = None
    none_behavior_event_ref: Optional[EventDefinition] = None

@dataclass
class ComplexBehaviorDefinition(BaseElement):
    condition: Optional[FormalExpression] = None
    implicit_event: Optional[ImplicitThrowEvent] = None

# ── Input/Output ─────────────────────────────────────────────────
@dataclass
class InputOutputSpecification(BaseElement):
    data_inputs: List[DataInput] = field(default_factory=list)
    data_outputs: List[DataOutput] = field(default_factory=list)
    input_sets: List[InputSet] = field(default_factory=list)
    output_sets: List[OutputSet] = field(default_factory=list)

@dataclass
class DataInput:
    id: str
    name: str
    item_subject_ref: Optional[ItemDefinition] = None
    is_collection: bool = False

@dataclass
class DataOutput:
    id: str
    name: str
    item_subject_ref: Optional[ItemDefinition] = None
    is_collection: bool = False

@dataclass
class InputSet(BaseElement):
    data_input_refs: List[DataInputRef] = field(default_factory=list)
    output_set_refs: List[OutputSet] = field(default_factory=list)

@dataclass
class OutputSet(BaseElement):
    data_output_refs: List[DataOutputRef] = field(default_factory=list)

@dataclass
class DataInputRef:
    data_input: Optional[DataInput] = None
    is_optional: bool = False
    available_while_executing: bool = False

@dataclass
class DataOutputRef:
    data_output: Optional[DataOutput] = None
    is_optional: bool = False
    can_be_produced_while_executing: bool = False

@dataclass
class InputOutputBinding:
    input_data_ref: Optional[DataInput] = None
    output_data_ref: Optional[DataOutput] = None
    operation_ref: Optional[Operation] = None

# ── Events and Event Definitions ─────────────────────────────────
@dataclass
class Event(FlowNode):
    event_type: EventType = EventType.START
    event_definitions: List[EventDefinition] = field(default_factory=list)
    properties: List[Property] = field(default_factory=list)

@dataclass
class CatchEvent(Event):
    data_outputs: List[DataOutput] = field(default_factory=list)
    output_sets: List[OutputSet] = field(default_factory=list)
    data_output_associations: List[DataOutputAssociation] = field(default_factory=list)
    parallel_multiple: bool = False

@dataclass
class ThrowEvent(Event):
    data_inputs: List[DataInput] = field(default_factory=list)
    input_sets: List[InputSet] = field(default_factory=list)
    data_input_associations: List[DataInputAssociation] = field(default_factory=list)

@dataclass
class StartEvent(CatchEvent):
    is_interrupting: bool = True

@dataclass
class EndEvent(ThrowEvent):
    pass

@dataclass
class IntermediateCatchEvent(CatchEvent):
    pass

@dataclass
class IntermediateThrowEvent(ThrowEvent):
    pass

@dataclass
class BoundaryEvent(CatchEvent):
    cancel_activity: bool = True
    attached_to_ref: Optional[Activity] = None

@dataclass
class ImplicitThrowEvent(ThrowEvent):
    pass

@dataclass
class EventDefinition(RootElement):
    type: EventDefinitionType = EventDefinitionType.NONE

@dataclass
class MessageEventDefinition(EventDefinition):
    message_ref: Optional[Message] = None
    operation_ref: Optional[Operation] = None

@dataclass
class TimerEventDefinition(EventDefinition):
    timer_type: TimerEventType = TimerEventType.DURATION
    time_date: Optional[FormalExpression] = None
    time_cycle: Optional[FormalExpression] = None
    time_duration: Optional[FormalExpression] = None
    due_duration: Optional[DueTimeDuration] = None

@dataclass
class SignalEventDefinition(EventDefinition):
    signal_ref: Optional[Signal] = None

@dataclass
class ErrorEventDefinition(EventDefinition):
    error_ref: Optional[Error] = None

@dataclass
class EscalationEventDefinition(EventDefinition):
    escalation_ref: Optional[Escalation] = None

@dataclass
class CompensateEventDefinition(EventDefinition):
    activity_ref: Optional[Activity] = None
    wait_for_completion: bool = True

@dataclass
class ConditionalEventDefinition(EventDefinition):
    condition: Optional[FormalExpression] = None

@dataclass
class LinkEventDefinition(EventDefinition):
    sources: List[LinkEventDefinition] = field(default_factory=list)   # typed references
    target: Optional[LinkEventDefinition] = None

@dataclass
class CancelEventDefinition(EventDefinition):
    pass

@dataclass
class TerminateEventDefinition(EventDefinition):
    pass

@dataclass
class DueTimeDuration:
    calculation_type: TimerCalculationType = TimerCalculationType.ISO8601   # enum
    formula: Optional[FormalExpression] = None
    time_reference: TimeReference = TimeReference.PROPERTY                # enum
    reference_property: Optional[Property] = None
    resolution: DurationResolution = DurationResolution.SECOND             # enum
    # cron_expression: Optional[str] = None
    
# ── Data Flow ────────────────────────────────────────────────────
@dataclass
class DataFlowElement(FlowElement):
    item_subject_ref: Optional[ItemDefinition] = None
    data_state: Optional[DataState] = None

@dataclass
class DataObject(DataFlowElement):
    is_collection: bool = False

@dataclass
class DataObjectReference(DataFlowElement):
    data_object: Optional[DataObject] = None

@dataclass
class DataStore(RootElement):
    is_unlimited: bool = True
    capacity: int = 0
    item_subject_ref: Optional[ItemDefinition] = None
    data_state: Optional[DataState] = None

@dataclass
class DataStoreReference(DataFlowElement):
    data_store: Optional[DataStore] = None

@dataclass
class DataState(BaseElement):
    pass

@dataclass
class DataElement(BaseElement):
    item_subject_ref: Optional[ItemDefinition] = None
    data_state: Optional[DataState] = None

@dataclass
class Property(DataElement):
    pass

@dataclass
class DataAssociation(BaseElement):
    source_refs: List[BaseElement] = field(default_factory=list)
    target_ref: Optional[BaseElement] = None
    transformation: Optional[FormalExpression] = None
    assignments: List[Assignment] = field(default_factory=list)

@dataclass
class DataInputAssociation(DataAssociation):
    pass

@dataclass
class DataOutputAssociation(DataAssociation):
    pass

@dataclass
class Assignment(BaseElement):
    from_expr: Optional[FormalExpression] = None
    to_expr: Optional[FormalExpression] = None

# ═══════════════════════════════════════════════════════════════
# Sequence & Message Flows
# ═══════════════════════════════════════════════════════════════
@dataclass
class SequenceFlow(FlowElement):
    source_ref: Optional[FlowNode] = None
    target_ref: Optional[FlowNode] = None
    condition_expression: Optional[FormalExpression] = None
    is_immediate: bool = True
    state_id: Optional[int] = None

@dataclass
class MessageFlow(BaseElement):
    source_ref: Optional[InteractionNode] = None
    target_ref: Optional[InteractionNode] = None
    message_ref: Optional[Message] = None

# ── Gateways ─────────────────────────────────────────────────────
@dataclass
class Gateway(FlowNode):
    gateway_type: GatewayType = GatewayType.EXCLUSIVE
    gateway_direction: GatewayDirection = GatewayDirection.UNSPECIFIED

@dataclass
class ExclusiveGateway(Gateway):
    default_sequence_flow: Optional[SequenceFlow] = None

@dataclass
class InclusiveGateway(Gateway):
    default_sequence_flow: Optional[SequenceFlow] = None

@dataclass
class ParallelGateway(Gateway):
    pass

@dataclass
class EventBasedGateway(Gateway):
    event_type: EventBasedGatewayType = EventBasedGatewayType.EXCLUSIVE

@dataclass
class ComplexGateway(Gateway):
    default_sequence_flow: Optional[SequenceFlow] = None
    activation_condition: Optional[FormalExpression] = None

# ── Lanes & Pools ────────────────────────────────────────────────
@dataclass
class Lane(BaseElement):
    child_lane_set: Optional[LaneSet] = None
    partition_element_ref: Optional[BaseElement] = None
    flow_node_refs: List[FlowNode] = field(default_factory=list)
    resources: List[ResourceRole] = field(default_factory=list)

@dataclass
class LaneSet(BaseElement):
    lanes: List[Lane] = field(default_factory=list)
    parent_lane: Optional[Lane] = None

# ── Process & Collaboration ──────────────────────────────────────
@dataclass
class Process(RootElement):
    process_type: ProcessType = ProcessType.NONE
    is_executable: bool = False
    is_closed: bool = False
    auditing: Optional[Auditing] = None
    monitoring: Optional[Monitoring] = None
    flow_elements: Dict[str, FlowElement] = field(default_factory=dict)
    lane_sets: List[LaneSet] = field(default_factory=list)
    artifacts: List[Artifact] = field(default_factory=list)
    resources: List[ResourceRole] = field(default_factory=list)
    properties: List[Property] = field(default_factory=list)
    correlation_subscriptions: List[CorrelationSubscription] = field(default_factory=list)
    definitional_collaboration_ref: Optional[Collaboration] = None
    io_specification: Optional[InputOutputSpecification] = None
    io_binding: List[InputOutputBinding] = field(default_factory=list)
    supported_interface_refs: List[Interface] = field(default_factory=list)
    supports: List[Process] = field(default_factory=list)

@dataclass
class Collaboration(RootElement):
    name: Optional[str] = None
    participants: List[Participant] = field(default_factory=list)
    message_flows: List[MessageFlow] = field(default_factory=list)
    artifacts: List[Artifact] = field(default_factory=list)
    correlation_keys: List[CorrelationKey] = field(default_factory=list)
    choreography_refs: List[Choreography] = field(default_factory=list)
    conversation_associations: List[ConversationAssociation] = field(default_factory=list)
    conversations: List[ConversationNode] = field(default_factory=list)
    conversation_links: List[ConversationLink] = field(default_factory=list)
    message_flow_associations: List[MessageFlowAssociation] = field(default_factory=list)
    participant_associations: List[ParticipantAssociation] = field(default_factory=list)
    is_closed: bool = False

# ── Artifacts ────────────────────────────────────────────────────
@dataclass
class Artifact(BaseElement):
    pass

@dataclass
class Association(Artifact):
    direction: AssociationDirection = AssociationDirection.NONE
    source_ref: Optional[BaseElement] = None
    target_ref: Optional[BaseElement] = None

@dataclass
class Group(Artifact):
    category_value: Optional[CategoryValue] = None
    categorized_flow_elements: List[FlowElement] = field(default_factory=list)

@dataclass
class TextAnnotation(Artifact):
    text: str = ""
    text_format: str = "text/plain"

# ── Auditing & Monitoring ────────────────────────────────────────
@dataclass
class Auditing(BaseElement):
    save_instances: bool = False
    generate_trace_log: bool = False
    log_condition: Optional[FormalExpression] = None   # was str
    break_point_condition: Optional[FormalExpression] = None

@dataclass
class Monitoring(BaseElement):
    pass

# ── Services ─────────────────────────────────────────────────────
@dataclass
class Interface(RootElement):
    implementation_ref: Optional[SSDM_DOCUMENT] = None
    operations: Dict[str, Operation] = field(default_factory=dict)

@dataclass
class Operation(BaseElement):
    in_message_ref: Optional[Message] = None
    out_message_ref: Optional[Message] = None
    error_refs: List[Error] = field(default_factory=list)
    implementation_ref: Optional[SSDM_DOCUMENT] = None

@dataclass
class EndPoint(RootElement):
    pass

# ── Messages, Signals, Errors, Escalations ──────────────────────
@dataclass
class Message(RootElement):
    item_ref: Optional[ItemDefinition] = None

@dataclass
class Signal(RootElement):
    structure_ref: Optional[MSDMDocument] = None

@dataclass
class Error(RootElement):
    error_code: Optional[str] = None      # errorCode is a string identifier in BPMN
    structure_ref: Optional[MSDMDocument] = None

@dataclass
class Escalation(RootElement):
    escalation_code: Optional[str] = None
    structure_ref: Optional[MSDMDocument] = None

# ── Correlation ──────────────────────────────────────────────────
@dataclass
class CorrelationKey(BaseElement):
    property_refs: List[CorrelationProperty] = field(default_factory=list)

@dataclass
class CorrelationProperty(RootElement):
    property_type: CorrelationPropertyType = CorrelationPropertyType.KEY   # enum
    retrieval_expressions: List[CorrelationPropertyRetrievalExpression] = field(default_factory=list)

@dataclass
class CorrelationPropertyRetrievalExpression(BaseElement):
    message_path: Optional[FormalExpression] = None
    message_ref: Optional[Message] = None

@dataclass
class CorrelationSubscription(BaseElement):
    correlation_key_ref: Optional[CorrelationKey] = None
    property_bindings: List[CorrelationPropertyBinding] = field(default_factory=list)

@dataclass
class CorrelationPropertyBinding(BaseElement):
    data_path: Optional[FormalExpression] = None
    property_ref: Optional[CorrelationProperty] = None

# ── Categories ───────────────────────────────────────────────────
@dataclass
class Category(RootElement):
    values: List[CategoryValue] = field(default_factory=list)

@dataclass
class CategoryValue(BaseElement):
    value: str = ""

# ── Collaboration / Conversation / Choreography ──────────────────
@dataclass
class InteractionNode:
    node_type: InteractionNodeType = InteractionNodeType.UNDEFINED
    event: Optional[Event] = None
    task: Optional[Task] = None
    participant: Optional[Participant] = None

@dataclass
class MessageFlowAssociation(BaseElement):
    inner_message_flow_ref: Optional[MessageFlow] = None
    outer_message_flow_ref: Optional[MessageFlow] = None

@dataclass
class Participant(BaseElement):
    process_ref: Optional[Process] = None
    partner_role_refs: List[PartnerRole] = field(default_factory=list)
    partner_entity_refs: List[PartnerEntity] = field(default_factory=list)
    interface_refs: List[Interface] = field(default_factory=list)
    participant_multiplicity: Optional[ParticipantMultiplicity] = None
    endpoint_refs: List[EndPoint] = field(default_factory=list)

@dataclass
class ParticipantMultiplicity:
    minimum: int = 1
    maximum: int = 0

@dataclass
class ParticipantAssociation(BaseElement):
    inner_participant_ref: Optional[Participant] = None
    outer_participant_ref: Optional[Participant] = None

@dataclass
class PartnerEntity(RootElement):
    participant_refs: List[Participant] = field(default_factory=list)

@dataclass
class PartnerRole(RootElement):
    participant_refs: List[Participant] = field(default_factory=list)

@dataclass
class ConversationNode(BaseElement):
    participant_refs: List[Participant] = field(default_factory=list)
    message_flow_refs: List[MessageFlow] = field(default_factory=list)
    correlation_keys: List[CorrelationKey] = field(default_factory=list)

@dataclass
class Conversation(ConversationNode):
    pass

@dataclass
class CallConversation(ConversationNode):
    called_collaboration_ref: Optional[Collaboration] = None
    participant_associations: List[ParticipantAssociation] = field(default_factory=list)

@dataclass
class GlobalConversation(ConversationNode):
    pass

@dataclass
class SubConversation(ConversationNode):
    conversation_nodes: List[ConversationNode] = field(default_factory=list)

@dataclass
class ConversationAssociation(BaseElement):
    inner_conversation_node_ref: Optional[ConversationNode] = None
    outer_conversation_node_refs: List[ConversationNode] = field(default_factory=list)

@dataclass
class ConversationLink(BaseElement):
    source_ref: Optional[InteractionNode] = None
    target_ref: Optional[InteractionNode] = None

@dataclass
class ChoreographyActivity(FlowNode):
    participant_refs: List[Participant] = field(default_factory=list)
    initiating_participant_ref: Optional[Participant] = None
    loop_type: ChoreographyLoopType = ChoreographyLoopType.NONE
    correlation_keys: List[CorrelationKey] = field(default_factory=list)

@dataclass
class ChoreographyTask(ChoreographyActivity):
    message_flow_refs: List[MessageFlow] = field(default_factory=list)

@dataclass
class CallChoreography(ChoreographyActivity):
    called_choreography_ref: Optional[Choreography] = None
    participant_associations: List[ParticipantAssociation] = field(default_factory=list)

@dataclass
class SubChoreography(ChoreographyActivity):
    artifacts: List[Artifact] = field(default_factory=list)

@dataclass
class Choreography(Collaboration):
    flow_elements: Dict[str, FlowElement] = field(default_factory=dict)
    lane_sets: List[LaneSet] = field(default_factory=list)

@dataclass
class GlobalChoreographyTask(Choreography):
    initiating_participant_ref: Optional[Participant] = None

# ── CMMN ────────────────────────────────────────────────────────
@dataclass
class PlanItem(BaseElement):
    definition_ref: Optional[Union[Stage, Milestone, EventListener]] = None
    entry_criteria: List[EntryCriterion] = field(default_factory=list)
    exit_criteria: List[ExitCriterion] = field(default_factory=list)
    repetition_count: int = 1
    is_blocking: bool = True

@dataclass
class DiscretionaryItem(PlanItem):
    applicability_rule: Optional[ApplicabilityRule] = None

@dataclass
class CaseFileItem(BaseElement):
    item_definition_ref: Optional[ItemDefinition] = None
    multiplicity: CaseFileMultiplicity = CaseFileMultiplicity.EXACTLY_ONE   # enum

@dataclass
class CaseTask(Activity):
    case_ref: Optional[CMMNDefinition] = None

@dataclass
class ProcessTask(Activity):
    process_ref: Optional[Process] = None

@dataclass
class HumanTask(Activity):
    role_ref: Optional[ResourceRole] = None

@dataclass
class ApplicabilityRule(BaseElement):
    condition: Optional[FormalExpression] = None

@dataclass
class EntryCriterion(BaseElement):
    sentry_ref: Optional[Sentry] = None

@dataclass
class ExitCriterion(BaseElement):
    sentry_ref: Optional[Sentry] = None

@dataclass
class Stage(FlowNode):
    flow_elements: Dict[str, FlowElement] = field(default_factory=dict)
    sentries: List[Sentry] = field(default_factory=list)

@dataclass
class Milestone(FlowNode):
    pass

@dataclass
class EventListener(FlowNode):
    event_type: EventListenerType = EventListenerType.USER   # enum

@dataclass
class Sentry(BaseElement):
    on_part: Optional[FormalExpression] = None   # was str
    if_part: Optional[FormalExpression] = None   # was str

@dataclass
class CMMNDefinition:
    id: str
    name: str
    case: Stage
    plan_items: List[PlanItem] = field(default_factory=list)
    discretionary_items: List[DiscretionaryItem] = field(default_factory=list)
    case_file_items: List[CaseFileItem] = field(default_factory=list)

# ── DMN ──────────────────────────────────────────────────────────
@dataclass
class InformationRequirement(BaseElement):
    required_decision: Optional[Decision] = None
    required_input: Optional[InputData] = None

@dataclass
class KnowledgeRequirement(BaseElement):
    required_knowledge: Optional[BusinessKnowledgeModel] = None

@dataclass
class AuthorityRequirement(BaseElement):
    required_authority: Optional[KnowledgeSource] = None

@dataclass
class DecisionService(BaseElement):
    decisions: List[Decision] = field(default_factory=list)
    output_decisions: List[Decision] = field(default_factory=list)
    input_data: List[InputData] = field(default_factory=list)

@dataclass
class Decision(FlowNode):
    logic: DecisionLogicType = DecisionLogicType.DECISION_TABLE
    expression: Optional[Script] = None
    table_data: Optional[DecisionTable] = None   # replaced List[Dict[str,str]]
    information_requirements: List[InformationRequirement] = field(default_factory=list)
    knowledge_requirements: List[KnowledgeRequirement] = field(default_factory=list)
    authority_requirements: List[AuthorityRequirement] = field(default_factory=list)

@dataclass
class BusinessKnowledgeModel(FlowNode):
    logic: DecisionLogicType = DecisionLogicType.LITERAL_EXPRESSION
    expression: Optional[FormalExpression] = None

@dataclass
class InputData(FlowNode):
    entity_ref: Optional[MSDMDocument] = None

@dataclass
class KnowledgeSource(FlowNode):
    pass

@dataclass
class DMNDefinition:
    id: str
    name: str
    decisions: List[Decision] = field(default_factory=list)
    bkms: List[BusinessKnowledgeModel] = field(default_factory=list)
    input_data: List[InputData] = field(default_factory=list)



# ── Cloud‑native extensions for AWS Step Functions / Azure Logic Apps ─

class ErrorHandlingOperator(str, Enum):
    EQUALS = "Equals"
    NOT_EQUALS = "NotEquals"
    MATCHES = "Matches"

class RetryBackoffRate(float, Enum):
    LINEAR = 1.0
    DEFAULT = 2.0

@dataclass
class CloudResourceBinding:
    """Binds a state to a specific cloud resource (e.g., Lambda ARN)."""
    resource_arn: Optional[str] = None           # AWS Lambda / ECS task ARN
    azure_function_id: Optional[str] = None      # Azure Function resource ID
    parameters: Dict[str, Any] = field(default_factory=dict)  # additional parameters

@dataclass
class ErrorHandlingConfig:
    """Catch / fail configuration for a state."""
    error_equals: List[str] = field(default_factory=list)
    next_state: Optional[State] = None           # reference to the next state on error
    result_path: Optional[str] = None

@dataclass
class RetryConfig:
    """Retry policy for a state."""
    error_equals: List[str] = field(default_factory=list)
    interval_seconds: int = 1
    max_attempts: int = 3
    backoff_rate: float = 2.0

@dataclass
class TimeoutConfig:
    """Timeout configuration for a state."""
    timeout_seconds: int = 300
    heartbeat_seconds: Optional[int] = None
# ── State Machines (unified) ─────────────────────────────────────
@dataclass
class State(StateNode):
    entry_actions: List[Script] = field(default_factory=list)     # was List[str]
    exit_actions: List[Script] = field(default_factory=list)
    do_actions: List[Script] = field(default_factory=list)
    is_composite: bool = False
    is_orthogonal: bool = False
    regions: List[StateMachineRegion] = field(default_factory=list)
    # Cloud‑native extensions for AWS Step Functions / Azure Logic Apps:
    cloud_resource: Optional[CloudResourceBinding] = None
    error_handling: Optional[ErrorHandlingConfig] = None
    retry: Optional[RetryConfig] = None
    timeout: Optional[TimeoutConfig] = None
    workflow_state_type: Optional[WorkflowStateType] = None
    is_final: bool = False

@dataclass
class StateTransition(Transition):
    trigger: Optional[FormalExpression] = None   # was str
    guard: Optional[FormalExpression] = None     # was str
    effect: Optional[FormalExpression] = None    # was str
    # SCXML extensions
    parallel: bool = False
    initial: Optional[State] = None              # reference to initial state
    invoke: Optional[StateInvoke] = None

@dataclass
class StateInvoke:
    invoke_type: str              # external protocol type (scxml, http, etc.)
    src: Optional[Union[str, SSDM_DOCUMENT]] = None   # reference to service or URL
    id: Optional[str] = None

@dataclass
class StateMachineRegion(BaseElement):
    states: List[State] = field(default_factory=list)
    transitions: List[StateTransition] = field(default_factory=list)
    initial_state: Optional[State] = None        # typed reference (replaces initial_state_id)
    references: List[Union[Place, PnTransition]] = field(default_factory=list)    

@dataclass
class StateMachineModel:
    id: str
    name: str
    top_region: StateMachineRegion = field(default_factory=StateMachineRegion)
    pseudo_states: List[PseudoState] = field(default_factory=list)
    timer_trigger: Optional[TimerEventDefinition] = None
    
@dataclass
class PseudoState(StateNode):
    kind: PseudoStateKind = PseudoStateKind.INITIAL
    parent_state: Optional[State] = None   # id of the parent State (so the writer can place it correctly)

# ── Petri net elements (extend unified state) ────────────────────
@dataclass
class Place(State):
    initial_marking: int = 0
    capacity: int = 0

@dataclass
class YAWLTaskDecorator(BaseElement):
    join_type: YAWLJoinType = YAWLJoinType.NONE
    split_type: YAWLSplitType = YAWLSplitType.NONE
    # custom_form: Optional[str] = None
    # documentation: Optional[str] = None    

@dataclass
class PnTransition(Transition):
    timing_expression: Optional[FormalExpression] = None
    yawl_decorator: Optional[YAWLTaskDecorator] = None

@dataclass
class Arc(Transition):
    weight: int = 1
    inhibitor: bool = False
    reset: bool = False

# ── CEP ──────────────────────────────────────────────────────────
@dataclass
class EventStream:
    name: str
    attributes: Dict[str, str] = field(default_factory=dict)   # attribute name -> type string (acceptable)

@dataclass
class CEPRule:
    name: str
    pattern: str                        # pattern expression (kept as str)
    operator: CEPOperator = CEPOperator.AND
    window_duration: Optional[str] = None   # duration string
    filter_expression: Optional[str] = None
    actions: ActionList = field(default_factory=ActionList)   # now typed ActionList

@dataclass
class CEPDefinition:
    streams: List[EventStream] = field(default_factory=list)
    rules: List[CEPRule] = field(default_factory=list)

# ── Multi‑agent Interaction ──────────────────────────────────────
@dataclass
class InteractionProtocol(BaseElement):
    strategy: InteractionStrategy = InteractionStrategy.BROADCAST
    participants: List[Participant] = field(default_factory=list)
    message_pattern: Optional[str] = None   # still a string pattern, but could be improved later
    coordinator_ref: Optional[Participant] = None

@dataclass
class InteractionModel:
    id: str
    name: str
    protocols: List[InteractionProtocol] = field(default_factory=list)

# ═══════════════════════════════════════════════════════════════
# Top‑level OSDM Document
# ═══════════════════════════════════════════════════════════════
@dataclass
class BaseOSDMDocument(BaseDocument):
    kind: DocumentStandard = DocumentStandard.OSDM
    source_format: Optional[DocumentFormat] = None
    source_file: Optional[str] = None
    version: str = "1.0.0"
    version_description: Optional[str] = None

    root_elements: Dict[str, RootElement] = field(default_factory=dict)
    diagrams: List[BPMNDiagram] = field(default_factory=list)
    imports: List[Import] = field(default_factory=list)
    extensions: List[Extension] = field(default_factory=list)
    relationships: List[Relationship] = field(default_factory=list)
    
   
class BPMNDocument(BaseOSDMDocument):
    processes: List[Process] = field(default_factory=list)
    collaborations: List[Collaboration] = field(default_factory=list)
    choreographies: List[Choreography] = field(default_factory=list)
    global_tasks: List[GlobalTask] = field(default_factory=list)

@dataclass
class CMMNDocument(BaseOSDMDocument):
    cmmn_definitions: List[CMMNDefinition] = field(default_factory=list)

@dataclass
class StateMachineDocument(BaseOSDMDocument):
    state_machines: List[StateMachineModel] = field(default_factory=list)

@dataclass
class DMNDocument(BaseOSDMDocument):
    dmn_definitions: List[DMNDefinition] = field(default_factory=list)

@dataclass
class CEPDocument(BaseOSDMDocument):
    cep_definitions: List[CEPDefinition] = field(default_factory=list)

@dataclass
class MultiAgentInteractionDocument(BaseOSDMDocument):
    interaction_models: List[InteractionModel] = field(default_factory=list)


@dataclass
class OSDMModel:
    processes: List[BPMNDocument] = field(default_factory=list)
    collaborations: List[BPMNDocument] = field(default_factory=list)
    choreographies: List[BPMNDocument] = field(default_factory=list)
    global_tasks: List[BPMNDocument] = field(default_factory=list)
    cmmn_definitions: List[CMMNDocument] = field(default_factory=list)
    state_machines: List[CMMNDocument] = field(default_factory=list)
    dmn_definitions: List[DMNDocument] = field(default_factory=list)
    cep_definitions: List[CEPDocument] = field(default_factory=list)
    interaction_models: List[MultiAgentInteractionDocument] = field(default_factory=list)

    msdm_refs: Dict[str, MSDMDocument] = field(default_factory=dict)
    ssdm_refs: Dict[str, SSDM_DOCUMENT] = field(default_factory=dict)
    tsdm_refs: Dict[str, TSDMDocument] = field(default_factory=dict)
