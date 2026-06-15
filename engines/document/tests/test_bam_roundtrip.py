import pytest
from engines.orchestration.bam.models.bam_models import (
    BusinessMetric, KPI, AlertRule, AlertSeverity, MetricCategory,
    SlaDefinition, Dashboard, DashboardWidget,
    MonitoringAgentDefinition, MonitoringDashboardDocument,
)
from engines.orchestration.bam.parsers.bam_json_parser import BamJsonParser
from engines.orchestration.bam.writers.bam_json_writer import BamJsonWriter
from engines.orchestration.bam.parsers.bam_yaml_parser import BamYamlParser
from engines.orchestration.bam.writers.bam_yaml_writer import BamYamlWriter


def _make_full_doc() -> MonitoringDashboardDocument:
    doc = MonitoringDashboardDocument(
        title="Production Monitoring",
        document_id="prod-1",
    )
    doc.metrics["cpu"] = BusinessMetric(
        metric_id="cpu", name="CPU Usage", unit="%",
        category=MetricCategory.OPERATIONAL,
    )
    doc.metrics["cycle"] = BusinessMetric(
        metric_id="cycle", name="Cycle Time", unit="ms",
        category=MetricCategory.PROCESS,
    )
    doc.kpis["sla"] = KPI(
        kpi_id="sla", name="SLA Compliance", metric_ref="cycle",
        target_value=95.0, threshold_warning=90.0, threshold_critical=80.0,
    )
    doc.slas["gold"] = SlaDefinition(
        sla_id="gold", name="Gold SLA",
        condition="cycle.value < 5000", target_value=0.99,
    )
    doc.alert_rules["high_cpu"] = AlertRule(
        rule_id="high_cpu", name="High CPU Alert",
        condition="cpu.value > 90", severity=AlertSeverity.CRITICAL,
    )
    doc.dashboards["ops"] = Dashboard(
        dashboard_id="ops", name="Operations",
        widgets=[DashboardWidget(
            widget_id="w1", type="gauge", title="CPU",
            data_source="metric:cpu",
        )],
    )
    doc.monitoring_agents["threshold1"] = MonitoringAgentDefinition(
        agent_id="threshold1", name="CPU Threshold Agent",
        input_metrics=["cpu"],
    )
    return doc


@pytest.mark.asyncio
async def test_json_roundtrip():
    original = _make_full_doc()
    writer = BamJsonWriter()
    data = await writer.write(original)

    parser = BamJsonParser()
    parsed = await parser.parse_bytes(data, "prod-1", "prod.bam.json")

    assert parsed.title == original.title
    assert set(parsed.metrics.keys()) == set(original.metrics.keys())
    assert set(parsed.kpis.keys()) == set(original.kpis.keys())
    assert set(parsed.slas.keys()) == set(original.slas.keys())
    assert set(parsed.alert_rules.keys()) == set(original.alert_rules.keys())
    assert set(parsed.dashboards.keys()) == set(original.dashboards.keys())
    assert set(parsed.monitoring_agents.keys()) == set(original.monitoring_agents.keys())


@pytest.mark.asyncio
async def test_yaml_roundtrip():
    original = _make_full_doc()
    writer = BamYamlWriter()
    data = await writer.write(original)

    parser = BamYamlParser()
    parsed = await parser.parse_bytes(data, "prod-1", "prod.bam.yaml")

    assert parsed.title == original.title
    assert set(parsed.metrics.keys()) == set(original.metrics.keys())
