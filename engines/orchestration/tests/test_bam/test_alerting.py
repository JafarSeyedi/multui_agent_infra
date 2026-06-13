import pytest
from datetime import datetime, timedelta
from engines.orchestration.bam.alerting.alert_manager import AlertManager
from engines.orchestration.models.bam_models import (
    AlertRule, AlertSeverity, AlertNotification, AlertState,
)


@pytest.mark.asyncio
async def test_alert_manager_evaluate():
    mgr = AlertManager()
    rule = AlertRule(
        rule_id="r1", name="CPU Alert",
        condition="value > 90", severity=AlertSeverity.CRITICAL,
    )
    notifications = mgr.evaluate(rule, 95.0)
    assert len(notifications) == 1
    assert notifications[0].rule_id == "r1"
    assert notifications[0].severity == AlertSeverity.CRITICAL
    assert notifications[0].metric_value == 95.0


@pytest.mark.asyncio
async def test_alert_manager_cooldown():
    mgr = AlertManager()
    rule = AlertRule(
        rule_id="r1", name="CPU Alert",
        condition="value > 90", severity=AlertSeverity.WARNING,
        cooldown_seconds=300,
    )
    n1 = mgr.evaluate(rule, 95.0)
    assert len(n1) == 1

    n2 = mgr.evaluate(rule, 96.0)
    assert len(n2) == 0


@pytest.mark.asyncio
async def test_alert_manager_acknowledge():
    mgr = AlertManager()
    rule = AlertRule(
        rule_id="r1", name="CPU Alert",
        condition="value > 90", severity=AlertSeverity.WARNING,
    )
    notifications = mgr.evaluate(rule, 95.0)
    assert len(notifications) == 1
    n = notifications[0]
    assert n.state == AlertState.ACTIVE

    mgr.acknowledge(n.alert_id)
    assert mgr._alerts[n.alert_id].state == AlertState.ACKNOWLEDGED


def test_alert_manager_get_active():
    mgr = AlertManager()
    rule = AlertRule(
        rule_id="r1", name="CPU Alert",
        condition="value > 90", severity=AlertSeverity.WARNING,
    )
    mgr.evaluate(rule, 95.0)
    active = mgr.get_active()
    assert len(active) == 1
