"""Collaboration and message-flow handling for BPMN collaborations.

Supports participants, message flow, lanes, pools, conversation/collaboration semantics.
Provides both dict-based (backward-compatible) and OSDM-typed object interfaces.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ...core.event_bus import Event, EventType
from ...core.engine import OrchestrationEngine

from ....document.models.osdm_models import (
    Collaboration as OSDMCollaboration,
    ConversationLink as OSDMConversationLink,
    Lane as OSDMLane,
    LaneSet as OSDMLaneSet,
    MessageFlow as OSDMMessageFlow,
    Participant as OSDMParticipant,
)


@dataclass
class HandlerCollaborationContext:
    collaboration_id: str
    pools: dict[str, dict[str, Any]] = field(default_factory=dict)
    participants: dict[str, dict[str, Any]] = field(default_factory=dict)
    message_flows: list[dict[str, Any]] = field(default_factory=list)
    conversation_links: list[dict[str, Any]] = field(default_factory=dict)


@dataclass
class MessageRoutingResult:
    routed: bool = False
    target_pool: str | None = None
    target_participant: str | None = None
    message_ref: str | None = None
    events_published: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _id_from_ref(ref: Any) -> str | None:
    if ref is None:
        return None
    if isinstance(ref, str):
        return ref
    return getattr(ref, "id", None)


class CollaborationHandler:
    def __init__(self, orchestration_engine: OrchestrationEngine | None = None) -> None:
        self._engine = orchestration_engine
        self._contexts: dict[str, HandlerCollaborationContext] = {}
        self._message_queue: list[dict[str, Any]] = []
        self._osdm_participants: dict[str, OSDMParticipant] = {}
        self._osdm_message_flows: list[OSDMMessageFlow] = []

    def create_context(self, collaboration_id: str) -> HandlerCollaborationContext:
        ctx = HandlerCollaborationContext(collaboration_id=collaboration_id)
        self._contexts[collaboration_id] = ctx
        return ctx

    def get_context(self, collaboration_id: str) -> HandlerCollaborationContext | None:
        return self._contexts.get(collaboration_id)

    def add_pool(self, collaboration_id: str, pool: dict[str, Any]) -> bool:
        ctx = self._contexts.get(collaboration_id)
        if ctx is None:
            return False
        ctx.pools[pool.get("id", "")] = pool
        return True

    def add_participant(self, collaboration_id: str, participant: dict[str, Any]) -> bool:
        ctx = self._contexts.get(collaboration_id)
        if ctx is None:
            return False
        ctx.participants[participant.get("id", "")] = participant
        return True

    def add_participant_osdm(self, participant: OSDMParticipant) -> str:
        pid = participant.id
        self._osdm_participants[pid] = participant
        for ctx in self._contexts.values():
            ctx.participants[pid] = {"id": pid, "name": participant.name, "_osdm": True}
        return pid

    def add_message_flow_osdm(self, message_flow: OSDMMessageFlow) -> None:
        self._osdm_message_flows.append(message_flow)
        entry: dict[str, Any] = {
            "id": message_flow.id,
            "name": message_flow.name,
            "source": _id_from_ref(message_flow.source_ref),
            "target": _id_from_ref(message_flow.target_ref),
            "message_ref": _id_from_ref(message_flow.message_ref),
            "_osdm": True,
        }
        for ctx in self._contexts.values():
            ctx.message_flows.append(entry)

    def add_lane_osdm(self, pool_id: str, lane: OSDMLane) -> bool:
        ctx = self._contexts.get(pool_id)
        if ctx is None:
            for c in self._contexts.values():
                pool = c.pools.get(pool_id)
                if pool is not None:
                    lane_entry: dict[str, Any] = {
                        "id": lane.id,
                        "name": lane.name,
                        "flow_node_refs": [
                            _id_from_ref(fn) for fn in lane.flow_node_refs
                            if _id_from_ref(fn) is not None
                        ],
                        "_osdm": True,
                    }
                    pool.setdefault("lane_sets", []).append({"lanes": [lane_entry]})
                    return True
            return False
        pool = ctx.pools.get(pool_id)
        if pool is None:
            return False
        lane_entry = {
            "id": lane.id,
            "name": lane.name,
            "flow_node_refs": [
                _id_from_ref(fn) for fn in lane.flow_node_refs
                if _id_from_ref(fn) is not None
            ],
            "_osdm": True,
        }
        pool.setdefault("lane_sets", []).append({"lanes": [lane_entry]})
        return True

    def add_lane(self, collaboration_id: str, pool_id: str, lane: dict[str, Any]) -> bool:
        ctx = self._contexts.get(collaboration_id)
        if ctx is None:
            return False
        pool = ctx.pools.get(pool_id)
        if pool is None:
            return False
        pool.setdefault("lane_sets", []).append({"lanes": [lane]})
        return True

    def route(self, message_flow: dict[str, Any] | OSDMMessageFlow) -> MessageRoutingResult:
        if isinstance(message_flow, OSDMMessageFlow):
            source = _id_from_ref(message_flow.source_ref)
            target = _id_from_ref(message_flow.target_ref)
            message_ref = _id_from_ref(message_flow.message_ref)
        else:
            source = message_flow.get("source")
            target = message_flow.get("target")
            message_ref = message_flow.get("message_ref")
        for ctx in self._contexts.values():
            source_pool = self._find_pool_for_element(ctx, source)
            target_pool = self._find_pool_for_element(ctx, target)
            if source_pool and target_pool and source_pool != target_pool:
                return MessageRoutingResult(
                    routed=True, target_pool=target_pool,
                    target_participant=self._resolve_participant(ctx, target),
                    message_ref=message_ref,
                )
        return MessageRoutingResult(routed=False, errors=[f"No collaboration context for {source}->{target}"])

    def validate(self, message_flow: dict[str, Any] | OSDMMessageFlow) -> bool:
        if isinstance(message_flow, OSDMMessageFlow):
            source = _id_from_ref(message_flow.source_ref)
            target = _id_from_ref(message_flow.target_ref)
        else:
            source = message_flow.get("source")
            target = message_flow.get("target")
        return bool(source and target and source != target)

    def validate_collaboration(self, collaboration_id: str) -> list[str]:
        errors = []
        ctx = self._contexts.get(collaboration_id)
        if ctx is None:
            errors.append(f"Collaboration context not found: {collaboration_id}")
            return errors
        if not ctx.pools:
            errors.append(f"Collaboration {collaboration_id} has no pools")
        return errors

    def send_message(self, collaboration_id: str, message_flow: dict[str, Any] | OSDMMessageFlow) -> MessageRoutingResult:
        if not self.validate(message_flow):
            return MessageRoutingResult(routed=False, errors=["Invalid message flow"])
        ctx = self._contexts.get(collaboration_id)
        if ctx is None:
            return MessageRoutingResult(routed=False, errors=[f"Context not found: {collaboration_id}"])
        result = self.route(message_flow)
        if result.routed and self._engine:
            if isinstance(message_flow, OSDMMessageFlow):
                source_val = _id_from_ref(message_flow.source_ref)
                target_val = _id_from_ref(message_flow.target_ref)
                message_ref_val = _id_from_ref(message_flow.message_ref)
                payload: dict[str, Any] = {}
            else:
                source_val = message_flow.get("source")
                target_val = message_flow.get("target")
                message_ref_val = message_flow.get("message_ref")
                payload = message_flow.get("payload", {})
            self._engine.event_bus.publish(
                Event(type=EventType.MESSAGE_SENT, data={
                    "collaboration_id": collaboration_id, "source": source_val,
                    "target": target_val, "message_ref": message_ref_val,
                    "payload": payload,
                })
            )
        return result

    def _find_pool_for_element(self, ctx: HandlerCollaborationContext, element_id: str) -> str | None:
        for pool_id, pool in ctx.pools.items():
            for lane_set in pool.get("lane_sets", []):
                for lane in lane_set.get("lanes", []):
                    if element_id in lane.get("flow_node_refs", []):
                        return pool_id
            if pool.get("participant", {}).get("id") == element_id:
                return pool_id
        return None

    def _resolve_participant(self, ctx: HandlerCollaborationContext, element_id: str) -> str | None:
        pool_id = self._find_pool_for_element(ctx, element_id)
        if pool_id is None:
            return None
        pool = ctx.pools.get(pool_id)
        participant = pool.get("participant", {}) if pool else {}
        return participant.get("id") or pool_id
