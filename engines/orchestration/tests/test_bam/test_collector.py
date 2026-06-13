import pytest
from datetime import datetime
from engines.orchestration.bam.collector.metric_collector import MetricCollector
from engines.orchestration.bam.collector.kpi_evaluator import KpiEvaluator
from engines.orchestration.models.bam_models import (
    BusinessMetric, KPI, MetricCategory, MetricValue,
)


@pytest.mark.asyncio
async def test_metric_collector_record():
    mc = MetricCollector()
    mc.record("cpu", 42.5, {"host": "web-1"})
    mc.record("cpu", 43.0, {"host": "web-1"})
    values = mc.get_history("cpu")
    assert len(values) == 2
    assert values[0].value == 42.5
    assert values[1].value == 43.0


@pytest.mark.asyncio
async def test_metric_collector_average():
    mc = MetricCollector()
    mc.record("cpu", 10.0)
    mc.record("cpu", 20.0)
    mc.record("cpu", 30.0)
    avg = mc.average("cpu")
    assert avg == 20.0


@pytest.mark.asyncio
async def test_metric_collector_stats():
    mc = MetricCollector()
    for v in [10.0, 20.0, 30.0, 40.0, 50.0]:
        mc.record("latency", v)
    stats = mc.stats("latency")
    assert stats["count"] == 5
    assert stats["avg"] == 30.0
    assert stats["min"] == 10.0
    assert stats["max"] == 50.0


@pytest.mark.asyncio
async def test_kpi_evaluator_track():
    mc = MetricCollector()
    kpi = KPI(kpi_id="sla", name="SLA", metric_ref="cycle",
               target_value=95.0, threshold_warning=90.0, threshold_critical=80.0)

    evaluator = KpiEvaluator(mc)
    mc.record("cycle", 100.0)
    result = evaluator.evaluate(kpi)
    assert result.kpi_id == "sla"
    assert result.current_value == 100.0
    assert result.target_value == 95.0


def test_kpi_evaluator_status_on_track():
    mc = MetricCollector()
    kpi = KPI(kpi_id="k1", name="K1", metric_ref="m1",
               target_value=90.0, threshold_warning=80.0, threshold_critical=60.0)
    evaluator = KpiEvaluator(mc)
    mc.record("m1", 95.0)
    result = evaluator.evaluate(kpi)
    assert result.status.value == "on_track"


def test_kpi_evaluator_status_warning():
    mc = MetricCollector()
    kpi = KPI(kpi_id="k1", name="K1", metric_ref="m1",
               target_value=90.0, threshold_warning=80.0, threshold_critical=60.0)
    evaluator = KpiEvaluator(mc)
    mc.record("m1", 85.0)
    result = evaluator.evaluate(kpi)
    assert result.status.value == "warning"


def test_kpi_evaluator_status_critical():
    mc = MetricCollector()
    kpi = KPI(kpi_id="k1", name="K1", metric_ref="m1",
               target_value=90.0, threshold_warning=80.0, threshold_critical=60.0)
    evaluator = KpiEvaluator(mc)
    mc.record("m1", 50.0)
    result = evaluator.evaluate(kpi)
    assert result.status.value == "critical"
