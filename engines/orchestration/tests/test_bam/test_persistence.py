import pytest
from datetime import datetime
from engines.orchestration.bam.persistence.metric_repository import MetricRepository
from engines.orchestration.bam.persistence.alert_repository import AlertRepository
from engines.orchestration.bam.models.bam_models import (
    MetricValue, AlertNotification, AlertSeverity, AlertState,
)


@pytest.mark.asyncio
async def test_metric_repository_store_and_query():
    repo = MetricRepository()
    mv = MetricValue(timestamp=datetime.utcnow(), metric_id="cpu", value=42.5)
    await repo.store(mv)
    results = await repo.query("cpu")
    assert len(results) == 1
    assert results[0].value == 42.5


@pytest.mark.asyncio
async def test_metric_repository_query_empty():
    repo = MetricRepository()
    results = await repo.query("nonexistent")
    assert results == []


@pytest.mark.asyncio
async def test_metric_repository_range():
    repo = MetricRepository()
    from datetime import timedelta
    now = datetime.utcnow()
    repo._store(MetricValue(timestamp=now - timedelta(hours=2), metric_id="cpu", value=10.0))
    repo._store(MetricValue(timestamp=now - timedelta(hours=1), metric_id="cpu", value=20.0))
    repo._store(MetricValue(timestamp=now, metric_id="cpu", value=30.0))
    results = await repo.query_range("cpu", now - timedelta(hours=1.5), now)
    assert len(results) == 2


@pytest.mark.asyncio
async def test_alert_repository_store_and_list():
    repo = AlertRepository()
    now = datetime.utcnow()
    alert = AlertNotification(
        alert_id="a1", rule_id="r1", name="Alert",
        severity=AlertSeverity.WARNING, state=AlertState.ACTIVE,
        message="test", triggered_at=now,
    )
    await repo.store(alert)
    alerts = await repo.list_active()
    assert len(alerts) == 1
    assert alerts[0].alert_id == "a1"


@pytest.mark.asyncio
async def test_alert_repository_acknowledge():
    repo = AlertRepository()
    now = datetime.utcnow()
    alert = AlertNotification(
        alert_id="a1", rule_id="r1", name="Alert",
        severity=AlertSeverity.WARNING, state=AlertState.ACTIVE,
        message="test", triggered_at=now,
    )
    await repo.store(alert)
    await repo.acknowledge("a1")
    alerts = await repo.list_active()
    assert len(alerts) == 1
    assert alerts[0].state == AlertState.ACKNOWLEDGED
