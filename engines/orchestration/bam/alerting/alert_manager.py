from __future__ import annotations

import time
from datetime import datetime
from typing import Any

from engines.document.models.bam_models import (
    AlertNotification, AlertRule, AlertSeverity, AlertState,
)


class AlertManager:
    def __init__(self) -> None:
        self._alerts: dict[str, AlertNotification] = {}
        self._last_fired: dict[str, float] = {}
        self._alert_counter = 0

    def evaluate(self, rule: AlertRule, metric_value: float) -> list[AlertNotification]:
        now = time.time()
        last = self._last_fired.get(rule.rule_id, 0)
        if now - last < rule.cooldown_seconds:
            return []

        self._last_fired[rule.rule_id] = now
        self._alert_counter += 1
        alert = AlertNotification(
            alert_id=f"{rule.rule_id}_{self._alert_counter}",
            rule_id=rule.rule_id,
            name=rule.name,
            severity=rule.severity,
            state=AlertState.ACTIVE,
            message=f"{rule.name} triggered (value={metric_value})",
            triggered_at=datetime.utcnow(),
            metric_value=metric_value,
        )
        self._alerts[alert.alert_id] = alert
        return [alert]

    def acknowledge(self, alert_id: str) -> None:
        alert = self._alerts.get(alert_id)
        if alert is not None:
            alert.state = AlertState.ACKNOWLEDGED
            alert.acknowledged_at = datetime.utcnow()

    def resolve(self, alert_id: str) -> None:
        alert = self._alerts.get(alert_id)
        if alert is not None:
            alert.state = AlertState.RESOLVED
            alert.resolved_at = datetime.utcnow()

    def get_active(self) -> list[AlertNotification]:
        return [
            a for a in self._alerts.values()
            if a.state in (AlertState.ACTIVE, AlertState.ACKNOWLEDGED)
        ]

    def get_by_rule(self, rule_id: str) -> list[AlertNotification]:
        return [a for a in self._alerts.values() if a.rule_id == rule_id]
