"""Choreography execution engine.

Executes BPMN choreography definitions with participant coordination,
message exchange, sub-choreography expansion, and call choreography resolution.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from engines.orchestration.models.osdm_models import (
    Choreography,
    ChoreographyTask,
    SubChoreography,
    CallChoreography,
    GlobalChoreographyTask,
    ChoreographyLoopType,
    Participant,
    MessageFlow,
    Collaboration,
)


logger = logging.getLogger(__name__)


@dataclass
class ChoreographyExecutionContext:
    choreography_id: str
    collaboration_id: str | None = None
    participants: dict[str, dict[str, Any]] = field(default_factory=dict)
    message_flows: list[dict[str, Any]] = field(default_factory=list)
    active_tasks: list[str] = field(default_factory=list)
    completed_tasks: list[str] = field(default_factory=list)
    status: str = "active"


class ChoreographyExecutor:
    """Executes BPMN choreography definitions."""

    def __init__(self, orchestration_engine: Any | None = None) -> None:
        self._engine = orchestration_engine
        self._contexts: dict[str, ChoreographyExecutionContext] = {}

    def create_context(
        self,
        choreography_id: str,
        collaboration: Collaboration | None = None,
    ) -> ChoreographyExecutionContext:
        ctx = ChoreographyExecutionContext(choreography_id=choreography_id)
        if collaboration:
            ctx.collaboration_id = collaboration.id
            if collaboration.participants:
                for participant in collaboration.participants:
                    ctx.participants[participant.id] = {
                        "id": participant.id,
                        "name": participant.name,
                        "process_ref": getattr(participant, "process_ref", None),
                    }
            if collaboration.message_flows:
                for mf in collaboration.message_flows:
                    ctx.message_flows.append({
                        "id": mf.id,
                        "source_ref": getattr(mf, "source_ref", None),
                        "target_ref": getattr(mf, "target_ref", None),
                        "message_ref": getattr(mf, "message_ref", None),
                    })
        self._contexts[choreography_id] = ctx
        return ctx

    def get_context(self, choreography_id: str) -> ChoreographyExecutionContext | None:
        return self._contexts.get(choreography_id)

    async def execute_task(
        self,
        task: ChoreographyTask,
        context: ChoreographyExecutionContext,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {
            "task_id": task.id,
            "choreography_id": context.choreography_id,
            "status": "initiated",
        }
        participant_refs = getattr(task, "participant_refs", [])
        initiating_ref = getattr(task, "initiating_participant_ref", None)
        if initiating_ref:
            result["initiating_participant"] = initiating_ref
        if participant_refs:
            result["receiving_participants"] = [
                p for p in participant_refs if p != initiating_ref
            ]
        message_flows = getattr(task, "message_flows", [])
        for mf in message_flows:
            await self._route_message_flow(mf, context, task)
        context.active_tasks.append(task.id)
        result["status"] = "completed"
        return result

    async def expand_sub_choreography(
        self,
        sub_choreography: SubChoreography,
        context: ChoreographyExecutionContext,
    ) -> list[dict[str, Any]]:
        results = []
        flow_elements = getattr(sub_choreography, "flow_elements", {})
        for element_id, element in flow_elements.items():
            if isinstance(element, ChoreographyTask):
                task_result = await self.execute_task(element, context)
                task_result["expanded_from"] = sub_choreography.id
                results.append(task_result)
            elif isinstance(element, SubChoreography):
                nested = await self.expand_sub_choreography(element, context)
                results.extend(nested)
        return results

    async def resolve_call_choreography(
        self,
        call_choreography: CallChoreography,
        context: ChoreographyExecutionContext,
    ) -> dict[str, Any]:
        called_ref = getattr(call_choreography, "called_choreography_ref", None)
        result: dict[str, Any] = {
            "call_id": call_choreography.id,
            "called_choreography_ref": called_ref,
            "status": "resolved",
        }
        if called_ref and self._engine:
            called_def = self._engine.definitions.get(called_ref)
            if called_def:
                result["definition_found"] = True
                result["definition_type"] = called_def.definition_type
            else:
                result["definition_found"] = False
                logger.warning("Called choreography not found: %s", called_ref)
        return result

    async def coordinate_participants(
        self,
        task: ChoreographyTask,
        context: ChoreographyExecutionContext,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {
            "task_id": task.id,
            "coordination_status": "initiated",
        }
        participant_refs = getattr(task, "participant_refs", [])
        initiating_ref = getattr(task, "initiating_participant_ref", None)
        active_participants = []
        for pref in participant_refs:
            pdata = context.participants.get(pref, {})
            active_participants.append({
                "id": pref,
                "name": pdata.get("name"),
                "is_initiating": pref == initiating_ref,
                "process_ref": pdata.get("process_ref"),
            })
        result["participants"] = active_participants
        result["coordination_status"] = "completed"
        return result

    async def _route_message_flow(
        self,
        message_flow: MessageFlow,
        context: ChoreographyExecutionContext,
        task: ChoreographyTask,
    ) -> None:
        source_ref = getattr(message_flow, "source_ref", None)
        target_ref = getattr(message_flow, "target_ref", None)
        message_ref = getattr(message_flow, "message_ref", None)
        if self._engine and source_ref and target_ref:
            self._engine.event_bus.publish(
                type=__import__("engines.orchestration.core.event_bus", fromlist=["EventType"]).EventType.MESSAGE_SENT,
                data={
                    "choreography_id": context.choreography_id,
                    "task_id": task.id,
                    "source": source_ref,
                    "target": target_ref,
                    "message_ref": str(message_ref) if message_ref else None,
                },
            )

    def get_statistics(self) -> dict[str, Any]:
        total_tasks = sum(len(ctx.active_tasks) + len(ctx.completed_tasks) for ctx in self._contexts.values())
        return {
            "total_choreographies": len(self._contexts),
            "total_tasks": total_tasks,
        }
