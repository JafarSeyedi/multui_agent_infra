# engines/orchestration/state_machine/models/state_machine_models.py
"""
State Machine models (SCXML / AWS Step Functions / Petri nets)
===============================================================
Extracted from osdm_models.py
"""
from __future__ import annotations

from dataclasses import dataclass, field

from engines.document.models.ssdm_models import ServiceOperation

from ...models.shared_models import (
    BaseElement,
    BaseOSDMDocument,
    CloudResourceBinding,
    ErrorHandlingConfig,
    Locator,
    PseudoStateKind,
    RetryConfig,
    TimeoutConfig,
    WorkflowStateType,
)
from ...bpmn.models.bpmn_models import (
    FormalExpression,
    Script,
    StateNode,
    TimerEventDefinition,
    Transition,
)


@dataclass
class State(StateNode):
    entry_actions: list[Script] = field(default_factory=list)
    exit_actions: list[Script] = field(default_factory=list)
    do_actions: list[Script] = field(default_factory=list)
    is_composite: bool = False
    is_orthogonal: bool = False
    regions: list[StateMachineRegion] = field(default_factory=list)
    cloud_resource: CloudResourceBinding | None = None
    error_handling: ErrorHandlingConfig | None = None
    retry: RetryConfig | None = None
    timeout: TimeoutConfig | None = None
    workflow_state_type: WorkflowStateType | None = None
    is_final: bool = False
    parallel: bool = False
    initial_state_id: str | None = None
    invoke: StateInvoke | None = None
    initial: State | PseudoState | None = None
    node_type: str | None = None
    locators: list[Locator] = field(default_factory=list)


@dataclass
class StateTransition(Transition):
    trigger: FormalExpression | None = None
    guard: FormalExpression | None = None
    effect: FormalExpression | None = None
    _target_id: str | None = None
    edge_type: str | None = None
    locators: list[Locator] = field(default_factory=list)
    directed: bool = True


@dataclass
class StateInvoke:
    invoke_type: str
    src: str | ServiceOperation | None = None
    id: str | None = None


@dataclass
class StateMachineRegion(BaseElement):
    states: list[State] = field(default_factory=list)
    transitions: list[StateTransition] = field(default_factory=list)
    initial_state: State | None = None
    places: list[Place] = field(default_factory=list)
    pn_transitions: list[PnTransition] = field(default_factory=list)
    arcs: list[Arc] = field(default_factory=list)


@dataclass
class StateMachineModel:
    id: str
    name: str
    top_region: StateMachineRegion = field(default_factory=lambda: StateMachineRegion(id=""))
    pseudo_states: list[PseudoState] = field(default_factory=list)
    timer_trigger: TimerEventDefinition | None = None


@dataclass
class PseudoState(StateNode):
    kind: PseudoStateKind = PseudoStateKind.INITIAL
    parent_state: State | None = None


@dataclass
class Place(State):
    initial_marking: int = 0
    capacity: int = 0


@dataclass
class PnTransition(Transition):
    timing_expression: FormalExpression | None = None


@dataclass
class Arc(Transition):
    weight: int = 1
    inhibitor: bool = False
    reset: bool = False
    arc_source: Place | PnTransition | None = None
    arc_target: Place | PnTransition | None = None


class StateMachineDocument(BaseOSDMDocument):
    state_machines: list[StateMachineModel] = field(default_factory=list)
