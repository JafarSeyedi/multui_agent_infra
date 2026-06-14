from __future__ import annotations

from datetime import datetime

from ..models.bam_models import (
    KPI, KpiResult, KpiStatus, TrendDirection,
)

from .metric_collector import MetricCollector


class KpiEvaluator:
    def __init__(self, collector: MetricCollector) -> None:
        self._collector = collector

    def evaluate(self, kpi: KPI) -> KpiResult:
        avg = self._collector.average(kpi.metric_ref) or 0.0
        if avg >= kpi.target_value:
            status = KpiStatus.ON_TRACK
        elif avg >= kpi.threshold_warning:
            status = KpiStatus.WARNING
        else:
            status = KpiStatus.CRITICAL
        return KpiResult(
            kpi_id=kpi.kpi_id,
            name=kpi.name,
            current_value=avg,
            target_value=kpi.target_value,
            status=status,
            trend=TrendDirection.STABLE,
            evaluated_at=datetime.utcnow(),
        )

    def evaluate_batch(self, kpis: list[KPI]) -> list[KpiResult]:
        return [self.evaluate(k) for k in kpis]
