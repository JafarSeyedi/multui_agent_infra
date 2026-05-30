"""Lightweight metrics collector with counters/gauges/histogram buckets."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from threading import Lock
from time import perf_counter


@dataclass(frozen=True)
class MetricSample:
    name: str
    value: float
    tags: dict[str, str]


@dataclass(frozen=True)
class HistogramBucket:
    label: str
    count: int


class MetricsCollector:
    """Thread-safe counters and timing metrics suitable for runtime polling."""

    def __init__(self) -> None:
        self._counters: Counter[str] = Counter()
        self._gauges: defaultdict[str, float] = defaultdict(float)
        self._durations_ms: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def inc(self, name: str, amount: float = 1.0, tags: dict[str, str] | None = None) -> None:
        key = self._key(name, tags)
        with self._lock:
            self._counters[key] += amount

    def gauge(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        key = self._key(name, tags)
        with self._lock:
            self._gauges[key] = value

    def observe(self, name: str, value_ms: float, tags: dict[str, str] | None = None) -> None:
        key = self._key(name, tags)
        with self._lock:
            self._durations_ms[key].append(value_ms)

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "durations": {
                    k: {
                        "count": len(values),
                        "avg_ms": (sum(values) / len(values)) if values else 0,
                        "p95_ms": self._percentile(values, 95),
                    }
                    for k, values in self._durations_ms.items()
                },
            }

    def clear(self) -> None:
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._durations_ms.clear()

    def _key(self, name: str, tags: dict[str, str] | None) -> str:
        if not tags:
            return name
        suffix = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}{{{suffix}}}"

    @staticmethod
    def _percentile(values: list[float], pct: int) -> float:
        if not values:
            return 0.0
        ordered = sorted(values)
        index = max(int((pct / 100) * (len(ordered) - 1)), 0)
        return ordered[index]

    def timed(self, name: str, tags: dict[str, str] | None = None):
        start = perf_counter()

        class _Timed:
            def __enter__(self_nonlocal) -> None:
                pass

            def __exit__(self_nonlocal, exc_type, exc, tb) -> None:
                duration_ms = (perf_counter() - start) * 1000
                self.observe(name, duration_ms, tags=tags)
                return None

        return _Timed()
