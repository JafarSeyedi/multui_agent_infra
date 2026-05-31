"""BPMN gateway decision support with full semantics.

Supports all BPMN gateway types at Camunda-level:
- ExclusiveGateway (XOR): single path based on conditions
- InclusiveGateway (OR): multiple paths if conditions are true
- ParallelGateway (AND): all paths taken simultaneously
- EventBasedGateway: path determined by first event that occurs
- ComplexGateway: custom activation conditions
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..expression.evaluator import EvaluationContext
from ..expression.python_evaluator import PythonEvaluator

from ....document.models.osdm_models import (
    GatewayType,
    GatewayDirection,
    EventBasedGatewayType,
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


class GatewayHandler:
    def __init__(self) -> None:
        self._evaluator = PythonEvaluator()

    def choose(self, *, gateway: dict[str, Any], context: dict[str, Any]) -> GatewayDecision:
        gateway_id = str(gateway.get("id", ""))
        gateway_type_str = gateway.get("gateway_type") or gateway.get("type", "Exclusive")
        gateway_type = self._to_gateway_type(gateway_type_str)
        gateway_direction = self._to_gateway_direction(gateway.get("direction", ""))
        branches = self._parse_branches(gateway, context)

        if gateway_type == GatewayType.EXCLUSIVE:
            return self._choose_exclusive(gateway_id, branches, gateway.get("default"))
        elif gateway_type == GatewayType.INCLUSIVE:
            return self._choose_inclusive(gateway_id, branches, gateway.get("default"))
        elif gateway_type == GatewayType.PARALLEL:
            return self._choose_parallel(gateway_id, branches)
        elif gateway_type == GatewayType.EVENT_BASED:
            return self._choose_event_based(gateway_id, gateway, context)
        elif gateway_type == GatewayType.COMPLEX:
            return self._choose_complex(gateway_id, gateway, context)
        else:
            return self._choose_exclusive(gateway_id, branches, gateway.get("default"))

    def _to_gateway_type(self, value: str) -> GatewayType:
        try:
            return GatewayType(value)
        except ValueError:
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
            return mapping.get(str(value).lower().replace(" ", "").replace("_", ""), GatewayType.EXCLUSIVE)

    def _to_gateway_direction(self, value: str) -> GatewayDirection:
        try:
            return GatewayDirection(value)
        except ValueError:
            return GatewayDirection.DIVERGING

    def _parse_branches(self, gateway, context):
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

    def _evaluate_condition(self, condition, context):
        if condition in {"true", "True", "1"}:
            return True
        if condition in {"false", "False", "0"}:
            return False
        try:
            return bool(self._evaluator.evaluate(condition, EvaluationContext(variables=context)))
        except Exception:
            return False

    def _choose_exclusive(self, gateway_id, branches, default):
        eval_ctx = {}
        for branch in sorted(branches, key=lambda b: b.priority):
            if branch.condition and not branch.is_default:
                if self._evaluate_condition(branch.condition, eval_ctx):
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

    def _choose_inclusive(self, gateway_id, branches, default):
        eval_ctx = {}
        selected = []
        for branch in sorted(branches, key=lambda b: b.priority):
            if branch.condition and not branch.is_default:
                if self._evaluate_condition(branch.condition, eval_ctx):
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

    def _choose_parallel(self, gateway_id, branches):
        all_targets = [branch.target for branch in branches]
        return GatewayDecision(gateway_id=gateway_id, next_targets=all_targets, gateway_type=GatewayType.PARALLEL)

    def _choose_event_based(self, gateway_id, gateway, context):
        outgoing = gateway.get("branches", gateway.get("outgoing", gateway.get("flows", [])))
        event_types = []
        for flow in outgoing:
            target = str(flow.get("target") or flow.get("targetRef") or flow.get("target_id", ""))
            event_type = flow.get("event_type") or flow.get("eventType") or (flow.get("eventDefinition", {}).get("type") if isinstance(flow.get("eventDefinition"), dict) else None)
            if event_type:
                event_types.append(event_type)
        triggered_event = gateway.get("triggered_event") or context.get(f"{gateway_id}.triggered_event")
        if triggered_event:
            for flow in outgoing:
                target = str(flow.get("target") or flow.get("targetRef") or flow.get("target_id", ""))
                flow_event = flow.get("event_type") or flow.get("eventType") or ""
                if flow_event == triggered_event:
                    return GatewayDecision(gateway_id=gateway_id, next_targets=[target], gateway_type=GatewayType.EVENT_BASED, event_triggered=triggered_event)
        return GatewayDecision(gateway_id=gateway_id, next_targets=[], gateway_type=GatewayType.EVENT_BASED)

    def _choose_complex(self, gateway_id, gateway, context):
        activation_condition = gateway.get("activationCondition") or gateway.get("activation_condition")
        if activation_condition:
            if not self._evaluate_condition(activation_condition, context):
                default = gateway.get("default")
                if default:
                    return GatewayDecision(gateway_id=gateway_id, next_targets=[str(default)], gateway_type=GatewayType.COMPLEX, activation_condition_met=False, default_used=True)
                return GatewayDecision(gateway_id=gateway_id, next_targets=[], gateway_type=GatewayType.COMPLEX, activation_condition_met=False)
        branches = self._parse_branches(gateway, context)
        selected = []
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
