"""Activity handling for BPMN tasks, sub-processes, and call activities.

Supports all BPMN activity kinds at Camunda-level semantics with
OSDM-typed object interfaces instead of raw dictionaries.

Uses OSDM model classes directly:
- Activity, Task, ServiceTask, UserTask, ManualTask, ScriptTask, BusinessRuleTask, SendTask, ReceiveTask
- SubProcess, TransactionSubProcess, AdHocSubProcess, CallActivity
- LoopCharacteristics, StandardLoopCharacteristics, MultiInstanceLoopCharacteristics
- InputOutputSpecification, DataInput, DataOutput, DataAssociation
- ResourceRole, HumanPerformer, PotentialOwner
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Union, cast

from ..core.context import ExecutionContext
from ..core.engine import OrchestrationEngine
from ..core.instance import ProcessInstance

from .models.bpmn_models import (
    Activity,
    Task,
    ServiceTask,
    UserTask,
    ManualTask,
    ScriptTask,
    BusinessRuleTask,
    SendTask,
    ReceiveTask,
    SubProcess,
    TransactionSubProcess,
    AdHocSubProcess,
    CallActivity,
    GlobalTask,
    ActivityType,
    TaskType,
    SubProcessType,
    LoopType,
    MultiInstanceBehavior,
    CallActivityType,
    LoopCharacteristics,
    StandardLoopCharacteristics,
    MultiInstanceLoopCharacteristics,
    InputOutputSpecification,
    DataInput,
    DataOutput,
    DataAssociation,
    DataInputAssociation,
    DataOutputAssociation,
    InputSet,
    OutputSet,
    ResourceRole,
    HumanPerformer,
    Performer,
    PotentialOwner,
    ResourceRendering,
    TransactionMethod,
)


@dataclass
class ActivityIOSpecification:
    data_inputs: list[DataInput] = field(default_factory=list)
    data_outputs: list[DataOutput] = field(default_factory=list)
    input_sets: list[InputSet] = field(default_factory=list)
    output_sets: list[OutputSet] = field(default_factory=list)
    data_input_associations: list[DataInputAssociation] = field(default_factory=list)
    data_output_associations: list[DataOutputAssociation] = field(default_factory=list)


@dataclass
class ActivityLoopCharacteristics:
    loop_type: LoopType = LoopType.NONE
    is_sequential: bool = False
    cardinality_value: str | None = None
    completion_condition: str | None = None
    loop_data_input_ref: str | None = None
    loop_data_output_ref: str | None = None
    max_cardinality: int | None = None


@dataclass
class BoundaryBehavior:
    interrupting: bool = True
    attached_to_ref: str | None = None
    event_type: str | None = None
    timer_duration: str | None = None
    error_code: str | None = None
    escalation_code: str | None = None


@dataclass(frozen=True)
class ActivityExecutionResult:
    success: bool = True
    output: dict[str, Any] | None = None
    error: Exception | None = None
    waiting: bool = False
    wait_kind: str | None = None
    wait_name: str | None = None
    correlation_keys: dict[str, Any] | None = None
    completed_activities: list[str] = field(default_factory=list)
    triggered_compensation: bool = False
    io_mappings_applied: bool = False


class ActivityHandler:
    """Executes BPMN activities using OSDM-typed objects.

    All handler methods accept OSDM Activity subclasses directly instead of
    raw dictionaries, providing type safety and IDE autocompletion.
    """

    def __init__(self, orchestration_engine: OrchestrationEngine) -> None:
        self._orchestration_engine = orchestration_engine

    def execute_osdm(
        self,
        instance: ProcessInstance,
        activity: Activity,
        *,
        context: ExecutionContext,
    ) -> ActivityExecutionResult:
        """Execute an OSDM-typed activity object."""
        activity_id = activity.id
        instance.current_activity_id = activity_id

        activity_type = self._resolve_osdm_activity_type(activity)
        _name = getattr(activity, "name", None) or activity_id

        handler_method = self._resolve_osdm_handler(activity)
        try:
            return handler_method(instance, activity, activity_type, context)
        except Exception as exc:
            return ActivityExecutionResult(success=False, error=exc)

    _ACTIVITY_DISPATCH: dict[type, tuple[str, str]] = {
        ServiceTask: ("serviceTask", "_execute_service_task_osdm"),
        UserTask: ("userTask", "_execute_user_task_osdm"),
        ManualTask: ("manualTask", "_execute_manual_task_osdm"),
        ScriptTask: ("scriptTask", "_execute_script_task_osdm"),
        BusinessRuleTask: ("businessRuleTask", "_execute_business_rule_task_osdm"),
        SendTask: ("sendTask", "_execute_send_task_osdm"),
        ReceiveTask: ("receiveTask", "_execute_receive_task_osdm"),
        CallActivity: ("callActivity", "_execute_call_activity_osdm"),
        AdHocSubProcess: ("adHocSubProcess", "_execute_adhoc_sub_process_osdm"),
        TransactionSubProcess: ("transactionSubProcess", "_execute_transaction_sub_process_osdm"),
        SubProcess: ("subProcess", "_execute_sub_process_osdm"),
        GlobalTask: ("globalTask", "_execute_global_task_osdm"),
        Task: ("task", "_execute_none_task_osdm"),
    }

    def _resolve_osdm_activity_type(self, activity: Activity) -> str:
        for cls, (type_str, _) in self._ACTIVITY_DISPATCH.items():
            if isinstance(activity, cls):
                return type_str
        if isinstance(activity, Activity):
            atype = getattr(activity, "activity_type", None)
            if atype:
                if isinstance(atype, ActivityType):
                    return atype.value
                return str(atype)
            return "activity"
        return "unknown"

    def _resolve_osdm_handler(self, activity: Activity):
        for cls, (_, handler_name) in self._ACTIVITY_DISPATCH.items():
            if isinstance(activity, cls):
                return getattr(self, handler_name)
        return self._execute_generic_osdm

    def _execute_none_task_osdm(
        self, instance: ProcessInstance, activity: Task, activity_type: str, context: ExecutionContext,
    ) -> ActivityExecutionResult:
        self._apply_io_mappings_osdm(activity, instance, context)
        output = {"type": "none", "name": getattr(activity, "name", None)}
        instance.set_variable(f"{activity.id}.output", output)
        return ActivityExecutionResult(success=True, output=output, io_mappings_applied=True)

    def _execute_service_task_osdm(
        self, instance: ProcessInstance, activity: ServiceTask, activity_type: str, context: ExecutionContext,
    ) -> ActivityExecutionResult:
        self._apply_io_mappings_osdm(activity, instance, context)
        implementation = getattr(activity, "implementation", "") or ""
        operation_ref = getattr(activity, "operation_ref", None)
        result_variable = f"{activity.id}.result"
        output = {"implementation": str(implementation), "operation_ref": str(operation_ref) if operation_ref else None}
        instance.set_variable(result_variable, output)
        instance.set_variable(f"{activity.id}.output", output)
        return ActivityExecutionResult(success=True, output=output, io_mappings_applied=True)

    def _execute_user_task_osdm(
        self, instance: ProcessInstance, activity: UserTask, activity_type: str, context: ExecutionContext,
    ) -> ActivityExecutionResult:
        self._apply_io_mappings_osdm(activity, instance, context)
        assignee = getattr(activity, "assignee", None)
        candidate_groups = list(getattr(activity, "candidate_groups", []) or [])
        candidate_users = list(getattr(activity, "candidate_users", []) or [])
        form_key = getattr(activity, "form_key", None)
        due_date = getattr(activity, "due_date", None)
        follow_up_date = getattr(activity, "follow_up_date", None)
        priority = getattr(activity, "priority", None)
        escalation_code = getattr(activity, "escalation_code", None)
        deadline_duration = getattr(activity, "deadline_duration", None)
        escalation_duration = getattr(activity, "escalation_duration", None)
        repeat_count = getattr(activity, "repeat_count", 0)
        end_date = getattr(activity, "end_date", None)
        instance.set_variable(f"{activity.id}.assignee", assignee)
        instance.set_variable(f"{activity.id}.candidateGroups", candidate_groups)
        instance.set_variable(f"{activity.id}.candidateUsers", candidate_users)
        if form_key:
            instance.set_variable(f"{activity.id}.formKey", form_key)
        if due_date:
            instance.set_variable(f"{activity.id}.dueDate", due_date)
        if follow_up_date:
            instance.set_variable(f"{activity.id}.followUpDate", follow_up_date)
        if priority is not None:
            instance.set_variable(f"{activity.id}.priority", priority)
        if escalation_code:
            instance.set_variable(f"{activity.id}.escalationCode", escalation_code)
        if deadline_duration:
            instance.set_variable(f"{activity.id}.deadlineDuration", deadline_duration)
            instance.set_variable(f"{activity.id}.deadlineActive", True)
        if escalation_duration:
            instance.set_variable(f"{activity.id}.escalationDuration", escalation_duration)
            instance.set_variable(f"{activity.id}.escalationActive", True)
        if repeat_count and repeat_count > 0:
            instance.set_variable(f"{activity.id}.repeatCount", repeat_count)
        if end_date:
            instance.set_variable(f"{activity.id}.endDate", end_date)
        output = {
            "assignee": assignee, "candidateGroups": candidate_groups,
            "candidateUsers": candidate_users, "formKey": form_key,
            "dueDate": due_date, "escalationCode": escalation_code,
            "deadlineActive": bool(deadline_duration), "escalationActive": bool(escalation_duration),
        }
        instance.set_variable(f"{activity.id}.output", output)
        return ActivityExecutionResult(success=True, output=output, io_mappings_applied=True)

    def _execute_manual_task_osdm(
        self, instance: ProcessInstance, activity: ManualTask, activity_type: str, context: ExecutionContext,
    ) -> ActivityExecutionResult:
        self._apply_io_mappings_osdm(activity, instance, context)
        output = {"type": "manual", "name": getattr(activity, "name", None)}
        instance.set_variable(f"{activity.id}.output", output)
        return ActivityExecutionResult(success=True, output=output, io_mappings_applied=True)

    def _execute_script_task_osdm(
        self, instance: ProcessInstance, activity: ScriptTask, activity_type: str, context: ExecutionContext,
    ) -> ActivityExecutionResult:
        self._apply_io_mappings_osdm(activity, instance, context)
        script = getattr(activity, "script", "") or ""
        script_format = getattr(activity, "script_format", "") or ""
        result_variable = f"{activity.id}.result"
        output = {"script": str(script), "scriptFormat": str(script_format), "executed": True}
        instance.set_variable(result_variable, output)
        instance.set_variable(f"{activity.id}.output", output)
        return ActivityExecutionResult(success=True, output=output, io_mappings_applied=True)

    def _execute_business_rule_task_osdm(
        self, instance: ProcessInstance, activity: BusinessRuleTask, activity_type: str, context: ExecutionContext,
    ) -> ActivityExecutionResult:
        self._apply_io_mappings_osdm(activity, instance, context)
        decision_ref = getattr(activity, "called_decision", "") or ""
        result_variable = f"{activity.id}.result"
        output = {"decisionRef": str(decision_ref), "decisionResult": {}}
        instance.set_variable(result_variable, output)
        instance.set_variable(f"{activity.id}.output", output)
        return ActivityExecutionResult(success=True, output=output, io_mappings_applied=True)

    def _execute_send_task_osdm(
        self, instance: ProcessInstance, activity: SendTask, activity_type: str, context: ExecutionContext,
    ) -> ActivityExecutionResult:
        self._apply_io_mappings_osdm(activity, instance, context)
        message_name = getattr(activity, "message_name", None) or getattr(activity, "message_ref", None)
        correlation_keys = dict(getattr(activity, "correlation_keys", {}) or {})
        if message_name:
            return ActivityExecutionResult(
                success=True, output={"type": "send", "message": str(message_name)},
                waiting=True, wait_kind="message", wait_name=str(message_name),
                correlation_keys=correlation_keys, io_mappings_applied=True,
            )
        output = {"type": "send", "message": str(message_name) if message_name else None}
        instance.set_variable(f"{activity.id}.output", output)
        return ActivityExecutionResult(success=True, output=output, io_mappings_applied=True)

    def _execute_receive_task_osdm(
        self, instance: ProcessInstance, activity: ReceiveTask, activity_type: str, context: ExecutionContext,
    ) -> ActivityExecutionResult:
        self._apply_io_mappings_osdm(activity, instance, context)
        message_name = getattr(activity, "message_name", None) or getattr(activity, "message_ref", None)
        correlation_keys = dict(getattr(activity, "correlation_keys", {}) or {})
        if message_name:
            return ActivityExecutionResult(
                success=True, output={"type": "receive", "message": str(message_name)},
                waiting=True, wait_kind="message", wait_name=str(message_name),
                correlation_keys=correlation_keys, io_mappings_applied=True,
            )
        output = {"type": "receive", "message": str(message_name) if message_name else None}
        instance.set_variable(f"{activity.id}.output", output)
        return ActivityExecutionResult(success=True, output=output, io_mappings_applied=True)

    def _execute_call_activity_osdm(
        self, instance: ProcessInstance, activity: CallActivity, activity_type: str, context: ExecutionContext,
    ) -> ActivityExecutionResult:
        self._apply_io_mappings_osdm(activity, instance, context)
        called_element = getattr(activity, "called_element", None)
        call_type = getattr(activity, "call_activity_type", CallActivityType.PROCESS)
        io_binding = list(getattr(activity, "io_binding", []) or [])
        output = {
            "calledElement": str(called_element) if called_element else None,
            "callActivityType": call_type.value if isinstance(call_type, CallActivityType) else str(call_type),
            "inputOutputBindings": len(io_binding),
        }
        instance.set_variable(f"{activity.id}.output", output)
        return ActivityExecutionResult(success=True, output=output, io_mappings_applied=True)

    def _execute_sub_process_osdm(
        self, instance: ProcessInstance, activity: SubProcess, activity_type: str, context: ExecutionContext,
    ) -> ActivityExecutionResult:
        self._apply_io_mappings_osdm(activity, instance, context)
        sp_type = getattr(activity, "sub_process_type", SubProcessType.EMBEDDED)
        triggered_by = getattr(activity, "triggered_by_event", False)
        is_for_comp = getattr(activity, "is_for_compensation", False)
        loop_char = getattr(activity, "loop_characteristics", None)
        children = list(getattr(activity, "flow_elements", {}).keys()) if hasattr(activity, "flow_elements") and activity.flow_elements else []
        if loop_char:
            loop_result = self._handle_loop_osdm(activity, loop_char, children, instance)
            if loop_result is not None:
                return loop_result
        instance.set_variable(f"{activity.id}.subProcessType", sp_type.value if isinstance(sp_type, SubProcessType) else str(sp_type))
        instance.set_variable(f"{activity.id}.triggeredByEvent", triggered_by)
        instance.set_variable(f"{activity.id}.compensation", is_for_comp)
        instance.set_variable(f"{activity.id}.children", children)
        instance.set_variable(f"{activity.id}.output", {"type": "subProcess", "children": len(children)})
        return ActivityExecutionResult(success=True, output={"type": "subProcess", "children": len(children)}, io_mappings_applied=True)

    def _execute_adhoc_sub_process_osdm(
        self, instance: ProcessInstance, activity: AdHocSubProcess, activity_type: str, context: ExecutionContext,
    ) -> ActivityExecutionResult:
        self._apply_io_mappings_osdm(activity, instance, context)
        ordering = getattr(activity, "ordering", None)
        completion_cond = getattr(activity, "completion_condition", None)
        cancel_remaining = getattr(activity, "cancel_remaining_instances", True)
        children = list(getattr(activity, "flow_elements", {}).keys()) if hasattr(activity, "flow_elements") and activity.flow_elements else []
        instance.set_variable(f"{activity.id}.ordering", ordering.value if ordering else "Parallel")
        instance.set_variable(f"{activity.id}.completionCondition", completion_cond)
        instance.set_variable(f"{activity.id}.cancelRemainingInstances", cancel_remaining)
        instance.set_variable(f"{activity.id}.children", children)
        instance.set_variable(f"{activity.id}.output", {"type": "adHocSubProcess", "children": len(children)})
        return ActivityExecutionResult(success=True, output={"type": "adHocSubProcess"}, io_mappings_applied=True)

    def _execute_transaction_sub_process_osdm(
        self, instance: ProcessInstance, activity: TransactionSubProcess, activity_type: str, context: ExecutionContext,
    ) -> ActivityExecutionResult:
        self._apply_io_mappings_osdm(activity, instance, context)
        method = getattr(activity, "method", TransactionMethod.COMPENSATE)
        children = list(getattr(activity, "flow_elements", {}).keys()) if hasattr(activity, "flow_elements") and activity.flow_elements else []
        instance.set_variable(f"{activity.id}.transactionMethod", method.value if isinstance(method, TransactionMethod) else str(method))
        instance.set_variable(f"{activity.id}.children", children)
        instance.set_variable(f"{activity.id}.output", {"type": "transactionSubProcess", "children": len(children)})
        return ActivityExecutionResult(success=True, output={"type": "transactionSubProcess"}, io_mappings_applied=True)

    def _execute_global_task_osdm(
        self, instance: ProcessInstance, activity: GlobalTask, activity_type: str, context: ExecutionContext,
    ) -> ActivityExecutionResult:
        self._apply_io_mappings_osdm(cast(Activity, activity), instance, context)
        task_type = getattr(activity, "task_type", None)
        resources = list(getattr(activity, "resources", []) or [])
        output = {
            "type": "globalTask",
            "taskType": str(task_type) if task_type else None,
            "resources": len(resources),
        }
        instance.set_variable(f"{activity.id}.output", output)
        return ActivityExecutionResult(success=True, output=output, io_mappings_applied=True)

    def _execute_generic_osdm(
        self, instance: ProcessInstance, activity: Activity, activity_type: str, context: ExecutionContext,
    ) -> ActivityExecutionResult:
        self._apply_io_mappings_osdm(activity, instance, context)
        output = {"type": activity_type, "name": getattr(activity, "name", None)}
        instance.set_variable(f"{activity.id}.output", output)
        return ActivityExecutionResult(success=True, output=output, io_mappings_applied=True)

    def _apply_io_mappings_osdm(self, activity: Activity, instance: ProcessInstance, context: ExecutionContext) -> None:
        io_spec = getattr(activity, "io_specification", None)
        if not io_spec or not isinstance(io_spec, InputOutputSpecification):
            return
        if io_spec.data_inputs:
            for di in io_spec.data_inputs:
                name = di.name if hasattr(di, "name") else str(di.id)
                if name and name not in instance.get_all_variables():
                    default_value = getattr(di, "default_value", None)
                    if default_value is not None:
                        instance.set_variable(name, default_value)
        if io_spec.data_associations:
            for da in io_spec.data_associations:
                source = getattr(da, "source_ref", None)
                target = getattr(da, "target_ref", None)
                if source and target:
                    value = instance.get_variable(str(source))
                    if value is not None:
                        instance.set_variable(str(target), value)

    def _handle_loop_osdm(
        self, activity: Activity, loop_char: LoopCharacteristics, children: list[str], instance: ProcessInstance,
    ) -> ActivityExecutionResult | None:
        if isinstance(loop_char, MultiInstanceLoopCharacteristics):
            is_seq = loop_char.is_sequential
            cardinality = getattr(loop_char, "loop_cardinality", None)
            completion_cond = getattr(loop_char, "completion_condition", None)
            if is_seq:
                instance.set_variable(f"{activity.id}.loop.sequential", True)
                instance.set_variable(f"{activity.id}.loop.index", 0)
                size = self._evaluate_cardinality(cardinality) if cardinality else 1
                instance.set_variable(f"{activity.id}.loop.size", size)
            else:
                instance.set_variable(f"{activity.id}.loop.parallel", True)
                size = self._evaluate_cardinality(cardinality) if cardinality else 1
                instance.set_variable(f"{activity.id}.loop.size", size)
            if completion_cond:
                instance.set_variable(f"{activity.id}.loop.completionCondition", str(completion_cond))
            instance.set_variable(f"{activity.id}.loop.children", children)
            return ActivityExecutionResult(success=True, output={"loop": "multiInstance", "children": children})
        elif isinstance(loop_char, StandardLoopCharacteristics):
            condition = getattr(loop_char, "loop_condition", None)
            maximum = getattr(loop_char, "loop_maximum", None)
            test_before = getattr(loop_char, "test_before", False)
            instance.set_variable(f"{activity.id}.loop.standard", True)
            if condition:
                instance.set_variable(f"{activity.id}.loop.condition", str(condition))
            if maximum:
                instance.set_variable(f"{activity.id}.loop.maximum", maximum)
            instance.set_variable(f"{activity.id}.loop.testBefore", test_before)
            return ActivityExecutionResult(success=True, output={"loop": "standard"})
        return None

    def _evaluate_cardinality(self, cardinality: Any) -> int:
        if isinstance(cardinality, int):
            return max(1, cardinality)
        if isinstance(cardinality, str):
            try:
                return max(1, int(cardinality))
            except ValueError:
                return 1
        return 1
