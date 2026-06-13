"""Sub-process, event sub-process, and transaction management for BPMN."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

from engines.orchestration.models.osdm_models import EndEvent, SubProcess
from .model_normalizer import _activity_get, _activity_id, _activity_type_str
from .process_model import TypedProcessModel
from ..core.instance import ProcessInstance


class _SubProcessContext:
    sub_process_id: str
    start_node_id: str
    is_event_sub_process: bool = False
    is_interrupting: bool = False
    is_transaction: bool = False
    is_adhoc: bool = False
    parent_token_id: str | None = None
    boundary_events: list[Any] | None = None


class BpmnSubProcessManager:
    """Manages event sub-process registration, transaction lifecycle, and sub-process completion checks."""

    def __init__(self) -> None:
        from .bpmn_execution_semantics import BpmnEventSubProcessHandler, BpmnTransactionHandler
        self._event_sub_process_handler = BpmnEventSubProcessHandler()
        self._transaction_handler = BpmnTransactionHandler()

    def register_event_sub_processes(self, instance_id: str, model: Any) -> None:
        for activity in model.activities:
            if isinstance(activity, dict):
                atype = str(activity.get("type", "")).lower()
                if "subprocess" in atype:
                    if activity.get("triggeredByEvent", False):
                        is_interrupting = activity.get("isInterrupting", True)
                        start_events = activity.get("startEvents", [])
                        for se in start_events:
                            self._event_sub_process_handler.register_event_sub_process(
                                instance_id, activity.get("id", ""), se, is_interrupting,
                            )
            else:
                atype = _activity_type_str(activity)
                if "subprocess" in atype:
                    triggered_by = getattr(activity, "triggered_by_event", False)
                    if triggered_by:
                        is_interrupting = getattr(activity, "is_interrupting", True)
                        start_events = getattr(activity, "start_events", []) or []
                        for se in start_events:
                            self._event_sub_process_handler.register_event_sub_process(
                                instance_id, getattr(activity, "id", ""), se, is_interrupting,
                            )

    def register_transactions(self, instance_id: str, model: Any) -> None:
        for activity in model.activities:
            atype = _activity_type_str(activity)
            if "transaction" in atype:
                a_id = _activity_id(activity)
                self._transaction_handler.begin_transaction(a_id, a_id)

    async def handle_activity_failure(
        self, activity_id: str, activity_type: str,
        sub_process_stack: list[_SubProcessContext],
        instance: ProcessInstance, orchestration_engine: Any,
    ) -> None:
        if sub_process_stack:
            ctx = sub_process_stack[-1]
            if ctx.is_transaction:
                self._transaction_handler.fail_activity(ctx.sub_process_id, activity_id)
                compensated = self._transaction_handler.compensate(ctx.sub_process_id)
                for comp_id in compensated:
                    instance.set_variable(f"compensated.{comp_id}", True)
                    from ..core.event_bus import Event as BusEvent, EventType
                    await orchestration_engine.event_bus.publish(
                        BusEvent(type=EventType.ACTIVITY_COMPLETED,
                              data={"instance_id": instance.id, "activity_id": comp_id, "compensated": True}),
                    )

    def check_adhoc_completion(
        self, instance: ProcessInstance, ctx: _SubProcessContext, model: Any,
        typed_model: TypedProcessModel | None = None,
    ) -> bool:
        completion_condition = None
        sub_process_node = None
        for activity in model.activities:
            if _activity_id(activity) == ctx.sub_process_id:
                if isinstance(activity, dict):
                    completion_condition = activity.get("payload", {}).get("completionCondition")
                else:
                    completion_cond = getattr(activity, "completion_condition", None)
                    if completion_cond:
                        completion_condition = getattr(completion_cond, "body", None) or str(completion_cond)
                break
        if typed_model:
            node = typed_model.get_node(ctx.sub_process_id)
            if isinstance(node, SubProcess):
                sub_process_node = node
                completion_cond = getattr(node, "completion_condition", None)
                if completion_cond:
                    completion_condition = getattr(completion_cond, "body", None) or str(completion_cond)
        if completion_condition:
            try:
                from ..expression.evaluator import EvaluationContext
                from ..expression.python_evaluator import PythonEvaluator
                return bool(PythonEvaluator().evaluate(
                    completion_condition, EvaluationContext(variables=instance.get_all_variables()),
                ))
            except Exception as exc:
                logger.debug("Completion condition evaluation failed: %s", exc)
                return False
        children: list[str] = []
        if sub_process_node and sub_process_node.flow_elements:
            children = [eid for eid in sub_process_node.flow_elements]
        else:
            for activity in model.activities:
                parent_id = _activity_get(activity, "parentSubProcessId") if isinstance(activity, dict) else getattr(activity, "parent_sub_process_id", None)
                if parent_id == ctx.sub_process_id:
                    children.append(_activity_id(activity))
        if not children:
            return True
        return all(
            instance.get_variable(f"activity.{c}.status") == "completed" for c in children
        )

    def check_sub_process_completion(
        self, instance: ProcessInstance, ctx: _SubProcessContext, model: Any,
        typed_model: TypedProcessModel | None = None,
    ) -> bool:
        end_events: list[str] = []
        for activity in model.activities:
            atype = _activity_type_str(activity)
            if "endevent" in atype:
                parent_id = _activity_get(activity, "parentSubProcessId") if isinstance(activity, dict) else getattr(activity, "parent_sub_process_id", None)
                if parent_id == ctx.sub_process_id:
                    end_events.append(_activity_id(activity))
        if typed_model:
            node = typed_model.get_node(ctx.sub_process_id)
            if isinstance(node, SubProcess) and node.flow_elements:
                for eid, elem in node.flow_elements.items():
                    if isinstance(elem, EndEvent):
                        if eid not in end_events:
                            end_events.append(eid)
        if end_events:
            completed_count = sum(
                1 for eid in end_events
                if instance.get_variable(f"activity.{eid}.status") == "completed"
            )
            return completed_count == len(end_events)
        return False

    def create_sub_process_context(
        self, sub_process_id: str, start_node_id: str, *,
        is_event_sub_process: bool = False, is_interrupting: bool = False,
        is_transaction: bool = False, is_adhoc: bool = False,
        parent_token_id: str | None = None,
    ) -> _SubProcessContext:
        ctx = _SubProcessContext()
        ctx.sub_process_id = sub_process_id
        ctx.start_node_id = start_node_id
        ctx.is_event_sub_process = is_event_sub_process
        ctx.is_interrupting = is_interrupting
        ctx.is_transaction = is_transaction
        ctx.is_adhoc = is_adhoc
        ctx.parent_token_id = parent_token_id
        ctx.boundary_events = []
        return ctx
