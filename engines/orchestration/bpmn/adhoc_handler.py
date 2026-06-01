"""Ad-hoc subprocess handler for BPMN ad-hoc tasks.

Supports ad hoc subprocess ordering (parallel/sequential), completion
conditions, and activation rules at Camunda-level semantics.

Uses OSDM-typed objects (AdHocSubProcess, FlowElement, AdHocOrdering)
with backward compatibility for dict-based construction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterator

from ...core.engine import OrchestrationEngine

from ....document.models.osdm_models import (
    AdHocOrdering,
    AdHocSubProcess,
    FlowElement,
    FormalExpression,
)


def get_ordering(adhoc: AdHocSubProcess) -> AdHocOrdering:
    """Return the ordering of an OSDM AdHocSubProcess."""
    return adhoc.ordering


@dataclass
class HandlerAdHocActivity:
    activity_id: str
    name: str | None = None
    activity_type: str = "task"
    is_enabled: bool = True
    is_active: bool = False
    is_completed: bool = False
    is_optional: bool = False
    dependencies: list[str] = field(default_factory=list)
    payload: dict[str, Any] = field(default_factory=dict)
    osdm_element: FlowElement | None = None

    @classmethod
    def from_osdm(cls, element: FlowElement, **overrides: Any) -> HandlerAdHocActivity:
        activity = cls(
            activity_id=element.id,
            name=element.name,
            osdm_element=element,
        )
        for key, value in overrides.items():
            setattr(activity, key, value)
        return activity


@dataclass
class HandlerAdHocProcess:
    activities: list[dict[str, Any]] = field(default_factory=list)
    ordering: AdHocOrdering = AdHocOrdering.PARALLEL
    completion_condition: str | None = None
    cancel_remaining_instances: bool = True
    process_id: str | None = None
    process_name: str | None = None
    children: list[FlowElement] = field(default_factory=list)
    osdm_sub_process: AdHocSubProcess | None = None

    @classmethod
    def prepare_from_osdm(cls, sub_process: AdHocSubProcess) -> HandlerAdHocProcess:
        completion = None
        if sub_process.completion_condition is not None:
            completion = sub_process.completion_condition.body
        children = list(sub_process.flow_elements.values()) if sub_process.flow_elements else []
        return cls(
            activities=[],
            ordering=get_ordering(sub_process),
            completion_condition=completion,
            cancel_remaining_instances=sub_process.cancel_remaining_instances,
            process_id=sub_process.id,
            process_name=sub_process.name,
            children=children,
            osdm_sub_process=sub_process,
        )


@dataclass
class HandlerAdHocExecutionState:
    process_id: str
    ordering: AdHocOrdering
    activities: dict[str, HandlerAdHocActivity] = field(default_factory=dict)
    completed_activities: list[str] = field(default_factory=list)
    active_activities: list[str] = field(default_factory=list)
    available_activities: list[str] = field(default_factory=list)
    is_completed: bool = False
    completion_satisfied: bool = False


@dataclass
class HandlerAdHocOutcome:
    activity_id: str
    completed: bool = True
    process_completed: bool = False
    remaining_active: list[str] = field(default_factory=list)
    completion_condition_met: bool = False


class AdhocHandler:
    def __init__(self, orchestration_engine: OrchestrationEngine | None = None) -> None:
        self._engine = orchestration_engine
        self._states: dict[str, HandlerAdHocExecutionState] = {}

    def prepare(self, process: HandlerAdHocProcess) -> HandlerAdHocExecutionState:
        process_id = process.process_id or f"adhoc:{id(process)}"
        state = HandlerAdHocExecutionState(process_id=process_id, ordering=process.ordering)

        if process.osdm_sub_process is not None:
            self._prepare_from_osdm_state(process, state)
        else:
            self._prepare_from_dicts(process, state)

        state.available_activities = self._compute_available(state)
        if process.ordering == AdHocOrdering.SEQUENTIAL and state.available_activities:
            state.available_activities = [state.available_activities[0]]

        self._states[process_id] = state
        return state

    def _prepare_from_osdm_state(
        self, process: HandlerAdHocProcess, state: HandlerAdHocExecutionState
    ) -> None:
        for element in process.children:
            activity = HandlerAdHocActivity.from_osdm(element)
            state.activities[activity.activity_id] = activity

    def _prepare_from_dicts(
        self, process: HandlerAdHocProcess, state: HandlerAdHocExecutionState
    ) -> None:
        for act_data in process.activities:
            activity = HandlerAdHocActivity(
                activity_id=act_data.get("id", f"activity_{len(state.activities)}"),
                name=act_data.get("name"),
                activity_type=act_data.get("type", "task"),
                is_optional=act_data.get("is_optional", False),
                dependencies=act_data.get("dependencies", []),
                payload=act_data.get("payload", {}),
            )
            state.activities[activity.activity_id] = activity

    def get_state(self, process_id: str) -> HandlerAdHocExecutionState | None:
        return self._states.get(process_id)

    def iterate(self, process: HandlerAdHocProcess) -> Iterator[dict[str, Any] | FlowElement]:
        if process.children:
            yield from process.children
        else:
            yield from process.activities

    def execute(self, process: HandlerAdHocProcess) -> list[str]:
        ids: list[str] = []
        for item in self.iterate(process):
            if isinstance(item, FlowElement):
                ids.append(item.id)
            else:
                ids.append(str(item.get("id", f"activity_{len(ids)}")))
        return ids

    def execute_activity(self, process_id: str, activity_id: str) -> HandlerAdHocOutcome | None:
        state = self._states.get(process_id)
        if state is None:
            return None
        activity = state.activities.get(activity_id)
        if activity is None or not activity.is_enabled:
            return None

        if state.ordering == AdHocOrdering.SEQUENTIAL:
            already_active = [state.activities[a] for a in state.active_activities]
            if already_active and not all(a.is_completed for a in already_active):
                return HandlerAdHocOutcome(activity_id=activity_id, completed=False)

        if state.active_activities and not activity.is_active:
            return HandlerAdHocOutcome(activity_id=activity_id, completed=False)

        activity.is_active = True
        activity.is_completed = True
        if activity_id not in state.completed_activities:
            state.completed_activities.append(activity_id)
        if activity_id in state.active_activities:
            state.active_activities.remove(activity_id)

        state.available_activities = self._compute_available(state)
        completion_met = self._check_completion_condition(state)
        if completion_met:
            state.is_completed = True
            state.completion_satisfied = True
            return HandlerAdHocOutcome(
                activity_id=activity_id,
                completed=True,
                process_completed=True,
                completion_condition_met=True,
            )

        return HandlerAdHocOutcome(
            activity_id=activity_id,
            completed=True,
            process_completed=False,
            remaining_active=list(state.active_activities),
            completion_condition_met=False,
        )

    def activate_activity(self, process_id: str, activity_id: str) -> bool:
        state = self._states.get(process_id)
        if state is None:
            return False
        activity = state.activities.get(activity_id)
        if activity is None:
            return False
        if activity_id in state.completed_activities:
            return False
        activity.is_enabled = True
        activity.is_active = True
        if activity_id not in state.active_activities:
            state.active_activities.append(activity_id)
        if activity_id not in state.available_activities:
            state.available_activities.append(activity_id)
        return True

    def disable_activity(self, process_id: str, activity_id: str) -> bool:
        state = self._states.get(process_id)
        if state is None:
            return False
        activity = state.activities.get(activity_id)
        if activity is None:
            return False
        activity.is_enabled = False
        activity.is_active = False
        if activity_id in state.active_activities:
            state.active_activities.remove(activity_id)
        if activity_id in state.available_activities:
            state.available_activities.remove(activity_id)
        return True

    def get_available_activities(self, process_id: str) -> list[str]:
        state = self._states.get(process_id)
        if state is None:
            return []
        return [a_id for a_id in state.available_activities if a_id not in state.completed_activities]

    def is_complete(self, process_id: str) -> bool:
        state = self._states.get(process_id)
        if state is None:
            return False
        return state.is_completed

    def _compute_available(self, state: HandlerAdHocExecutionState) -> list[str]:
        available = []
        completed_set = set(state.completed_activities)
        for act_id, activity in state.activities.items():
            if act_id in completed_set:
                continue
            if not activity.is_enabled:
                continue
            if all(d in completed_set for d in activity.dependencies):
                available.append(act_id)
        return available

    def _check_completion_condition(self, state: HandlerAdHocExecutionState) -> bool:
        if all(a.is_completed for a in state.activities.values()):
            return True
        enabled_remaining = [a for a in state.activities.values() if a.is_enabled and not a.is_completed]
        if not enabled_remaining:
            return True
        return False
