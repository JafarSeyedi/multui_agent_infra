from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

from engines.document.models.bam_models import MetricValue


class MetricRepository:
    def __init__(self) -> None:
        self._store_impl: list[MetricValue] = []

    async def store(self, mv: MetricValue) -> None:
        self._store_impl.append(mv)

    def _store(self, mv: MetricValue) -> None:
        self._store_impl.append(mv)

    async def query(self, metric_id: str) -> list[MetricValue]:
        return [v for v in self._store_impl if v.metric_id == metric_id]

    async def query_range(
        self,
        metric_id: str,
        start: datetime,
        end: datetime,
    ) -> list[MetricValue]:
        return [
            v for v in self._store_impl
            if v.metric_id == metric_id and start <= v.timestamp <= end
        ]

    async def latest(self, metric_id: str) -> MetricValue | None:
        matches = [v for v in self._store_impl if v.metric_id == metric_id]
        return max(matches, key=lambda v: v.timestamp) if matches else None

    async def clear(self) -> None:
        self._store_impl.clear()
