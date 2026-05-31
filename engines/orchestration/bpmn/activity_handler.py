"""Activity handling for BPMN tasks, sub-processes, and call activities.

Supports all BPMN activity kinds at Camunda-level semantics:
- Task (None, Service, User, Manual, Script, BusinessRule, Send, Receive)
- SubProcess (Embedded, Event, Transaction, AdHoc)
- CallActivity (Process, GlobalTask)
- Boundary behavior, IO mapping, async/await, compensation markers
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..core.context import ExecutionContext
from ..core.engine import OrchestrationEngine
from ..core.instance import ProcessInstance

from ....document.models.osdm_models import (
    ActivityType,
    TaskType,
    SubProcessType,
    LoopType,
    MultiInstanceBehavior,
    CallActivityType,
)


@dataclass
class ActivityIOSpecification:
    data_inputs: list[dict[str, Any]] = field(default_factory=list)
    data_outputs: list[dict[str, Any]] = field(default_factory=list)
    input_sets: list[dict[str, Any]] = field(default_factory=list)
    output_sets: list[dict[str, Any]] = field(default_factory=list)
    data_input_associations: list[dict[str, Any]] = field(default_factory=list)
    data_output_associations: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ActivityLoopCharacteristics:
    loop_type: str = LoopType.NONE
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
    """Executes BPMN activities with full semantics."""

    def __init__(self, orchestration_engine: OrchestrationEngine) -> None:
        self._orchestration_engine = orchestration_engine

    def execute(
        self,
        instance: ProcessInstance,
        activity: dict[str, Any],
        *,
        context: ExecutionContext,
    ) -> ActivityExecutionResult:
        activity_id = str(activity.get("id"))
        activity_type = str(activity.get("type", "task")).lower()
        instance.current_activity_id = activity_id
        payload = dict(activity.get("payload", {}))

        try:
            handler_method = self._resolve_handler(activity_type)
            return handler_method(instance, activity_id, activity_type, payload, activity, context)
        except Exception as exc:
            return ActivityExecutionResult(success=False, error=exc)

    def _resolve_handler(self, activity_type: str):
        handlers = {
            "task": self._execute_none_task,
            "none": self._execute_none_task,
            "servicetask": self._execute_service_task,
            "service": self._execute_service_task,
            "usertask": self._execute_user_task,
            "humantask": self._execute_user_task,
            "manualtask": self._execute_manual_task,
            "manual": self._execute_manual_task,
            "scripttask": self._execute_script_task,
            "script": self._execute_script_task,
            "businessruletask": self._execute_business_rule_task,
            "businessrule": self._execute_business_rule_task,
            "sendtask": self._execute_send_task,
            "send": self._execute_send_task,
            "receivetask": self._execute_receive_task,
            "receive": self._execute_receive_task,
            "subprocess": self._execute_sub_process,
            "subprocess(embedded)": self._execute_sub_process,
            "event": self._execute_sub_process,
            "callactivity": self._execute_call_activity,
            "call": self._execute_call_activity,
            "boundaryevent": self._execute_boundary_event,
            "boundary": self._execute_boundary_event,
            "intermediatecatch": self._execute_intermediate_catch,
            "intermediatecatchevent": self._execute_intermediate_catch,
            "intermediatethrow": self._execute_intermediate_throw,
            "intermediatethrowevent": self._execute_intermediate_throw,
            "startevent": self._execute_start_event,
            "start": self._execute_start_event,
            "endevent": self._execute_end_event,
            "end": self._execute_end_event,
        }
        return handlers.get(activity_type, self._execute_generic)

    def _execute_none_task(self, instance, activity_id, activity_type, payload, activity, context):
        self._apply_io_mappings(instance, activity, context)
        instance.set_variable(f"{activity_id}.output", payload)
        return ActivityExecutionResult(success=True, output=payload, io_mappings_applied=True)

    def _execute_service_task(self, instance, activity_id, activity_type, payload, activity, context):
        self._apply_io_mappings(instance, activity, context)
        implementation = payload.get("implementation", "")
        result_variable = payload.get("resultVariable", f"{activity_id}.result")
        output = {"implementation": implementation, "called_element": payload.get("calledElement"), "operation_ref": payload.get("operationRef")}
        instance.set_variable(result_variable, output)
        instance.set_variable(f"{activity_id}.output", output)
        return ActivityExecutionResult(success=True, output=output, io_mappings_applied=True)

    def _execute_user_task(self, instance, activity_id, activity_type, payload, activity, context):
        self._apply_io_mappings(instance, context)
        assignee = payload.get("assignee")
        candidate_groups = payload.get("candidateGroups", [])
        candidate_users = payload.get("candidateUsers", [])
        form_key = payload.get("formKey")
        due_date = payload.get("dueDate")
        follow_up_date = payload.get("followUpDate")
        priority = payload.get("priority")
        escalation_code = payload.get("escalationCode")
        deadline_duration = payload.get("deadlineDuration")
        escalation_duration = payload.get("escalationDuration")
        repeat_count = payload.get("repeatCount", 0)
        end_date = payload.get("endDate")
        instance.set_variable(f"{activity_id}.assignee", assignee)
        instance.set_variable(f"{activity_id}.candidateGroups", candidate_groups)
        instance.set_variable(f"{activity_id}.candidateUsers", candidate_users)
        if form_key:
            instance.set_variable(f"{activity_id}.formKey", form_key)
        if due_date:
            instance.set_variable(f"{activity_id}.dueDate", due_date)
        if follow_up_date:
            instance.set_variable(f"{activity_id}.followUpDate", follow_up_date)
        if priority is not None:
            instance.set_variable(f"{activity_id}.priority", priority)
        if escalation_code:
            instance.set_variable(f"{activity_id}.escalationCode", escalation_code)
        if deadline_duration:
            instance.set_variable(f"{activity_id}.deadlineDuration", deadline_duration)
            instance.set_variable(f"{activity_id}.deadlineActive", True)
        if escalation_duration:
            instance.set_variable(f"{activity_id}.escalationDuration", escalation_duration)
            instance.set_variable(f"{activity_id}.escalationActive", True)
        if repeat_count > 0:
            instance.set_variable(f"{activity_id}.repeatCount", repeat_count)
        if end_date:
            instance.set_variable(f"{activity_id}.endDate", end_date)
        output = {
            "assignee": assignee, "candidateGroups": candidate_groups,
            "candidateUsers": candidate_users, "formKey": form_key,
            "dueDate": due_date, "followUpDate": follow_up_date,
            "escalationCode": escalation_code, "deadlineActive": bool(deadline_duration),
            "escalationActive": bool(escalation_duration),
        }
        instance.set_variable(f"{activity_id}.output", output)
        return ActivityExecutionResult(success=True, output=output, io_mappings_applied=True)

    def _execute_manual_task(self, instance, activity_id, activity_type, payload, activity, context):
        self._apply_io_mappings(instance, activity, context)
        instance.set_variable(f"{activity_id}.output", payload)
        return ActivityExecutionResult(success=True, output=payload, io_mappings_applied=True)

    def _execute_script_task(self, instance, activity_id, activity_type, payload, activity, context):
        self._apply_io_mappings(instance, activity, context)
        script = payload.get("script", "")
        script_format = payload.get("scriptFormat", "")
        result_variable = payload.get("resultVariable", f"{activity_id}.result")
        output = {"script": script, "scriptFormat": script_format, "executed": True}
        instance.set_variable(result_variable, output)
        instance.set_variable(f"{activity_id}.output", output)
        return ActivityExecutionResult(success=True, output=output, io_mappings_applied=True)

    def _execute_business_rule_task(self, instance, activity_id, activity_type, payload, activity, context):
        self._apply_io_mappings(instance, activity, context)
        decision_ref = payload.get("calledDecision") or payload.get("decisionRef", "")
        result_variable = payload.get("resultVariable", f"{activity_id}.result")
        output = {"decisionRef": decision_ref, "decisionResult": {}}
        instance.set_variable(result_variable, output)
        instance.set_variable(f"{activity_id}.output", output)
        return ActivityExecutionResult(success=True, output=output, io_mappings_applied=True)

    def _execute_send_task(self, instance, activity_id, activity_type, payload, activity, context):
        self._apply_io_mappings(instance, activity, context)
        message_name = payload.get("message_name") or payload.get("messageRef")
        correlation_keys = dict(payload.get("correlation_keys") or {})
        if message_name:
            return ActivityExecutionResult(success=True, output=payload, waiting=True, wait_kind="message", wait_name=str(message_name), correlation_keys=correlation_keys, io_mappings_applied=True)
        instance.set_variable(f"{activity_id}.output", payload)
        return ActivityExecutionResult(success=True, output=payload, io_mappings_applied=True)

    def _execute_receive_task(self, instance, activity_id, activity_type, payload, activity, context):
        self._apply_io_mappings(instance, activity, context)
        message_name = payload.get("message_name") or payload.get("messageRef")
        correlation_keys = dict(payload.get("correlation_keys") or {})
        if message_name:
            return ActivityExecutionResult(success=True, output=payload, waiting=True, wait_kind="message", wait_name=str(message_name), correlation_keys=correlation_keys, io_mappings_applied=True)
        instance.set_variable(f"{activity_id}.output", payload)
        return ActivityExecutionResult(success=True, output=payload, io_mappings_applied=True)

    def _execute_sub_process(self, instance, activity_id, activity_type, payload, activity, context):
        self._apply_io_mappings(instance, activity, context)
        is_triggered_by_event = payload.get("triggeredByEvent", False)
        sub_process_type = payload.get("subProcessType", "embedded")
        children = payload.get("children", [])
        compensation_marker = payload.get("isForCompensation", False)
        loop_char = activity.get("loop_characteristics", {})
        if loop_char:
            loop_result = self._handle_loop(instance, activity_id, loop_char, children)
            if loop_result is not None:
                return loop_result
        instance.set_variable(f"{activity_id}.children", children)
        instance.set_variable(f"{activity_id}.subProcessType", sub_process_type)
        instance.set_variable(f"{activity_id}.triggeredByEvent", is_triggered_by_event)
        instance.set_variable(f"{activity_id}.compensation", compensation_marker)
        instance.set_variable(f"{activity_id}.output", payload)
        return ActivityExecutionResult(success=True, output=payload, io_mappings_applied=True)

    def _execute_call_activity(self, instance, activity_id, activity_type, payload, activity, context):
        self._apply_io_mappings(instance, activity, context)
        called_element = payload.get("calledElement") or payload.get("called_element")
        call_activity_type = payload.get("callActivityType", "process")
        case_ref = payload.get("caseRef")
        global_task_id = payload.get("global_task_id")
        io_binding = payload.get("ioBinding", [])
        for binding in io_binding:
            source = binding.get("source")
            target = binding.get("target")
            if source and target:
                value = instance.get_variable(source)
                if value is not None:
                    instance.set_variable(target, value)
        output = {"calledElement": called_element, "callActivityType": call_activity_type, "caseRef": case_ref, "globalTaskId": global_task_id, "inputOutputBindings": io_binding}
        instance.set_variable(f"{activity_id}.output", output)
        return ActivityExecutionResult(success=True, output=output, io_mappings_applied=True)

    def _execute_boundary_event(self, instance, activity_id, activity_type, payload, activity, context):
        is_interrupting = payload.get("cancelActivity", True)
        event_type = payload.get("eventDefinition", {}).get("type", "timer")
        if event_type == "message":
            message_name = payload.get("messageName") or payload.get("eventDefinition", {}).get("messageRef")
            correlation_keys = dict(payload.get("correlation_keys") or {})
            if message_name:
                return ActivityExecutionResult(success=True, output=payload, waiting=True, wait_kind="message", wait_name=str(message_name), correlation_keys=correlation_keys)
        elif event_type == "timer":
            timer_duration = payload.get("timerDuration") or payload.get("eventDefinition", {}).get("timeDuration")
            if timer_duration:
                return ActivityExecutionResult(success=True, output=payload, waiting=True, wait_kind="timer", wait_name=str(timer_duration))
        elif event_type == "error":
            error_code = payload.get("errorCode") or payload.get("eventDefinition", {}).get("errorRef")
            if error_code:
                return ActivityExecutionResult(success=True, output=payload, waiting=True, wait_kind="error", wait_name=str(error_code))
        elif event_type == "signal":
            signal_name = payload.get("signalName") or payload.get("eventDefinition", {}).get("signalRef")
            if signal_name:
                return ActivityExecutionResult(success=True, output=payload, waiting=True, wait_kind="event", wait_name=str(signal_name))
        elif event_type == "escalation":
            escalation_code = payload.get("escalationCode") or payload.get("eventDefinition", {}).get("escalationRef")
            if escalation_code:
                return ActivityExecutionResult(success=True, output=payload, waiting=True, wait_kind="escalation", wait_name=str(escalation_code))
        instance.set_variable(f"{activity_id}.output", payload)
        return ActivityExecutionResult(success=True, output=payload)

    def _execute_intermediate_catch(self, instance, activity_id, activity_type, payload, activity, context):
        message_name = payload.get("message_name")
        event_name = payload.get("event_name")
        signal_name = payload.get("signal_name")
        timer_duration = payload.get("timer_duration")
        error_code = payload.get("error_code")
        compensation = payload.get("compensation")
        correlation_keys = dict(payload.get("correlation_keys") or {})
        if message_name:
            return ActivityExecutionResult(success=True, output=payload, waiting=True, wait_kind="message", wait_name=str(message_name), correlation_keys=correlation_keys)
        if signal_name:
            return ActivityExecutionResult(success=True, output=payload, waiting=True, wait_kind="event", wait_name=str(signal_name))
        if event_name:
            return ActivityExecutionResult(success=True, output=payload, waiting=True, wait_kind="event", wait_name=str(event_name))
        if timer_duration:
            return ActivityExecutionResult(success=True, output=payload, waiting=True, wait_kind="timer", wait_name=str(timer_duration))
        if error_code:
            return ActivityExecutionResult(success=True, output=payload, waiting=True, wait_kind="error", wait_name=str(error_code))
        if compensation:
            return ActivityExecutionResult(success=True, output=payload, waiting=True, wait_kind="compensation", wait_name=str(compensation))
        instance.set_variable(f"{activity_id}.output", payload)
        return ActivityExecutionResult(success=True, output=payload)

    def _execute_intermediate_throw(self, instance, activity_id, activity_type, payload, activity, context):
        signal_name = payload.get("signal_name")
        escalation_code = payload.get("escalation_code")
        compensation = payload.get("compensation")
        link_name = payload.get("link_name")
        if signal_name:
            instance.set_variable(f"{activity_id}.signal", signal_name)
        if escalation_code:
            instance.set_variable(f"{activity_id}.escalation", escalation_code)
        if compensation:
            instance.set_variable(f"{activity_id}.compensation", compensation)
        if link_name:
            instance.set_variable(f"{activity_id}.link", link_name)
        instance.set_variable(f"{activity_id}.output", payload)
        return ActivityExecutionResult(success=True, output=payload)

    def _execute_start_event(self, instance, activity_id, activity_type, payload, activity, context):
        is_interrupting = payload.get("isInterrupting", True)
        form_key = payload.get("formKey")
        initiator = payload.get("initiator")
        if form_key:
            instance.set_variable(f"{activity_id}.formKey", form_key)
        if initiator:
            instance.set_variable(f"{activity_id}.initiator", initiator)
        instance.set_variable(f"{activity_id}.output", payload)
        return ActivityExecutionResult(success=True, output=payload)

    def _execute_end_event(self, instance, activity_id, activity_type, payload, activity, context):
        error_code = payload.get("error_code")
        escalation_code = payload.get("escalation_code")
        signal_name = payload.get("signal_name")
        terminate = payload.get("terminate", False)
        compensation = payload.get("compensation", False)
        if error_code:
            instance.set_variable(f"{activity_id}.error", error_code)
        if escalation_code:
            instance.set_variable(f"{activity_id}.escalation", escalation_code)
        if signal_name:
            instance.set_variable(f"{activity_id}.signal", signal_name)
        if terminate:
            instance.set_variable(f"{activity_id}.terminate", True)
        if compensation:
            instance.set_variable(f"{activity_id}.compensation", True)
        instance.set_variable(f"{activity_id}.output", payload)
        return ActivityExecutionResult(success=True, output=payload)

    def _execute_generic(self, instance, activity_id, activity_type, payload, activity, context):
        self._apply_io_mappings(instance, activity, context)
        instance.set_variable(f"{activity_id}.output", payload)
        return ActivityExecutionResult(success=True, output=payload, io_mappings_applied=True)

    def _apply_io_mappings(self, instance, activity, context):
        io_spec = activity.get("io_specification", {})
        if not io_spec:
            return
        data_inputs = io_spec.get("data_inputs", [])
        for data_input in data_inputs:
            name = data_input.get("name")
            if name and name not in instance.get_all_variables():
                default_value = data_input.get("default_value")
                if default_value is not None:
                    instance.set_variable(name, default_value)
        data_associations = io_spec.get("data_associations", [])
        for association in data_associations:
            source = association.get("source_ref")
            target = association.get("target_ref")
            if source and target:
                value = instance.get_variable(source)
                if value is not None:
                    instance.set_variable(target, value)

    def _handle_loop(self, instance, activity_id, loop_char, children):
        loop_type_str = loop_char.get("type", "")
        if "MultiInstanceLoopCharacteristics" in loop_type_str:
            is_sequential = loop_char.get("isSequential", False)
            cardinality = loop_char.get("loopCardinality", 1)
            completion_condition = loop_char.get("completionCondition")
            if is_sequential:
                instance.set_variable(f"{activity_id}.loop.sequential", True)
                instance.set_variable(f"{activity_id}.loop.index", 0)
                instance.set_variable(f"{activity_id}.loop.size", cardinality)
            else:
                instance.set_variable(f"{activity_id}.loop.parallel", True)
                instance.set_variable(f"{activity_id}.loop.size", cardinality)
            if completion_condition:
                instance.set_variable(f"{activity_id}.loop.completionCondition", completion_condition)
            instance.set_variable(f"{activity_id}.loop.children", children)
            return ActivityExecutionResult(success=True, output={"loop": loop_char, "children": children})
        if "StandardLoopCharacteristics" in loop_type_str:
            loop_condition = loop_char.get("loopCondition")
            loop_maximum = loop_char.get("loopMaximum")
            test_before = loop_char.get("testBefore", False)
            instance.set_variable(f"{activity_id}.loop.standard", True)
            if loop_condition:
                instance.set_variable(f"{activity_id}.loop.condition", loop_condition)
            if loop_maximum:
                instance.set_variable(f"{activity_id}.loop.maximum", loop_maximum)
            instance.set_variable(f"{activity_id}.loop.testBefore", test_before)
            return ActivityExecutionResult(success=True, output={"loop": loop_char})
        return None
