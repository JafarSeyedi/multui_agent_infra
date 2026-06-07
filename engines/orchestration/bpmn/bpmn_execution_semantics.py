"""BPMN 2.0 execution semantics per Annex A of the specification.

Implements token-based execution, gateway join/fork synchronization,
event sub-process handling, transaction semantics, and boundary event
activation rules.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ...document.models.osdm_models import (
    Process,
    FlowNode,
    Activity,
    Event,
    StartEvent,
    EndEvent,
    CatchEvent,
    ThrowEvent,
    BoundaryEvent,
    Gateway,
    ExclusiveGateway,
    InclusiveGateway,
    ParallelGateway,
    EventBasedGateway,
    ComplexGateway,
    SequenceFlow,
    SubProcess,
    TransactionSubProcess,
    AdHocSubProcess,
    EventType,
    EventDefinitionType,
    GatewayType,
)

from ..core.token import Token, TokenState
from ..dmn.feel_engine import EvaluationContext


logger = logging.getLogger(__name__)


class BpmnExecutionError(RuntimeError):
    pass


@dataclass
class TokenPlacement:
    """Represents a token at a specific node in the process."""
    token_id: str
    current_node_id: str
    state: TokenState = TokenState.ACTIVE
    parent_token_id: str | None = None
    scope_id: str | None = None


@dataclass
class GatewaySplit:
    """Result of a diverging gateway — which branches get tokens."""
    target_node_ids: list[str]
    gateway_id: str
    gateway_type: str
    conditions_evaluated: dict[str, bool] = field(default_factory=dict)


@dataclass
class EventSubProcessContext:
    """Tracks an active event sub-process."""
    sub_process_id: str
    start_event_id: str
    is_interrupting: bool
    parent_instance_id: str
    triggered: bool = False
    trigger_event_type: str | None = None


@dataclass
class TransactionContext:
    """Tracks a transaction sub-process."""
    transaction_id: str
    sub_process_id: str
    state: str = "active"
    completed_activities: list[str] = field(default_factory=list)
    failed_activity: str | None = None


class BpmnTokenEngine:
    """Token-based execution engine per BPMN 2.0 Annex A."""

    def __init__(self, token_manager: Any) -> None:
        self._token_manager = token_manager
        self._placements: dict[str, TokenPlacement] = {}

    def create_token(self, token_id: str, node_id: str, parent_token_id: str | None = None) -> TokenPlacement:
        placement = TokenPlacement(
            token_id=token_id,
            current_node_id=node_id,
            state=TokenState.ACTIVE,
            parent_token_id=parent_token_id,
        )
        self._placements[token_id] = placement
        return placement

    def remove_token(self, token_id: str) -> None:
        self._placements.pop(token_id, None)

    def get_tokens_at(self, node_id: str) -> list[TokenPlacement]:
        return [p for p in self._placements.values() if p.current_node_id == node_id and p.state == TokenState.ACTIVE]

    def get_active_tokens(self, instance_id: str | None = None) -> list[TokenPlacement]:
        return [p for p in self._placements.values() if p.state == TokenState.ACTIVE]


class BpmnGatewaySemantics:
    """Gateway activation rules per BPMN 2.0 §13.2."""

    @staticmethod
    def evaluate_diverging(
        gateway: Gateway,
        outgoing_flows: list[SequenceFlow],
        context: dict[str, Any],
    ) -> GatewaySplit:
        from ..expression.evaluator import EvaluationContext
        from ..expression.python_evaluator import PythonEvaluator

        if isinstance(gateway, ExclusiveGateway):
            return BpmnGatewaySemantics._split_exclusive(gateway, outgoing_flows, context, PythonEvaluator)
        elif isinstance(gateway, InclusiveGateway):
            return BpmnGatewaySemantics._split_inclusive(gateway, outgoing_flows, context, PythonEvaluator)
        elif isinstance(gateway, ParallelGateway):
            return BpmnGatewaySemantics._split_parallel(gateway, outgoing_flows)
        elif isinstance(gateway, EventBasedGateway):
            return BpmnGatewaySemantics._split_event_based(gateway, outgoing_flows)
        elif isinstance(gateway, ComplexGateway):
            return BpmnGatewaySemantics._split_complex(gateway, outgoing_flows, context)
        else:
            return BpmnGatewaySemantics._split_exclusive(gateway, outgoing_flows, context, PythonEvaluator)

    @staticmethod
    def _split_exclusive(gateway, outgoing_flows, context, evaluator) -> GatewaySplit:
        targets = []
        conditions = {}
        for flow in outgoing_flows:
            if not flow.target_ref:
                continue
            if flow.condition_expression:
                try:
                    result = bool(evaluator().evaluate(flow.condition_expression, EvaluationContext(variables=context)))
                    conditions[flow.target_ref] = result
                    if result:
                        targets.append(flow.target_ref)
                except Exception:
                    conditions[flow.target_ref] = False
            else:
                targets.append(flow.target_ref)
        if not targets:
            for flow in outgoing_flows:
                if flow.target_ref and not flow.condition_expression:
                    targets.append(flow.target_ref)
                    break
        if not targets and outgoing_flows:
            last = outgoing_flows[-1]
            if last.target_ref:
                targets.append(last.target_ref)
        return GatewaySplit(target_node_ids=targets, gateway_id=gateway.id, gateway_type="exclusive", conditions_evaluated=conditions)

    @staticmethod
    def _split_inclusive(gateway, outgoing_flows, context, evaluator) -> GatewaySplit:
        targets = []
        conditions = {}
        for flow in outgoing_flows:
            if not flow.target_ref:
                continue
            if flow.condition_expression:
                try:
                    result = bool(evaluator().evaluate(flow.condition_expression, EvaluationContext(variables=context)))
                    conditions[flow.target_ref] = result
                    if result:
                        targets.append(flow.target_ref)
                except Exception:
                    conditions[flow.target_ref] = False
            else:
                targets.append(flow.target_ref)
        if not targets and outgoing_flows:
            for flow in outgoing_flows:
                if flow.target_ref:
                    targets.append(flow.target_ref)
        return GatewaySplit(target_node_ids=targets, gateway_id=gateway.id, gateway_type="inclusive", conditions_evaluated=conditions)

    @staticmethod
    def _split_parallel(gateway, outgoing_flows) -> GatewaySplit:
        targets = [f.target_ref for f in outgoing_flows if f.target_ref]
        return GatewaySplit(target_node_ids=targets, gateway_id=gateway.id, gateway_type="parallel")

    @staticmethod
    def _split_event_based(gateway, outgoing_flows) -> GatewaySplit:
        return GatewaySplit(target_node_ids=[], gateway_id=gateway.id, gateway_type="eventBased")

    @staticmethod
    def _split_complex(gateway, outgoing_flows, context) -> GatewaySplit:
        activation_condition = getattr(gateway, 'activation_condition', None)
        if activation_condition:
            try:
                from ..expression.evaluator import EvaluationContext
                from ..expression.python_evaluator import PythonEvaluator
                if not bool(PythonEvaluator().evaluate(str(activation_condition), EvaluationContext(variables=context))):
                    return GatewaySplit(target_node_ids=[], gateway_id=gateway.id, gateway_type="complex")
            except Exception:
                pass
        default = getattr(gateway, 'default_sequence_flow', None)
        if default:
            return GatewaySplit(target_node_ids=[default.target_ref] if default.target_ref else [], gateway_id=gateway.id, gateway_type="complex")
        targets = [f.target_ref for f in outgoing_flows if f.target_ref]
        return GatewaySplit(target_node_ids=targets, gateway_id=gateway.id, gateway_type="complex")

    @staticmethod
    def can_converge(gateway: Gateway, incoming_flows: list[SequenceFlow], active_tokens: list[TokenPlacement]) -> bool:
        if isinstance(gateway, ParallelGateway):
            arrived_from = {t.current_node_id for t in active_tokens}
            for flow in incoming_flows:
                source = flow.source_ref.id if flow.source_ref else None
                if source and source not in arrived_from:
                    return False
            return True
        elif isinstance(gateway, InclusiveGateway):
            arrived_from = {t.current_node_id for t in active_tokens}
            activated_sources = set()
            for flow in incoming_flows:
                source = flow.source_ref.id if flow.source_ref else None
                if source and source in arrived_from:
                    activated_sources.add(source)
            return len(activated_sources) > 0
        else:
            return len(active_tokens) > 0


class BpmnEventSubProcessHandler:
    """Event sub-process handling per BPMN 2.0 §8.3.4."""

    def __init__(self) -> None:
        self._active_subprocesses: dict[str, list[EventSubProcessContext]] = {}

    def register_event_sub_process(
        self,
        instance_id: str,
        sub_process_id: str,
        start_event: StartEvent,
        is_interrupting: bool,
    ) -> EventSubProcessContext:
        ctx = EventSubProcessContext(
            sub_process_id=sub_process_id,
            start_event_id=start_event.id,
            is_interrupting=is_interrupting,
            parent_instance_id=instance_id,
        )
        if instance_id not in self._active_subprocesses:
            self._active_subprocesses[instance_id] = []
        self._active_subprocesses[instance_id].append(ctx)
        return ctx

    def find_triggered_sub_process(
        self,
        instance_id: str,
        event_type: str,
        event_definition_type: str,
    ) -> EventSubProcessContext | None:
        subprocesses = self._active_subprocesses.get(instance_id, [])
        for ctx in subprocesses:
            if ctx.triggered:
                continue
            if self._matches_start_event(ctx, event_type, event_definition_type):
                return ctx
        return None

    def _matches_start_event(self, ctx: EventSubProcessContext, event_type: str, event_definition_type: str) -> bool:
        if event_type != EventType.START:
            return False
        return event_definition_type in {
            EventDefinitionType.MESSAGE,
            EventDefinitionType.TIMER,
            EventDefinitionType.SIGNAL,
            EventDefinitionType.ERROR,
            EventDefinitionType.ESCALATION,
            EventDefinitionType.CONDITIONAL,
            EventDefinitionType.CANCEL,
            EventDefinitionType.COMPENSATION,
        }

    def mark_triggered(self, ctx: EventSubProcessContext, trigger_event_type: str) -> None:
        ctx.triggered = True
        ctx.trigger_event_type = trigger_event_type

    def should_interrupt_parent(self, ctx: EventSubProcessContext) -> bool:
        return ctx.is_interrupting and ctx.triggered

    def get_active_sub_processes(self, instance_id: str) -> list[EventSubProcessContext]:
        return [ctx for ctx in self._active_subprocesses.get(instance_id, []) if not ctx.triggered]

    def clear_instance(self, instance_id: str) -> int:
        count = len(self._active_subprocesses.pop(instance_id, []))
        return count


class BpmnTransactionHandler:
    """Transaction sub-process handling per BPMN 2.0 §8.3.5."""

    def __init__(self) -> None:
        self._transactions: dict[str, TransactionContext] = {}

    def begin_transaction(
        self,
        transaction_id: str,
        sub_process_id: str,
    ) -> TransactionContext:
        ctx = TransactionContext(
            transaction_id=transaction_id,
            sub_process_id=sub_process_id,
            state="active",
        )
        self._transactions[transaction_id] = ctx
        return ctx

    def complete_activity(self, transaction_id: str, activity_id: str) -> None:
        ctx = self._transactions.get(transaction_id)
        if ctx and activity_id not in ctx.completed_activities:
            ctx.completed_activities.append(activity_id)

    def fail_activity(self, transaction_id: str, activity_id: str) -> None:
        ctx = self._transactions.get(transaction_id)
        if ctx:
            ctx.state = "failed"
            ctx.failed_activity = activity_id

    def compensate(self, transaction_id: str) -> list[str]:
        ctx = self._transactions.get(transaction_id)
        if ctx is None:
            return []
        ctx.state = "compensating"
        compensated = list(reversed(ctx.completed_activities))
        ctx.state = "compensated"
        return compensated

    def cancel(self, transaction_id: str) -> bool:
        ctx = self._transactions.get(transaction_id)
        if ctx is None:
            return False
        ctx.state = "cancelled"
        return True

    def commit(self, transaction_id: str) -> bool:
        ctx = self._transactions.get(transaction_id)
        if ctx is None:
            return False
        ctx.state = "committed"
        return True

    def get_context(self, transaction_id: str) -> TransactionContext | None:
        return self._transactions.get(transaction_id)


class BpmnBoundaryEventHandler:
    """Boundary event activation rules per BPMN 2.0 §9.4.3."""

    @staticmethod
    def should_activate(
        boundary_event: BoundaryEvent,
        trigger_event_type: str,
        trigger_event_definition_type: str,
    ) -> bool:
        if boundary_event.event_type != trigger_event_type:
            return False
        for event_def in boundary_event.event_definitions:
            if event_def.type == trigger_event_definition_type:
                return True
        return False

    @staticmethod
    def is_interrupting(boundary_event: BoundaryEvent) -> bool:
        return getattr(boundary_event, 'cancel_activity', True)

    @staticmethod
    def get_outgoing_flows(boundary_event: BoundaryEvent, all_flows: list[SequenceFlow]) -> list[SequenceFlow]:
        outgoing = []
        for flow in all_flows:
            source = flow.source_ref.id if flow.source_ref else None
            if source == boundary_event.id:
                outgoing.append(flow)
        return outgoing
