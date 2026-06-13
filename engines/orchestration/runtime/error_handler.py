"""Error capture, recovery, and cross-layer error event generation.

Handles errors from all layers (bus, communication, storage) and generates
OSDM-standard ErrorEvent instances that the orchestration engine can process.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from collections.abc import Callable

from engines.orchestration.models.osdm_models import (
    ErrorEventDefinition,
    Error,
    EscalationEventDefinition,
    Escalation,
)


logger = logging.getLogger(__name__)


class ErrorLevel(Enum):
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorSource(Enum):
    """Origin layer of the error."""
    ORCHESTRATION = "orchestration"
    BUS = "bus"
    COMMUNICATION = "communication"
    STORAGE = "storage"
    EXTERNAL = "external"


class ExecutionError(RuntimeError):
    """Domain error for execution engine failures."""


@dataclass
class ErrorRecord:
    scope: str
    error: str
    level: ErrorLevel
    source: ErrorSource = ErrorSource.ORCHESTRATION
    metadata: dict[str, Any] = field(default_factory=dict)
    osdm_error_event: dict[str, Any] | None = None


@dataclass
class ErrorRecoveryContext:
    scope: str
    retries: int = 0
    max_retries: int = 3


@dataclass
class CrossLayerErrorEvent:
    """Represents an error from another layer translated to an OSDM error event."""
    error_code: str
    error_message: str
    source: ErrorSource
    source_detail: str
    escalation_code: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)

    def to_osdm_error_event_definition(self) -> dict[str, Any]:
        """Convert to OSDM ErrorEventDefinition-compatible dict."""
        result: dict[str, Any] = {
            "error_code": self.error_code,
            "error_message": self.error_message,
            "source": self.source.value,
            "source_detail": self.source_detail,
        }
        if self.escalation_code:
            result["escalation_code"] = self.escalation_code
        if self.payload:
            result["payload"] = self.payload
        return result

    def to_osdm_escalation_event_definition(self) -> dict[str, Any] | None:
        """Convert to OSDM EscalationEventDefinition if escalation applies."""
        if not self.escalation_code:
            return None
        return {
            "escalation_code": self.escalation_code,
            "error_code": self.error_code,
            "source": self.source.value,
        }


class ErrorResolver:
    """Apply recover/retry strategy to a function invocation."""

    def __init__(
        self,
        *,
        default_handler: Callable[[ExecutionError, ErrorRecoveryContext], None] | None = None,
    ) -> None:
        self._default_handler = default_handler
        self._errors: list[ErrorRecord] = []

    def record(self, scope: str, exc: Exception, *, level: ErrorLevel = ErrorLevel.ERROR, source: ErrorSource = ErrorSource.ORCHESTRATION) -> None:
        self._errors.append(
            ErrorRecord(
                scope=scope,
                error=str(exc),
                level=level,
                source=source,
                metadata={"type": type(exc).__name__},
            )
        )

    def handle(self, exc: Exception, context: ErrorRecoveryContext) -> None:
        if isinstance(exc, ExecutionError):
            self.record(context.scope, exc, level=ErrorLevel.ERROR)
        else:
            self.record(context.scope, exc, level=ErrorLevel.CRITICAL)

        if self._default_handler is not None:
            self._default_handler(ExecutionError(str(exc)), context)

    def errors(self) -> list[ErrorRecord]:
        return list(self._errors)

    def clear(self) -> None:
        self._errors.clear()


class CrossLayerErrorHandler:
    """Catches errors from bus, communication, and storage layers
    and translates them into OSDM error events for the orchestration engine."""

    def __init__(self, event_bus: Any | None = None) -> None:
        self._event_bus = event_bus
        self._error_counts: dict[str, int] = {}

    def set_event_bus(self, event_bus: Any) -> None:
        self._event_bus = event_bus

    def handle_bus_error(
        self,
        error_code: str,
        error_message: str,
        detail: str = "",
        escalation_code: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> CrossLayerErrorEvent:
        """Handle an error from engines/communication/buses layer."""
        event = CrossLayerErrorEvent(
            error_code=error_code,
            error_message=error_message,
            source=ErrorSource.BUS,
            source_detail=detail,
            escalation_code=escalation_code,
            payload=payload or {},
        )
        self._track_error(error_code)
        self._publish_error_event(event)
        logger.error("Bus error [%s]: %s — %s", error_code, error_message, detail)
        return event

    def handle_communication_error(
        self,
        error_code: str,
        error_message: str,
        detail: str = "",
        escalation_code: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> CrossLayerErrorEvent:
        """Handle an error from engines/communication layer."""
        event = CrossLayerErrorEvent(
            error_code=error_code,
            error_message=error_message,
            source=ErrorSource.COMMUNICATION,
            source_detail=detail,
            escalation_code=escalation_code,
            payload=payload or {},
        )
        self._track_error(error_code)
        self._publish_error_event(event)
        logger.error("Communication error [%s]: %s — %s", error_code, error_message, detail)
        return event

    def handle_storage_error(
        self,
        error_code: str,
        error_message: str,
        detail: str = "",
        escalation_code: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> CrossLayerErrorEvent:
        """Handle an error from engines/storage layer."""
        event = CrossLayerErrorEvent(
            error_code=error_code,
            error_message=error_message,
            source=ErrorSource.STORAGE,
            source_detail=detail,
            escalation_code=escalation_code,
            payload=payload or {},
        )
        self._track_error(error_code)
        self._publish_error_event(event)
        logger.error("Storage error [%s]: %s — %s", error_code, error_message, detail)
        return event

    def publish_error_events(self, events: list[CrossLayerErrorEvent]) -> None:
        """Publish multiple cross-layer error events to the orchestration event bus."""
        for event in events:
            self._publish_error_event(event)

    def _publish_error_event(self, event: CrossLayerErrorEvent) -> None:
        if self._event_bus is None:
            return
        try:
            error_def = event.to_osdm_error_event_definition()
            self._event_bus.publish(
                type="error",
                data={
                    "event_type": "error",
                    "source": event.source.value,
                    "error_definition": error_def,
                },
            )
            escalation_def = event.to_osdm_escalation_event_definition()
            if escalation_def:
                self._event_bus.publish(
                    type="escalation",
                    data={
                        "event_type": "escalation",
                        "source": event.source.value,
                        "escalation_definition": escalation_def,
                    },
                )
        except Exception as exc:
            logger.error("Failed to publish error event to bus: %s", exc)

    def _track_error(self, error_code: str) -> None:
        self._error_counts[error_code] = self._error_counts.get(error_code, 0) + 1

    def get_error_counts(self) -> dict[str, int]:
        return dict(self._error_counts)
