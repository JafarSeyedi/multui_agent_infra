import pytest
from datetime import datetime, timedelta
from engines.orchestration.bam.slas.sla_tracker import SlaTracker
from engines.orchestration.models.bam_models import (
    SlaDefinition, BusinessMetric, MetricValue,
)


@pytest.mark.asyncio
async def test_sla_tracker_compliance():
    tracker = SlaTracker()
    sla = SlaDefinition(
        sla_id="s1", name="Gold SLA", condition="value < 5000", target_value=0.95,
    )
    tracker.register(sla)

    for v in [1000, 2000, 3000, 4000, 5000, 6000]:
        tracker.record_evaluation("s1", v)

    report = tracker.get_report("s1")
    assert report is not None
    assert report.sla_id == "s1"
    assert report.total_evaluations == 6
    assert report.breach_count == 1


@pytest.mark.asyncio
async def test_sla_tracker_no_breaches():
    tracker = SlaTracker()
    sla = SlaDefinition(
        sla_id="s1", name="Gold SLA", condition="value < 5000", target_value=1.0,
    )
    tracker.register(sla)
    for v in [1000, 2000, 3000]:
        tracker.record_evaluation("s1", v)
    report = tracker.get_report("s1")
    assert report is not None
    assert report.compliance_rate == 1.0
