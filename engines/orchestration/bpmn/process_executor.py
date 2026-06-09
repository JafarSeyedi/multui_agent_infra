"""Core BPMN process traversal and scheduling.

Implements BPMN 2.0 Annex A execution semantics including:
- Token-based execution with proper gateway join/fork synchronization
- Event sub-process handling (interrupting and non-interrupting)
- Transaction sub-process handling with compensation
- Ad-hoc sub-process completion condition evaluation
- Boundary event activation and token management

Uses OSDM-typed objects (Activity, Task, Event, Gateway, SequenceFlow, etc.)
instead of raw dictionaries for type-safe model traversal.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, cast

from ..core.correlation import CorrelationKeySet
from ..core.event_bus import Event as BusEvent, EventType
from ..core.context import ContextManager, ContextScope, ExecutionContext
from ..core.engine import OrchestrationEngine, ProcessDefinition
from ..core.instance import ProcessInstance
from ..core.token import Token, TokenState
from ..runtime.state_manager import StateManager
from .activity_handler import ActivityHandler, ActivityExecutionResult
from .sequence_flow import compute_next_nodes, HandlerSequenceFlow
from .bpmn_execution_semantics import (
    BpmnEventSubProcessHandler,
    BpmnTransactionHandler,
    BpmnBoundaryEventHandler,
    BpmnGatewaySemantics,
)
from .process_model import TypedProcessModel, classify_node
from ...document.models.osdm_models import (
    Activity,
    Task,
    Event as OsdmEvent,
    Gateway,
    SequenceFlow,
    SubProcess,
    StartEvent,
    EndEvent,
    CatchEvent,
    ThrowEvent,
    BoundaryEvent,
    IntermediateCatchEvent,
    IntermediateThrowEvent,
    ExclusiveGateway,
    InclusiveGateway,
    ParallelGateway,
    EventBasedGateway,
    ComplexGateway,
    FlowNode,
    FlowElement,
    LoopCharacteristics,
    ActivityType,
)


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProcessModel:
    definition_id: str
    start_node: str | None
    activities: list[dict[str, Any]]
    flows: list[HandlerSequenceFlow]


@dataclass(frozen=True)
class ProcessExecutionOutcome:
    completed: bool
    waiting: bool = False
    current_node: str | None = None


@dataclass
class _SubProcessContext:
    sub_process_id: str
    start_node_id: str
    is_event_sub_process: bool = False
    is_interrupting: bool = False
    is_transaction: bool = False
    is_adhoc: bool = False
    parent_token_id: str | None = None
    boundary_events: list[BoundaryEvent] = field(default_factory=list)


class BPMNProcessExecutor:
    """Evaluate a BPMN process dictionary and perform activity transitions.

    Implements BPMN 2.0 Annex A execution semantics:
    - Token-based execution with proper fork/join at gateways
    - Event sub-process registration and triggering
    - Transaction sub-process with compensation
    - Ad-hoc sub-process with completion conditions
    - Boundary event activation (interrupting and non-interrupting)

    Supports two model input paths:
    1. Legacy dict-based payload via _normalize_model (backward compatible)
    2. OSDM-typed process definitions via _normalize_model_osdm (preferred)
    """

    def __init__(
        self,
        *,
        engine: object,
        orchestration_engine: OrchestrationEngine,
        state_manager: StateManager,
        context_manager: ContextManager,
    ) -> None:
        self._engine = engine
        self._orchestration_engine = orchestration_engine
        self._state_manager = state_manager
        self._context_manager = context_manager
        self._activity_handler = ActivityHandler(orchestration_engine=orchestration_engine)
        self._event_sub_process_handler = BpmnEventSubProcessHandler()
        self._transaction_handler = BpmnTransactionHandler()

    async def execute(self, instance: ProcessInstance, definition_payload: dict[str, Any]) -> ProcessExecutionOutcome:
        model = self._normalize_model(definition_payload)
        typed_model = self._normalize_model_osdm(definition_payload, model.definition_id)

        context = self._context_manager.get_context(instance.id)
        if context is None:
            context = self._context_manager.create_context(ContextScope.PROCESS, instance.id)

        if model.start_node is None:
            return ProcessExecutionOutcome(completed=True)

        start_node_id = model.start_node
        token = self._ensure_runtime_token(instance, start_node_id)

        sub_process_stack: list[_SubProcessContext] = []
        self._register_event_sub_processes(instance.id, model)
        self._register_transactions(instance.id, model)

        current: str | None = start_node_id
        visited: set[str] = set()
        guard_steps = 0
        active_tokens: dict[str, Token] = {token.token_id: token}
        # Track activated branches from inclusive gateway forks for proper join semantics
        activated_branches: dict[str, set[str]] = {}

        while current and guard_steps < 200:
            guard_steps += 1

            if current in visited and not self._is_gateway_typed(current, typed_model):
                break
            visited.add(current)

            activity = typed_model.get_node(current)
            if activity is None:
                activity = self._find_activity(model, current)
            if activity is None:
                break

            activity_id = self._resolve_node_id(activity)
            activity_type = self._resolve_activity_type(activity)
            before_variables = instance.get_all_variables()

            instance.start_activity(activity_id, self._resolve_node_name(activity, activity_id), activity_type)

            tokens_at_node = [t for t in active_tokens.values()
                             if t.current_element_id == current and t.state == TokenState.ACTIVE]

            if not tokens_at_node:
                break

            for t in tokens_at_node:
                t.move_to(activity_id, activity_type)
                t.create_snapshot(before_variables)

            await self._persist_tokens(active_tokens)
            await self._orchestration_engine.instance_manager.persist_instance(instance.id)
            await self._orchestration_engine.event_bus.publish(
                BusEvent(type=EventType.ACTIVITY_STARTED,
                      data={"instance_id": instance.id, "activity_id": activity_id, "activity_type": activity_type}),
            )

            execution_result = await self._execute_activity(instance, activity, context)

            if not execution_result.success:
                instance.fail_activity(activity_id, str(execution_result.error))
                await self._orchestration_engine.instance_manager.persist_instance(instance.id)
                await self._handle_activity_failure(instance, activity_id, activity_type, execution_result, sub_process_stack)
                raise RuntimeError(f"Activity failed: {execution_result.error}")

            await self._persist_new_variables(instance, before_variables)

            if execution_result.waiting:
                for t in tokens_at_node:
                    t.wait(f"{execution_result.wait_kind}:{execution_result.wait_name}")
                    t.create_snapshot(instance.get_all_variables())
                await self._persist_tokens(active_tokens)
                await self._register_wait(instance, activity_id, execution_result)
                await self._state_manager.set_persisted(instance.id, "waiting", data={
                    "activity_id": activity_id, "wait_kind": execution_result.wait_kind,
                    "wait_name": execution_result.wait_name,
                })
                await self._orchestration_engine.instance_manager.persist_instance(instance.id)
                return ProcessExecutionOutcome(completed=False, waiting=True, current_node=activity_id)

            instance.complete_activity(activity_id)
            for t in tokens_at_node:
                t.create_snapshot(instance.get_all_variables())
            await self._persist_tokens(active_tokens)
            await self._orchestration_engine.instance_manager.persist_instance(instance.id)
            await self._orchestration_engine.event_bus.publish(
                BusEvent(type=EventType.ACTIVITY_COMPLETED,
                      data={"instance_id": instance.id, "activity_id": activity_id, "activity_type": activity_type}),
            )

            next_nodes = self._compute_next(current, model, typed_model)

            if not next_nodes:
                # End event reached — complete tokens at this node
                for t in tokens_at_node:
                    t.complete()
                await self._persist_tokens(active_tokens)
                # Parallel end event aggregation: check if ALL active tokens are completed
                remaining_active = [t for t in active_tokens.values() if t.state == TokenState.ACTIVE]
                if not remaining_active:
                    # All tokens completed — process is done
                    if sub_process_stack:
                        # We're inside a sub-process; let the parent handle completion
                        pass
                    else:
                        # Top-level process completion
                        return ProcessExecutionOutcome(completed=True)
                # Some tokens still active — continue the loop (they're on other branches)
                if sub_process_stack:
                    ctx = sub_process_stack[-1]
                    if ctx.is_adhoc:
                        if self._check_adhoc_completion(instance, ctx, model, typed_model):
                            sub_process_stack.pop()
                    elif self._check_sub_process_completion(instance, ctx, model, typed_model):
                        sub_process_stack.pop()
                # Find the next active token to continue execution
                next_active = [t for t in active_tokens.values() if t.state == TokenState.ACTIVE]
                if next_active:
                    current = next_active[0].current_element_id
                else:
                    current = None
                continue

            gateway_type = self._classify_gateway_typed(current, typed_model)
            if gateway_type == "parallel":
                new_tokens = []
                for target in next_nodes:
                    for source_token in tokens_at_node:
                        new_token = self._orchestration_engine.token_manager.create_token(
                            instance.id, current_element_id=target,
                            parent_token_id=source_token.token_id,
                        )
                        new_token.move_to(target, "flow")
                        new_tokens.append(new_token)
                        active_tokens[new_token.token_id] = new_token
                await self._persist_tokens(active_tokens)
                current = next_nodes[0] if next_nodes else None
            elif gateway_type == "inclusive":
                if len(next_nodes) > 1:
                    selected = self._evaluate_gateway_split_typed(current, next_nodes, instance.get_all_variables(), gateway_type, typed_model)
                else:
                    selected = next_nodes if next_nodes else []
                # Track activated branches for inclusive join semantics
                if current and selected and len(selected) > 1:
                    activated_branches[current] = set(selected)
                elif current and selected and len(selected) == 1:
                    activated_branches[current] = set(selected)
                for t in tokens_at_node:
                    if selected:
                        t.move_to(selected[0], "flow")
                await self._persist_tokens(active_tokens)
                current = selected[0] if selected else None
            elif gateway_type in ("exclusive",):
                if len(next_nodes) > 1:
                    selected = self._evaluate_gateway_split_typed(current, next_nodes, instance.get_all_variables(), gateway_type, typed_model)
                else:
                    selected = next_nodes if next_nodes else []
                for t in tokens_at_node:
                    if selected:
                        t.move_to(selected[0], "flow")
                await self._persist_tokens(active_tokens)
                current = selected[0] if selected else None
            else:
                for t in tokens_at_node:
                    if next_nodes:
                        t.move_to(next_nodes[0], "flow")
                await self._persist_tokens(active_tokens)
                current = next_nodes[0] if next_nodes else None

            if current:
                converging = self._is_converging_gateway_typed(current, typed_model)
                if converging:
                    arrived = [t for t in active_tokens.values()
                              if t.current_element_id == current and t.state == TokenState.ACTIVE]
                    converging_gw_type = self._classify_gateway_typed(current, typed_model)
                    if converging_gw_type == "inclusive":
                        # Inclusive join: wait only for tokens on ACTIVATED branches
                        fork_gw = self._find_fork_for_converging(current, model, typed_model)
                        if fork_gw and fork_gw in activated_branches:
                            expected_count = len(activated_branches[fork_gw])
                        else:
                            incoming_flows = self._get_incoming_flows(current, model, typed_model)
                            expected_count = len(incoming_flows)
                        if len(arrived) < expected_count:
                            current = None
                            break
                    else:
                        # Other converging gateways: wait for all incoming flows
                        incoming_flows = self._get_incoming_flows(current, model, typed_model)
                        if len(arrived) < len(incoming_flows):
                            current = None
                            break

        if current and guard_steps >= 200:
            raise RuntimeError("BPMN process execution exceeded step limit")
        return ProcessExecutionOutcome(completed=False, current_node=current)

    async def _execute_activity(
        self, instance: ProcessInstance, activity: FlowNode | dict[str, Any], context: ExecutionContext,
    ) -> ActivityExecutionResult:
        if isinstance(activity, Activity):
            return self._activity_handler.execute_osdm(instance, activity, context=context)
        if isinstance(activity, dict):
            return self._activity_handler.execute_osdm(instance, cast(Activity, activity), context=context)
        if isinstance(activity, FlowNode):
            return self._activity_handler.execute_osdm(instance, cast(Activity, activity), context=context)
        return ActivityExecutionResult(success=True, output={"type": "unknown"})

    def _compute_next(
        self, current: str, model: ProcessModel, typed_model: TypedProcessModel,
    ) -> list[str]:
        """Compute next nodes, trying typed flows first, then falling back to dict flows."""
        outgoing_osdm = typed_model.get_outgoing_flows(current)
        if outgoing_osdm:
            results = []
            for flow in outgoing_osdm:
                target = self._resolve_ref_id(flow.target_ref)
                if target:
                    results.append(target)
            if results:
                return results
        typed_result = compute_next_nodes(model.flows, current)
        return typed_result.selected_targets

    def _get_incoming_flows(
        self, node_id: str, model: ProcessModel, typed_model: TypedProcessModel,
    ) -> list[Any]:
        """Get all incoming flows for a node from either typed or dict sources."""
        all_outgoing = []
        for flows in typed_model._flow_index.values():
            for flow in flows:
                target = self._resolve_ref_id(flow.target_ref)
                if target == node_id:
                    all_outgoing.append(flow)
        if all_outgoing:
            return all_outgoing
        return [f for f in model.flows
                if f.target_ref == node_id]

    def _resolve_ref_id(self, ref: Any) -> str | None:
        if ref is None:
            return None
        if isinstance(ref, str):
            return ref
        return getattr(ref, "id", None)

    def _resolve_node_id(self, node: Any) -> str:
        if isinstance(node, str):
            return node
        node_id = getattr(node, "id", None)
        return str(node_id) if node_id is not None else ""

    def _resolve_node_name(self, node: Any, fallback: str) -> str:
        if isinstance(node, str):
            return fallback
        name = getattr(node, "name", None)
        return str(name) if name else fallback

    def _resolve_activity_type(self, node: Any) -> str:
        if isinstance(node, str):
            return "task"
        classified = classify_node(node)
        if classified != "unknown":
            return classified
        if isinstance(node, Activity):
            atype = getattr(node, "activity_type", None)
            if atype:
                if isinstance(atype, ActivityType):
                    return atype.value
                return str(atype)
            return "task"
        if isinstance(node, Task):
            return "task"
        if isinstance(node, OsdmEvent):
            return "event"
        if isinstance(node, Gateway):
            return "gateway"
        return "task"

    def _normalize_model(self, payload: dict[str, Any]) -> ProcessModel:
        activities = list(payload.get("activities", []))
        raw_flows = list(payload.get("flows", []))
        typed_flows: list[HandlerSequenceFlow] = []
        for f in raw_flows:
            if isinstance(f, HandlerSequenceFlow):
                typed_flows.append(f)
            elif isinstance(f, dict):
                typed_flows.append(self._dict_to_handler_flow(f))
        start_node = payload.get("start_event_id")
        if not start_node:
            for item in activities:
                if str(item.get("type", "")).lower() in {"startevent", "start"}:
                    start_node = item.get("id")
                    break
        if not start_node:
            flow_elements = payload.get("flow_elements", payload.get("elements", {}))
            if isinstance(flow_elements, dict):
                for eid, elem in flow_elements.items():
                    if isinstance(elem, StartEvent):
                        start_node = eid
                        break
                    if isinstance(elem, dict) and str(elem.get("type", "")).lower() in {"startevent", "start"}:
                        start_node = eid
                        break
        return ProcessModel(
            definition_id=str(payload.get("id", "process")),
            start_node=start_node, activities=activities, flows=typed_flows,
        )

    @staticmethod
    def _dict_to_handler_flow(d: dict[str, Any]) -> HandlerSequenceFlow:
        return HandlerSequenceFlow(
            flow_id=str(d.get("id", "")),
            source_ref=str(d.get("source") or d.get("sourceRef") or d.get("source_id") or ""),
            target_ref=str(d.get("target") or d.get("targetRef") or d.get("target_id") or ""),
            condition_expression=str(d.get("condition") or d.get("conditionExpression") or "") or None,
            is_default=d.get("isDefault", d.get("is_default", False)),
        )

    def _normalize_model_osdm(self, definition_xml: dict[str, Any], definition_id: str) -> TypedProcessModel:
        """Build a TypedProcessModel from a definition payload containing OSDM flow elements.

        Accepts a dict payload that may include an OSDM Process object or a
        ``flow_elements`` mapping of FlowElement instances.
        """
        typed_model = TypedProcessModel(definition_id=definition_id)

        flow_elements = definition_xml.get("flow_elements", definition_xml.get("elements", {}))
        if isinstance(flow_elements, dict):
            for element_id, element in flow_elements.items():
                if isinstance(element, FlowNode):
                    typed_model._node_index[element_id] = element
                    if isinstance(element, SequenceFlow):
                        src = self._resolve_ref_id(element.source_ref)
                        if src:
                            if src not in typed_model._flow_index:
                                typed_model._flow_index[src] = []
                            typed_model._flow_index[src].append(element)
                    if isinstance(element, BoundaryEvent):
                        attached_id = None
                        if element.attached_to_ref:
                            attached_id = self._resolve_ref_id(element.attached_to_ref)
                        if attached_id and isinstance(attached_id, str):
                            if attached_id not in typed_model._boundary_events:
                                typed_model._boundary_events[attached_id] = []
                            typed_model._boundary_events[attached_id].append(element)

        processes = definition_xml.get("processes", [])
        if isinstance(processes, list):
            for proc in processes:
                if hasattr(proc, "flow_elements") and proc.flow_elements:
                    for element_id, element in proc.flow_elements.items():
                        if isinstance(element, FlowNode):
                            typed_model._node_index[element_id] = element
                    for element_id, element in proc.flow_elements.items():
                        if isinstance(element, SequenceFlow):
                            src = self._resolve_ref_id(element.source_ref)
                            if src:
                                if src not in typed_model._flow_index:
                                    typed_model._flow_index[src] = []
                                typed_model._flow_index[src].append(element)
                    for element_id, element in proc.flow_elements.items():
                        if isinstance(element, BoundaryEvent):
                            attached_id = None
                            if element.attached_to_ref:
                                attached_id = self._resolve_ref_id(element.attached_to_ref)
                            if attached_id and isinstance(attached_id, str):
                                if attached_id not in typed_model._boundary_events:
                                    typed_model._boundary_events[attached_id] = []
                                typed_model._boundary_events[attached_id].append(element)
                    typed_model.process = proc
                    break

        if not typed_model.start_node_id:
            typed_model.start_node_id = definition_xml.get("start_event_id")
        if not typed_model.start_node_id:
            for eid, elem in typed_model._node_index.items():
                if isinstance(elem, StartEvent):
                    typed_model.start_node_id = eid
                    break

        return typed_model

    def _convert_flow_elements_to_activities_and_flows(
        self, flow_elements: dict[str, FlowElement],
    ) -> tuple[list[FlowNode], list[SequenceFlow]]:
        """Convert OSDM flow elements to typed activities and flows lists.

        Returns typed FlowNode objects and SequenceFlow objects instead of raw dicts.
        """
        activities: list[FlowNode] = []
        flows: list[SequenceFlow] = []

        for element_id, element in flow_elements.items():
            if isinstance(element, SequenceFlow):
                flows.append(element)
            elif isinstance(element, FlowNode):
                activities.append(element)

        return activities, flows

    def _find_activity(self, model: ProcessModel, activity_id: str) -> dict[str, Any] | None:
        for item in model.activities:
            if item.get("id") == activity_id:
                return item
        return None

    # ── Typed gateway / node classification ──────────────────────────

    def _is_gateway_typed(self, node_id: str, typed_model: TypedProcessModel) -> bool:
        node = typed_model.get_node(node_id)
        if node is not None:
            return isinstance(node, Gateway)
        return False

    def _classify_gateway_typed(self, node_id: str, typed_model: TypedProcessModel) -> str:
        node = typed_model.get_node(node_id)
        if node is None:
            return "none"
        if isinstance(node, ExclusiveGateway):
            return "exclusive"
        if isinstance(node, InclusiveGateway):
            return "inclusive"
        if isinstance(node, ParallelGateway):
            return "parallel"
        if isinstance(node, EventBasedGateway):
            return "eventBased"
        if isinstance(node, ComplexGateway):
            return "complex"
        return "none"

    def _is_converging_gateway_typed(self, node_id: str, typed_model: TypedProcessModel) -> bool:
        node = typed_model.get_node(node_id)
        if node is None:
            return False
        return isinstance(node, (ParallelGateway, InclusiveGateway))

    def _find_fork_for_converging(
        self, converging_node: str, model: ProcessModel, typed_model: TypedProcessModel,
    ) -> str | None:
        """Find the diverging gateway that corresponds to this converging gateway.
        Used for inclusive gateway join semantics — join must know which branches
        were activated at the corresponding fork."""
        # Look backward through incoming sequence flows to find the matching diverging gateway
        incoming = self._get_incoming_flows(converging_node, model, typed_model)
        for flow_id in incoming:
            source = self._get_flow_source(flow_id, model, typed_model)
            if source and self._classify_gateway_typed(source, typed_model) in ("inclusive", "parallel"):
                return source
            # One more hop for nested flows
            if source:
                incoming2 = self._get_incoming_flows(source, model, typed_model)
                for flow_id2 in incoming2:
                    source2 = self._get_flow_source(flow_id2, model, typed_model)
                    if source2 and self._classify_gateway_typed(source2, typed_model) in ("inclusive", "parallel"):
                        return source2
        return None

    def _get_flow_source(self, flow_id: str, model: ProcessModel, typed_model: TypedProcessModel) -> str | None:
        """Get the source node ID for a given sequence flow."""
        for f in model.flows:
            if f.flow_id == flow_id:
                return f.source_ref if f.source_ref else None
        return None

    # ── Gateway condition evaluation (typed) ─────────────────────────

    def _evaluate_gateway_split_typed(
        self, gateway_id: str, targets: list[str], context: dict[str, Any], gateway_type: str,
        typed_model: TypedProcessModel,
    ) -> list[str]:
        from ..expression.evaluator import EvaluationContext
        from ..expression.python_evaluator import PythonEvaluator
        evaluator = PythonEvaluator()

        _outgoing = typed_model.get_outgoing_flows(gateway_id)

        if gateway_type == "exclusive":
            for target in targets:
                flow = self._find_flow_to_target_typed(gateway_id, target, typed_model)
                condition = self._extract_flow_condition(flow) if flow else None
                if condition:
                    try:
                        if bool(evaluator.evaluate(condition, EvaluationContext(variables=context))):
                            return [target]
                    except Exception:
                        continue
                else:
                    return [target]
            return [targets[-1]] if targets else []

        elif gateway_type == "inclusive":
            selected = []
            for target in targets:
                flow = self._find_flow_to_target_typed(gateway_id, target, typed_model)
                condition = self._extract_flow_condition(flow) if flow else None
                if condition:
                    try:
                        if bool(evaluator.evaluate(condition, EvaluationContext(variables=context))):
                            selected.append(target)
                    except Exception:
                        continue
                else:
                    selected.append(target)
            return selected if selected else ([targets[-1]] if targets else [])

        return targets

    def _find_flow_to_target_typed(
        self, source_id: str, target_id: str, typed_model: TypedProcessModel,
    ) -> SequenceFlow | None:
        for flow in typed_model.get_outgoing_flows(source_id):
            target = self._resolve_ref_id(flow.target_ref)
            if target == target_id:
                return flow
        return None

    def _extract_flow_condition(self, flow: SequenceFlow | None) -> str | None:
        if flow is None:
            return None
        if flow.condition_expression is None:
            return None
        body = getattr(flow.condition_expression, "body", None)
        return body if body else None

    # ── Legacy dict-based helpers (kept for backward compat) ─────────

    def _is_gateway(self, node_id: str, model: ProcessModel) -> bool:
        activity = self._find_activity(model, node_id)
        if activity:
            return str(activity.get("type", "")).lower().endswith("gateway")
        return False

    def _classify_gateway(self, node_id: str, model: ProcessModel) -> str:
        activity = self._find_activity(model, node_id)
        if not activity:
            return "none"
        t = str(activity.get("type", "")).lower()
        if "parallel" in t:
            return "parallel"
        if "exclusive" in t:
            return "exclusive"
        if "inclusive" in t:
            return "inclusive"
        if "eventbased" in t:
            return "eventBased"
        if "complex" in t:
            return "complex"
        return "none"

    def _is_converging_gateway(self, node_id: str, model: ProcessModel) -> bool:
        activity = self._find_activity(model, node_id)
        if not activity:
            return False
        t = str(activity.get("type", "")).lower()
        return "parallel" in t or "inclusive" in t

    def _evaluate_gateway_split(
        self, gateway_id: str, targets: list[str], context: dict[str, Any], gateway_type: str, model: ProcessModel | None = None,
    ) -> list[str]:
        from ..expression.evaluator import EvaluationContext
        from ..expression.python_evaluator import PythonEvaluator
        evaluator = PythonEvaluator()
        if gateway_type == "exclusive":
            for target in targets:
                if model:
                    flow = self._find_flow_to_target(gateway_id, target, model)
                else:
                    flow = None
                if flow and flow.condition_expression:
                    try:
                        if bool(evaluator.evaluate(flow.condition_expression, EvaluationContext(variables=context))):
                            return [target]
                    except Exception:
                        continue
                elif not flow or not flow.condition_expression:
                    return [target]
            return [targets[-1]] if targets else []
        elif gateway_type == "inclusive":
            selected = []
            for target in targets:
                if model:
                    flow = self._find_flow_to_target(gateway_id, target, model)
                else:
                    flow = None
                if flow and flow.condition_expression:
                    try:
                        if bool(evaluator.evaluate(flow.condition_expression, EvaluationContext(variables=context))):
                            selected.append(target)
                    except Exception:
                        continue
                else:
                    selected.append(target)
            return selected if selected else ([targets[-1]] if targets else [])
        return targets

    def _find_flow_to_target(self, source_id: str, target_id: str, model: ProcessModel) -> HandlerSequenceFlow | None:
        for f in model.flows:
            if f.source_ref == source_id and f.target_ref == target_id:
                return f
        return None

    # ── Token and variable persistence ───────────────────────────────

    def _ensure_runtime_token(self, instance: ProcessInstance, start_node: str) -> Token:
        tokens = self._orchestration_engine.token_manager.get_instance_tokens(instance.id)
        for token in tokens:
            if token.state in {TokenState.ACTIVE, TokenState.WAITING}:
                return token
        return self._orchestration_engine.token_manager.create_token(
            instance.id, current_element_id=start_node,
        )

    async def _persist_tokens(self, tokens: dict[str, Token]) -> None:
        for token in tokens.values():
            await self._orchestration_engine.token_manager.persist_token(token.token_id)

    async def _persist_new_variables(self, instance: ProcessInstance, before_variables: dict[str, Any]) -> None:
        after_variables = instance.get_all_variables()
        for name, value in after_variables.items():
            if name in before_variables and before_variables[name] == value:
                continue
            await self._orchestration_engine.variable_manager.set_persisted(instance.id, instance.id, name, value)

    async def _register_wait(
        self, instance: ProcessInstance, activity_id: str, execution_result: ActivityExecutionResult,
    ) -> None:
        if execution_result.wait_kind == "message" and execution_result.wait_name:
            keys = CorrelationKeySet()
            for name, value in dict(execution_result.correlation_keys or {}).items():
                resolved = instance.get_variable(str(value), value) if isinstance(value, str) else value
                keys.add_key(str(name), str(resolved))
            await self._orchestration_engine.correlation_engine.subscribe_message_persisted(
                execution_result.wait_name, keys, instance.id, activity_id,
            )
        elif execution_result.wait_kind == "event" and execution_result.wait_name:
            await self._orchestration_engine.correlation_engine.subscribe_event_persisted(
                execution_result.wait_name, instance.id, activity_id,
            )

    # ── Event sub-process and transaction registration ───────────────

    def _register_event_sub_processes(self, instance_id: str, model: ProcessModel) -> None:
        for activity in model.activities:
            atype = str(activity.get("type", "")).lower()
            if "subprocess" in atype:
                payload = activity.get("payload", {})
                triggered_by = payload.get("triggeredByEvent", False)
                if triggered_by:
                    is_interrupting = payload.get("isInterrupting", True)
                    start_events = payload.get("startEvents", [])
                    for se in start_events:
                        self._event_sub_process_handler.register_event_sub_process(
                            instance_id, activity.get("id", ""), se, is_interrupting,
                        )

    def _register_transactions(self, instance_id: str, model: ProcessModel) -> None:
        for activity in model.activities:
            atype = str(activity.get("type", "")).lower()
            if "transaction" in atype:
                self._transaction_handler.begin_transaction(
                    activity.get("id", ""), activity.get("id", ""),
                )

    async def _handle_activity_failure(
        self, instance: ProcessInstance, activity_id: str, activity_type: str,
        execution_result: ActivityExecutionResult, sub_process_stack: list[_SubProcessContext],
    ) -> None:
        if sub_process_stack:
            ctx = sub_process_stack[-1]
            if ctx.is_transaction:
                self._transaction_handler.fail_activity(ctx.sub_process_id, activity_id)
                compensated = self._transaction_handler.compensate(ctx.sub_process_id)
                for comp_id in compensated:
                    instance.set_variable(f"compensated.{comp_id}", True)
                    await self._orchestration_engine.event_bus.publish(
                        BusEvent(type=EventType.ACTIVITY_COMPLETED,
                              data={"instance_id": instance.id, "activity_id": comp_id, "compensated": True}),
                    )

    # ── Sub-process completion checks ────────────────────────────────

    def _check_adhoc_completion(
        self, instance: ProcessInstance, ctx: _SubProcessContext, model: ProcessModel,
        typed_model: TypedProcessModel | None = None,
    ) -> bool:
        completion_condition = None
        sub_process_node = None
        for activity in model.activities:
            if activity.get("id") == ctx.sub_process_id:
                completion_condition = activity.get("payload", {}).get("completionCondition")
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
            except Exception:
                return False
        children: list[str] = []
        if sub_process_node and sub_process_node.flow_elements:
            children = [eid for eid in sub_process_node.flow_elements]
        else:
            for activity in model.activities:
                if activity.get("payload", {}).get("parentSubProcessId") == ctx.sub_process_id:
                    children.append(activity.get("id", ""))
        if not children:
            return True
        all_completed = all(
            instance.get_variable(f"activity.{c}.status") == "completed" for c in children
        )
        return all_completed

    def _check_sub_process_completion(
        self, instance: ProcessInstance, ctx: _SubProcessContext, model: ProcessModel,
        typed_model: TypedProcessModel | None = None,
    ) -> bool:
        """Check if all end events in a sub-process are completed for proper parallel completion."""
        end_events = []
        
        # Collect end events from dict-based model
        for activity in model.activities:
            atype = str(activity.get("type", "")).lower()
            if "endevent" in atype:
                parent_id = activity.get("payload", {}).get("parentSubProcessId")
                if parent_id == ctx.sub_process_id:
                    end_events.append(activity.get('id'))
        
        # Collect end events from OSDM-typed model
        if typed_model:
            node = typed_model.get_node(ctx.sub_process_id)
            if isinstance(node, SubProcess) and node.flow_elements:
                for eid, elem in node.flow_elements.items():
                    if isinstance(elem, EndEvent):
                        if eid not in end_events:  # Avoid duplicates
                            end_events.append(eid)
        
        # For parallel completion: require ALL end events to be completed
        if end_events:
            completed_count = sum(
                1 for eid in end_events 
                if instance.get_variable(f"activity.{eid}.status") == "completed"
            )
            return completed_count == len(end_events)
        
        return False
