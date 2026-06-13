"""BPMN gateway decision support with full semantics.

Supports all BPMN gateway types at Camunda-level:
- ExclusiveGateway (XOR): single path based on conditions
- InclusiveGateway (OR): multiple paths if conditions are true
- ParallelGateway (AND): all paths taken simultaneously
- EventBasedGateway: path determined by first event that occurs
- ComplexGateway: custom activation conditions

Uses Strategy pattern for polymorphic gateway routing.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, cast

logger = logging.getLogger(__name__)

from ..expression.evaluator import EvaluationContext
from ..expression.python_evaluator import PythonEvaluator

from ...document.models.osdm_models import (
    FlowNode,
    GatewayType,
    GatewayDirection,
    EventBasedGatewayType,
    Gateway,
    ExclusiveGateway,
    InclusiveGateway,
    ParallelGateway,
    EventBasedGateway,
    ComplexGateway,
    SequenceFlow,
)


@dataclass(frozen=True)
class GatewayDecision:
    gateway_id: str
    next_targets: list[str]
    gateway_type: GatewayType = GatewayType.EXCLUSIVE
    default_used: bool = False
    event_triggered: str | None = None
    activation_condition_met: bool = True


@dataclass
class GatewayBranch:
    target: str
    condition: str | None = None
    priority: int = 0
    is_default: bool = False


@dataclass
class GatewayContext:
    gateway_id: str
    gateway_type: GatewayType = GatewayType.EXCLUSIVE
    gateway_direction: GatewayDirection = GatewayDirection.DIVERGING
    branches: list[GatewayBranch] = field(default_factory=list)
    default_branch: str | None = None
    activation_condition: str | None = None
    event_types: list[str] = field(default_factory=list)


class GatewayStrategy(ABC):
    """Strategy interface for gateway routing."""

    @abstractmethod
    def choose(
        self,
        gateway_id: str,
        branches: list[GatewayBranch],
        default: str | None,
        gateway: dict[str, Any] | None,
        context: dict[str, Any],
    ) -> GatewayDecision: ...

    def choose_osdm(
        self,
        gateway_id: str,
        branches: list[GatewayBranch],
        default: str | None,
        gateway: Gateway,
        outgoing_flows: list[SequenceFlow],
        context: dict[str, Any],
    ) -> GatewayDecision:
        return self.choose(gateway_id, branches, default, None, context)


class ExclusiveGatewayStrategy(GatewayStrategy):
    """XOR: exactly one path based on conditions."""

    def __init__(self) -> None:
        self._evaluator = PythonEvaluator()

    def choose(
        self,
        gateway_id: str,
        branches: list[GatewayBranch],
        default: str | None,
        gateway: dict[str, Any] | None,
        context: dict[str, Any],
    ) -> GatewayDecision:
        for branch in sorted(branches, key=lambda b: b.priority):
            if branch.condition and not branch.is_default:
                if self._evaluate_condition(branch.condition, context):
                    return GatewayDecision(gateway_id=gateway_id, next_targets=[branch.target], gateway_type=GatewayType.EXCLUSIVE)
            elif not branch.condition and not branch.is_default:
                continue
        for branch in branches:
            if branch.is_default:
                return GatewayDecision(gateway_id=gateway_id, next_targets=[branch.target], gateway_type=GatewayType.EXCLUSIVE, default_used=True)
        if default:
            return GatewayDecision(gateway_id=gateway_id, next_targets=[str(default)], gateway_type=GatewayType.EXCLUSIVE, default_used=True)
        if branches:
            return GatewayDecision(gateway_id=gateway_id, next_targets=[branches[0].target], gateway_type=GatewayType.EXCLUSIVE, default_used=True)
        return GatewayDecision(gateway_id=gateway_id, next_targets=[], gateway_type=GatewayType.EXCLUSIVE)

    def _evaluate_condition(self, condition: str, context: dict[str, Any]) -> bool:
        if condition in {"true", "True", "1"}:
            return True
        if condition in {"false", "False", "0"}:
            return False
        try:
            return bool(self._evaluator.evaluate(condition, EvaluationContext(variables=context)))
        except Exception as e:
            logger.warning("Condition evaluation failed for %r: %s", condition, e)
            return False


class InclusiveGatewayStrategy(GatewayStrategy):
    """OR: multiple paths if conditions are true."""

    def __init__(self) -> None:
        self._evaluator = PythonEvaluator()

    def choose(
        self,
        gateway_id: str,
        branches: list[GatewayBranch],
        default: str | None,
        gateway: dict[str, Any] | None,
        context: dict[str, Any],
    ) -> GatewayDecision:
        selected: list[str] = []
        for branch in sorted(branches, key=lambda b: b.priority):
            if branch.condition and not branch.is_default:
                if self._evaluate_condition(branch.condition, context):
                    selected.append(branch.target)
            elif not branch.condition and not branch.is_default:
                continue
        if not selected:
            for branch in branches:
                if branch.is_default:
                    selected.append(branch.target)
                    return GatewayDecision(gateway_id=gateway_id, next_targets=selected, gateway_type=GatewayType.INCLUSIVE, default_used=True)
            if default:
                selected.append(str(default))
                return GatewayDecision(gateway_id=gateway_id, next_targets=selected, gateway_type=GatewayType.INCLUSIVE, default_used=True)
        return GatewayDecision(gateway_id=gateway_id, next_targets=selected, gateway_type=GatewayType.INCLUSIVE)

    def _evaluate_condition(self, condition: str, context: dict[str, Any]) -> bool:
        if condition in {"true", "True", "1"}:
            return True
        if condition in {"false", "False", "0"}:
            return False
        try:
            return bool(self._evaluator.evaluate(condition, EvaluationContext(variables=context)))
        except Exception as e:
            logger.warning("Condition evaluation failed for %r: %s", condition, e)
            return False


class ParallelGatewayStrategy(GatewayStrategy):
    """AND: all paths taken simultaneously."""

    def choose(
        self,
        gateway_id: str,
        branches: list[GatewayBranch],
        default: str | None,
        gateway: dict[str, Any] | None,
        context: dict[str, Any],
    ) -> GatewayDecision:
        all_targets = [branch.target for branch in branches]
        return GatewayDecision(gateway_id=gateway_id, next_targets=all_targets, gateway_type=GatewayType.PARALLEL)


class EventBasedGatewayStrategy(GatewayStrategy):
    """Path determined by first event that occurs."""

    def choose(
        self,
        gateway_id: str,
        branches: list[GatewayBranch],
        default: str | None,
        gateway: dict[str, Any] | None,
        context: dict[str, Any],
    ) -> GatewayDecision:
        if gateway is None:
            return GatewayDecision(gateway_id=gateway_id, next_targets=[], gateway_type=GatewayType.EVENT_BASED)
        outgoing = gateway.get("branches", gateway.get("outgoing", gateway.get("flows", [])))
        is_parallel = gateway.get("parallelMultiple", False) or gateway.get("isParallelMultiple", False)
        triggered_event = gateway.get("triggered_event") or context.get(f"{gateway_id}.triggered_event")
        if triggered_event:
            for flow in outgoing:
                target = str(flow.get("target") or flow.get("targetRef") or flow.get("target_id", ""))
                flow_event = flow.get("event_type") or flow.get("eventType") or ""
                if flow_event == triggered_event:
                    return GatewayDecision(
                        gateway_id=gateway_id, next_targets=[target],
                        gateway_type=GatewayType.EVENT_BASED, event_triggered=triggered_event,
                    )
            return GatewayDecision(gateway_id=gateway_id, next_targets=[], gateway_type=GatewayType.EVENT_BASED)
        elif is_parallel:
            triggered_events_raw = gateway.get("triggered_events") or context.get(f"{gateway_id}.triggered_events") or []
            selected_targets: list[str] = []
            all_events_present = True
            for flow in outgoing:
                target = str(flow.get("target") or flow.get("targetRef") or flow.get("target_id", ""))
                flow_event = flow.get("event_type") or flow.get("eventType") or ""
                if flow_event:
                    if flow_event in triggered_events_raw:
                        selected_targets.append(target)
                    else:
                        all_events_present = False
            if selected_targets and all_events_present:
                return GatewayDecision(gateway_id=gateway_id, next_targets=selected_targets, gateway_type=GatewayType.EVENT_BASED)
            else:
                return GatewayDecision(gateway_id=gateway_id, next_targets=[], gateway_type=GatewayType.EVENT_BASED)
        return GatewayDecision(gateway_id=gateway_id, next_targets=[], gateway_type=GatewayType.EVENT_BASED)

    def choose_osdm(
        self,
        gateway_id: str,
        branches: list[GatewayBranch],
        default: str | None,
        gateway: Gateway,
        outgoing_flows: list[SequenceFlow],
        context: dict[str, Any],
    ) -> GatewayDecision:
        event_gateway = cast(EventBasedGateway, gateway)
        is_parallel = getattr(event_gateway, "parallel_multiple", False)
        triggered_event = context.get(f"{gateway_id}.triggered_event")
        if triggered_event:
            for flow in outgoing_flows:
                target = flow.target_ref if hasattr(flow, "target_ref") else None
                target_id = target.id if isinstance(target, FlowNode) else str(target) if target else None
                flow_events = getattr(flow, "event_types", []) or []
                if triggered_event in [str(e) for e in flow_events]:
                    return GatewayDecision(gateway_id=gateway_id, next_targets=[target_id] if target_id else [], gateway_type=GatewayType.EVENT_BASED, event_triggered=triggered_event)
        if is_parallel:
            triggered_events = context.get(f"{gateway_id}.triggered_events") or []
            flows_with_events: list[tuple[str | None, list[str]]] = []
            flows_without_events: list[str | None] = []
            for flow in outgoing_flows:
                target = flow.target_ref if hasattr(flow, "target_ref") else None
                target_id = target.id if isinstance(target, FlowNode) else str(target) if target else None
                flow_events = [str(e) for e in getattr(flow, "event_types", []) or []]
                if flow_events:
                    flows_with_events.append((target_id, flow_events))
                else:
                    flows_without_events.append(target_id)
            selected: list[str] = []
            all_present = True
            for target_id, flow_events in flows_with_events:
                if any(e in triggered_events for e in flow_events):
                    if target_id:
                        selected.append(target_id)
                else:
                    all_present = False
            if selected and all_present:
                return GatewayDecision(gateway_id=gateway_id, next_targets=selected, gateway_type=GatewayType.EVENT_BASED)
            elif selected and not all_present:
                return GatewayDecision(gateway_id=gateway_id, next_targets=[], gateway_type=GatewayType.EVENT_BASED)
        return GatewayDecision(gateway_id=gateway_id, next_targets=[], gateway_type=GatewayType.EVENT_BASED)


class ComplexGatewayStrategy(GatewayStrategy):
    """Custom activation conditions."""

    def __init__(self) -> None:
        self._evaluator = PythonEvaluator()

    def _evaluate_condition(self, condition: str, context: dict[str, Any]) -> bool:
        if condition in {"true", "True", "1"}:
            return True
        if condition in {"false", "False", "0"}:
            return False
        try:
            return bool(self._evaluator.evaluate(condition, EvaluationContext(variables=context)))
        except Exception as e:
            logger.warning("Condition evaluation failed for %r: %s", condition, e)
            return False

    def choose(
        self,
        gateway_id: str,
        branches: list[GatewayBranch],
        default: str | None,
        gateway: dict[str, Any] | None,
        context: dict[str, Any],
    ) -> GatewayDecision:
        if gateway is None:
            return GatewayDecision(gateway_id=gateway_id, next_targets=[b.target for b in branches], gateway_type=GatewayType.COMPLEX)
        activation_condition = gateway.get("activationCondition") or gateway.get("activation_condition")
        if activation_condition:
            if not self._evaluate_condition(activation_condition, context):
                if default:
                    return GatewayDecision(gateway_id=gateway_id, next_targets=[str(default)], gateway_type=GatewayType.COMPLEX, activation_condition_met=False, default_used=True)
                return GatewayDecision(gateway_id=gateway_id, next_targets=[], gateway_type=GatewayType.COMPLEX, activation_condition_met=False)
        selected: list[str] = []
        for branch in branches:
            if branch.condition:
                if self._evaluate_condition(branch.condition, context):
                    selected.append(branch.target)
            elif branch.is_default:
                pass
            else:
                selected.append(branch.target)
        if not selected:
            for branch in branches:
                if branch.is_default:
                    selected.append(branch.target)
        return GatewayDecision(gateway_id=gateway_id, next_targets=selected, gateway_type=GatewayType.COMPLEX, activation_condition_met=True)

    def choose_osdm(
        self,
        gateway_id: str,
        branches: list[GatewayBranch],
        default: str | None,
        gateway: Gateway,
        outgoing_flows: list[SequenceFlow],
        context: dict[str, Any],
    ) -> GatewayDecision:
        activation_cond = getattr(gateway, "activation_condition", None)
        if activation_cond and not self._evaluate_condition(str(activation_cond), context):
            default_id = default
            if not default_id:
                if hasattr(gateway, "default_sequence_flow") and gateway.default_sequence_flow:
                    default_flow = gateway.default_sequence_flow
                    if hasattr(default_flow, "target_ref"):
                        default_id = default_flow.target_ref.id if isinstance(default_flow.target_ref, FlowNode) else str(default_flow.target_ref)
            return GatewayDecision(gateway_id=gateway_id, next_targets=[default_id] if default_id else [], gateway_type=GatewayType.COMPLEX, activation_condition_met=False, default_used=bool(default_id))
        return GatewayDecision(gateway_id=gateway_id, next_targets=[b.target for b in branches], gateway_type=GatewayType.COMPLEX, activation_condition_met=True)


class GatewayHandler:
    """BPMN gateway decision handler using Strategy pattern.

    Delegates to the appropriate GatewayStrategy based on gateway type.
    """

    def __init__(self) -> None:
        self._strategies: dict[GatewayType, GatewayStrategy] = {
            GatewayType.EXCLUSIVE: ExclusiveGatewayStrategy(),
            GatewayType.INCLUSIVE: InclusiveGatewayStrategy(),
            GatewayType.PARALLEL: ParallelGatewayStrategy(),
            GatewayType.EVENT_BASED: EventBasedGatewayStrategy(),
            GatewayType.COMPLEX: ComplexGatewayStrategy(),
        }

    def choose(self, *, gateway: dict[str, Any], context: dict[str, Any]) -> GatewayDecision:
        gateway_id = str(gateway.get("id", ""))
        gateway_type_str = gateway.get("gateway_type") or gateway.get("type", "Exclusive")
        gateway_type = self._to_gateway_type(gateway_type_str)
        branches = self._parse_branches(gateway, context)
        strategy = self._strategies.get(gateway_type, self._strategies[GatewayType.EXCLUSIVE])
        return strategy.choose(gateway_id, branches, gateway.get("default"), gateway, context)

    def choose_osdm(self, *, gateway: Gateway, outgoing_flows: list[SequenceFlow], context: dict[str, Any]) -> GatewayDecision:
        gateway_id = gateway.id
        gateway_type = self._resolve_osdm_gateway_type(gateway)
        default_flow = getattr(gateway, "default_sequence_flow", None)
        default_id = default_flow.target_ref if default_flow and hasattr(default_flow, "target_ref") else None
        branches = self._parse_osdm_branches(outgoing_flows)
        strategy = self._strategies.get(gateway_type, self._strategies[GatewayType.EXCLUSIVE])
        return strategy.choose_osdm(gateway_id, branches, default_id, gateway, outgoing_flows, context)

    def _resolve_osdm_gateway_type(self, gateway: Gateway) -> GatewayType:
        if isinstance(gateway, ExclusiveGateway):
            return GatewayType.EXCLUSIVE
        if isinstance(gateway, InclusiveGateway):
            return GatewayType.INCLUSIVE
        if isinstance(gateway, ParallelGateway):
            return GatewayType.PARALLEL
        if isinstance(gateway, EventBasedGateway):
            return GatewayType.EVENT_BASED
        if isinstance(gateway, ComplexGateway):
            return GatewayType.COMPLEX
        return GatewayType.EXCLUSIVE

    def register_strategy(self, gateway_type: GatewayType, strategy: GatewayStrategy) -> None:
        """Register a custom strategy for a gateway type (extensibility point)."""
        self._strategies[gateway_type] = strategy

    def _parse_osdm_branches(self, outgoing_flows: list[SequenceFlow]) -> list[GatewayBranch]:
        branches = []
        for i, flow in enumerate(outgoing_flows):
            target = flow.target_ref if hasattr(flow, "target_ref") else None
            if not target:
                continue
            target_id = target.id if isinstance(target, FlowNode) else str(target)
            condition = getattr(flow, "condition_expression", None)
            is_default = getattr(flow, "is_default", False)
            priority = getattr(flow, "priority", i)
            branches.append(GatewayBranch(target=target_id, condition=condition, priority=priority, is_default=is_default))
        return branches

    def _to_gateway_type(self, value: str) -> GatewayType:
        try:
            return GatewayType(value)
        except ValueError:
            clean = str(value).lower().replace(" ", "").replace("_", "").replace("-", "")
            if clean.endswith("gateway"):
                clean = clean[:-len("gateway")]
            mapping = {
                "exclusive": GatewayType.EXCLUSIVE,
                "xor": GatewayType.EXCLUSIVE,
                "inclusive": GatewayType.INCLUSIVE,
                "or": GatewayType.INCLUSIVE,
                "parallel": GatewayType.PARALLEL,
                "and": GatewayType.PARALLEL,
                "eventbased": GatewayType.EVENT_BASED,
                "event_based": GatewayType.EVENT_BASED,
                "complex": GatewayType.COMPLEX,
            }
            return mapping.get(clean, GatewayType.EXCLUSIVE)

    def _parse_branches(self, gateway: dict[str, Any], context: dict[str, Any]) -> list[GatewayBranch]:
        branches = []
        flow_list = gateway.get("branches", gateway.get("flows", gateway.get("outgoing", [])))
        for i, flow in enumerate(flow_list):
            target = flow.get("target") or flow.get("targetRef") or flow.get("target_id")
            if target is None:
                continue
            condition = flow.get("condition") or flow.get("conditionExpression") or flow.get("expr")
            is_default = flow.get("isDefault", False)
            priority = flow.get("priority", i)
            branches.append(GatewayBranch(target=str(target), condition=condition, priority=priority, is_default=is_default))
        return branches
