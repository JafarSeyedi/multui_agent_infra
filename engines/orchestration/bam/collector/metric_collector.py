from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

from engines.document.models.bam_models import MetricValue


class MetricCollector:
    def __init__(self) -> None:
        self._history: dict[str, list[MetricValue]] = defaultdict(list)

    def record(
        self,
        metric_id: str,
        value: float,
        dimensions: dict[str, str] | None = None,
    ) -> None:
        mv = MetricValue(
            timestamp=datetime.utcnow(),
            metric_id=metric_id,
            value=value,
            dimensions=dimensions or {},
        )
        self._history[metric_id].append(mv)

    def get_history(self, metric_id: str) -> list[MetricValue]:
        return list(self._history.get(metric_id, []))

    def average(self, metric_id: str) -> float | None:
        values = self._history.get(metric_id, [])
        if not values:
            return None
        return sum(v.value for v in values) / len(values)

    def stats(self, metric_id: str) -> dict[str, Any]:
        values = self._history.get(metric_id, [])
        if not values:
            return {"count": 0, "avg": 0, "min": 0, "max": 0}
        vals = [v.value for v in values]
        return {
            "count": len(vals),
            "avg": sum(vals) / len(vals),
            "min": min(vals),
            "max": max(vals),
        }

    def clear(self, metric_id: str | None = None) -> None:
        if metric_id:
            self._history.pop(metric_id, None)
        else:
            self._history.clear()
