"""OSDM compliance tests — verify handlers use OSDM types correctly."""

from __future__ import annotations

import pytest

from engines.orchestration.models.osdm_models import (
    ActivityType,
    AdHocOrdering,
    ChoreographyLoopType,
    EventDefinitionType,
    EventType,
    GatewayType,
    GatewayDirection,
    LoopType,
    MultiInstanceBehavior,
    TransactionMethod,
    ScriptLanguage,
    ProcessType,
    SubProcessType,
    TaskType,
    CallActivityType,
    TimerEventType,
    ItemKind,
    AssociationDirection,
    EventBasedGatewayType,
    MessageVisibleKind,
    ParticipantBandKind,
    RelationshipDirection,
    CaseFileMultiplicity,
    CorrelationPropertyType,
    EscapeType,
    DurationResolution,
    TimeReference,
    TimerCalculationType,
    WorkflowStateType,
    ResourceParameterType,
    ResourceRoleType,
    PotentialOwnerType,
    InteractionNodeType,
    DecisionLogicType,
    InteractionStrategy,
    AlignmentKind,
    PseudoStateKind,
)


class TestOsdmEnumsImported:
    """Verify all OSDM enums used by handlers are importable and correct."""

    def test_gateway_type_values(self):
        assert GatewayType.EXCLUSIVE == "Exclusive"
        assert GatewayType.INCLUSIVE == "Inclusive"
        assert GatewayType.PARALLEL == "Parallel"
        assert GatewayType.COMPLEX == "Complex"
        assert GatewayType.EVENT_BASED == "EventBased"

    def test_event_type_values(self):
        assert EventType.START == "Start"
        assert EventType.END == "End"
        assert EventType.INTERMEDIATE_CATCH == "IntermediateCatch"
        assert EventType.INTERMEDIATE_THROW == "IntermediateThrow"
        assert EventType.BOUNDARY == "Boundary"

    def test_event_definition_type_values(self):
        assert EventDefinitionType.NONE == "None"
        assert EventDefinitionType.MESSAGE == "Message"
        assert EventDefinitionType.TIMER == "Timer"
        assert EventDefinitionType.SIGNAL == "Signal"
        assert EventDefinitionType.ERROR == "Error"
        assert EventDefinitionType.ESCALATION == "Escalation"
        assert EventDefinitionType.CONDITIONAL == "Conditional"
        assert EventDefinitionType.LINK == "Link"
        assert EventDefinitionType.CANCEL == "Cancel"
        assert EventDefinitionType.TERMINATE == "Terminate"
        assert EventDefinitionType.COMPENSATION == "Compensation"

    def test_loop_type_values(self):
        assert LoopType.NONE == "None"
        assert LoopType.STANDARD == "Standard"
        assert LoopType.MULTI_INSTANCE == "MultiInstance"

    def test_multi_instance_behavior_values(self):
        assert MultiInstanceBehavior.NONE == "None"
        assert MultiInstanceBehavior.ONE == "One"
        assert MultiInstanceBehavior.ALL == "All"
        assert MultiInstanceBehavior.COMPLEX == "Complex"

    def test_adhoc_ordering_values(self):
        assert AdHocOrdering.PARALLEL == "Parallel"
        assert AdHocOrdering.SEQUENTIAL == "Sequential"

    def test_choreography_loop_type_values(self):
        assert ChoreographyLoopType.NONE == "None"
        assert ChoreographyLoopType.STANDARD == "Standard"
        assert ChoreographyLoopType.MULTI_INSTANCE_PARALLEL == "MultiInstanceParallel"
        assert ChoreographyLoopType.MULTI_INSTANCE_SEQUENTIAL == "MultiInstanceSequential"

    def test_transaction_method_values(self):
        assert TransactionMethod.COMPENSATE == "##compensate"
        assert TransactionMethod.STORE == "##store"
        assert TransactionMethod.IMAGE == "##image"

    def test_gateway_direction_values(self):
        assert GatewayDirection.UNSPECIFIED == "Unspecified"
        assert GatewayDirection.CONVERGING == "Converging"
        assert GatewayDirection.DIVERGING == "Diverging"
        assert GatewayDirection.MIXED == "Mixed"

    def test_process_type_values(self):
        assert ProcessType.NONE == "None"
        assert ProcessType.PUBLIC == "Public"
        assert ProcessType.PRIVATE == "Private"

    def test_sub_process_type_values(self):
        assert SubProcessType.EMBEDDED == "Embedded"
        assert SubProcessType.EVENT == "Event"
        assert SubProcessType.TRANSACTION == "Transaction"
        assert SubProcessType.AD_HOC == "AdHoc"

    def test_task_type_values(self):
        assert TaskType.NONE == "None"
        assert TaskType.SERVICE == "Service"
        assert TaskType.USER == "User"
        assert TaskType.MANUAL == "Manual"
        assert TaskType.SCRIPT == "Script"
        assert TaskType.BUSINESS_RULE == "BusinessRule"
        assert TaskType.SEND == "Send"
        assert TaskType.RECEIVE == "Receive"

    def test_call_activity_type_values(self):
        assert CallActivityType.PROCESS == "Process"
        assert CallActivityType.GLOBAL_TASK == "GlobalTask"


class TestOsdmHandlerImports:
    """Verify handlers import from OSDM rather than redefining."""

    def test_activity_handler_uses_osdm_enums(self):
        from engines.orchestration.bpmn.activity_handler import ActivityHandler
        import inspect
        source = inspect.getsource(ActivityHandler)
        # Should NOT redefine LoopType, MultiInstanceBehavior etc.
        assert "class LoopType" not in source
        assert "class MultiInstanceBehavior" not in source
        assert "class IOSpecification" not in source
        assert "class LoopCharacteristics" not in source
        # Should use handler-specific renamed classes
        assert "ActivityLoopCharacteristics" in source or "ActivityExecutionResult" in source

    def test_gateway_handler_uses_osdm_enums(self):
        from engines.orchestration.bpmn.gateway_handler import GatewayHandler
        import inspect
        source = inspect.getsource(GatewayHandler)
        assert "class GatewayType" not in source
        assert "class GatewayDirection" not in source
        assert "class BPMNGatewayType" not in source

    def test_event_handler_uses_osdm_enums(self):
        from engines.orchestration.bpmn.event_handler import EventHandler
        import inspect
        source = inspect.getsource(EventHandler)
        assert "class EventType" not in source
        assert "class EventDefinitionType" not in source
        assert "class BPMNEventType" not in source

    def test_loop_handler_uses_osdm_enums(self):
        from engines.orchestration.bpmn.loop_handler import LoopHandler
        import inspect
        source = inspect.getsource(LoopHandler)
        assert "class LoopType" not in source
        assert "class MultiInstanceBehavior" not in source

    def test_transaction_handler_uses_osdm(self):
        from engines.orchestration.bpmn.transaction_handler import TransactionHandler
        import inspect
        source = inspect.getsource(TransactionHandler)
        assert "class TransactionMethod" not in source


class TestOsdmClassTypeHierarchy:
    """Verify OSDM class hierarchy is preserved when imported."""

    def test_event_hierarchy(self):
        from engines.orchestration.models.osdm_models import (
            StartEvent, EndEvent, IntermediateCatchEvent, IntermediateThrowEvent,
            BoundaryEvent, CatchEvent, ThrowEvent,
        )
        assert issubclass(StartEvent, CatchEvent)
        assert issubclass(EndEvent, ThrowEvent)
        assert issubclass(IntermediateCatchEvent, CatchEvent)
        assert issubclass(IntermediateThrowEvent, ThrowEvent)
        assert issubclass(BoundaryEvent, CatchEvent)

    def test_gateway_hierarchy(self):
        from engines.orchestration.models.osdm_models import (
            Gateway, ExclusiveGateway, InclusiveGateway, ParallelGateway,
            EventBasedGateway, ComplexGateway,
        )
        assert issubclass(ExclusiveGateway, Gateway)
        assert issubclass(InclusiveGateway, Gateway)
        assert issubclass(ParallelGateway, Gateway)
        assert issubclass(EventBasedGateway, Gateway)
        assert issubclass(ComplexGateway, Gateway)

    def test_task_hierarchy(self):
        from engines.orchestration.models.osdm_models import (
            Activity, Task, ServiceTask, UserTask, ManualTask, ScriptTask,
            BusinessRuleTask, SendTask, ReceiveTask, CallActivity,
        )
        assert issubclass(Task, Activity)
        assert issubclass(ServiceTask, Task)
        assert issubclass(UserTask, Task)
        assert issubclass(ManualTask, Task)
        assert issubclass(ScriptTask, Task)
        assert issubclass(BusinessRuleTask, Task)
        assert issubclass(SendTask, Task)
        assert issubclass(ReceiveTask, Task)
        assert issubclass(CallActivity, Activity)


class TestOsdmComplianceGaps:
    """Document known OSDM compliance gaps as failing tests."""

    @pytest.mark.xfail(reason="Handlers use dict-based processing instead of OSDM typed objects")
    def test_bpmn_engine_uses_osdm_process_model(self):
        """BPMN engine should use OSDM Process objects, not dicts."""
        from engines.orchestration.bpmn.engine import BPMNEngine
        import inspect
        source = inspect.getsource(BPMNEngine)
        assert "Process" in source or "TypedProcessModel" in source

    @pytest.mark.xfail(reason="Event handler fully uses OSDM Event classes")
    def test_event_handler_uses_osdm_event_classes(self):
        from engines.orchestration.bpmn.event_handler import EventHandler
        import inspect
        source = inspect.getsource(EventHandler)
        assert "StartEvent" in source
        assert "EndEvent" in source
        assert "BoundaryEvent" in source
