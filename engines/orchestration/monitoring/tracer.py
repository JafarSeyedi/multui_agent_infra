"""Simple execution tracing context objects."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from collections.abc import Iterator
from uuid import uuid4


@dataclass(frozen=True)
class Span:
    span_id: str
    name: str
    trace_id: str
    start_time: datetime
    end_time: datetime | None = None
    tags: dict[str, Any] | None = None


@dataclass(frozen=True)
class TraceContext:
    trace_id: str
    span_id: str


class Tracer:
    """Trace span helper with lightweight nesting."""

    def __init__(self) -> None:
        self._stack: list[Span] = []

    @contextmanager
    def start_span(self, name: str, *, trace_id: str | None = None, tags: dict[str, Any] | None = None) -> Iterator[Span]:
        active_trace_id = trace_id or (self._stack[-1].trace_id if self._stack else uuid4().hex)
        span = Span(
            span_id=uuid4().hex,
            name=name,
            trace_id=active_trace_id,
            start_time=datetime.utcnow(),
            tags=dict(tags or {}),
        )
        self._stack.append(span)
        try:
            yield span
        finally:
            completed = Span(
                span_id=span.span_id,
                name=span.name,
                trace_id=span.trace_id,
                start_time=span.start_time,
                end_time=datetime.utcnow(),
                tags=span.tags,
            )
            self._stack.pop()
            # Replace reference with completed span to capture end time.
            self._emit(completed)

    def _emit(self, span: Span) -> None:
        # Hook for metrics/logging integration.
        _ = span

    def current_context(self) -> TraceContext | None:
        if not self._stack:
            return None
        top = self._stack[-1]
        return TraceContext(trace_id=top.trace_id, span_id=top.span_id)
