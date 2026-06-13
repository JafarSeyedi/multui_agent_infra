"""Core BPMN process traversal and scheduling.

Implements BPMN 2.0 Annex A execution semantics including:
- Token-based execution with proper gateway join/fork synchronization
- Event sub-process handling (interrupting and non-interrupting)
- Transaction sub-process handling with compensation
- Ad-hoc sub-process completion condition evaluation
- Boundary event activation and token management

Uses OSDM-typed objects (Activity, Task, Event, Gateway, SequenceFlow, etc.)
instead of raw dictionaries for type-safe model traversal.

Delegates to focused services for model normalization, gateway classification,
and sub-process management to keep the execution loop lean.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, cast

from ..core.correlation import CorrelationKeySet
from ..core.event_bus import Event as BusEvent, EventType
from ..core.context import ContextManager, ContextScope, ExecutionContext
from ..core.engine import OrchestrationEngine
from ..core.instance import ProcessInstance
from ..core.token import Token, TokenStateEnum
from ..runtime.state_manager import StateManager
from .activity_handler import ActivityHandler, ActivityExecutionResult
from .sequence_flow import compute_next_nodes, HandlerSequenceFlow
from .process_model import TypedProcessModel, classify_node
from .model_normalizer import BpmnModelNormalizer, _activity_get, _activity_type_str, _activity_id
from .gateway_classifier import BpmnGatewayClassifier
from .sub_process_manager import BpmnSubProcessManager, _SubProcessContext
from ...document.models.osdm_models import (
    Activity,
    Task,
    Event as OsdmEvent,
    Gateway,
    SequenceFlow,
    FlowNode,
    ActivityType,
)


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProcessModel:
    definition_id: str
    start_node: str | None
    activities: list[Any]
    flows: list[HandlerSequenceFlow]


@dataclass(frozen=True)
class ProcessExecutionOutcome:
    completed: bool
    waiting: bool = False
    current_node: str | None = None


class BPMNProcessExecutor:
    """Evaluate a BPMN process dictionary and perform activity transitions.

    Implements BPMN 2.0 Annex A execution semantics with operations delegated
    to focused services injected via constructor.
    """

    def __init__(
        self,
        *,
        engine: object,
        orchestration_engine: OrchestrationEngine,
        state_manager: StateManager,
        context_manager: ContextManager,
        model_normalizer: BpmnModelNormalizer | None = None,
        gateway_classifier: BpmnGatewayClassifier | None = None,
        sub_process_manager: BpmnSubProcessManager | None = None,
    ) -> None:
        self._engine = engine
        self._orchestration_engine = orchestration_engine
        self._state_manager = state_manager
        self._context_manager = context_manager
        self._activity_handler = ActivityHandler(orchestration_engine=orchestration_engine)
        self.model_normalizer = model_normalizer or BpmnModelNormalizer()
        self.gateway_classifier = gateway_classifier or BpmnGatewayClassifier()
        self.sub_process_manager = sub_process_manager or BpmnSubProcessManager()

    async def execute(self, instance: ProcessInstance, definition_payload: dict[str, Any]) -> ProcessExecutionOutcome:
        model = self.model_normalizer.normalize(definition_payload)
        typed_model = self.model_normalizer.normalize_osdm(definition_payload, model.definition_id)

        context = self._context_manager.get_context(instance.id)
        if context is None:
            context = self._context_manager.create_context(ContextScope.PROCESS, instance.id)

        if model.start_node is None:
            return ProcessExecutionOutcome(completed=True)

        start_node_id = model.start_node
        token = self._ensure_runtime_token(instance, start_node_id)

        sub_process_stack: list[_SubProcessContext] = []
        self.sub_process_manager.register_event_sub_processes(instance.id, model)
        self.sub_process_manager.register_transactions(instance.id, model)

        current: str | None = start_node_id
        visited: set[str] = set()
        guard_steps = 0
        active_tokens: dict[str, Token] = {token.token_id: token}
        activated_branches: dict[str, set[str]] = {}

        while current and guard_steps < 200:
            guard_steps += 1

            if current in visited and not self.gateway_classifier.is_gateway_typed(current, typed_model):
                break
            visited.add(current)

            activity = typed_model.get_node(current)
            if activity is None:
                activity = self.model_normalizer.find_activity(model, current)
            if activity is None:
                break

            activity_id = self._resolve_node_id(activity)
            activity_type = self._resolve_activity_type(activity)
            before_variables = instance.get_all_variables()

            instance.start_activity(activity_id, self._resolve_node_name(activity, activity_id), activity_type)

            tokens_at_node = [t for t in active_tokens.values()
                             if t.current_element_id == current and t.state == TokenStateEnum.ACTIVE]

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
                await self.sub_process_manager.handle_activity_failure(
                    activity_id, activity_type, sub_process_stack, instance, self._orchestration_engine,
                )
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
                for t in tokens_at_node:
                    t.complete()
                await self._persist_tokens(active_tokens)
                remaining_active = [t for t in active_tokens.values() if t.state == TokenStateEnum.ACTIVE]
                if not remaining_active:
                    if sub_process_stack:
                        pass
                    else:
                        return ProcessExecutionOutcome(completed=True)
                if sub_process_stack:
                    ctx = sub_process_stack[-1]
                    if ctx.is_adhoc:
                        if self.sub_process_manager.check_adhoc_completion(instance, ctx, model, typed_model):
                            sub_process_stack.pop()
                    elif self.sub_process_manager.check_sub_process_completion(instance, ctx, model, typed_model):
                        sub_process_stack.pop()
                next_active = [t for t in active_tokens.values() if t.state == TokenStateEnum.ACTIVE]
                if next_active:
                    current = next_active[0].current_element_id
                else:
                    current = None
                continue

            gateway_type = self.gateway_classifier.classify_gateway_typed(current, typed_model)
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
                    selected = self.gateway_classifier.evaluate_gateway_split_typed(
                        current, typed_model, instance,
                    )
                else:
                    selected = next_nodes if next_nodes else []
                if current and selected:
                    activated_branches[current] = set(selected)
                for t in tokens_at_node:
                    if selected:
                        t.move_to(selected[0], "flow")
                await self._persist_tokens(active_tokens)
                current = selected[0] if selected else None
            elif gateway_type in ("exclusive",):
                if len(next_nodes) > 1:
                    selected = self.gateway_classifier.evaluate_gateway_split_typed(
                        current, typed_model, instance,
                    )
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
                converging = self.gateway_classifier.is_converging_gateway_typed(current, typed_model)
                if converging:
                    arrived = [t for t in active_tokens.values()
                              if t.current_element_id == current and t.state == TokenStateEnum.ACTIVE]
                    converging_gw_type = self.gateway_classifier.classify_gateway_typed(current, typed_model)
                    if converging_gw_type == "inclusive":
                        fork_gw = self.gateway_classifier.find_fork_for_converging(current, typed_model)
                        if fork_gw and fork_gw in activated_branches:
                            expected_count = len(activated_branches[fork_gw])
                        else:
                            incoming_flows = self._get_incoming_flows(current, model, typed_model)
                            expected_count = len(incoming_flows)
                        if len(arrived) < expected_count:
                            current = None
                            break
                    else:
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
        return self.model_normalizer.normalize(payload)

    @staticmethod
    def _dict_to_handler_flow(d: dict[str, Any]) -> HandlerSequenceFlow:
        from .model_normalizer import _dict_to_handler_flow as _norm_flow
        return _norm_flow(d)

    def _normalize_model_osdm(self, definition_xml: dict[str, Any], definition_id: str) -> TypedProcessModel:
        return self.model_normalizer.normalize_osdm(definition_xml, definition_id)

    def _find_activity(self, model: ProcessModel, activity_id: str) -> Any | None:
        return self.model_normalizer.find_activity(model, activity_id)

    def _is_gateway_typed(self, node_id: str, typed_model: TypedProcessModel) -> bool:
        return self.gateway_classifier.is_gateway_typed(node_id, typed_model)

    def _classify_gateway_typed(self, node_id: str, typed_model: TypedProcessModel) -> str:
        return self.gateway_classifier.classify_gateway_typed(node_id, typed_model)

    def _is_converging_gateway_typed(self, node_id: str, typed_model: TypedProcessModel) -> bool:
        return self.gateway_classifier.is_converging_gateway_typed(node_id, typed_model)

    def _find_fork_for_converging(
        self, converging_node: str, model: ProcessModel, typed_model: TypedProcessModel,
    ) -> str | None:
        return self.gateway_classifier.find_fork_for_converging(converging_node, typed_model)

    def _get_flow_source(self, flow_id: str, model: ProcessModel, typed_model: TypedProcessModel) -> str | None:
        return self.gateway_classifier.get_flow_source(flow_id, model, typed_model)

    def _evaluate_gateway_split_typed(
        self, gateway_id: str, targets: list[str], context: dict[str, Any], gateway_type: str,
        typed_model: TypedProcessModel,
    ) -> list[str]:
        # Build a minimal object with get_all_variables for classifier compatibility
        _ctx = type("_ctx", (), {"get_all_variables": lambda: context})()
        return self.gateway_classifier.evaluate_gateway_split_typed(
            gateway_id, typed_model, _ctx,
        )

    def _find_flow_to_target_typed(
        self, source_id: str, target_id: str, typed_model: TypedProcessModel,
    ) -> SequenceFlow | None:
        return self.gateway_classifier.find_flow_to_target_typed(source_id, target_id, typed_model)

    def _extract_flow_condition(self, flow: SequenceFlow | None) -> str | None:
        return self.gateway_classifier.extract_flow_condition(flow)

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
                    except Exception as exc:
                        logger.debug("Condition evaluation skipped for target %s: %s", target, exc)
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
                    except Exception as exc:
                        logger.debug("Condition evaluation skipped for target %s: %s", target, exc)
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
            if token.state in {TokenStateEnum.ACTIVE, TokenStateEnum.WAITING}:
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

    def _register_event_sub_processes(self, instance_id: str, model: ProcessModel) -> None:
        self.sub_process_manager.register_event_sub_processes(instance_id, model)

    def _register_transactions(self, instance_id: str, model: ProcessModel) -> None:
        self.sub_process_manager.register_transactions(instance_id, model)

    async def _handle_activity_failure(
        self, instance: ProcessInstance, activity_id: str, activity_type: str,
        execution_result: ActivityExecutionResult, sub_process_stack: list[_SubProcessContext],
    ) -> None:
        await self.sub_process_manager.handle_activity_failure(
            activity_id, activity_type, sub_process_stack, instance, self._orchestration_engine,
        )

    def _check_adhoc_completion(
        self, instance: ProcessInstance, ctx: _SubProcessContext, model: ProcessModel,
        typed_model: TypedProcessModel | None = None,
    ) -> bool:
        return self.sub_process_manager.check_adhoc_completion(instance, ctx, model, typed_model)

    def _check_sub_process_completion(
        self, instance: ProcessInstance, ctx: _SubProcessContext, model: ProcessModel,
        typed_model: TypedProcessModel | None = None,
    ) -> bool:
        return self.sub_process_manager.check_sub_process_completion(instance, ctx, model, typed_model)
