from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from engines.document.models.bam_models import (
    MetricValue, SlaComplianceReport, SlaDefinition,
)


class SlaTracker:
    def __init__(self) -> None:
        self._slas: dict[str, SlaDefinition] = {}
        self._evaluations: dict[str, list[float]] = {}

    def register(self, sla: SlaDefinition) -> None:
        self._slas[sla.sla_id] = sla
        self._evaluations.setdefault(sla.sla_id, [])

    def unregister(self, sla_id: str) -> None:
        self._slas.pop(sla_id, None)
        self._evaluations.pop(sla_id, None)

    def record_evaluation(self, sla_id: str, value: float) -> None:
        if sla_id in self._evaluations:
            self._evaluations[sla_id].append(value)

    def get_report(self, sla_id: str) -> SlaComplianceReport | None:
        sla = self._slas.get(sla_id)
        if sla is None:
            return None
        values = self._evaluations.get(sla_id, [])
        if not values:
            return SlaComplianceReport(
                sla_id=sla_id,
                name=sla.name,
                compliance_rate=1.0,
                breach_count=0,
                total_evaluations=0,
                period_start=datetime.utcnow() - timedelta(days=30),
                period_end=datetime.utcnow(),
            )
        threshold = self._parse_condition_threshold(sla.condition)
        breaches = sum(1 for v in values if v > threshold) if threshold is not None else 0
        total = len(values)
        rate = (total - breaches) / total if total > 0 else 1.0
        return SlaComplianceReport(
            sla_id=sla_id,
            name=sla.name,
            compliance_rate=rate,
            breach_count=breaches,
            total_evaluations=total,
            period_start=datetime.utcnow() - timedelta(days=30),
            period_end=datetime.utcnow(),
        )

    def get_all_reports(self) -> list[SlaComplianceReport]:
        return [r for sid in self._slas if (r := self.get_report(sid)) is not None]

    def _parse_condition_threshold(self, condition: str) -> float | None:
        if " < " in condition:
            _, val = condition.rsplit(" < ", 1)
            try:
                return float(val.strip())
            except ValueError:
                return None
        if " > " in condition:
            _, val = condition.rsplit(" > ", 1)
            try:
                return float(val.strip())
            except ValueError:
                return None
        if " <= " in condition:
            _, val = condition.rsplit(" <= ", 1)
            try:
                return float(val.strip())
            except ValueError:
                return None
        if " >= " in condition:
            _, val = condition.rsplit(" >= ", 1)
            try:
                return float(val.strip())
            except ValueError:
                return None
        return None
