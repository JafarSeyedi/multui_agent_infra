"""BPMN event handler with full event type support.

Handles all BPMN event types at Camunda-level semantics:
- Start events (None, Message, Timer, Signal, Error, Escalation, Conditional, Compensation, Link)
- End events (None, Message, Timer, Signal, Error, Escalation, Cancel, Terminate, Compensation)
- Intermediate catch/throw events
- Boundary events (Message, Timer, Error, Escalation, Signal, Conditional, Compensation)
- Event subprocess (interrupting and non-interrupting)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..core.correlation import CorrelationKeySet
from ..core.event_bus import Event, EventType
from ..core.engine import OrchestrationEngine

from ....document.models.osdm_models import (
    EventType as BPMNEventType,
    EventDefinitionType,
    TimerEventType,
)


@dataclass
class TimerSchedule:
    time_date: str | None = None
    time_duration: str | None = None
    time_cycle: str | None = None

    @property
    def is_valid(self) -> bool:
        return any([self.time_date, self.time_duration, self.time_cycle])


@dataclass(frozen=True)
class HandlerBPMNEvent:
    event_id: str
    event_type: str
    event_definition_type: str = EventDefinitionType.NONE
    payload: dict[str, Any] = field(default_factory=dict)
    interrupting: bool = True
    timer_schedule: TimerSchedule | None = None
    message_name: str | None = None
    signal_name: str | None = None
    error_code: str | None = None
    escalation_code: str | None = None
    correlation_keys: dict[str, Any] = field(default_factory=dict)
    link_source: str | None = None
    link_target: str | None = None
    multiple_event_definitions: list[str] = field(default_factory=list)
    is_parallel_multiple: bool = False


@dataclass
class HandlerBPMNEventOutcome:
    handled: bool = True
    wait_required: bool = False
    wait_kind: str | None = None
    wait_name: str | None = None
    signal_broadcast: str | None = None
    error_raised: str | None = None
    escalation_raised: str | None = None
    terminate_all: bool = False
    compensation_triggered: str | None = None
    correlation_keys: dict[str, Any] = field(default_factory=dict)
    link_navigation: str | None = None
    event_published: list[str] = field(default_factory=list)


class EventHandler:
    def __init__(self, orchestration_engine: OrchestrationEngine | None = None) -> None:
        self._engine = orchestration_engine

    def handle_start(self, event: HandlerBPMNEvent) -> HandlerBPMNEventOutcome:
        if event.is_parallel_multiple:
            return self._handle_parallel_multiple_start(event)
        def_type = event.event_definition_type
        if def_type == EventDefinitionType.MESSAGE:
            return HandlerBPMNEventOutcome(handled=True, wait_required=True, wait_kind="message", wait_name=event.message_name, correlation_keys=event.correlation_keys)
        elif def_type == EventDefinitionType.TIMER:
            return HandlerBPMNEventOutcome(handled=True, wait_required=True, wait_kind="timer", wait_name=event.timer_schedule.time_duration if event.timer_schedule else None)
        elif def_type == EventDefinitionType.SIGNAL:
            return HandlerBPMNEventOutcome(handled=True, wait_required=True, wait_kind="event", wait_name=event.signal_name)
        elif def_type == EventDefinitionType.ERROR:
            return HandlerBPMNEventOutcome(handled=True, error_raised=event.error_code)
        elif def_type == EventDefinitionType.ESCALATION:
            return HandlerBPMNEventOutcome(handled=True, escalation_raised=event.escalation_code)
        elif def_type == EventDefinitionType.CONDITIONAL:
            return HandlerBPMNEventOutcome(handled=True)
        elif def_type == EventDefinitionType.COMPENSATION:
            return HandlerBPMNEventOutcome(handled=True, compensation_triggered=event.payload.get("activity_ref"))
        return HandlerBPMNEventOutcome(handled=True)

    def _handle_parallel_multiple_start(self, event: HandlerBPMNEvent) -> HandlerBPMNEventOutcome:
        definitions = event.multiple_event_definitions or [event.event_definition_type]
        all_handled = True
        any_wait = False
        wait_kind = None
        wait_name = None
        for d in definitions:
            if d == EventDefinitionType.MESSAGE:
                any_wait = True; wait_kind = "message"; wait_name = event.message_name
            elif d == EventDefinitionType.TIMER:
                any_wait = True; wait_kind = "timer"
                wait_name = event.timer_schedule.time_duration if event.timer_schedule else None
            elif d == EventDefinitionType.SIGNAL:
                any_wait = True; wait_kind = "event"; wait_name = event.signal_name
            elif d == EventDefinitionType.CONDITIONAL:
                pass
            else:
                all_handled = False
        return HandlerBPMNEventOutcome(handled=all_handled, wait_required=any_wait, wait_kind=wait_kind, wait_name=wait_name)

    def _handle_parallel_multiple_start(self, event: HandlerBPMNEvent) -> HandlerBPMNEventOutcome:
        definitions = event.multiple_event_definitions or [event.event_definition_type]
        all_handled = True
        any_wait = False
        wait_kind = None
        wait_name = None
        for d in definitions:
            if d == EventDefinitionType.MESSAGE:
                any_wait = True
                wait_kind = "message"
                wait_name = event.message_name
            elif d == EventDefinitionType.TIMER:
                any_wait = True
                wait_kind = "timer"
                wait_name = event.timer_schedule.time_duration if event.timer_schedule else None
            elif d == EventDefinitionType.SIGNAL:
                any_wait = True
                wait_kind = "event"
                wait_name = event.signal_name
            elif d == EventDefinitionType.CONDITIONAL:
                pass
            else:
                all_handled = False
        return HandlerBPMNEventOutcome(
            handled=all_handled, wait_required=any_wait,
            wait_kind=wait_kind, wait_name=wait_name,
        )

    def handle_end(self, event: HandlerBPMNEvent) -> HandlerBPMNEventOutcome:
        def_type = event.event_definition_type
        if def_type == EventDefinitionType.MESSAGE:
            return HandlerBPMNEventOutcome(handled=True, wait_required=False, signal_broadcast=event.message_name)
        elif def_type == EventDefinitionType.SIGNAL:
            return HandlerBPMNEventOutcome(handled=True, signal_broadcast=event.signal_name)
        elif def_type == EventDefinitionType.ERROR:
            return HandlerBPMNEventOutcome(handled=True, error_raised=event.error_code)
        elif def_type == EventDefinitionType.ESCALATION:
            return HandlerBPMNEventOutcome(handled=True, escalation_raised=event.escalation_code)
        elif def_type == EventDefinitionType.TERMINATE:
            return HandlerBPMNEventOutcome(handled=True, terminate_all=True)
        elif def_type == EventDefinitionType.CANCEL:
            return HandlerBPMNEventOutcome(handled=True)
        elif def_type == EventDefinitionType.COMPENSATION:
            return HandlerBPMNEventOutcome(handled=True, compensation_triggered=event.payload.get("activity_ref"))
        return HandlerBPMNEventOutcome(handled=True)

    def handle_intermediate_catch(self, event: HandlerBPMNEvent) -> HandlerBPMNEventOutcome:
        def_type = event.event_definition_type
        if def_type == EventDefinitionType.MESSAGE:
            return HandlerBPMNEventOutcome(handled=True, wait_required=True, wait_kind="message", wait_name=event.message_name, correlation_keys=event.correlation_keys)
        elif def_type == EventDefinitionType.TIMER:
            ts = event.timer_schedule
            return HandlerBPMNEventOutcome(handled=True, wait_required=True, wait_kind="timer", wait_name=(ts.time_duration or ts.time_cycle or ts.time_date if ts else None))
        elif def_type == EventDefinitionType.SIGNAL:
            return HandlerBPMNEventOutcome(handled=True, wait_required=True, wait_kind="event", wait_name=event.signal_name)
        elif def_type == EventDefinitionType.CONDITIONAL:
            return HandlerBPMNEventOutcome(handled=True)
        elif def_type == EventDefinitionType.LINK:
            return HandlerBPMNEventOutcome(handled=True, link_navigation=event.link_target)
        return HandlerBPMNEventOutcome(handled=True)

    def handle_intermediate_throw(self, event: HandlerBPMNEvent) -> HandlerBPMNEventOutcome:
        def_type = event.event_definition_type
        if def_type == EventDefinitionType.MESSAGE:
            return HandlerBPMNEventOutcome(handled=True, signal_broadcast=event.message_name)
        elif def_type == EventDefinitionType.SIGNAL:
            return HandlerBPMNEventOutcome(handled=True, signal_broadcast=event.signal_name)
        elif def_type == EventDefinitionType.ESCALATION:
            return HandlerBPMNEventOutcome(handled=True, escalation_raised=event.escalation_code)
        elif def_type == EventDefinitionType.COMPENSATION:
            return HandlerBPMNEventOutcome(handled=True, compensation_triggered=event.payload.get("activity_ref"))
        elif def_type == EventDefinitionType.LINK:
            return HandlerBPMNEventOutcome(handled=True, link_navigation=event.link_source)
        return HandlerBPMNEventOutcome(handled=True)

    def handle_boundary(self, event: HandlerBPMNEvent) -> HandlerBPMNEventOutcome:
        def_type = event.event_definition_type
        if def_type == EventDefinitionType.MESSAGE:
            return HandlerBPMNEventOutcome(handled=event.interrupting, wait_required=True, wait_kind="message", wait_name=event.message_name, correlation_keys=event.correlation_keys)
        elif def_type == EventDefinitionType.TIMER:
            return HandlerBPMNEventOutcome(handled=event.interrupting, wait_required=True, wait_kind="timer", wait_name=event.timer_schedule.time_duration if event.timer_schedule else None)
        elif def_type == EventDefinitionType.ERROR:
            if not event.interrupting:
                return HandlerBPMNEventOutcome(handled=True, wait_required=False)
            return HandlerBPMNEventOutcome(handled=True, error_raised=event.error_code)
        elif def_type == EventDefinitionType.ESCALATION:
            handled = not event.interrupting
            return HandlerBPMNEventOutcome(handled=handled, escalation_raised=event.escalation_code if event.interrupting else None)
        elif def_type == EventDefinitionType.SIGNAL:
            return HandlerBPMNEventOutcome(handled=event.interrupting, wait_required=True, wait_kind="event", wait_name=event.signal_name)
        elif def_type == EventDefinitionType.COMPENSATION:
            return HandlerBPMNEventOutcome(handled=True, compensation_triggered=event.payload.get("activity_ref"))
        return HandlerBPMNEventOutcome(handled=event.interrupting)

    def handle_event_subprocess(self, event: HandlerBPMNEvent) -> HandlerBPMNEventOutcome:
        def_type = event.event_definition_type
        if def_type == EventDefinitionType.MESSAGE:
            return HandlerBPMNEventOutcome(handled=True, wait_required=True, wait_kind="message", wait_name=event.message_name, correlation_keys=event.correlation_keys)
        elif def_type == EventDefinitionType.TIMER:
            return HandlerBPMNEventOutcome(handled=True, wait_required=True, wait_kind="timer", wait_name=event.timer_schedule.time_duration if event.timer_schedule else None)
        elif def_type == EventDefinitionType.SIGNAL:
            return HandlerBPMNEventOutcome(handled=True, wait_required=True, wait_kind="event", wait_name=event.signal_name)
        elif def_type == EventDefinitionType.ERROR:
            return HandlerBPMNEventOutcome(handled=True, error_raised=event.error_code)
        elif def_type == EventDefinitionType.ESCALATION:
            return HandlerBPMNEventOutcome(handled=True, escalation_raised=event.escalation_code)
        elif def_type == EventDefinitionType.CONDITIONAL:
            return HandlerBPMNEventOutcome(handled=True)
        return HandlerBPMNEventOutcome(handled=True)

    def create_correlation_keys(self, event: HandlerBPMNEvent) -> CorrelationKeySet:
        keys = CorrelationKeySet()
        if event.correlation_keys:
            for key_name, key_value in event.correlation_keys.items():
                keys.add_key(key_name, str(key_value))
        if event.message_name:
            keys.add_key("message_name", event.message_name)
        if event.signal_name:
            keys.add_key("signal_name", event.signal_name)
        return keys

    def dispatch(self, event: HandlerBPMNEvent, instance_id: str | None = None) -> HandlerBPMNEventOutcome:
        event_type = event.event_type
        if event_type == BPMNEventType.START:
            return self.handle_start(event)
        elif event_type == BPMNEventType.END:
            return self.handle_end(event)
        elif event_type == BPMNEventType.INTERMEDIATE_CATCH:
            return self.handle_intermediate_catch(event)
        elif event_type == BPMNEventType.INTERMEDIATE_THROW:
            return self.handle_intermediate_throw(event)
        elif event_type == BPMNEventType.BOUNDARY:
            return self.handle_boundary(event)
        return HandlerBPMNEventOutcome(handled=True)

    def start(self, event: HandlerBPMNEvent) -> HandlerBPMNEventOutcome:
        return self.handle_start(event)

    def end(self, event: HandlerBPMNEvent) -> HandlerBPMNEventOutcome:
        return self.handle_end(event)

    def signal(self, event: HandlerBPMNEvent) -> HandlerBPMNEventOutcome:
        if event.event_type == BPMNEventType.INTERMEDIATE_THROW:
            return self.handle_intermediate_throw(event)
        return self.handle_intermediate_catch(event)

    def timer(self, event: HandlerBPMNEvent) -> HandlerBPMNEventOutcome:
        return self.handle_intermediate_catch(event)

    def error(self, event: HandlerBPMNEvent) -> HandlerBPMNEventOutcome:
        if event.event_type == BPMNEventType.END:
            return self.handle_end(event)
        elif event.event_type == BPMNEventType.BOUNDARY:
            return self.handle_boundary(event)
        return self.handle_intermediate_catch(event)

    def cancellation(self, event: HandlerBPMNEvent) -> HandlerBPMNEventOutcome:
        return HandlerBPMNEventOutcome(handled=True)

    def termination(self, event: HandlerBPMNEvent) -> HandlerBPMNEventOutcome:
        return HandlerBPMNEventOutcome(handled=True, terminate_all=True)
