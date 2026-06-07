"""Pool and lane execution semantics for BPMN collaborations.

Implements pool-based execution scoping, lane-based task assignment,
and hierarchical lane nesting per BPMN 2.0 §15.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from ...document.models.osdm_models import (
    Pool,
    Lane,
    LaneSet,
    Participant,
    Process,
    MessageFlow,
)


logger = logging.getLogger(__name__)


@dataclass
class PoolExecutionContext:
    pool_id: str
    participant: dict[str, Any] = field(default_factory=dict)
    process_ref: str | None = None
    lane_hierarchy: dict[str, list[str]] = field(default_factory=dict)
    scoped_variables: dict[str, Any] = field(default_factory=dict)


@dataclass
class LaneAssignment:
    lane_id: str
    lane_name: str | None = None
    performer: str | None = None
    candidate_users: list[str] = field(default_factory=list)
    candidate_groups: list[str] = field(default_factory=list)


class PoolLaneExecutor:
    """Manages pool scoping and lane-based task assignment."""

    def __init__(self) -> None:
        self._pool_contexts: dict[str, PoolExecutionContext] = {}
        self._activity_lanes: dict[str, str] = {}
        self._lane_hierarchy: dict[str, list[str]] = {}

    def register_pool(
        self,
        pool: Pool,
        collaboration_participant: Participant | None = None,
    ) -> PoolExecutionContext:
        ctx = PoolExecutionContext(pool_id=pool.id)
        if collaboration_participant:
            ctx.participant = {
                "id": collaboration_participant.id,
                "name": getattr(collaboration_participant, "name", None),
                "process_ref": getattr(collaboration_participant, "process_ref", None),
            }
            ctx.process_ref = getattr(collaboration_participant, "process_ref", None)
        if pool.lane_sets:
            for lane_set in pool.lane_sets:
                for lane in lane_set.lanes:
                    child_refs = []
                    if lane.child_lane_set:
                        for child_lane in lane.child_lane_set.lanes:
                            child_refs.append(child_lane.id)
                    ctx.lane_hierarchy[lane.id] = child_refs
                    self._activity_lanes[lane.id] = lane.id
        self._pool_contexts[pool.id] = ctx
        return ctx

    def get_pool_context(self, pool_id: str) -> PoolExecutionContext | None:
        return self._pool_contexts.get(pool_id)

    def assign_activity_to_lane(self, activity_id: str, lane_id: str) -> None:
        self._activity_lanes[activity_id] = lane_id

    def get_lane_for_activity(self, activity_id: str) -> str | None:
        return self._activity_lanes.get(activity_id)

    def resolve_lane_assignment(
        self,
        activity_id: str,
        instance: Any,
    ) -> LaneAssignment | None:
        lane_id = self._activity_lanes.get(activity_id)
        if not lane_id:
            return None
        for pool_id, ctx in self._pool_contexts.items():
            for parent_lane_id, children in ctx.lane_hierarchy.items():
                if lane_id == parent_lane_id or lane_id in children:
                    assignment = LaneAssignment(
                        lane_id=lane_id,
                        performer=instance.get_variable(f"task.{activity_id}.assignee"),
                    )
                    candidate_users = instance.get_variable(f"task.{activity_id}.candidateUsers") or []
                    candidate_groups = instance.get_variable(f"task.{activity_id}.candidateGroups") or []
                    assignment.candidate_users = candidate_users
                    assignment.candidate_groups = candidate_groups
                    return assignment
        return LaneAssignment(lane_id=lane_id)

    def get_child_lanes(self, lane_id: str) -> list[str]:
        for pool_id, ctx in self._pool_contexts.items():
            if lane_id in ctx.lane_hierarchy:
                return ctx.lane_hierarchy[lane_id]
        return []

    def is_lane_in_pool(self, lane_id: str, pool_id: str) -> bool:
        ctx = self._pool_contexts.get(pool_id)
        if not ctx:
            return False
        all_lanes = set(ctx.lane_hierarchy.keys())
        for children in ctx.lane_hierarchy.values():
            all_lanes.update(children)
        return lane_id in all_lanes

    def scope_variables_to_pool(
        self,
        pool_id: str,
        variables: dict[str, Any],
    ) -> dict[str, Any]:
        ctx = self._pool_contexts.get(pool_id)
        if not ctx:
            return variables
        scoped = dict(variables)
        scoped["_pool_id"] = pool_id
        scoped["_process_ref"] = ctx.process_ref
        return scoped

    def get_statistics(self) -> dict[str, Any]:
        return {
            "total_pools": len(self._pool_contexts),
            "total_lanes": sum(len(ctx.lane_hierarchy) for ctx in self._pool_contexts.values()),
            "total_assignments": len(self._activity_lanes),
        }
