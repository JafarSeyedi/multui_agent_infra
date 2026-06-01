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
from typing import Any, Optional, List, Dict

from .media_types import DocumentFormat
from .media_types import DocumentStandard
from .base import BaseDocument
from .msdm_models import MSDMDocument, Entity
from .ssdm_models import SSDMDocument, ServiceOperation, ServiceBinding
from .tsdm_models import TSDMDocument

# ═══════════════════════════════════════════════════════════════
# New Enums for previously untyped fields
# ═══════════════════════════════════════════════════════════════

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
    pass

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
    IMPLICIT_THROW = "ImplicitThrow"
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
    name: str | None = None
    documentation: str | None = None

@dataclass
class RootElement(BaseElement):
    pass

@dataclass
class StateNode(BaseElement):
    incoming_transitions: list[Transition] = field(default_factory=list)
    outgoing_transitions: list[Transition] = field(default_factory=list)

@dataclass
class Transition(BaseElement):
    source: StateNode | None = None
    target: StateNode | None = None
    condition: FormalExpression | None = None
    action: Script | None = None

# ── Extension definitions ────────────────────────────────────────
@dataclass
class ExtensionAttributeDefinition:
    name: str
    extension_type: str
    is_reference: bool = False

@dataclass
class ExtensionDefinition:
    name: str
    extension_attribute_definitions: list[ExtensionAttributeDefinition] = field(default_factory=list)

@dataclass
class ExtensionAttributeValue:
    extension_attribute_definition: ExtensionAttributeDefinition | None = None
    value: str | None = None
    value_ref: str | None = None

@dataclass
class Extension:
    definition: ExtensionDefinition | None = None
    must_understand: bool = False

# ── Diagram interchange ──────────────────────────────────────────
@dataclass
class Bounds:
    x: float = 0
    y: float = 0
    width: float = 0
    height: float = 0

@dataclass
class Locator(BaseElement):
    x: float = 0.0
    y: float = 0.0

@dataclass
class DiagramElement(BaseElement):
    owning_element: DiagramElement | None = None
    model_element: BaseElement | None = None
    model_element_id: str | None = None  # temporary ID for resolution

@dataclass
class Edge(DiagramElement):
    source: DiagramElement | None = None
    target: DiagramElement | None = None

@dataclass
class Shape(DiagramElement):
    bounds: Bounds = field(default_factory=Bounds)

@dataclass
class BPMNDiagram:
    id: str
    name: str | None = None
    bounds: Bounds = field(default_factory=Bounds)
    model_element: RootElement | None = None
    model_element_id: str | None = None   # temporary ID
    owned_elements: list[DiagramElement] = field(default_factory=list)

@dataclass
class BPMNPlane(DiagramElement):
    bpmn_element: BaseElement | None = None

@dataclass
class BPMNShape(Shape):
    label: BPMNLabel | None = None
    is_horizontal: bool = True
    is_expanded: bool = False
    is_marker_visible: bool = False
    is_message_visible: bool = False
    participant_band_kind: ParticipantBandKind = ParticipantBandKind.TOP_INITIATING

@dataclass
class BPMNEdge(Edge):
    label: BPMNLabel | None = None
    message_visible_kind: MessageVisibleKind = MessageVisibleKind.NON_INITIATING

@dataclass
class BPMNLabel:
    text: str
    bounds: Bounds = field(default_factory=Bounds)
    alignment: AlignmentKind = AlignmentKind.LEFT

# ═══════════════════════════════════════════════════════════════
# Expressions
# ═══════════════════════════════════════════════════════════════
@dataclass
class BpmnExpression(BaseElement):
    pass

@dataclass
class FormalExpression(BpmnExpression):
    language: ScriptLanguage | None = None
    body: str | None = None
    evaluates_to_type_ref: ItemDefinition | None = None

# ── Item Definition ──────────────────────────────────────────────
@dataclass
class ItemDefinition(RootElement):
    item_kind: ItemKind = ItemKind.INFORMATION
    structure_ref: Entity | None = None
    import_ref: str | None = None
    is_collection: bool = False

# ── Resources ────────────────────────────────────────────────────
@dataclass
class Resource(RootElement):
    resource_parameters: list[ResourceParameter] = field(default_factory=list)

@dataclass
class ResourceParameter(BaseElement):
    type: ResourceParameterType = ResourceParameterType.USER_FIELD
    is_required: bool = False

@dataclass
class ResourceAssignmentExpression(BaseElement):
    expression: FormalExpression | None = None

@dataclass
class ResourceParameterBinding(BaseElement):
    parameter_ref: ResourceParameter | None = None
    expression: FormalExpression | None = None

@dataclass
class ResourceRole(BaseElement):
    type: ResourceRoleType = ResourceRoleType.NONE
    resource_ref: Resource | None = None
    resource_ref_id: str | None = None  # temporary ID
    resource_assignment_expression: ResourceAssignmentExpression | None = None
    resource_parameter_bindings: list[ResourceParameterBinding] = field(default_factory=list)

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
    category_values: list[CategoryValue] = field(default_factory=list)
    auditing: Auditing | None = None
    monitoring: Monitoring | None = None

@dataclass
class FlowNode(FlowElement):
    incoming: list[SequenceFlow] = field(default_factory=list)
    outgoing: list[SequenceFlow] = field(default_factory=list)
    input_state_id: int | None = None
    output_state_id: int | None = None

@dataclass
class Activity(FlowNode):
    activity_type: ActivityType = ActivityType.TASK
    loop_characteristics: LoopCharacteristics | None = None
    io_specification: InputOutputSpecification | None = None
    resources: list[ResourceRole] = field(default_factory=list)
    properties: list[Property] = field(default_factory=list)
    # For storing DataInput/DataOutput/DataAssociation during parsing:
    data_inputs: list[DataInput] = field(default_factory=list)
    data_outputs: list[DataOutput] = field(default_factory=list)
    data_associations: list[DataAssociation] = field(default_factory=list)

@dataclass
class Task(Activity):
    task_type: TaskType = TaskType.NONE
    priority_level: float | None = None
    priority_level_property: Property | None = None

@dataclass
class ServiceTask(Task):
    implementation: ServiceOperation  | None = None
    operation_ref: Operation | None = None

@dataclass
class SendTask(Task):
    implementation: ServiceOperation  | None = None
    message_ref: Message | None = None
    operation_ref: Operation | None = None
    # Temporary fields
    message_ref_id: str | None = None
    operation_ref_id: str | None = None

@dataclass
class ReceiveTask(Task):
    implementation: ServiceOperation  | None = None
    message_ref: Message | None = None
    operation_ref: Operation | None = None
    instantiate: bool = False
    # Temporary fields
    message_ref_id: str | None = None
    operation_ref_id: str | None = None

@dataclass
class UserTask(Task):
    implementation: str = "##unspecified"
    rendering: list[Rendering] = field(default_factory=list)
    work_distribution_policy: Any | None = None

@dataclass
class ManualTask(Task):
    control_by_system: bool = False

@dataclass
class Script(BaseElement):
    script_body: str = ""
    script_language: ScriptLanguage = ScriptLanguage.PYTHON

@dataclass
class ScriptTask(Task):
    script: Script | None = None

@dataclass
class BusinessRuleTask(Task):
    implementation: Optional[DecisionService] = None

@dataclass
class CallActivity(Activity):
    called_element: Process | GlobalTask | None = None
    call_activity_type: CallActivityType = CallActivityType.PROCESS
    io_binding: list[InputOutputBinding] = field(default_factory=list)

@dataclass
class SubProcess(Activity):
    sub_process_type: SubProcessType = SubProcessType.EMBEDDED
    flow_elements: dict[str, FlowElement] = field(default_factory=dict)
    lane_sets: list[LaneSet] = field(default_factory=list)
    artifacts: list[Artifact] = field(default_factory=list)
    triggered_by_event: bool = False

@dataclass
class TransactionSubProcess(SubProcess):
    method: TransactionMethod = TransactionMethod.COMPENSATE

@dataclass
class AdHocSubProcess(SubProcess):
    ordering: AdHocOrdering = AdHocOrdering.PARALLEL
    completion_condition: FormalExpression | None = None
    cancel_remaining_instances: bool = True

@dataclass
class GlobalTask(RootElement):
    task_type: TaskType = TaskType.NONE
    resources: list[ResourceRole] = field(default_factory=list)
    io_specification: InputOutputSpecification | None = None
    io_binding: list[InputOutputBinding] = field(default_factory=list)
    supported_interface_refs: list[Interface] = field(default_factory=list)

@dataclass
class GlobalUserTask(GlobalTask):
    implementation: str = "##unspecified"
    rendering: list[Rendering] = field(default_factory=list)
    work_distribution_policy: Any | None = None

@dataclass
class GlobalScriptTask(GlobalTask):
    script: Script | None = None

@dataclass
class GlobalManualTask(GlobalTask):
    control_by_system: bool = False

@dataclass
class GlobalBusinessRuleTask(GlobalTask):
    implementation: DecisionService = field(default_factory=lambda: DecisionService(id="", decisions=[]))

@dataclass
class Rendering(BaseElement):
    pass

@dataclass
class RenderingForm(Rendering):
    form_id: str | None = None
    index_form_id: str | None = None
    association_field_id: str | None = None

# ── Loop Characteristics ─────────────────────────────────────────
@dataclass
class LoopCharacteristics(BaseElement):
    loop_type: LoopType = LoopType.NONE

@dataclass
class StandardLoopCharacteristics(LoopCharacteristics):
    test_before: bool = False
    loop_maximum: int = 0
    loop_condition: FormalExpression | None = None

@dataclass
class MultiInstanceLoopCharacteristics(LoopCharacteristics):
    is_sequential: bool = False
    completion_condition: FormalExpression | None = None
    loop_cardinality: FormalExpression | None = None
    loop_data_input_ref: DataInput | None = None
    loop_data_output_ref: DataOutput | None = None
    input_data_item: DataInput | None = None
    output_data_item: DataOutput | None = None
    behavior: MultiInstanceBehavior = MultiInstanceBehavior.ALL
    complex_behavior_definition: list[ComplexBehaviorDefinition] = field(default_factory=list)
    one_behavior_event_ref: EventDefinition | None = None
    none_behavior_event_ref: EventDefinition | None = None
    # Temporary fields
    loop_data_input_ref_id: str | None = None
    loop_data_output_ref_id: str | None = None

@dataclass
class ComplexBehaviorDefinition(BaseElement):
    condition: FormalExpression | None = None
    implicit_event: ImplicitThrowEvent | None = None

# ── Input/Output ─────────────────────────────────────────────────
@dataclass
class InputOutputSpecification(BaseElement):
    data_inputs: list[DataInput] = field(default_factory=list)
    data_outputs: list[DataOutput] = field(default_factory=list)
    input_sets: list[InputSet] = field(default_factory=list)
    output_sets: list[OutputSet] = field(default_factory=list)

@dataclass
class DataInput:
    id: str
    name: str | None = None  # name might be None in XML, but our model expects str; we'll handle in parser
    item_subject_ref: ItemDefinition | None = None
    is_collection: bool = False
    # Temporary field
    item_subject_ref_id: str | None = None

@dataclass
class DataOutput:
    id: str
    name: str | None = None
    item_subject_ref: ItemDefinition | None = None
    is_collection: bool = False
    # Temporary field
    item_subject_ref_id: str | None = None

@dataclass
class InputSet(BaseElement):
    data_input_refs: list[DataInputRef] = field(default_factory=list)
    output_set_refs: list[OutputSet] = field(default_factory=list)

@dataclass
class OutputSet(BaseElement):
    data_output_refs: list[DataOutputRef] = field(default_factory=list)

@dataclass
class DataInputRef:
    data_input: DataInput | None = None
    is_optional: bool = False
    available_while_executing: bool = False

@dataclass
class DataOutputRef:
    data_output: DataOutput | None = None
    is_optional: bool = False
    can_be_produced_while_executing: bool = False

@dataclass
class InputOutputBinding:
    input_data_ref: DataInput | None = None
    output_data_ref: DataOutput | None = None
    operation_ref: Operation | None = None

# ── Events and Event Definitions ─────────────────────────────────
@dataclass
class Event(FlowNode):
    event_type: EventType = EventType.START
    event_definitions: list[EventDefinition] = field(default_factory=list)
    properties: list[Property] = field(default_factory=list)

@dataclass
class CatchEvent(Event):
    data_outputs: list[DataOutput] = field(default_factory=list)
    output_sets: list[OutputSet] = field(default_factory=list)
    data_output_associations: list[DataOutputAssociation] = field(default_factory=list)
    parallel_multiple: bool = False

@dataclass
class ThrowEvent(Event):
    data_inputs: list[DataInput] = field(default_factory=list)
    input_sets: list[InputSet] = field(default_factory=list)
    data_input_associations: list[DataInputAssociation] = field(default_factory=list)

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
    attached_to_ref: Activity | None = None
    attached_to_ref_id: str | None = None   # temporary ID

@dataclass
class ImplicitThrowEvent(ThrowEvent):
    pass

@dataclass
class EventDefinition(RootElement):
    type: EventDefinitionType = EventDefinitionType.NONE

@dataclass
class MessageEventDefinition(EventDefinition):
    message_ref: Message | None = None
    operation_ref: Operation | None = None
    # Temporary fields
    message_ref_id: str | None = None
    operation_ref_id: str | None = None

@dataclass
class TimerEventDefinition(EventDefinition):
    timer_type: TimerEventType = TimerEventType.DURATION
    time_date: FormalExpression | None = None
    time_cycle: FormalExpression | None = None
    time_duration: FormalExpression | None = None
    due_duration: DueTimeDuration | None = None

@dataclass
class SignalEventDefinition(EventDefinition):
    signal_ref: Signal | None = None
    signal_ref_id: str | None = None   # temporary ID

@dataclass
class ErrorEventDefinition(EventDefinition):
    error_ref: Error | None = None
    error_ref_id: str | None = None    # temporary ID

@dataclass
class EscalationEventDefinition(EventDefinition):
    escalation_ref: Escalation | None = None
    escalation_ref_id: str | None = None  # temporary ID

@dataclass
class CompensateEventDefinition(EventDefinition):
    activity_ref: Activity | None = None
    wait_for_completion: bool = True
    activity_ref_id: str | None = None   # temporary ID

@dataclass
class ConditionalEventDefinition(EventDefinition):
    condition: FormalExpression | None = None

@dataclass
class LinkEventDefinition(EventDefinition):
    sources: list[LinkEventDefinition] = field(default_factory=list)
    target: LinkEventDefinition | None = None
    source_ids: list[str] = field(default_factory=list)   # temporary list of IDs
    target_id: str | None = None                         # temporary ID

@dataclass
class CancelEventDefinition(EventDefinition):
    pass

@dataclass
class TerminateEventDefinition(EventDefinition):
    pass

@dataclass
class DueTimeDuration:
    calculation_type: TimerCalculationType = TimerCalculationType.ISO8601
    formula: FormalExpression | None = None
    time_reference: TimeReference = TimeReference.PROPERTY
    reference_property: Property | None = None
    resolution: DurationResolution = DurationResolution.SECOND

# ── Data Flow ────────────────────────────────────────────────────
@dataclass
class DataFlowElement(FlowElement):
    item_subject_ref: ItemDefinition | None = None
    data_state: DataState | None = None
    # Temporary field
    item_subject_ref_id: str | None = None

@dataclass
class DataObject(DataFlowElement):
    is_collection: bool = False
    item_subject_ref: ItemDefinition | None = None
    item_subject_ref_id: str | None = None   # temporary ID

@dataclass
class DataObjectReference(DataFlowElement):
    data_object: DataObject | None = None
    data_object_id: str | None = None        # temporary ID

@dataclass
class DataStore(RootElement):
    is_unlimited: bool = True
    capacity: int = 0
    item_subject_ref: ItemDefinition | None = None
    data_state: DataState | None = None
    item_subject_ref_id: str | None = None   # temporary ID

@dataclass
class DataStoreReference(DataFlowElement):
    data_store: DataStore | None = None
    data_store_id: str | None = None         # temporary ID

@dataclass
class DataState(BaseElement):
    pass

@dataclass
class DataElement(BaseElement):
    item_subject_ref: ItemDefinition | None = None
    data_state: DataState | None = None
    item_subject_ref_id: str | None = None   # temporary ID

@dataclass
class Property(DataElement):
    item_subject_ref: ItemDefinition | None = None
    item_subject_ref_id: str | None = None   # temporary ID

@dataclass
class DataAssociation(BaseElement):
    source_refs: list[BaseElement] = field(default_factory=list)
    target_ref: BaseElement | None = None
    transformation: FormalExpression | None = None
    assignments: list[Assignment] = field(default_factory=list)
    # Temporary fields
    source_ref_ids: list[str] = field(default_factory=list)
    target_ref_id: str | None = None

@dataclass
class DataInputAssociation(DataAssociation):
    pass

@dataclass
class DataOutputAssociation(DataAssociation):
    pass

@dataclass
class Assignment(BaseElement):
    from_expr: FormalExpression | None = None
    to_expr: FormalExpression | None = None

# ═══════════════════════════════════════════════════════════════
# Sequence & Message Flows
# ═══════════════════════════════════════════════════════════════
@dataclass
class SequenceFlow(FlowElement):
    source_ref: FlowNode | None = None
    target_ref: FlowNode | None = None
    condition_expression: FormalExpression | None = None
    is_immediate: bool = True
    state_id: int | None = None
    source_ref_id: str | None = None   # temporary ID
    target_ref_id: str | None = None   # temporary ID

@dataclass
class MessageFlow(BaseElement):
    source_ref: InteractionNode | None = None
    target_ref: InteractionNode | None = None
    message_ref: Message | None = None
    # Temporary fields
    source_ref_id: str | None = None
    target_ref_id: str | None = None
    message_ref_id: str | None = None

# ── Gateways ─────────────────────────────────────────────────────
@dataclass
class Gateway(FlowNode):
    gateway_type: GatewayType = GatewayType.EXCLUSIVE
    gateway_direction: GatewayDirection = GatewayDirection.UNSPECIFIED

@dataclass
class ExclusiveGateway(Gateway):
    default_sequence_flow: SequenceFlow | None = None
    default_sequence_flow_id: str | None = None   # temporary ID

@dataclass
class InclusiveGateway(Gateway):
    default_sequence_flow: SequenceFlow | None = None
    default_sequence_flow_id: str | None = None   # temporary ID

@dataclass
class ParallelGateway(Gateway):
    pass

@dataclass
class EventBasedGateway(Gateway):
    event_type: EventBasedGatewayType = EventBasedGatewayType.EXCLUSIVE

@dataclass
class ComplexGateway(Gateway):
    default_sequence_flow: SequenceFlow | None = None
    activation_condition: FormalExpression | None = None
    default_sequence_flow_id: str | None = None   # temporary ID

# ── Lanes & Pools ────────────────────────────────────────────────
@dataclass
class Lane(BaseElement):
    child_lane_set: LaneSet | None = None
    partition_element_ref: BaseElement | None = None
    flow_node_refs: list[FlowNode] = field(default_factory=list)
    resources: list[ResourceRole] = field(default_factory=list)
    # Temporary fields
    partition_element_ref_id: str | None = None
    flow_node_ref_ids: list[str] = field(default_factory=list)

@dataclass
class LaneSet(BaseElement):
    lanes: list[Lane] = field(default_factory=list)
    parent_lane: Lane | None = None

# ── Process & Collaboration ──────────────────────────────────────
@dataclass
class Process(RootElement):
    process_type: ProcessType = ProcessType.NONE
    is_executable: bool = False
    is_closed: bool = False
    auditing: Auditing | None = None
    monitoring: Monitoring | None = None
    flow_elements: dict[str, FlowElement] = field(default_factory=dict)
    lane_sets: list[LaneSet] = field(default_factory=list)
    artifacts: list[Artifact] = field(default_factory=list)
    resources: list[ResourceRole] = field(default_factory=list)
    properties: list[Property] = field(default_factory=list)
    correlation_subscriptions: list[CorrelationSubscription] = field(default_factory=list)
    definitional_collaboration_ref: Collaboration | None = None
    io_specification: InputOutputSpecification | None = None
    io_binding: list[InputOutputBinding] = field(default_factory=list)
    supported_interface_refs: list[Interface] = field(default_factory=list)
    supports: list[Process] = field(default_factory=list)

    data_inputs: list[DataInput] = field(default_factory=list)
    data_outputs: list[DataOutput] = field(default_factory=list)
    data_associations: list[DataAssociation] = field(default_factory=list)
    message_flows: list[MessageFlow] = field(default_factory=list)

@dataclass
class Collaboration(RootElement):
    name: str | None = None
    participants: list[Participant] = field(default_factory=list)
    message_flows: list[MessageFlow] = field(default_factory=list)
    artifacts: list[Artifact] = field(default_factory=list)
    correlation_keys: list[CorrelationKey] = field(default_factory=list)
    choreography_refs: list[Choreography] = field(default_factory=list)
    conversation_associations: list[ConversationAssociation] = field(default_factory=list)
    conversations: list[ConversationNode] = field(default_factory=list)
    conversation_links: list[ConversationLink] = field(default_factory=list)
    message_flow_associations: list[MessageFlowAssociation] = field(default_factory=list)
    participant_associations: list[ParticipantAssociation] = field(default_factory=list)
    is_closed: bool = False

# ── Artifacts ────────────────────────────────────────────────────
@dataclass
class Artifact(BaseElement):
    pass

@dataclass
class Association(Artifact):
    direction: AssociationDirection = AssociationDirection.NONE
    source_ref: BaseElement | None = None
    target_ref: BaseElement | None = None
    source_ref_id: str | None = None   # temporary ID
    target_ref_id: str | None = None   # temporary ID

@dataclass
class Group(Artifact):
    category_value: CategoryValue | None = None
    categorized_flow_elements: list[FlowElement] = field(default_factory=list)

@dataclass
class TextAnnotation(Artifact):
    text: str = ""
    text_format: str = "text/plain"

# ── Auditing & Monitoring ────────────────────────────────────────
@dataclass
class Auditing(BaseElement):
    save_instances: bool = False
    generate_trace_log: bool = False
    log_condition: FormalExpression | None = None
    break_point_condition: FormalExpression | None = None

@dataclass
class Monitoring(BaseElement):
    pass

# ── Services ─────────────────────────────────────────────────────
@dataclass
class Interface(RootElement):
    implementation_ref: ServiceBinding  | None = None
    operations: dict[str, Operation] = field(default_factory=dict)

@dataclass
class Operation(BaseElement):
    in_message_ref: Message | None = None
    out_message_ref: Message | None = None
    error_refs: list[Error] = field(default_factory=list)
    implementation_ref: ServiceOperation  | None = None
    # Temporary fields
    in_message_ref_id: str | None = None
    out_message_ref_id: str | None = None
    error_ref_ids: list[str] = field(default_factory=list)

@dataclass
class EndPoint(RootElement):
    pass

# ── Messages, Signals, Errors, Escalations ──────────────────────
@dataclass
class Message(RootElement):
    item_ref: ItemDefinition | None = None
    item_ref_id: str | None = None   # temporary ID

@dataclass
class Signal(RootElement):
    structure_ref: Entity | None = None

@dataclass
class Error(RootElement):
    error_code: str | None = None
    structure_ref: Entity | None = None

@dataclass
class Escalation(RootElement):
    escalation_code: str | None = None
    structure_ref: Entity | None = None

# ── Correlation ──────────────────────────────────────────────────
@dataclass
class CorrelationKey(BaseElement):
    property_refs: list[CorrelationProperty] = field(default_factory=list)
    property_ref_ids: list[str] = field(default_factory=list)   # temporary IDs

@dataclass
class CorrelationProperty(RootElement):
    property_type: CorrelationPropertyType = CorrelationPropertyType.KEY
    retrieval_expressions: list[CorrelationPropertyRetrievalExpression] = field(default_factory=list)

@dataclass
class CorrelationPropertyRetrievalExpression(BaseElement):
    message_path: FormalExpression | None = None
    message_ref: Message | None = None

@dataclass
class CorrelationSubscription(BaseElement):
    correlation_key_ref: CorrelationKey | None = None
    property_bindings: list[CorrelationPropertyBinding] = field(default_factory=list)
    correlation_key_ref_id: str | None = None   # temporary ID

@dataclass
class CorrelationPropertyBinding(BaseElement):
    data_path: FormalExpression | None = None
    property_ref: CorrelationProperty | None = None

# ── Categories ───────────────────────────────────────────────────
@dataclass
class Category(RootElement):
    values: list[CategoryValue] = field(default_factory=list)

@dataclass
class CategoryValue(BaseElement):
    value: str = ""

# ── Collaboration / Conversation / Choreography ──────────────────
@dataclass
class InteractionNode:
    node_type: InteractionNodeType = InteractionNodeType.UNDEFINED
    event: Event | None = None
    task: Task | None = None
    participant: Participant | None = None

@dataclass
class MessageFlowAssociation(BaseElement):
    inner_message_flow_ref: MessageFlow | None = None
    outer_message_flow_ref: MessageFlow | None = None
    inner_message_flow_ref_id: str | None = None   # temporary ID
    outer_message_flow_ref_id: str | None = None   # temporary ID

@dataclass
class Participant(BaseElement):
    process_ref: Process | None = None
    partner_role_refs: list[PartnerRole] = field(default_factory=list)
    partner_entity_refs: list[PartnerEntity] = field(default_factory=list)
    interface_refs: list[Interface] = field(default_factory=list)
    participant_multiplicity: ParticipantMultiplicity | None = None
    endpoint_refs: list[EndPoint] = field(default_factory=list)
    process_ref_id: str | None = None   # temporary ID

@dataclass
class ParticipantMultiplicity:
    minimum: int = 1
    maximum: int = 0

@dataclass
class ParticipantAssociation(BaseElement):
    inner_participant_ref: Participant | None = None
    outer_participant_ref: Participant | None = None
    inner_participant_ref_id: str | None = None   # temporary ID
    outer_participant_ref_id: str | None = None   # temporary ID

@dataclass
class PartnerEntity(RootElement):
    participant_refs: list[Participant] = field(default_factory=list)

@dataclass
class PartnerRole(RootElement):
    participant_refs: list[Participant] = field(default_factory=list)

@dataclass
class ConversationNode(BaseElement):
    participant_refs: list[Participant] = field(default_factory=list)
    message_flow_refs: list[MessageFlow] = field(default_factory=list)
    correlation_keys: list[CorrelationKey] = field(default_factory=list)
    participant_ref_ids: list[str] = field(default_factory=list)   # temporary IDs
    message_flow_ref_ids: list[str] = field(default_factory=list) # temporary IDs

@dataclass
class Conversation(ConversationNode):
    pass

@dataclass
class CallConversation(ConversationNode):
    called_collaboration_ref: Collaboration | None = None
    participant_associations: list[ParticipantAssociation] = field(default_factory=list)

@dataclass
class GlobalConversation(ConversationNode):
    pass

@dataclass
class SubConversation(ConversationNode):
    conversation_nodes: list[ConversationNode] = field(default_factory=list)

@dataclass
class ConversationAssociation(BaseElement):
    inner_conversation_node_ref: ConversationNode | None = None
    outer_conversation_node_refs: list[ConversationNode] = field(default_factory=list)
    inner_conversation_node_ref_id: str | None = None          # temporary ID
    outer_conversation_node_ref_ids: list[str] = field(default_factory=list)  # temporary IDs

@dataclass
class ConversationLink(BaseElement):
    source_ref: InteractionNode | None = None
    target_ref: InteractionNode | None = None
    source_ref_id: str | None = None   # temporary ID
    target_ref_id: str | None = None   # temporary ID

@dataclass
class ChoreographyActivity(FlowNode):
    participant_refs: list[Participant] = field(default_factory=list)
    initiating_participant_ref: Participant | None = None
    loop_type: ChoreographyLoopType = ChoreographyLoopType.NONE
    correlation_keys: list[CorrelationKey] = field(default_factory=list)
    # Temporary fields
    participant_ref_ids: list[str] = field(default_factory=list)
    initiating_participant_ref_id: str | None = None

@dataclass
class ChoreographyTask(ChoreographyActivity):
    message_flow_refs: list[MessageFlow] = field(default_factory=list)

@dataclass
class CallChoreography(ChoreographyActivity):
    called_choreography_ref: Choreography | None = None
    participant_associations: list[ParticipantAssociation] = field(default_factory=list)

@dataclass
class SubChoreography(ChoreographyActivity):
    artifacts: list[Artifact] = field(default_factory=list)

@dataclass
class Choreography(Collaboration):
    flow_elements: dict[str, FlowElement] = field(default_factory=dict)
    lane_sets: list[LaneSet] = field(default_factory=list)

@dataclass
class GlobalChoreographyTask(Choreography):
    initiating_participant_ref: Participant | None = None

# ── CMMN ────────────────────────────────────────────────────────
@dataclass
class PlanItem(BaseElement):
    definition_ref: Stage | Milestone | EventListener | None = None
    entry_criteria: list[EntryCriterion] = field(default_factory=list)
    exit_criteria: list[ExitCriterion] = field(default_factory=list)
    repetition_count: int = 1
    is_blocking: bool = True
    # Temporary field for parsing
    _definition_ref_id: str | None = None
    
@dataclass
class DiscretionaryItem(PlanItem):
    applicability_rule: ApplicabilityRule | None = None

@dataclass
class CaseFileItem(BaseElement):
    item_definition_ref: ItemDefinition | None = None
    multiplicity: CaseFileMultiplicity = CaseFileMultiplicity.EXACTLY_ONE
    _item_definition_ref_id: str | None = None
    
@dataclass
class CaseTask(Activity):
    case_ref: CMMNDefinition | None = None
    _case_ref_id: str | None = None

@dataclass
class ProcessTask(Activity):
    process_ref: Process | None = None
    _process_ref_id: str | None = None

@dataclass
class HumanTask(Activity):
    role_ref: ResourceRole | None = None
    _role_ref_id: str | None = None

@dataclass
class ApplicabilityRule(BaseElement):
    condition: FormalExpression | None = None

@dataclass
class EntryCriterion(BaseElement):
    sentry_ref: Sentry | None = None
    _sentry_ref_id: str | None = None

@dataclass
class ExitCriterion(BaseElement):
    sentry_ref: Sentry | None = None
    _sentry_ref_id: str | None = None

@dataclass
class Stage(FlowNode):
    flow_elements: dict[str, FlowElement] = field(default_factory=dict)
    sentries: list[Sentry] = field(default_factory=list)

@dataclass
class Milestone(FlowNode):
    pass

@dataclass
class EventListener(FlowNode):
    event_type: EventListenerType = EventListenerType.USER

@dataclass
class Sentry(BaseElement):
    on_part: FormalExpression | None = None
    if_part: FormalExpression | None = None

@dataclass
class CMMNDefinition:
    id: str
    name: str
    case: Stage
    plan_items: list[PlanItem] = field(default_factory=list)
    discretionary_items: list[DiscretionaryItem] = field(default_factory=list)
    case_file_items: list[CaseFileItem] = field(default_factory=list)

# ── DMN ──────────────────────────────────────────────────────────
@dataclass
class InformationRequirement(BaseElement):
    required_decision: Decision | None = None
    required_input: InputData | None = None
    # Temporary fields for parsing (not serialized)
    _required_decision_id: str | None = None
    _required_input_id: str | None = None
    
@dataclass
class KnowledgeRequirement(BaseElement):
    required_knowledge: BusinessKnowledgeModel | None = None
    _required_knowledge_id: str | None = None    

@dataclass
class AuthorityRequirement(BaseElement):
    required_authority: KnowledgeSource | None = None
    _required_authority_id: str | None = None
    
@dataclass
class DecisionService(BaseElement):
    decisions: list[Decision] = field(default_factory=list)
    output_decisions: list[Decision] = field(default_factory=list)
    input_data: list[InputData] = field(default_factory=list)

@dataclass
class LiteralExpression(BaseElement):
    body: str | None = None

@dataclass
class UnaryTests(BaseElement):
    body: str | None = None

@dataclass
class InputClause(BaseElement):
    input_expression: FormalExpression | LiteralExpression | None = None
    input_values: list[Any] | None = None

@dataclass
class OutputClause(BaseElement):
    name: str | None = None
    output_values: list[Any] | None = None
    default_output: LiteralExpression | None = None

@dataclass
class DecisionRule(BaseElement):
    input_entries: list[UnaryTests | FormalExpression] = field(default_factory=list)
    output_entries: list[LiteralExpression | FormalExpression] = field(default_factory=list)

@dataclass
class DecisionTable(BaseElement):
    hit_policy: str = "UNIQUE"
    aggregation: str | None = None
    inputs: list[InputClause] = field(default_factory=list)
    outputs: list[OutputClause] = field(default_factory=list)
    rules: list[DecisionRule] = field(default_factory=list)

@dataclass
class Decision(FlowNode):
    logic: DecisionLogicType = DecisionLogicType.DECISION_TABLE
    expression: Script | None = None
    table_data: DecisionTable | None = None
    decision_table: DecisionTable | None = None
    information_requirements: list[InformationRequirement] = field(default_factory=list)
    knowledge_requirements: list[KnowledgeRequirement] = field(default_factory=list)
    authority_requirements: list[AuthorityRequirement] = field(default_factory=list)

@dataclass
class BusinessKnowledgeModel(FlowNode):
    logic: DecisionLogicType = DecisionLogicType.LITERAL_EXPRESSION
    expression: FormalExpression | None = None

@dataclass
class InputData(FlowNode):
    entity_ref: Entity | None = None

@dataclass
class KnowledgeSource(FlowNode):
    pass

@dataclass
class DMNDefinition:
    id: str
    name: str
    decisions: list[Decision] = field(default_factory=list)
    bkms: list[BusinessKnowledgeModel] = field(default_factory=list)
    input_data: list[InputData] = field(default_factory=list)
    knowledge_sources: list[KnowledgeSource] = field(default_factory=list)

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
    resource_arn: str | None = None
    azure_function_id: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)

@dataclass
class ErrorHandlingConfig:
    error_equals: list[str] = field(default_factory=list)
    next_state: State | None = None
    result_path: str | None = None

@dataclass
class RetryConfig:
    error_equals: list[str] = field(default_factory=list)
    interval_seconds: int = 1
    max_attempts: int = 3
    backoff_rate: float = 2.0

@dataclass
class TimeoutConfig:
    timeout_seconds: int = 300
    heartbeat_seconds: int | None = None

# ── State Machines (unified) ─────────────────────────────────────
@dataclass
class State(StateNode):
    entry_actions: list[Script] = field(default_factory=list)
    exit_actions: list[Script] = field(default_factory=list)
    do_actions: list[Script] = field(default_factory=list)
    is_composite: bool = False
    is_orthogonal: bool = False
    regions: list[StateMachineRegion] = field(default_factory=list)
    cloud_resource: CloudResourceBinding | None = None
    error_handling: ErrorHandlingConfig | None = None
    retry: RetryConfig | None = None
    timeout: TimeoutConfig | None = None
    workflow_state_type: WorkflowStateType | None = None
    is_final: bool = False
    parallel: bool = False                     # SCXML <parallel>
    initial_state_id: str | None = None        # Temporary reference to child state ID
    invoke: StateInvoke | None = None          # SCXML <invoke>
    initial: State | PseudoState | None = None
    # graphml fields:
    node_type: str | None = None
    locators: list[Locator] = field(default_factory=list)

@dataclass
class StateTransition(Transition):
    trigger: FormalExpression | None = None
    guard: FormalExpression | None = None
    effect: FormalExpression | None = None
    # Temporary field for target ID during parsing
    _target_id: str | None = None
    # graphml fields:
    edge_type: str | None = None
    locators: list[Locator] = field(default_factory=list)
    directed: bool = True    
    
@dataclass
class StateInvoke:
    invoke_type: str
    src: str | ServiceOperation  | None = None
    id: str | None = None

@dataclass
class StateMachineRegion(BaseElement):
    states: list[State] = field(default_factory=list)
    transitions: list[StateTransition] = field(default_factory=list)
    initial_state: State | None = None
    places: list[Place] = field(default_factory=list)               # Petri net places
    pn_transitions: list[PnTransition] = field(default_factory=list) # Petri net transitions    
    arcs: list[Arc] = field(default_factory=list)                   # Petri net arcs
    
@dataclass
class StateMachineModel:
    id: str
    name: str
    top_region: StateMachineRegion = field(default_factory=lambda: StateMachineRegion(id=""))
    pseudo_states: list[PseudoState] = field(default_factory=list)
    timer_trigger: TimerEventDefinition | None = None

@dataclass
class PseudoState(StateNode):
    kind: PseudoStateKind = PseudoStateKind.INITIAL
    parent_state: State | None = None

# ── Petri net elements (extend unified state) ────────────────────
@dataclass
class Place(State):
    initial_marking: int = 0
    capacity: int = 0

@dataclass
class PnTransition(Transition):
    timing_expression: FormalExpression | None = None

@dataclass
class Arc(Transition):
    weight: int = 1
    inhibitor: bool = False
    reset: bool = False
    arc_source: Place | PnTransition | None = None
    arc_target: Place | PnTransition | None = None
    
# ── CEP ──────────────────────────────────────────────────────────
@dataclass
class EventStream:
    name: str
    attributes: dict[str, str] = field(default_factory=dict)

@dataclass
class CEPRule:
    name: str
    pattern: str
    operator: CEPOperator = CEPOperator.AND
    window_duration: str | None = None
    filter_expression: str | None = None
    actions: ActionList = field(default_factory=lambda: ActionList(id="", actions=[]))

@dataclass
class CEPDefinition:
    id: str
    name: str
    streams: list[EventStream] = field(default_factory=list)
    rules: list[CEPRule] = field(default_factory=list)

# ── Multi‑agent Interaction ──────────────────────────────────────
@dataclass
class InteractionProtocol(BaseElement):
    strategy: InteractionStrategy = InteractionStrategy.BROADCAST
    participants: list[Participant] = field(default_factory=list)
    message_pattern: str | None = None
    coordinator_ref: Participant | None = None

@dataclass
class InteractionModel:
    id: str
    name: str
    protocols: list[InteractionProtocol] = field(default_factory=list)

# ═══════════════════════════════════════════════════════════════
# Top‑level OSDM Document
# ═══════════════════════════════════════════════════════════════
@dataclass
class BaseOSDMDocument(BaseDocument):
    kind: DocumentStandard = DocumentStandard.OSDM
    source_format: DocumentFormat | None = None
    source_file: str | None = None
    version: str = "1.0.0"
    version_description: str | None = None

    root_elements: dict[str, RootElement] = field(default_factory=dict)
    diagrams: list[BPMNDiagram] = field(default_factory=list)
    extensions: list[Extension] = field(default_factory=list)


class BPMNDocument(BaseOSDMDocument):
    processes: list[Process] = field(default_factory=list)
    collaborations: list[Collaboration] = field(default_factory=list)
    choreographies: list[Choreography] = field(default_factory=list)
    global_tasks: list[GlobalTask] = field(default_factory=list)

@dataclass
class CMMNDocument(BaseOSDMDocument):
    cmmn_definitions: list[CMMNDefinition] = field(default_factory=list)

@dataclass
class StateMachineDocument(BaseOSDMDocument):
    state_machines: list[StateMachineModel] = field(default_factory=list)

@dataclass
class DMNDocument(BaseOSDMDocument):
    dmn_definitions: list[DMNDefinition] = field(default_factory=list)

@dataclass
class CEPDocument(BaseOSDMDocument):
    cep_definitions: list[CEPDefinition] = field(default_factory=list)

@dataclass
class MultiAgentInteractionDocument(BaseOSDMDocument):
    interaction_models: list[InteractionModel] = field(default_factory=list)


@dataclass
class OSDMModel:
    processes: list[BPMNDocument] = field(default_factory=list)
    collaborations: list[BPMNDocument] = field(default_factory=list)
    choreographies: list[BPMNDocument] = field(default_factory=list)
    global_tasks: list[BPMNDocument] = field(default_factory=list)
    cmmn_definitions: list[CMMNDocument] = field(default_factory=list)
    state_machines: list[CMMNDocument] = field(default_factory=list)
    dmn_definitions: list[DMNDocument] = field(default_factory=list)
    cep_definitions: list[CEPDocument] = field(default_factory=list)
    interaction_models: list[MultiAgentInteractionDocument] = field(default_factory=list)

    msdm_refs: dict[str, MSDMDocument] = field(default_factory=dict)
    ssdm_refs: dict[str, SSDMDocument ] = field(default_factory=dict)
    tsdm_refs: dict[str, TSDMDocument] = field(default_factory=dict)


# Helper dataclasses that need to be defined after the main ones
@dataclass
class SentryExpression(FormalExpression):
    pass

@dataclass
class DecisionTable(BaseElement):
    columns: list[str] = field(default_factory=list)
    rows: list[dict[str, str]] = field(default_factory=list)

@dataclass
class ActionList(BaseElement):
    actions: list[str | Script] = field(default_factory=list)