from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

from engines.document.models.msdm_models import Entity
from engines.document.models.ssdm_models import ServiceBinding, ServiceOperation

from ...models.shared_models import (
    AlignmentKind,
    BaseElement,
    BaseOSDMDocument,
    Bounds,
    CaseFileMultiplicity,
    CloudResourceBinding,
    CorrelationPropertyType,
    DiagramElement,
    DurationResolution,
    Edge,
    ErrorHandlingConfig,
    ErrorHandlingOperator,
    EscapeType,
    Extension,
    ExtensionAttributeDefinition,
    ExtensionAttributeValue,
    ExtensionDefinition,
    ItemKind,
    Locator,
    MessageVisibleKind,
    ParticipantBandKind,
    PseudoStateKind,
    RelationshipDirection,
    ResourceParameterType,
    RetryBackoffRate,
    RetryConfig,
    RootElement,
    Shape,
    TimeReference,
    TimeoutConfig,
    TimerCalculationType,
    TimerEventType,
    WorkflowStateType,
)

if TYPE_CHECKING:
    from ...dmn.models.dmn_models import DecisionService


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


HandlerAdHocOrdering = AdHocOrdering


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


class TransactionMethod(str, Enum):
    COMPENSATE = "##compensate"
    STORE = "##store"
    IMAGE = "##image"
    WS_ATOMIC_TRANSACTION = "http://schemas.xmlsoap.org/ws/2004/10/wsat"
    WS_BUSINESS_ACTIVITY = "http://docs.oasis-open.org/ws-tx/wsba/2006/06/AtomicOutcome"


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


class InteractionNodeType(str, Enum):
    EVENT = "event"
    TASK = "task"
    PARTICIPANT = "participant"
    UNDEFINED = "undefined"


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


@dataclass
class BpmnExpression(BaseElement):
    pass


@dataclass
class FormalExpression(BpmnExpression):
    language: ScriptLanguage | None = None
    body: str | None = None
    evaluates_to_type_ref: ItemDefinition | None = None


@dataclass
class ItemDefinition(RootElement):
    item_kind: ItemKind = ItemKind.INFORMATION
    structure_ref: Entity | None = None
    import_ref: str | None = None
    is_collection: bool = False


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
    resource_ref_id: str | None = None
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
class Script(BaseElement):
    script_body: str = ""
    script_language: ScriptLanguage = ScriptLanguage.PYTHON


@dataclass
class Activity(FlowNode):
    activity_type: ActivityType = ActivityType.TASK
    loop_characteristics: LoopCharacteristics | None = None
    io_specification: InputOutputSpecification | None = None
    resources: list[ResourceRole] = field(default_factory=list)
    properties: list[Property] = field(default_factory=list)
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
    implementation: ServiceOperation | None = None
    operation_ref: Operation | None = None


@dataclass
class SendTask(Task):
    implementation: ServiceOperation | None = None
    message_ref: Message | None = None
    operation_ref: Operation | None = None
    message_ref_id: str | None = None
    operation_ref_id: str | None = None


@dataclass
class ReceiveTask(Task):
    implementation: ServiceOperation | None = None
    message_ref: Message | None = None
    operation_ref: Operation | None = None
    instantiate: bool = False
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
class ScriptTask(Task):
    script: Script | None = None


@dataclass
class BusinessRuleTask(Task):
    implementation: DecisionService | None = None


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
    implementation: DecisionService | None = None


@dataclass
class Pool(BaseElement):
    participants: list[Participant] = field(default_factory=list)
    lane_sets: list[LaneSet] = field(default_factory=list)


@dataclass
class Rendering(BaseElement):
    pass


@dataclass
class ResourceRendering(BaseElement):
    pass


@dataclass
class RenderingForm(Rendering):
    form_id: str | None = None
    index_form_id: str | None = None
    association_field_id: str | None = None


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
    loop_data_input_ref_id: str | None = None
    loop_data_output_ref_id: str | None = None


@dataclass
class ComplexBehaviorDefinition(BaseElement):
    condition: FormalExpression | None = None
    implicit_event: ImplicitThrowEvent | None = None


@dataclass
class InputOutputSpecification(BaseElement):
    data_inputs: list[DataInput] = field(default_factory=list)
    data_outputs: list[DataOutput] = field(default_factory=list)
    input_sets: list[InputSet] = field(default_factory=list)
    output_sets: list[OutputSet] = field(default_factory=list)


@dataclass
class DataInput:
    id: str
    name: str | None = None
    item_subject_ref: ItemDefinition | None = None
    is_collection: bool = False
    item_subject_ref_id: str | None = None


@dataclass
class DataOutput:
    id: str
    name: str | None = None
    item_subject_ref: ItemDefinition | None = None
    is_collection: bool = False
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
    attached_to_ref_id: str | None = None


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
    signal_ref_id: str | None = None


@dataclass
class ErrorEventDefinition(EventDefinition):
    error_ref: Error | None = None
    error_ref_id: str | None = None


@dataclass
class EscalationEventDefinition(EventDefinition):
    escalation_ref: Escalation | None = None
    escalation_ref_id: str | None = None


@dataclass
class CompensateEventDefinition(EventDefinition):
    activity_ref: Activity | None = None
    wait_for_completion: bool = True
    activity_ref_id: str | None = None


@dataclass
class ConditionalEventDefinition(EventDefinition):
    condition: FormalExpression | None = None


@dataclass
class LinkEventDefinition(EventDefinition):
    sources: list[LinkEventDefinition] = field(default_factory=list)
    target: LinkEventDefinition | None = None
    source_ids: list[str] = field(default_factory=list)
    target_id: str | None = None


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


@dataclass
class DataFlowElement(FlowElement):
    item_subject_ref: ItemDefinition | None = None
    data_state: DataState | None = None
    item_subject_ref_id: str | None = None


@dataclass
class DataObject(DataFlowElement):
    is_collection: bool = False
    item_subject_ref: ItemDefinition | None = None
    item_subject_ref_id: str | None = None


@dataclass
class DataObjectReference(DataFlowElement):
    data_object: DataObject | None = None
    data_object_id: str | None = None


@dataclass
class DataStore(RootElement):
    is_unlimited: bool = True
    capacity: int = 0
    item_subject_ref: ItemDefinition | None = None
    data_state: DataState | None = None
    item_subject_ref_id: str | None = None


@dataclass
class DataStoreReference(DataFlowElement):
    data_store: DataStore | None = None
    data_store_id: str | None = None


@dataclass
class DataState(BaseElement):
    pass


@dataclass
class DataElement(BaseElement):
    item_subject_ref: ItemDefinition | None = None
    data_state: DataState | None = None
    item_subject_ref_id: str | None = None


@dataclass
class Property(DataElement):
    item_subject_ref: ItemDefinition | None = None
    item_subject_ref_id: str | None = None


@dataclass
class DataAssociation(BaseElement):
    source_refs: list[BaseElement] = field(default_factory=list)
    target_ref: BaseElement | None = None
    transformation: FormalExpression | None = None
    assignments: list[Assignment] = field(default_factory=list)
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


@dataclass
class SequenceFlow(FlowElement):
    source_ref: FlowNode | None = None
    target_ref: FlowNode | None = None
    condition_expression: FormalExpression | None = None
    is_immediate: bool = True
    state_id: int | None = None
    source_ref_id: str | None = None
    target_ref_id: str | None = None


@dataclass
class MessageFlow(BaseElement):
    source_ref: InteractionNode | None = None
    target_ref: InteractionNode | None = None
    message_ref: Message | None = None
    source_ref_id: str | None = None
    target_ref_id: str | None = None
    message_ref_id: str | None = None


@dataclass
class Gateway(FlowNode):
    gateway_type: GatewayType = GatewayType.EXCLUSIVE
    gateway_direction: GatewayDirection = GatewayDirection.UNSPECIFIED


@dataclass
class ExclusiveGateway(Gateway):
    default_sequence_flow: SequenceFlow | None = None
    default_sequence_flow_id: str | None = None


@dataclass
class InclusiveGateway(Gateway):
    default_sequence_flow: SequenceFlow | None = None
    default_sequence_flow_id: str | None = None


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
    default_sequence_flow_id: str | None = None


@dataclass
class Lane(BaseElement):
    child_lane_set: LaneSet | None = None
    partition_element_ref: BaseElement | None = None
    flow_node_refs: list[FlowNode] = field(default_factory=list)
    resources: list[ResourceRole] = field(default_factory=list)
    partition_element_ref_id: str | None = None
    flow_node_ref_ids: list[str] = field(default_factory=list)


@dataclass
class LaneSet(BaseElement):
    lanes: list[Lane] = field(default_factory=list)
    parent_lane: Lane | None = None


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


@dataclass
class Artifact(BaseElement):
    pass


@dataclass
class Association(Artifact):
    direction: AssociationDirection = AssociationDirection.NONE
    source_ref: BaseElement | None = None
    target_ref: BaseElement | None = None
    source_ref_id: str | None = None
    target_ref_id: str | None = None


@dataclass
class Group(Artifact):
    category_value: CategoryValue | None = None
    categorized_flow_elements: list[FlowElement] = field(default_factory=list)


@dataclass
class TextAnnotation(Artifact):
    text: str = ""
    text_format: str = "text/plain"


@dataclass
class Auditing(BaseElement):
    save_instances: bool = False
    generate_trace_log: bool = False
    log_condition: FormalExpression | None = None
    break_point_condition: FormalExpression | None = None


@dataclass
class Monitoring(BaseElement):
    pass


@dataclass
class Interface(RootElement):
    implementation_ref: ServiceBinding | None = None
    operations: dict[str, Operation] = field(default_factory=dict)


@dataclass
class Operation(BaseElement):
    in_message_ref: Message | None = None
    out_message_ref: Message | None = None
    error_refs: list[Error] = field(default_factory=list)
    implementation_ref: ServiceOperation | None = None
    in_message_ref_id: str | None = None
    out_message_ref_id: str | None = None
    error_ref_ids: list[str] = field(default_factory=list)


@dataclass
class EndPoint(RootElement):
    pass


@dataclass
class Message(RootElement):
    item_ref: ItemDefinition | None = None
    item_ref_id: str | None = None


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


@dataclass
class CorrelationKey(BaseElement):
    property_refs: list[CorrelationProperty] = field(default_factory=list)
    property_ref_ids: list[str] = field(default_factory=list)


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
    correlation_key_ref_id: str | None = None


@dataclass
class CorrelationPropertyBinding(BaseElement):
    data_path: FormalExpression | None = None
    property_ref: CorrelationProperty | None = None


@dataclass
class Category(RootElement):
    values: list[CategoryValue] = field(default_factory=list)


@dataclass
class CategoryValue(BaseElement):
    value: str = ""


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
    inner_message_flow_ref_id: str | None = None
    outer_message_flow_ref_id: str | None = None


@dataclass
class Participant(BaseElement):
    process_ref: Process | None = None
    partner_role_refs: list[PartnerRole] = field(default_factory=list)
    partner_entity_refs: list[PartnerEntity] = field(default_factory=list)
    interface_refs: list[Interface] = field(default_factory=list)
    participant_multiplicity: ParticipantMultiplicity | None = None
    endpoint_refs: list[EndPoint] = field(default_factory=list)
    process_ref_id: str | None = None


@dataclass
class ParticipantMultiplicity:
    minimum: int = 1
    maximum: int = 0


@dataclass
class ParticipantAssociation(BaseElement):
    inner_participant_ref: Participant | None = None
    outer_participant_ref: Participant | None = None
    inner_participant_ref_id: str | None = None
    outer_participant_ref_id: str | None = None


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
    participant_ref_ids: list[str] = field(default_factory=list)
    message_flow_ref_ids: list[str] = field(default_factory=list)


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
    inner_conversation_node_ref_id: str | None = None
    outer_conversation_node_ref_ids: list[str] = field(default_factory=list)


@dataclass
class ConversationLink(BaseElement):
    source_ref: InteractionNode | None = None
    target_ref: InteractionNode | None = None
    source_ref_id: str | None = None
    target_ref_id: str | None = None


@dataclass
class ChoreographyActivity(FlowNode):
    participant_refs: list[Participant] = field(default_factory=list)
    initiating_participant_ref: Participant | None = None
    loop_type: ChoreographyLoopType = ChoreographyLoopType.NONE
    correlation_keys: list[CorrelationKey] = field(default_factory=list)
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


@dataclass
class BPMNDiagram:
    id: str
    name: str | None = None
    bounds: Bounds = field(default_factory=Bounds)
    model_element: RootElement | None = None
    model_element_id: str | None = None
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


class BPMNDocument(BaseOSDMDocument):
    processes: list[Process] = field(default_factory=list)
    collaborations: list[Collaboration] = field(default_factory=list)
    choreographies: list[Choreography] = field(default_factory=list)
    global_tasks: list[GlobalTask] = field(default_factory=list)


