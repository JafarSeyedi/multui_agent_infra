# BAM — Business Activity Monitoring Engine

## Overview

A production-grade Business Activity Monitoring (BAM) system extending the
agentic BPMS infrastructure with real-time business metrics, KPIs, SLAs,
agentic monitoring agents, and dashboard data provisioning.

## Standards

| Standard | Code | Location |
|----------|------|----------|
| BAM models | `bam` | `engines/document/models/bam_models.py` |
| BAM parsers | — | `engines/document/parsers/bam_parsers/` |
| BAM writers | — | `engines/document/writers/bam_writers/` |
| BAM engine | — | `engines/orchestration/bam/` |

## Model Layer (`bam_models.py`)

### New Constants

- `DocumentStandard.BAM = "bam"`
- `DocumentFormat.BAM_JSON = "bam_json"`
- `DocumentFormat.BAM_YAML = "bam_yaml"`
- Two new `MediaType` entries in `MEDIA_TYPES`: `bam_json`, `bam_yaml`

### Enums

```python
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
```

### Core Models

```python
class BusinessMetric(BaseModel):
    metric_id: str
    name: str
    description: str | None = None
    category: MetricCategory = MetricCategory.PROCESS
    aggregation: MetricAggregation = MetricAggregation.AVG
    unit: str | None = None
    source_entity: Entity | None = None         # MSDM ref
    source_process: Process | None = None       # OSDM ref
    calculation_formula: str | None = None
    dimensions: list[str] = []
    tags: dict[str, str] = {}
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
    process_ref: Process | None = None          # OSDM ref
    activity_ids: list[str] = []
    condition: str
    target_value: float
    compliance_period: str = "monthly"
    penalty: str | None = None
    notifications: list[str] = []

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
    notification_channels: list[str] = []
    cep_rule: CEPRule | None = None

class DashboardWidget(BaseModel):
    widget_id: str
    type: str
    title: str
    position: dict[str, int] = {}
    data_source: str
    configuration: dict[str, Any] = {}
    refresh_interval: int = 30

class Dashboard(BaseModel):
    dashboard_id: str
    name: str
    description: str | None = None
    layout: str = "grid"
    widgets: list[DashboardWidget] = []
    refresh_interval: int = 30
    roles: list[str] = []
    tags: dict[str, str] = {}

class MonitoringAgentDefinition(BaseModel):
    agent_id: str
    name: str
    description: str | None = None
    agent_type: MonitoringAgentType = MonitoringAgentType.THRESHOLD
    input_metrics: list[str] = []
    output_actions: list[str] = []
    configuration: dict[str, Any] = {}
    schedule: str | None = None
    enabled: bool = True
```

### Runtime Data Models

```python
class MetricValue(BaseModel):
    timestamp: datetime
    metric_id: str
    value: float
    dimensions: dict[str, str] = {}
    tags: dict[str, str] = {}

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
    context: dict[str, Any] = {}

class AgentReport(BaseModel):
    agent_id: str
    name: str
    executed_at: datetime
    status: str
    findings: list[str] = []
    recommendations: list[str] = []
    metrics: dict[str, float] = {}
```

### Top-level Document

```python
class MonitoringDashboardDocument(BaseDocument):
    kind: DocumentStandard = DocumentStandard.BAM
    title: str = ""
    document_id: str = ""
    metrics: dict[str, BusinessMetric] = {}
    kpis: dict[str, KPI] = {}
    slas: dict[str, SlaDefinition] = {}
    alert_rules: dict[str, AlertRule] = {}
    dashboards: dict[str, Dashboard] = {}
    monitoring_agents: dict[str, MonitoringAgentDefinition] = {}
    metadata: dict[str, Any] = {}
```

## Parser/Writer Layer

```
engines/document/parsers/bam_parsers/
├── __init__.py
├── bam_json_parser.py    # .bam.json → MonitoringDashboardDocument
└── bam_yaml_parser.py    # .bam.yaml → MonitoringDashboardDocument

engines/document/writers/bam_writers/
├── __init__.py
├── bam_json_writer.py    # MonitoringDashboardDocument → .bam.json
└── bam_yaml_writer.py    # MonitoringDashboardDocument → .bam.yaml
```

Both parsers implement `BaseDocumentParser`; both writers implement
`BaseDocumentWriter`.

## Engine Layer (`engines/orchestration/bam/`)

### Directory Structure

```
engines/orchestration/bam/
├── __init__.py
├── engine.py                  # BamEngine — registered as "bam" handler
├── collector/
│   ├── __init__.py
│   ├── metric_collector.py    # Business metric calculation pipeline
│   └── kpi_evaluator.py       # KPI evaluation vs targets
├── realtime/
│   ├── __init__.py
│   ├── cep_bridge.py          # CEP events → metric pipeline
│   └── ring_buffer.py         # Lock-free metric ring buffer
├── alerting/
│   ├── __init__.py
│   ├── alert_manager.py       # Alert lifecycle state machine
│   ├── escalation.py          # Escalation policies
│   └── notification.py        # Notification channel dispatch
├── agents/
│   ├── __init__.py
│   ├── monitoring_orchestrator.py
│   ├── threshold_agent.py
│   ├── predictive_agent.py
│   ├── anomaly_agent.py
│   └── advisory_agent.py
├── dashboard/
│   ├── __init__.py
│   └── dashboard_manager.py
├── persistence/
│   ├── __init__.py
│   ├── metric_repository.py
│   └── alert_repository.py
└── slas/
    ├── __init__.py
    └── sla_tracker.py
```

### BamEngine Core API

```python
class BamEngine:
    async def start(self): ...
    async def stop(self): ...

    async def deploy(self, doc: MonitoringDashboardDocument): ...
    async def load(self, path: str) -> MonitoringDashboardDocument: ...
    async def parse(self, content: str, fmt: str) -> MonitoringDashboardDocument: ...

    async def record_metric(self, metric_id: str, value: float, dimensions: dict[str, str] = None): ...
    async def calculate_metric(self, metric_id: str) -> MetricValue: ...
    async def get_metric_history(self, metric_id: str, window: str = "1h") -> list[MetricValue]: ...

    async def evaluate_kpis(self) -> list[KpiResult]: ...
    async def get_kpi_status(self, kpi_id: str) -> KpiResult: ...

    async def track_sla_compliance(self, sla_id: str) -> SlaComplianceReport: ...
    async def get_sla_dashboard(self) -> list[SlaComplianceReport]: ...

    async def evaluate_alerts(self) -> list[AlertNotification]: ...
    async def acknowledge_alert(self, alert_id: str): ...

    async def run_monitoring_agents(self) -> list[AgentReport]: ...
    async def get_agent_status(self, agent_id: str) -> AgentStatus: ...

    async def get_dashboard_data(self, dashboard_id: str) -> DashboardData: ...
    async def get_widget_data(self, widget_id: str) -> WidgetData: ...
```

### Integration into OrchestrationEngine

```python
class EngineConfig:
    ...
    enable_bam: bool = True
    bam_metric_buffer_size: int = 100000
    bam_persistence_interval: int = 60
    bam_enable_predictive: bool = True
```

- `BamEngine` receives a reference to `OrchestrationEngine` at init
- Subscribes to `EventBus` for process lifecycle events
- Registers in `_engine_handlers["bam"]` for BAM deployment documents
- Uses `MetricsCollector` and `ProcessHeatmap` from existing orchestration/monitoring

### Event Flow

```
Process instance events → MetricsCollector → MetricCollector
                                                    ↓
                                            Ring Buffer (100K)
                                                    ↓
                                            Flusher (every 60s)
                                                    ↓
                              ┌───────────────────┼───────────────────┐
                              ↓                   ↓                   ↓
                       Persist to DB        Evaluate KPIs       Feed CEP Bridge
                                                                    ↓
                                                              Alert Rules
                                                                    ↓
                                                           Alert Manager
                                                                    ↓
                              ┌───────────────────┼───────────────────┐
                              ↓                   ↓                   ↓
                    Notification          Escalation           Dashboard
```

### Agentic Monitoring Agents

Four monitoring agent types, each a `BaseAgent` subclass deployable via
`AgenticTask(agent_id=...)` or autonomous scheduling:

| Agent | Type | Trigger | Behavior |
|-------|------|---------|----------|
| Threshold | self | metric breach | Rule-based alerting, immediate action |
| Predictive | agentic | scheduled/event | ML forecast → preemptive mitigation |
| Anomaly | self | metric stream | Statistical deviation detection |
| Advisory | interaction | request | Metric + graph context + LLM → recommendations |

## Implementation Order

1. **`DocumentStandard.BAM` + `DocumentFormat`** — Add BAM to
   `standard.py` and `media_types.py` with `MediaType` registration
2. **`bam_models.py`** — All core types, enums, runtime data models,
   and `MonitoringDashboardDocument`
3. **`bam_parsers/` + `bam_writers/`** — JSON/YAML parser and writer
   implementing `BaseDocumentParser`/`BaseDocumentWriter`
4. **`engines/orchestration/bam/engine.py`** — `BamEngine` skeleton
   with lifecycle, deployment, and handler registration
5. **`collector/`** — Metric collection pipeline + KPI evaluation engine
6. **`persistence/`** — Time-series metric store + alert history
7. **`alerting/`** — Alert lifecycle state machine, escalation, notifications
8. **`realtime/`** — CEP bridge + lock-free ring buffer
9. **`agents/`** — Four monitoring agent types (threshold, predictive, anomaly, advisory)
10. **`dashboard/`** — Dashboard data provisioning
11. **`slas/`** — SLA compliance computation
