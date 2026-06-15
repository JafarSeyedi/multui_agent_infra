from datetime import datetime
from engines.orchestration.bam.models.bam_models import (
    MetricCategory, MetricAggregation, AlertSeverity, AlertState,
    KpiStatus, TrendDirection, MonitoringAgentType,
    BusinessMetric, KPI, SlaDefinition, AlertRule,
    DashboardWidget, Dashboard, MonitoringAgentDefinition,
    MetricValue, KpiResult, SlaComplianceReport,
    AlertNotification, AgentReport,
    MonitoringDashboardDocument,
)
from engines.document.models.standard import DocumentStandard


def test_enums():
    assert MetricCategory.PROCESS.value == "process"
    assert MetricAggregation.AVG.value == "avg"
    assert AlertSeverity.CRITICAL.value == "critical"
    assert AlertState.ACTIVE.value == "active"
    assert KpiStatus.ON_TRACK.value == "on_track"
    assert TrendDirection.IMPROVING.value == "improving"
    assert MonitoringAgentType.THRESHOLD.value == "threshold"


def test_business_metric_defaults():
    m = BusinessMetric(metric_id="m1", name="Test Metric")
    assert m.category == MetricCategory.PROCESS
    assert m.aggregation == MetricAggregation.AVG
    assert m.enabled is True


def test_kpi_defaults():
    k = KPI(kpi_id="k1", name="Test KPI", metric_ref="m1",
              target_value=100.0, threshold_warning=80.0, threshold_critical=50.0)
    assert k.direction == "increase"
    assert k.weight == 1.0
    assert k.time_period == "daily"


def test_sla_definition():
    sla = SlaDefinition(sla_id="s1", name="Test SLA",
                         condition="completion_time < 5000", target_value=0.95)
    assert sla.compliance_period == "monthly"


def test_alert_rule_defaults():
    r = AlertRule(rule_id="r1", name="Test Rule", condition="value > 90")
    assert r.severity == AlertSeverity.WARNING
    assert r.cooldown_seconds == 300


def test_dashboard_widget():
    w = DashboardWidget(widget_id="w1", type="gauge", title="CPU", data_source="metric:1")
    assert w.refresh_interval == 30


def test_dashboard():
    d = Dashboard(dashboard_id="d1", name="Ops")
    assert d.layout == "grid"
    assert d.widgets == []


def test_monitoring_agent_definition():
    a = MonitoringAgentDefinition(agent_id="a1", name="Threshold Agent")
    assert a.agent_type == MonitoringAgentType.THRESHOLD
    assert a.enabled is True


def test_metric_value():
    now = datetime.utcnow()
    mv = MetricValue(timestamp=now, metric_id="m1", value=42.5)
    assert mv.dimensions == {}


def test_kpi_result():
    r = KpiResult(kpi_id="k1", name="Test", current_value=90.0,
                   target_value=100.0, evaluated_at=datetime.utcnow())
    assert r.status == KpiStatus.ON_TRACK
    assert r.trend == TrendDirection.STABLE


def test_sla_compliance_report():
    now = datetime.utcnow()
    r = SlaComplianceReport(sla_id="s1", name="Test", compliance_rate=0.95,
                              breach_count=1, total_evaluations=100,
                              period_start=now, period_end=now)
    assert 0.0 <= r.compliance_rate <= 1.0


def test_alert_notification_defaults():
    now = datetime.utcnow()
    n = AlertNotification(alert_id="a1", rule_id="r1", name="Alert",
                            severity=AlertSeverity.CRITICAL, state=AlertState.ACTIVE,
                            message="test", triggered_at=now)
    assert n.state == AlertState.ACTIVE


def test_agent_report():
    now = datetime.utcnow()
    r = AgentReport(agent_id="a1", name="Agent", executed_at=now, status="success")
    assert r.findings == []


def test_monitoring_dashboard_document():
    doc = MonitoringDashboardDocument(
        title="Test", document_id="test-1",
    )
    assert doc.kind == DocumentStandard.BAM
    assert doc.metrics == {}
    assert doc.kpis == {}
