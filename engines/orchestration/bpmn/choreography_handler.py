"""Choreography-oriented BPMN handler.

Supports choreography tasks, loop types, and participant/message coordination.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

from ..core.event_bus import Event, EventType
from ..core.engine import OrchestrationEngine

from .models.bpmn_models import ChoreographyLoopType, ChoreographyTask as OSDMChoreographyTask


logger = logging.getLogger(__name__)


@dataclass
class HandlerChoreographyStep:
    choreography_id: str
    participants: list[str]
    initiating_participant: str | None = None
    loop_type: ChoreographyLoopType = ChoreographyLoopType.NONE
    message_flows: list[dict[str, Any]] = field(default_factory=list)
    correlation_keys: dict[str, str] = field(default_factory=dict)


@dataclass
class HandlerChoreographyState:
    choreography_id: str
    current_tasks: list[str] = field(default_factory=list)
    completed_tasks: list[str] = field(default_factory=list)
    active_participants: list[str] = field(default_factory=list)
    message_queue: list[dict[str, Any]] = field(default_factory=list)
    correlation_bindings: dict[str, str] = field(default_factory=dict)


@dataclass
class HandlerChoreographyOutcome:
    step_id: str
    success: bool = True
    participants_notified: list[str] = field(default_factory=list)
    messages_sent: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    loop_remaining: int = 0


class ChoreographyHandler:
    def __init__(self, orchestration_engine: OrchestrationEngine | None = None) -> None:
        self._engine = orchestration_engine
        self._states: dict[str, HandlerChoreographyState] = {}

    def create_state(self, choreography_id: str) -> HandlerChoreographyState:
        state = HandlerChoreographyState(choreography_id=choreography_id)
        self._states[choreography_id] = state
        return state

    def get_state(self, choreography_id: str) -> HandlerChoreographyState | None:
        return self._states.get(choreography_id)

    def execute(self, step: HandlerChoreographyStep, context: dict[str, Any]) -> HandlerChoreographyOutcome:
        state = self._states.get(step.choreography_id)
        if state is None:
            state = self.create_state(step.choreography_id)

        state.current_tasks.append(step.choreography_id)
        state.active_participants.extend(p for p in step.participants if p not in state.active_participants)

        errors: list[str] = []
        participants_notified: list[str] = []
        messages_sent: list[dict[str, Any]] = []

        for msg_flow in step.message_flows:
            source = msg_flow.get("sourceRef") or msg_flow.get("source")
            target = msg_flow.get("targetRef") or msg_flow.get("target")
            message_name = msg_flow.get("messageRef") or msg_flow.get("message_name")
            if source and target:
                messages_sent.append({"source": source, "target": target, "message_name": message_name})
                participants_notified.extend([source, target])
                if self._engine:
                    asyncio.ensure_future(self._engine.event_bus.publish(
                        Event(type=EventType.MESSAGE_SENT, data={
                            "choreography_id": step.choreography_id, "source": source, "target": target, "message_name": message_name,
                        })
                    ))

        loop_remaining = 0
        if step.loop_type != ChoreographyLoopType.NONE:
            loop_remaining = int(step.correlation_keys.get("loopCardinality", "1")) - 1
        else:
            state.completed_tasks.append(step.choreography_id)

        return HandlerChoreographyOutcome(
            step_id=step.choreography_id, success=len(errors) == 0,
            participants_notified=participants_notified, messages_sent=messages_sent, errors=errors, loop_remaining=loop_remaining,
        )

    def is_task_completed(self, choreography_id: str, task_id: str) -> bool:
        state = self._states.get(choreography_id)
        return state is not None and task_id in state.completed_tasks

    def bind_correlation(self, choreography_id: str, key_name: str, value: str) -> None:
        state = self._states.get(choreography_id)
        if state is None:
            state = self.create_state(choreography_id)
        state.correlation_bindings[key_name] = value

    def resolve_correlation(self, choreography_id: str, key_name: str) -> str | None:
        state = self._states.get(choreography_id)
        return state.correlation_bindings.get(key_name) if state else None
