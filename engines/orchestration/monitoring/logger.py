"""Structured logging helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class StructuredEvent:
    event: str
    level: str
    message: str
    tags: dict[str, str]
    timestamp: datetime


class StructuredLogger:
    """Small helper to keep logs consistent with event payloads."""

    def emit(self, event: str, message: str, *, level: str = "info", tags: dict[str, str] | None = None) -> StructuredEvent:
        return StructuredEvent(
            event=event,
            level=level,
            message=message,
            tags=dict(tags or {}),
            timestamp=datetime.utcnow(),
        )
