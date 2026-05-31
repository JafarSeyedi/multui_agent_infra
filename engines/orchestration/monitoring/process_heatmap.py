"""Process heatmap and bottleneck detection per Camunda Optimize/CIB ins7ght patterns."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from .metrics_collector import ProcessMetrics, ActivityMetrics


logger = logging.getLogger(__name__)


@dataclass
class HeatmapDataPoint:
    element_id: str = ""
    element_name: str | None = None
    element_type: str = ""
    instance_count: int = 0
    average_duration_ms: float = 0.0
    heat_score: float = 0.0


@dataclass
class KpiMetric:
    name: str = ""
    value: float = 0.0
    unit: str = ""
    threshold_warning: float | None = None
    threshold_critical: float | None = None

    @property
    def status(self) -> str:
        if self.threshold_critical is not None and self.value >= self.threshold_critical:
            return "critical"
        if self.threshold_warning is not None and self.value >= self.threshold_warning:
            return "warning"
        return "ok"


class ProcessHeatmap:
    """Generates process activity heatmaps."""

    def __init__(self) -> None:
        self._data: dict[str, list[HeatmapDataPoint]] = {}

    def build_heatmap(
        self,
        definition_key: str,
        process_metrics: ProcessMetrics,
    ) -> list[HeatmapDataPoint]:
        points: list[HeatmapDataPoint] = []
        max_count = 1
        for am in process_metrics.activity_metrics.values():
            if am.execution_count > max_count:
                max_count = am.execution_count

        for am in process_metrics.activity_metrics.values():
            heat_score = am.execution_count / max_count if max_count > 0 else 0
            points.append(HeatmapDataPoint(
                element_id=am.activity_id,
                element_name=am.activity_name,
                element_type=am.activity_type,
                instance_count=am.execution_count,
                average_duration_ms=am.average_duration_ms,
                heat_score=heat_score,
            ))

        points.sort(key=lambda p: p.heat_score, reverse=True)
        self._data[definition_key] = points
        return points

    def get_hotspots(self, definition_key: str, top_n: int = 5) -> list[HeatmapDataPoint]:
        points = self._data.get(definition_key, [])
        return points[:top_n]

    def get_coldspots(self, definition_key: str, bottom_n: int = 5) -> list[HeatmapDataPoint]:
        points = self._data.get(definition_key, [])
        return list(reversed(points[-bottom_n:]))


class BottleneckDetection:
    """Detects process bottlenecks from metrics."""

    @staticmethod
    def detect_bottlenecks(
        process_metrics: ProcessMetrics,
        min_failure_rate: float = 0.1,
        min_avg_duration_ms: float = 5000,
    ) -> list[dict[str, Any]]:
        bottlenecks = []
        for am in process_metrics.activity_metrics.values():
            reasons = []
            if am.failure_rate >= min_failure_rate:
                reasons.append(f"high_failure_rate:{am.failure_rate:.2%}")
            if am.average_duration_ms >= min_avg_duration_ms:
                reasons.append(f"high_duration:{am.average_duration_ms:.0f}ms")
            if am.max_duration_ms > am.average_duration_ms * 5 and am.execution_count > 5:
                reasons.append(f"duration_variance:max={am.max_duration_ms:.0f}ms,avg={am.average_duration_ms:.0f}ms")
            if reasons:
                bottlenecks.append({
                    "activity_id": am.activity_id,
                    "activity_name": am.activity_name,
                    "activity_type": am.activity_type,
                    "reasons": reasons,
                    "failure_rate": am.failure_rate,
                    "average_duration_ms": am.average_duration_ms,
                    "max_duration_ms": am.max_duration_ms,
                    "execution_count": am.execution_count,
                })
        bottlenecks.sort(key=lambda b: b["failure_rate"], reverse=True)
        return bottlenecks


class KpiTracker:
    """Tracks key performance indicators."""

    def __init__(self) -> None:
        self._metrics: dict[str, KpiMetric] = {}
        self._history: dict[str, list[tuple[str, float]]] = {}

    def set_kpi(self, name: str, value: float, unit: str = "", warning: float | None = None, critical: float | None = None) -> None:
        self._metrics[name] = KpiMetric(name=name, value=value, unit=unit, threshold_warning=warning, threshold_critical=critical)
        if name not in self._history:
            self._history[name] = []
        self._history[name].append((__import__("datetime").datetime.utcnow().isoformat(), value))

    def get_kpi(self, name: str) -> KpiMetric | None:
        return self._metrics.get(name)

    def get_all_kpis(self) -> list[KpiMetric]:
        return list(self._metrics.values())

    def get_history(self, name: str) -> list[tuple[str, float]]:
        return list(self._history.get(name, []))

    def compute_process_kpis(self, process_metrics: ProcessMetrics) -> list[KpiMetric]:
        kpis = []
        total = process_metrics.total_instances
        if total > 0:
            kpis.append(KpiMetric(
                name="completion_rate",
                value=process_metrics.completed_instances / total * 100,
                unit="%",
                warning=80, critical=50,
            ))
            kpis.append(KpiMetric(
                name="failure_rate",
                value=process_metrics.failed_instances / total * 100,
                unit="%",
                warning=10, critical=30,
            ))
            kpis.append(KpiMetric(
                name="avg_completion_time_seconds",
                value=process_metrics.average_completion_time_ms / 1000,
                unit="s",
            ))
        for kpi in kpis:
            self.set_kpi(kpi.name, kpi.value, kpi.unit)
        return kpis
