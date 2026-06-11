from __future__ import annotations

from datetime import datetime
from typing import Any

from engines.document.models.bam_models import AlertNotification, AlertState


class AlertRepository:
    def __init__(self) -> None:
        self._alerts: dict[str, AlertNotification] = {}

    async def store(self, alert: AlertNotification) -> None:
        self._alerts[alert.alert_id] = alert

    async def get(self, alert_id: str) -> AlertNotification | None:
        return self._alerts.get(alert_id)

    async def list_active(self) -> list[AlertNotification]:
        return [
            a for a in self._alerts.values()
            if a.state in (AlertState.ACTIVE, AlertState.ACKNOWLEDGED)
        ]

    async def list_by_rule(self, rule_id: str) -> list[AlertNotification]:
        return [a for a in self._alerts.values() if a.rule_id == rule_id]

    async def acknowledge(self, alert_id: str) -> None:
        alert = self._alerts.get(alert_id)
        if alert is not None:
            alert.state = AlertState.ACKNOWLEDGED
            alert.acknowledged_at = datetime.utcnow()

    async def resolve(self, alert_id: str) -> None:
        alert = self._alerts.get(alert_id)
        if alert is not None:
            alert.state = AlertState.RESOLVED
            alert.resolved_at = datetime.utcnow()

    async def count_by_severity(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for a in self._alerts.values():
            counts[a.severity.value] = counts.get(a.severity.value, 0) + 1
        return counts
