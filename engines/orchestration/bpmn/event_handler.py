"""BPMN event handler with full event type support.

Uses OSDM Event subclasses directly instead of raw dictionaries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from ..core.correlation import CorrelationKeySet
from ..core.engine import OrchestrationEngine

from engines.document.models.osdm_models import (
    Event as OsdmEvent,
    EventType,
    StartEvent,
    EndEvent,
    IntermediateCatchEvent,
    IntermediateThrowEvent,
    BoundaryEvent,
    ImplicitThrowEvent,
    EventDefinitionType,
    TimerEventDefinition,
    MessageEventDefinition,
    SignalEventDefinition,
    ErrorEventDefinition,
    EscalationEventDefinition,
    CompensateEventDefinition,
    ConditionalEventDefinition,
    LinkEventDefinition,
    CancelEventDefinition,
    TerminateEventDefinition,
    DueTimeDuration,
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

        def handle_timer_event(self, instance_id: str, timer_schedule: TimerSchedule) -> HandlerBPMNEventOutcome:
            """Handle timer event expiration and queue completion actions."""
            current_time = datetime.now().isoformat()

            if timer_schedule.time_date:
                if current_time >= timer_schedule.time_date:
                    return self._trigger_timer_completion(instance_id, timer_schedule)

            return HandlerBPMNEventOutcome(handled=True)

        def _parse_duration(self, duration_str: str) -> timedelta | None:
            return timedelta(minutes=int(duration_str)) if duration_str else None

        def _trigger_timer_completion(self, instance_id: str, timer_schedule: TimerSchedule) -> HandlerBPMNEventOutcome:
            """Trigger completion actions when timer expires."""
            # Find associated end event or activity
            # Implementation details from process_executor.py needed
            return HandlerBPMNEventOutcome(handled=True, wait_required=False)

        # Add timer schedule initialization if needed in _osdm_to_handler_event

    def _osdm_to_handler_event(self, event: OsdmEvent) -> HandlerBPMNEvent:
        event_definitions = getattr(event, "event_definitions", []) or []
        primary_def = event_definitions[0] if event_definitions else None
        def_type = primary_def.type if primary_def else EventDefinitionType.NONE
        timer_schedule = None
        message_name = None
        signal_name = None
        error_code = None
        escalation_code = None
        link_source = None
        link_target = None
        for ed in event_definitions:
            if isinstance(ed, TimerEventDefinition):
                timer_schedule = TimerSchedule(
                    time_date=getattr(ed, "time_date", None),
                    time_duration=getattr(ed, "time_duration", None),
                    time_cycle=getattr(ed, "time_cycle", None),
                )
            elif isinstance(ed, MessageEventDefinition):
                msg_ref = getattr(ed, "message_ref", None)
                message_name = msg_ref.name if msg_ref and hasattr(msg_ref, "name") else str(msg_ref) if msg_ref else None
            elif isinstance(ed, SignalEventDefinition):
                sig_ref = getattr(ed, "signal_ref", None)
                signal_name = sig_ref.name if sig_ref and hasattr(sig_ref, "name") else str(sig_ref) if sig_ref else None
            elif isinstance(ed, ErrorEventDefinition):
                err_ref = getattr(ed, "error_ref", None)
                error_code = err_ref.error_code if err_ref and hasattr(err_ref, "error_code") else str(err_ref) if err_ref else None
            elif isinstance(ed, EscalationEventDefinition):
                esc_ref = getattr(ed, "escalation_ref", None)
                escalation_code = esc_ref.escalation_code if esc_ref and hasattr(esc_ref, "escalation_code") else str(esc_ref) if esc_ref else None
            elif isinstance(ed, LinkEventDefinition):
                link_source = getattr(ed, "source", None)
                link_target = getattr(ed, "target", None)
        is_parallel = getattr(event, "parallel_multiple", False)
        multiple_defs = [ed.type.value if hasattr(ed, "type") else str(ed) for ed in event_definitions]
        return HandlerBPMNEvent(
            event_id=event.id,
            event_type=self._resolve_osdm_event_type(event).value,
            event_definition_type=def_type.value if hasattr(def_type, "value") else str(def_type),
            interrupting=getattr(event, "cancel_activity", True) if isinstance(event, BoundaryEvent) else True,
            timer_schedule=timer_schedule,
            message_name=message_name,
            signal_name=signal_name,
            error_code=error_code,
            escalation_code=escalation_code,
            link_source=str(link_source) if link_source else None,
            link_target=str(link_target) if link_target else None,
            multiple_event_definitions=multiple_defs,
            is_parallel_multiple=is_parallel,
        )

    def _resolve_osdm_event_type(self, event: OsdmEvent) -> EventType:
        if isinstance(event, StartEvent):
            return EventType.START
        elif isinstance(event, EndEvent):
            return EventType.END
        elif isinstance(event, ImplicitThrowEvent):
            return EventType.IMPLICIT_THROW
        elif isinstance(event, IntermediateCatchEvent):
            return EventType.INTERMEDIATE_CATCH
        elif isinstance(event, IntermediateThrowEvent):
            return EventType.INTERMEDIATE_THROW
        elif isinstance(event, BoundaryEvent):
            return EventType.BOUNDARY
        return EventType.START

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
        return HandlerBPMNEventOutcome(handled=all_handled, wait_required=any_wait, wait_kind=wait_kind, wait_name=wait_name)

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
        if event_type == EventType.START:
            return self.handle_start(event)
        elif event_type == EventType.END:
            return self.handle_end(event)
        elif event_type == EventType.IMPLICIT_THROW:
            return self.handle_implicit_throw(event)
        elif event_type == EventType.INTERMEDIATE_CATCH:
            return self.handle_intermediate_catch(event)
        elif event_type == EventType.INTERMEDIATE_THROW:
            return self.handle_intermediate_throw(event)
        elif event_type == EventType.BOUNDARY:
            return self.handle_boundary(event)
        return HandlerBPMNEventOutcome(handled=True)

    def handle_implicit_throw(self, event: HandlerBPMNEvent) -> HandlerBPMNEventOutcome:
        """Handle ImplicitThrowEvent — intermediate events inside sub-processes
        that are neither start nor end. Dispatches to the appropriate handler
        based on event definition type (message, signal, escalation, etc.)."""
        def_type = event.event_definition_type
        if def_type == EventDefinitionType.LINK:
            return HandlerBPMNEventOutcome(handled=True, link_navigation=event.link_source)
        elif def_type == EventDefinitionType.ESCALATION:
            return HandlerBPMNEventOutcome(handled=True, escalation_raised=event.escalation_code)
        elif def_type == EventDefinitionType.COMPENSATION:
            return HandlerBPMNEventOutcome(handled=True, compensation_triggered=event.payload.get("activity_ref"))
        return self.handle_intermediate_throw(event)

    def start(self, event: HandlerBPMNEvent) -> HandlerBPMNEventOutcome:
        return self.handle_start(event)

    def end(self, event: HandlerBPMNEvent) -> HandlerBPMNEventOutcome:
        return self.handle_end(event)

    def signal(self, event: HandlerBPMNEvent) -> HandlerBPMNEventOutcome:
        if event.event_type == EventType.INTERMEDIATE_THROW:
            return self.handle_intermediate_throw(event)
        return self.handle_intermediate_catch(event)

    def timer(self, event: HandlerBPMNEvent) -> HandlerBPMNEventOutcome:
        return self.handle_intermediate_catch(event)

    def error(self, event: HandlerBPMNEvent) -> HandlerBPMNEventOutcome:
        if event.event_type == EventType.END:
            return self.handle_end(event)
        elif event.event_type == EventType.BOUNDARY:
            return self.handle_boundary(event)
        return self.handle_intermediate_catch(event)

    def cancellation(self, event: HandlerBPMNEvent) -> HandlerBPMNEventOutcome:
        return HandlerBPMNEventOutcome(handled=True)

    def termination(self, event: HandlerBPMNEvent) -> HandlerBPMNEventOutcome:
        return HandlerBPMNEventOutcome(handled=True, terminate_all=True)
