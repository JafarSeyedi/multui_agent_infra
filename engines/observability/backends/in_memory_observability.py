# engines/observability/backends/in_memory_observability.py
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from ..models.observability_models import MetricPoint, LogEntry, Span
from ..plugin import IMetricsCollector, ILogger, ITracer


class InMemoryMetricsCollector(IMetricsCollector):
    name = "in_memory"

    def __init__(self) -> None:
        self.metrics: list[MetricPoint] = []

    async def increment(self, metric: str, tags: dict[str, str] | None = None, value: float = 1.0) -> None:
        self.metrics.append(MetricPoint(name=metric, value=value, tags=tags or {}))

    async def gauge(self, metric: str, value: float, tags: dict[str, str] | None = None) -> None:
        self.metrics.append(MetricPoint(name=metric, value=value, tags=tags or {}))

    async def histogram(self, metric: str, value: float, tags: dict[str, str] | None = None) -> None:
        self.metrics.append(MetricPoint(name=metric, value=value, tags=tags or {}))


class InMemoryLogger(ILogger):
    name = "in_memory"

    def __init__(self) -> None:
        self.entries: list[LogEntry] = []

    async def log(self, level: str, message: str, context: dict[str, Any] | None = None) -> None:
        self.entries.append(LogEntry(level=level, message=message, context=context or {}))


class InMemoryTracer(ITracer):
    name = "in_memory"

    def __init__(self) -> None:
        self.spans: dict[str, Span] = {}

    async def start_span(self, name: str, parent_id: Optional[str] = None) -> str:
        span_id = str(uuid.uuid4())
        self.spans[span_id] = Span(span_id=span_id, name=name, parent_id=parent_id)
        return span_id

    async def end_span(self, span_id: str) -> None:
        if span_id in self.spans:
            self.spans[span_id].end_time = datetime.now(timezone.utc)
