# engines/document/parsers/osdm_parsers/bpmn_constants.py
"""BPMN 2.0 namespace constants and tag-to-class mapping tables."""

from __future__ import annotations

from ..models.bpmn_models import (
    AdHocSubProcess,
    BoundaryEvent,
    BusinessRuleTask,
    CallActivity,
    CancelEventDefinition,
    CompensateEventDefinition,
    ComplexGateway,
    ConditionalEventDefinition,
    EndEvent,
    ErrorEventDefinition,
    EscalationEventDefinition,
    EventBasedGateway,
    ExclusiveGateway,
    InclusiveGateway,
    IntermediateCatchEvent,
    IntermediateThrowEvent,
    LinkEventDefinition,
    ManualTask,
    MessageEventDefinition,
    ParallelGateway,
    ReceiveTask,
    ScriptTask,
    SendTask,
    ServiceTask,
    SignalEventDefinition,
    StartEvent,
    SubProcess,
    Task,
    TerminateEventDefinition,
    TimerEventDefinition,
    TransactionSubProcess,
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
