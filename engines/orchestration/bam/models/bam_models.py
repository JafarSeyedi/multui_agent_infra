from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from engines.document.models.base import BaseDocument
from engines.document.models.media_types import DocumentFormat, MediaContentKind, MediaRawType, MediaType
from engines.document.models.msdm_models import Entity
from ...cep.models.cep_models import CEPRule
from ...bpmn.models.bpmn_models import Process
from engines.document.models.standard import DocumentStandard


_BAM_MEDIA_TYPE = MediaType(
    mime="application/json",
    format=DocumentFormat.BAM_JSON,
    standard=DocumentStandard.BAM,
    extensions=[".bam.json"],
    kind=MediaContentKind.STRUCTURED,
    raw_type=MediaRawType.TEXT,
    description="Business Activity Monitoring Definition (JSON)",
)


class MetricCategory(str, Enum):
    BUSINESS = "business"
    PROCESS = "process"
    OPERATIONAL = "operational"
    AGENTIC = "agentic"
    COMPOSITE = "composite"


class MetricAggregation(str, Enum):
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    DISTINCT_COUNT = "distinct_count"
    RATE = "rate"
    PERCENTILE = "percentile"
    MOVING_AVG = "moving_avg"
    WEIGHTED_AVG = "weighted_avg"
    CUSTOM = "custom"


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertState(str, Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class KpiStatus(str, Enum):
    ON_TRACK = "on_track"
    WARNING = "warning"
    CRITICAL = "critical"


class TrendDirection(str, Enum):
    IMPROVING = "improving"
    STABLE = "stable"
    DEGRADING = "degrading"


class MonitoringAgentType(str, Enum):
    THRESHOLD = "threshold"
    PREDICTIVE = "predictive"
    ANOMALY = "anomaly"
    ADVISORY = "advisory"


class MetricType(str, Enum):
    GAUGE = "gauge"
    COUNTER = "counter"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class BusinessMetric(BaseModel):
    metric_id: str
    name: str
    description: str | None = None
    category: MetricCategory = MetricCategory.PROCESS
    aggregation: MetricAggregation = MetricAggregation.AVG
    metric_type: MetricType = MetricType.GAUGE
    unit: str | None = None
    source_entity: Entity | None = None
    source_process: Process | None = None
    calculation_formula: str | None = None
    dimensions: list[str] = Field(default_factory=list)
    tags: dict[str, str] = Field(default_factory=dict)
    enabled: bool = True


class KPI(BaseModel):
    kpi_id: str
    name: str
    description: str | None = None
    metric_ref: str
    target_value: float
    threshold_warning: float
    threshold_critical: float
    direction: str = "increase"
    weight: float = 1.0
    owner: str | None = None
    time_period: str = "daily"


class SlaDefinition(BaseModel):
    sla_id: str
    name: str
    description: str | None = None
    process_ref: Process | None = None
    activity_ids: list[str] = Field(default_factory=list)
    condition: str
    target_value: float
    compliance_period: str = "monthly"
    penalty: str | None = None
    notifications: list[str] = Field(default_factory=list)


class AlertRule(BaseModel):
    rule_id: str
    name: str
    description: str | None = None
    condition: str
    severity: AlertSeverity = AlertSeverity.WARNING
    metric_ref: str | None = None
    cooldown_seconds: int = 300
    auto_resolve_seconds: int | None = None
    escalation_policy: str | None = None
    notification_channels: list[str] = Field(default_factory=list)
    cep_rule: CEPRule | None = None


class DashboardWidget(BaseModel):
    widget_id: str
    type: str
    title: str
    position: dict[str, int] = Field(default_factory=dict)
    data_source: str
    configuration: dict[str, Any] = Field(default_factory=dict)
    refresh_interval: int = 30


class Dashboard(BaseModel):
    dashboard_id: str
    name: str
    description: str | None = None
    layout: str = "grid"
    widgets: list[DashboardWidget] = Field(default_factory=list)
    refresh_interval: int = 30
    roles: list[str] = Field(default_factory=list)
    tags: dict[str, str] = Field(default_factory=dict)


class MonitoringAgentDefinition(BaseModel):
    agent_id: str
    name: str
    description: str | None = None
    agent_type: MonitoringAgentType = MonitoringAgentType.THRESHOLD
    input_metrics: list[str] = Field(default_factory=list)
    output_actions: list[str] = Field(default_factory=list)
    configuration: dict[str, Any] = Field(default_factory=dict)
    schedule: str | None = None
    enabled: bool = True


class MetricValue(BaseModel):
    timestamp: datetime
    metric_id: str
    value: float
    dimensions: dict[str, str] = Field(default_factory=dict)
    tags: dict[str, str] = Field(default_factory=dict)


class KpiResult(BaseModel):
    kpi_id: str
    name: str
    current_value: float
    target_value: float
    status: KpiStatus = KpiStatus.ON_TRACK
    trend: TrendDirection = TrendDirection.STABLE
    evaluated_at: datetime


class SlaComplianceReport(BaseModel):
    sla_id: str
    name: str
    compliance_rate: float
    breach_count: int
    total_evaluations: int
    period_start: datetime
    period_end: datetime


class AlertNotification(BaseModel):
    alert_id: str
    rule_id: str
    name: str
    severity: AlertSeverity
    state: AlertState
    message: str
    triggered_at: datetime
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None
    metric_value: float | None = None
    context: dict[str, Any] = Field(default_factory=dict)


class AgentReport(BaseModel):
    agent_id: str
    name: str
    executed_at: datetime
    status: str
    findings: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    metrics: dict[str, float] = Field(default_factory=dict)


class MonitoringDashboardDocument(BaseDocument):
    kind: DocumentStandard = DocumentStandard.BAM
    title: str = ""
    document_id: str = ""
    media_type: MediaType = _BAM_MEDIA_TYPE
    metrics: dict[str, BusinessMetric] = Field(default_factory=dict)
    kpis: dict[str, KPI] = Field(default_factory=dict)
    slas: dict[str, SlaDefinition] = Field(default_factory=dict)
    alert_rules: dict[str, AlertRule] = Field(default_factory=dict)
    dashboards: dict[str, Dashboard] = Field(default_factory=dict)
    monitoring_agents: dict[str, MonitoringAgentDefinition] = Field(default_factory=dict)

# Resolve forward references for pydantic models that use types from other modules.
from engines.orchestration.bpmn.models.bpmn_models import Script  # noqa: E402
for _model in [BusinessMetric, KPI, SlaDefinition, AlertRule, DashboardWidget, Dashboard,
               MonitoringAgentDefinition, MetricValue, KpiResult, SlaComplianceReport,
               AlertNotification, AgentReport, MonitoringDashboardDocument]:
    _model.model_rebuild()  # type: ignore[attr-defined]
