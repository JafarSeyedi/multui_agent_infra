"""Decorator/context wrappers to measure execution duration."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from time import perf_counter
from collections.abc import Iterator

from .metrics_collector import MetricsCollector


@dataclass(frozen=True)
class TrackContext:
    name: str
    elapsed_ms: float


class PerformanceMonitor:
    """Collects timing for functions and arbitrary code blocks."""

    def __init__(self, collector: MetricsCollector | None = None) -> None:
        self.collector = collector or MetricsCollector()

    @contextmanager
    def track(self, name: str) -> Iterator[TrackContext]:
        start = perf_counter()
        try:
            yield TrackContext(name=name, elapsed_ms=0.0)
        finally:
            elapsed_ms = (perf_counter() - start) * 1000
            self.collector.observe(name, elapsed_ms)

    def summary(self) -> dict[str, object]:
        return self.collector.snapshot()
