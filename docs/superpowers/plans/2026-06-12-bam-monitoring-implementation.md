# BAM Monitoring Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a production-grade Business Activity Monitoring (BAM) engine with model layer, parsers/writers, and orchestration integration.

**Architecture:** Three layers — (1) BDM models in `engines/document/models/bam_models.py` with parsers/writers, (2) `BamEngine` handler in `engines/orchestration/bam/`, (3) agentic monitoring agents, metric collector, alerting, dashboards. Follows existing *SDM patterns exactly.

**Tech Stack:** Python 3.11+, pydantic v2, asyncio, existing `BaseDocument`/`BaseDocumentParser`/`BaseDocumentWriter` interfaces, existing `OrchestrationEngine`, existing `CEPEngine`.

---

### Task 1: DocumentStandard BAM + DocumentFormat + MediaTypes

**Files:**
- Modify: `engines/document/models/standard.py:6`
- Modify: `engines/document/models/media_types.py:14`
- Test: `tests/document/test_bam_media_types.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/document/test_bam_media_types.py
from engines.document.models.media_types import DocumentFormat, MEDIA_TYPES, MediaTypeRegistry
from engines.document.models.standard import DocumentStandard


def test_bam_standard_exists():
    assert DocumentStandard.BAM == "bam"


def test_bam_formats_exist():
    assert DocumentFormat.BAM_JSON == "bam_json"
    assert DocumentFormat.BAM_YAML == "bam_yaml"


def test_bam_media_types_registered():
    mt_json = MEDIA_TYPES.get("bam_json")
    assert mt_json is not None
    assert mt_json.standard == DocumentStandard.BAM
    assert mt_json.format == DocumentFormat.BAM_JSON
    assert ".bam.json" in mt_json.extensions

    mt_yaml = MEDIA_TYPES.get("bam_yaml")
    assert mt_yaml is not None
    assert mt_yaml.standard == DocumentStandard.BAM
    assert mt_yaml.format == DocumentFormat.BAM_YAML
    assert ".bam.yaml" in mt_yaml.extensions


def test_bam_media_type_registry():
    mt = MediaTypeRegistry.get_by_format(DocumentFormat.BAM_JSON)
    assert mt is not None
    assert mt.mime == "application/json"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/document/test_bam_media_types.py -v`
Expected: FAIL with `DocumentStandard has no attribute 'BAM'`

- [ ] **Step 3: Add BAM to DocumentStandard**

In `engines/document/models/standard.py`, add to `DocumentStandard` enum:
```python
BAM = "bam"   # Business Activity Monitoring Model
```

In `full_name` property dict:
```python
"bam": "Business Activity Monitoring Model",
```

In `description` property dict:
```python
"bam": "Business Activity Monitoring model for metrics, KPIs, SLAs, dashboards, alert rules, and monitoring agent definitions",
```

In `STANDARD_TO_CATEGORY`:
```python
DocumentStandard.BAM: MediaCategory.STRUCTURED_DATA,
```

In `ABBREVIATIONS`:
```python
"BAM": "Business Activity Monitoring Model",
```

In `get_common_formats`:
```python
DocumentStandard.BAM: ["bam_json", "bam_yaml"],
```

- [ ] **Step 4: Add BAM DocumentFormats**

In `engines/document/models/media_types.py`, add to `DocumentFormat` enum (before `UNKNOWN`):
```python
# BAM formats
BAM_JSON = "bam_json"
BAM_YAML = "bam_yaml"
```

- [ ] **Step 5: Register BAM MediaTypes in MEDIA_TYPES**

Add to `MEDIA_TYPES` dict (before `"binary"`):
```python
"bam_json": MediaType(
    mime="application/json",
    format=DocumentFormat.BAM_JSON,
    standard=DocumentStandard.BAM,
    extensions=[".bam.json"],
    kind=MediaContentKind.STRUCTURED,
    raw_type=MediaRawType.TEXT,
    description="Business Activity Monitoring Definition (JSON)"
),
"bam_yaml": MediaType(
    mime="application/x-yaml",
    format=DocumentFormat.BAM_YAML,
    standard=DocumentStandard.BAM,
    extensions=[".bam.yaml", ".bam.yml"],
    kind=MediaContentKind.STRUCTURED,
    raw_type=MediaRawType.TEXT,
    description="Business Activity Monitoring Definition (YAML)"
),
```

- [ ] **Step 6: Run test to verify it passes**

Run: `pytest tests/document/test_bam_media_types.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add tests/document/test_bam_media_types.py engines/document/models/standard.py engines/document/models/media_types.py
git commit -m "feat(bam): add DocumentStandard.BAM, DocumentFormat BAM_JSON/BAM_YAML, media types"
```

---

### Task 2: bam_models.py — Core Model Definitions

**Files:**
- Create: `engines/document/models/bam_models.py`
- Test: `tests/document/test_bam_models.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/document/test_bam_models.py
from datetime import datetime
from engines.document.models.bam_models import (
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
    doc = MonitoringDashboardDocument(title="Test", document_id="test-1")
    assert doc.kind == DocumentStandard.BAM
    assert doc.metrics == {}
    assert doc.kpis == {}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/document/test_bam_models.py -v`
Expected: FAIL with `ImportError: No module named bam_models`

- [ ] **Step 3: Create `engines/document/models/bam_models.py`**

```python
# engines/document/models/bam_models.py
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from .base import BaseDocument
from .msdm_models import Entity
from .osdm_models import CEPRule, Process
from .standard import DocumentStandard


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


class BusinessMetric(BaseModel):
    metric_id: str
    name: str
    description: str | None = None
    category: MetricCategory = MetricCategory.PROCESS
    aggregation: MetricAggregation = MetricAggregation.AVG
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
    metrics: dict[str, BusinessMetric] = Field(default_factory=dict)
    kpis: dict[str, KPI] = Field(default_factory=dict)
    slas: dict[str, SlaDefinition] = Field(default_factory=dict)
    alert_rules: dict[str, AlertRule] = Field(default_factory=dict)
    dashboards: dict[str, Dashboard] = Field(default_factory=dict)
    monitoring_agents: dict[str, MonitoringAgentDefinition] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/document/test_bam_models.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/document/test_bam_models.py engines/document/models/bam_models.py
git commit -m "feat(bam): add bam_models.py with core BDM types"
```

---

### Task 3: Re-export BAM Models from models/__init__.py

**Files:**
- Modify: `engines/document/models/__init__.py`

- [ ] **Step 1: Add BAM model re-exports**

Add after the LSDM import block in `engines/document/models/__init__.py`:
```python
from .bam_models import (
    AlertNotification, AlertRule, AlertSeverity, AlertState,
    AgentReport, BusinessMetric, Dashboard, DashboardWidget,
    KPI, KpiResult, KpiStatus, MetricAggregation, MetricCategory,
    MetricValue, MonitoringAgentDefinition, MonitoringAgentType,
    MonitoringDashboardDocument, SlaComplianceReport, SlaDefinition,
    TrendDirection,
)
```

Add to `__all__` list:
```python
    "AlertNotification",
    "AlertRule",
    "AlertSeverity",
    "AlertState",
    "AgentReport",
    "BusinessMetric",
    "Dashboard",
    "DashboardWidget",
    "KPI",
    "KpiResult",
    "KpiStatus",
    "MetricAggregation",
    "MetricCategory",
    "MetricValue",
    "MonitoringAgentDefinition",
    "MonitoringAgentType",
    "MonitoringDashboardDocument",
    "SlaComplianceReport",
    "SlaDefinition",
    "TrendDirection",
```

- [ ] **Step 2: Run import test**

Run: `python3 -c "from engines.document.models import MonitoringDashboardDocument, BusinessMetric, KPI; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add engines/document/models/__init__.py
git commit -m "feat(bam): re-export BAM models from models __init__"
```

---

### Task 4: BAM JSON Parser

**Files:**
- Create: `engines/document/parsers/bam_parsers/__init__.py`
- Create: `engines/document/parsers/bam_parsers/bam_json_parser.py`
- Test: `tests/document/test_bam_json_parser.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/document/test_bam_json_parser.py
import json
import pytest
from engines.document.models.bam_models import (
    MonitoringDashboardDocument, BusinessMetric, KPI,
)
from engines.document.parsers.bam_parsers.bam_json_parser import BamJsonParser


@pytest.fixture
def valid_bam_json():
    return json.dumps({
        "title": "Test Dashboard",
        "document_id": "test-1",
        "metrics": {
            "m1": {
                "metric_id": "m1",
                "name": "Process Cycle Time",
                "category": "process",
                "aggregation": "avg",
                "unit": "ms"
            }
        },
        "kpis": {
            "k1": {
                "kpi_id": "k1",
                "name": "SLA Compliance",
                "metric_ref": "m1",
                "target_value": 95.0,
                "threshold_warning": 90.0,
                "threshold_critical": 80.0
            }
        }
    })


@pytest.mark.asyncio
async def test_parse_bam_json(valid_bam_json):
    parser = BamJsonParser()
    doc = await parser.parse_bytes(valid_bam_json.encode("utf-8"), "test-1", "test.bam.json")
    assert isinstance(doc, MonitoringDashboardDocument)
    assert doc.title == "Test Dashboard"
    assert doc.document_id == "test-1"
    assert "m1" in doc.metrics
    assert doc.metrics["m1"].name == "Process Cycle Time"
    assert "k1" in doc.kpis
    assert doc.kpis["k1"].name == "SLA Compliance"


@pytest.mark.asyncio
async def test_parse_bam_json_empty():
    parser = BamJsonParser()
    doc = await parser.parse_bytes(b"{}", "empty", "empty.bam.json")
    assert isinstance(doc, MonitoringDashboardDocument)


@pytest.mark.asyncio
async def test_parse_bam_json_invalid():
    parser = BamJsonParser()
    with pytest.raises(Exception):
        await parser.parse_bytes(b"not json", "bad", "bad.bam.json")


def test_json_parser_supported_extensions():
    parser = BamJsonParser()
    exts = list(parser.iter_supported_extensions())
    assert ".bam.json" in exts
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/document/test_bam_json_parser.py -v`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Create `engines/document/parsers/bam_parsers/__init__.py`**

```python
from .bam_json_parser import BamJsonParser

__all__ = ["BamJsonParser"]
```

- [ ] **Step 4: Create `engines/document/parsers/bam_parsers/bam_json_parser.py`**

```python
# engines/document/parsers/bam_parsers/bam_json_parser.py
from __future__ import annotations

import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from ...models.base import BaseDocument
from ...models.bam_models import (
    AlertRule, BusinessMetric, Dashboard, DashboardWidget,
    KPI, MonitoringAgentDefinition, MonitoringDashboardDocument,
    SlaDefinition,
)
from ..base import BaseDocumentParser


class BamJsonParser(BaseDocumentParser):
    async def parse_bytes(
        self,
        data: bytes,
        document_id: str,
        source_name: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> BaseDocument:
        raw = json.loads(data.decode("utf-8"))
        return self._build_document(raw, document_id, source_name, metadata or {})

    async def parse_path(
        self,
        path: str | Path,
        document_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> BaseDocument:
        p = Path(path)
        data = p.read_bytes()
        return await self.parse_bytes(data, document_id or p.stem, str(p), metadata)

    async def parse_stream(
        self,
        stream: AsyncIterator[bytes],
        document_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> BaseDocument:
        chunks = [chunk async for chunk in stream]
        data = b"".join(chunks)
        return await self.parse_bytes(data, document_id, "stream", metadata)

    def can_parse(self, path: str | Path) -> bool:
        return str(path).endswith(".bam.json")

    def supports_extension(self, ext: str) -> bool:
        return ext in (".bam.json",)

    def iter_supported_extensions(self):
        yield ".bam.json"

    def _build_document(
        self,
        raw: dict[str, Any],
        document_id: str,
        source_name: str,
        metadata: dict[str, Any],
    ) -> MonitoringDashboardDocument:
        doc = MonitoringDashboardDocument(
            title=raw.get("title", ""),
            document_id=document_id,
        )
        for mid, mdata in raw.get("metrics", {}).items():
            doc.metrics[mid] = BusinessMetric(**mdata)
        for kid, kdata in raw.get("kpis", {}).items():
            doc.kpis[kid] = KPI(**kdata)
        for sid, sdata in raw.get("slas", {}).items():
            doc.slas[sid] = SlaDefinition(**sdata)
        for rid, rdata in raw.get("alert_rules", {}).items():
            doc.alert_rules[rid] = AlertRule(**rdata)
        for did, ddata in raw.get("dashboards", {}).items():
            dash = Dashboard(**ddata)
            doc.dashboards[did] = dash
        for aid, adata in raw.get("monitoring_agents", {}).items():
            doc.monitoring_agents[aid] = MonitoringAgentDefinition(**adata)
        doc.metadata = raw.get("metadata", {})
        return doc
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/document/test_bam_json_parser.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add tests/document/test_bam_json_parser.py engines/document/parsers/bam_parsers/
git commit -m "feat(bam): add BAM JSON parser"
```

---

### Task 5: BAM YAML Parser

**Files:**
- Create: `engines/document/parsers/bam_parsers/bam_yaml_parser.py`
- Modify: `engines/document/parsers/bam_parsers/__init__.py`
- Test: `tests/document/test_bam_yaml_parser.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/document/test_bam_yaml_parser.py
import pytest
from engines.document.models.bam_models import MonitoringDashboardDocument
from engines.document.parsers.bam_parsers.bam_yaml_parser import BamYamlParser


YAML_CONTENT = """
title: Test Dashboard
document_id: test-1
metrics:
  m1:
    metric_id: m1
    name: Process Cycle Time
    category: process
    aggregation: avg
    unit: ms
kpis:
  k1:
    kpi_id: k1
    name: SLA Compliance
    metric_ref: m1
    target_value: 95.0
    threshold_warning: 90.0
    threshold_critical: 80.0
"""


@pytest.mark.asyncio
async def test_parse_bam_yaml():
    parser = BamYamlParser()
    doc = await parser.parse_bytes(YAML_CONTENT.encode("utf-8"), "test-1", "test.bam.yaml")
    assert isinstance(doc, MonitoringDashboardDocument)
    assert doc.title == "Test Dashboard"
    assert "m1" in doc.metrics
    assert "k1" in doc.kpis


def test_yaml_parser_supported_extensions():
    parser = BamYamlParser()
    exts = list(parser.iter_supported_extensions())
    assert ".bam.yaml" in exts or ".bam.yml" in exts
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/document/test_bam_yaml_parser.py -v`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Create `engines/document/parsers/bam_parsers/bam_yaml_parser.py`**

```python
# engines/document/parsers/bam_parsers/bam_yaml_parser.py
from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from ...models.base import BaseDocument
from ...models.bam_models import (
    AlertRule, BusinessMetric, Dashboard, DashboardWidget,
    KPI, MonitoringAgentDefinition, MonitoringDashboardDocument,
    SlaDefinition,
)
from ..base import BaseDocumentParser


try:
    import yaml as _yaml
except ImportError:
    _yaml = None


class BamYamlParser(BaseDocumentParser):
    async def parse_bytes(
        self,
        data: bytes,
        document_id: str,
        source_name: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> BaseDocument:
        if _yaml is None:
            raise ImportError("PyYAML is required for .bam.yaml parsing")
        raw = _yaml.safe_load(data.decode("utf-8"))
        return self._build_document(raw, document_id, source_name, metadata or {})

    async def parse_path(
        self,
        path: str | Path,
        document_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> BaseDocument:
        p = Path(path)
        data = p.read_bytes()
        return await self.parse_bytes(data, document_id or p.stem, str(p), metadata)

    async def parse_stream(
        self,
        stream: AsyncIterator[bytes],
        document_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> BaseDocument:
        chunks = [chunk async for chunk in stream]
        data = b"".join(chunks)
        return await self.parse_bytes(data, document_id, "stream", metadata)

    def can_parse(self, path: str | Path) -> bool:
        p = str(path)
        return p.endswith(".bam.yaml") or p.endswith(".bam.yml")

    def supports_extension(self, ext: str) -> bool:
        return ext in (".bam.yaml", ".bam.yml")

    def iter_supported_extensions(self):
        yield ".bam.yaml"
        yield ".bam.yml"

    def _build_document(
        self,
        raw: dict[str, Any],
        document_id: str,
        source_name: str,
        metadata: dict[str, Any],
    ) -> MonitoringDashboardDocument:
        doc = MonitoringDashboardDocument(
            title=raw.get("title", ""),
            document_id=document_id,
        )
        for mid, mdata in raw.get("metrics", {}).items():
            doc.metrics[mid] = BusinessMetric(**mdata)
        for kid, kdata in raw.get("kpis", {}).items():
            doc.kpis[kid] = KPI(**kdata)
        for sid, sdata in raw.get("slas", {}).items():
            doc.slas[sid] = SlaDefinition(**sdata)
        for rid, rdata in raw.get("alert_rules", {}).items():
            doc.alert_rules[rid] = AlertRule(**rdata)
        for did, ddata in raw.get("dashboards", {}).items():
            doc.dashboards[did] = Dashboard(**ddata)
        for aid, adata in raw.get("monitoring_agents", {}).items():
            doc.monitoring_agents[aid] = MonitoringAgentDefinition(**adata)
        doc.metadata = raw.get("metadata", {})
        return doc
```

- [ ] **Step 4: Update `engines/document/parsers/bam_parsers/__init__.py`**

```python
from .bam_json_parser import BamJsonParser
from .bam_yaml_parser import BamYamlParser

__all__ = ["BamJsonParser", "BamYamlParser"]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/document/test_bam_yaml_parser.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add tests/document/test_bam_yaml_parser.py engines/document/parsers/bam_parsers/bam_yaml_parser.py engines/document/parsers/bam_parsers/__init__.py
git commit -m "feat(bam): add BAM YAML parser"
```

---

### Task 6: BAM JSON Writer

**Files:**
- Create: `engines/document/writers/bam_writers/__init__.py`
- Create: `engines/document/writers/bam_writers/bam_json_writer.py`
- Test: `tests/document/test_bam_json_writer.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/document/test_bam_json_writer.py
import json
import pytest
from engines.document.models.bam_models import (
    BusinessMetric, KPI, MonitoringDashboardDocument,
)
from engines.document.writers.bam_writers.bam_json_writer import BamJsonWriter


@pytest.mark.asyncio
async def test_write_bam_json():
    doc = MonitoringDashboardDocument(title="Test", document_id="test-1")
    doc.metrics["m1"] = BusinessMetric(metric_id="m1", name="CPU Usage", unit="%")
    doc.kpis["k1"] = KPI(kpi_id="k1", name="SLA", metric_ref="m1",
                           target_value=95.0, threshold_warning=90.0, threshold_critical=80.0)

    writer = BamJsonWriter()
    data = await writer.write(doc)
    parsed = json.loads(data.decode("utf-8"))
    assert parsed["title"] == "Test"
    assert "m1" in parsed["metrics"]
    assert parsed["metrics"]["m1"]["name"] == "CPU Usage"
    assert "k1" in parsed["kpis"]


@pytest.mark.asyncio
async def test_write_bam_json_empty():
    doc = MonitoringDashboardDocument(title="Empty", document_id="empty")
    writer = BamJsonWriter()
    data = await writer.write(doc)
    parsed = json.loads(data.decode("utf-8"))
    assert parsed["title"] == "Empty"


@pytest.mark.asyncio
async def test_json_writer_roundtrip():
    import json
    from engines.document.parsers.bam_parsers.bam_json_parser import BamJsonParser

    doc = MonitoringDashboardDocument(title="RT", document_id="rt-1")
    doc.metrics["m1"] = BusinessMetric(metric_id="m1", name="Test", unit="ms")

    writer = BamJsonWriter()
    data = await writer.write(doc)

    parser = BamJsonParser()
    parsed = await parser.parse_bytes(data, "rt-1", "rt.bam.json")
    assert parsed.title == "RT"
    assert "m1" in parsed.metrics
    assert parsed.metrics["m1"].name == "Test"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/document/test_bam_json_writer.py -v`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Create `engines/document/writers/bam_writers/__init__.py`**

```python
from .bam_json_writer import BamJsonWriter

__all__ = ["BamJsonWriter"]
```

- [ ] **Step 4: Create `engines/document/writers/bam_writers/bam_json_writer.py`**

```python
# engines/document/writers/bam_writers/bam_json_writer.py
from __future__ import annotations

import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from ...models.base import BaseDocument
from ...models.bam_models import MonitoringDashboardDocument
from ..base import BaseDocumentWriter


class BamJsonWriter(BaseDocumentWriter):
    async def write(self, document: BaseDocument) -> bytes:
        assert isinstance(document, MonitoringDashboardDocument)
        raw = self._to_dict(document)
        return json.dumps(raw, indent=2, default=str).encode("utf-8")

    async def write_stream(self, document: BaseDocument) -> AsyncIterator[bytes]:
        yield await self.write(document)

    async def write_to_file(
        self,
        document: BaseDocument,
        target: Path,
        options: dict[str, Any] | None = None,
    ) -> None:
        data = await self.write(document)
        target.write_bytes(data)

    def get_supported_media_types(self) -> list[str]:
        return ["application/json"]

    def get_supported_extensions(self) -> list[str]:
        return [".bam.json"]

    def _to_dict(self, doc: MonitoringDashboardDocument) -> dict[str, Any]:
        result: dict[str, Any] = {
            "title": doc.title,
            "document_id": doc.document_id,
        }
        if doc.metrics:
            result["metrics"] = {
                mid: m.model_dump(exclude_none=True)
                for mid, m in doc.metrics.items()
            }
        if doc.kpis:
            result["kpis"] = {
                kid: k.model_dump(exclude_none=True)
                for kid, k in doc.kpis.items()
            }
        if doc.slas:
            result["slas"] = {
                sid: s.model_dump(exclude_none=True)
                for sid, s in doc.slas.items()
            }
        if doc.alert_rules:
            result["alert_rules"] = {
                rid: r.model_dump(exclude_none=True)
                for rid, r in doc.alert_rules.items()
            }
        if doc.dashboards:
            result["dashboards"] = {
                did: d.model_dump(exclude_none=True)
                for did, d in doc.dashboards.items()
            }
        if doc.monitoring_agents:
            result["monitoring_agents"] = {
                aid: a.model_dump(exclude_none=True)
                for aid, a in doc.monitoring_agents.items()
            }
        if doc.metadata:
            result["metadata"] = doc.metadata
        return result
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/document/test_bam_json_writer.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add tests/document/test_bam_json_writer.py engines/document/writers/bam_writers/
git commit -m "feat(bam): add BAM JSON writer"
```

---

### Task 7: BAM YAML Writer

**Files:**
- Create: `engines/document/writers/bam_writers/bam_yaml_writer.py`
- Modify: `engines/document/writers/bam_writers/__init__.py`
- Test: `tests/document/test_bam_yaml_writer.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/document/test_bam_yaml_writer.py
import pytest
from engines.document.models.bam_models import (
    BusinessMetric, KPI, MonitoringDashboardDocument,
)
from engines.document.writers.bam_writers.bam_yaml_writer import BamYamlWriter


@pytest.mark.asyncio
async def test_write_bam_yaml():
    doc = MonitoringDashboardDocument(title="Test", document_id="test-1")
    doc.metrics["m1"] = BusinessMetric(metric_id="m1", name="CPU Usage", unit="%")
    doc.kpis["k1"] = KPI(kpi_id="k1", name="SLA", metric_ref="m1",
                           target_value=95.0, threshold_warning=90.0, threshold_critical=80.0)

    writer = BamYamlWriter()
    data = await writer.write(doc)
    text = data.decode("utf-8")
    assert "title: Test" in text
    assert "metric_id: m1" in text
    assert "kpi_id: k1" in text


@pytest.mark.asyncio
async def test_yaml_writer_roundtrip():
    from engines.document.parsers.bam_parsers.bam_yaml_parser import BamYamlParser

    doc = MonitoringDashboardDocument(title="RT", document_id="rt-1")
    doc.metrics["m1"] = BusinessMetric(metric_id="m1", name="Test")

    writer = BamYamlWriter()
    data = await writer.write(doc)

    parser = BamYamlParser()
    parsed = await parser.parse_bytes(data, "rt-1", "rt.bam.yaml")
    assert parsed.title == "RT"
    assert "m1" in parsed.metrics
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/document/test_bam_yaml_writer.py -v`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Create `engines/document/writers/bam_writers/bam_yaml_writer.py`**

```python
# engines/document/writers/bam_writers/bam_yaml_writer.py
from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from ...models.base import BaseDocument
from ...models.bam_models import MonitoringDashboardDocument
from ..base import BaseDocumentWriter


try:
    import yaml as _yaml
except ImportError:
    _yaml = None


class BamYamlWriter(BaseDocumentWriter):
    async def write(self, document: BaseDocument) -> bytes:
        assert isinstance(document, MonitoringDashboardDocument)
        if _yaml is None:
            raise ImportError("PyYAML is required for .bam.yaml writing")
        raw = self._to_dict(document)
        return _yaml.safe_dump(raw, default_flow_style=False, sort_keys=False).encode("utf-8")

    async def write_stream(self, document: BaseDocument) -> AsyncIterator[bytes]:
        yield await self.write(document)

    async def write_to_file(
        self,
        document: BaseDocument,
        target: Path,
        options: dict[str, Any] | None = None,
    ) -> None:
        data = await self.write(document)
        target.write_bytes(data)

    def get_supported_media_types(self) -> list[str]:
        return ["application/x-yaml"]

    def get_supported_extensions(self) -> list[str]:
        return [".bam.yaml", ".bam.yml"]

    def _to_dict(self, doc: MonitoringDashboardDocument) -> dict[str, Any]:
        result: dict[str, Any] = {
            "title": doc.title,
            "document_id": doc.document_id,
        }
        if doc.metrics:
            result["metrics"] = {
                mid: m.model_dump(exclude_none=True)
                for mid, m in doc.metrics.items()
            }
        if doc.kpis:
            result["kpis"] = {
                kid: k.model_dump(exclude_none=True)
                for kid, k in doc.kpis.items()
            }
        if doc.slas:
            result["slas"] = {
                sid: s.model_dump(exclude_none=True)
                for sid, s in doc.slas.items()
            }
        if doc.alert_rules:
            result["alert_rules"] = {
                rid: r.model_dump(exclude_none=True)
                for rid, r in doc.alert_rules.items()
            }
        if doc.dashboards:
            result["dashboards"] = {
                did: d.model_dump(exclude_none=True)
                for did, d in doc.dashboards.items()
            }
        if doc.monitoring_agents:
            result["monitoring_agents"] = {
                aid: a.model_dump(exclude_none=True)
                for aid, a in doc.monitoring_agents.items()
            }
        if doc.metadata:
            result["metadata"] = doc.metadata
        return result
```

- [ ] **Step 4: Update `engines/document/writers/bam_writers/__init__.py`**

```python
from .bam_json_writer import BamJsonWriter
from .bam_yaml_writer import BamYamlWriter

__all__ = ["BamJsonWriter", "BamYamlWriter"]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/document/test_bam_yaml_writer.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add tests/document/test_bam_yaml_writer.py engines/document/writers/bam_writers/bam_yaml_writer.py engines/document/writers/bam_writers/__init__.py
git commit -m "feat(bam): add BAM YAML writer"
```

---

### Task 8: Document Round-Trip Test

**Files:**
- Test: `tests/document/test_bam_roundtrip.py`

- [ ] **Step 1: Write the round-trip test**

```python
# tests/document/test_bam_roundtrip.py
import pytest
from engines.document.models.bam_models import (
    BusinessMetric, KPI, AlertRule, AlertSeverity,
    SlaDefinition, Dashboard, DashboardWidget,
    MonitoringAgentDefinition, MonitoringDashboardDocument,
)
from engines.document.parsers.bam_parsers.bam_json_parser import BamJsonParser
from engines.document.writers.bam_writers.bam_json_writer import BamJsonWriter
from engines.document.parsers.bam_parsers.bam_yaml_parser import BamYamlParser
from engines.document.writers.bam_writers.bam_yaml_writer import BamYamlWriter


def _make_full_doc() -> MonitoringDashboardDocument:
    doc = MonitoringDashboardDocument(
        title="Production Monitoring",
        document_id="prod-1",
    )
    doc.metrics["cpu"] = BusinessMetric(
        metric_id="cpu", name="CPU Usage", unit="%",
        category="operational",
    )
    doc.metrics["cycle"] = BusinessMetric(
        metric_id="cycle", name="Cycle Time", unit="ms",
        category="process",
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
```

- [ ] **Step 2: Run test to verify it passes**

Run: `pytest tests/document/test_bam_roundtrip.py -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/document/test_bam_roundtrip.py
git commit -m "test(bam): add document round-trip tests"
```

---

### Task 9: BamEngine Skeleton

**Files:**
- Create: `engines/orchestration/bam/__init__.py`
- Create: `engines/orchestration/bam/engine.py`
- Create: `engines/orchestration/bam/collector/__init__.py`
- Create: `engines/orchestration/bam/realtime/__init__.py`
- Create: `engines/orchestration/bam/alerting/__init__.py`
- Create: `engines/orchestration/bam/agents/__init__.py`
- Create: `engines/orchestration/bam/dashboard/__init__.py`
- Create: `engines/orchestration/bam/persistence/__init__.py`
- Create: `engines/orchestration/bam/slas/__init__.py`
- Test: `tests/orchestration/test_bam/__init__.py`
- Test: `tests/orchestration/test_bam/test_bam_engine.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/orchestration/test_bam/test_bam_engine.py
import pytest
from engines.orchestration.bam.engine import BamEngine
from engines.document.models.bam_models import MonitoringDashboardDocument, BusinessMetric


@pytest.mark.asyncio
async def test_bam_engine_create():
    engine = BamEngine()
    assert engine is not None


@pytest.mark.asyncio
async def test_bam_engine_lifecycle():
    engine = BamEngine()
    await engine.start()
    assert engine._running is True
    await engine.stop()
    assert engine._running is False


@pytest.mark.asyncio
async def test_bam_engine_deploy():
    engine = BamEngine()
    await engine.start()
    doc = MonitoringDashboardDocument(title="Test", document_id="test-1")
    doc.metrics["m1"] = BusinessMetric(metric_id="m1", name="Test")
    await engine.deploy(doc)
    assert "test-1" in engine._deployments


@pytest.mark.asyncio
async def test_bam_engine_record_metric():
    engine = BamEngine()
    await engine.start()
    await engine.record_metric("m1", 42.5)
    history = await engine.get_metric_history("m1", "1h")
    assert len(history) >= 1
    assert history[-1].value == 42.5
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/orchestration/test_bam/test_bam_engine.py -v`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Create `engines/orchestration/bam/__init__.py`**

```python
from .engine import BamEngine

__all__ = ["BamEngine"]
```

- [ ] **Step 4: Create all subdirectory `__init__.py` files**

```python
# engines/orchestration/bam/collector/__init__.py
# engines/orchestration/bam/realtime/__init__.py
# engines/orchestration/bam/alerting/__init__.py
# engines/orchestration/bam/agents/__init__.py
# engines/orchestration/bam/dashboard/__init__.py
# engines/orchestration/bam/persistence/__init__.py
# engines/orchestration/bam/slas/__init__.py
```
Each is: empty file with just a docstring and `__all__`.

- [ ] **Step 5: Create `engines/orchestration/bam/engine.py`**

```python
# engines/orchestration/bam/engine.py
from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from engines.document.models.bam_models import (
    AlertNotification, AlertState, KpiResult, KpiStatus,
    MetricValue, MonitoringDashboardDocument, TrendDirection,
)


class BamEngine:
    def __init__(self, engine: Any | None = None):
        self._engine = engine
        self._running = False
        self._deployments: dict[str, MonitoringDashboardDocument] = {}
        self._metric_buffer: list[MetricValue] = []
        self._metric_history: dict[str, list[MetricValue]] = defaultdict(list)
        self._metric_lock = asyncio.Lock()

    async def start(self) -> None:
        self._running = True

    async def stop(self) -> None:
        self._running = False
        await self._flush_metrics()

    async def deploy(self, doc: MonitoringDashboardDocument) -> None:
        self._deployments[doc.document_id] = doc

    async def load(self, path: str) -> MonitoringDashboardDocument:
        from pathlib import Path
        p = Path(path)
        if p.suffix == ".json" or ".bam.json" in str(p):
            from engines.document.parsers.bam_parsers.bam_json_parser import BamJsonParser
            parser = BamJsonParser()
            doc = await parser.parse_path(p)
            assert isinstance(doc, MonitoringDashboardDocument)
            return doc
        elif ".bam.yaml" in str(p) or ".bam.yml" in str(p):
            from engines.document.parsers.bam_parsers.bam_yaml_parser import BamYamlParser
            parser = BamYamlParser()
            doc = await parser.parse_path(p)
            assert isinstance(doc, MonitoringDashboardDocument)
            return doc
        raise ValueError(f"Unsupported BAM file: {path}")

    async def parse(self, content: str, fmt: str) -> MonitoringDashboardDocument:
        if fmt == "json":
            from engines.document.parsers.bam_parsers.bam_json_parser import BamJsonParser
            parser = BamJsonParser()
            doc = await parser.parse_bytes(content.encode("utf-8"), "inline", "inline.bam.json")
        elif fmt == "yaml":
            from engines.document.parsers.bam_parsers.bam_yaml_parser import BamYamlParser
            parser = BamYamlParser()
            doc = await parser.parse_bytes(content.encode("utf-8"), "inline", "inline.bam.yaml")
        else:
            raise ValueError(f"Unsupported BAM format: {fmt}")
        assert isinstance(doc, MonitoringDashboardDocument)
        return doc

    async def record_metric(
        self,
        metric_id: str,
        value: float,
        dimensions: dict[str, str] | None = None,
    ) -> None:
        mv = MetricValue(
            timestamp=datetime.utcnow(),
            metric_id=metric_id,
            value=value,
            dimensions=dimensions or {},
        )
        async with self._metric_lock:
            self._metric_buffer.append(mv)
            self._metric_history[metric_id].append(mv)
            if len(self._metric_buffer) >= 1000:
                await self._flush_metrics()

    async def calculate_metric(self, metric_id: str) -> MetricValue | None:
        history = self._metric_history.get(metric_id, [])
        if not history:
            return None
        values = [m.value for m in history]
        avg_val = sum(values) / len(values)
        return MetricValue(
            timestamp=datetime.utcnow(),
            metric_id=metric_id,
            value=avg_val,
        )

    async def get_metric_history(
        self,
        metric_id: str,
        window: str = "1h",
    ) -> list[MetricValue]:
        all_vals = list(self._metric_history.get(metric_id, []))
        cutoff = self._parse_window(window)
        return [v for v in all_vals if v.timestamp >= cutoff]

    async def evaluate_kpis(self) -> list[KpiResult]:
        results: list[KpiResult] = []
        for dep in self._deployments.values():
            for kid, kpi in dep.kpis.items():
                mv = await self.calculate_metric(kpi.metric_ref)
                current = mv.value if mv else 0.0
                if current >= kpi.target_value:
                    status = KpiStatus.ON_TRACK
                elif current >= kpi.threshold_warning:
                    status = KpiStatus.WARNING
                else:
                    status = KpiStatus.CRITICAL
                results.append(KpiResult(
                    kpi_id=kid,
                    name=kpi.name,
                    current_value=current,
                    target_value=kpi.target_value,
                    status=status,
                    trend=TrendDirection.STABLE,
                    evaluated_at=datetime.utcnow(),
                ))
        return results

    async def get_kpi_status(self, kpi_id: str) -> KpiResult | None:
        results = await self.evaluate_kpis()
        for r in results:
            if r.kpi_id == kpi_id:
                return r
        return None

    async def track_sla_compliance(self, sla_id: str) -> SlaComplianceReport | None:
        from engines.document.models.bam_models import SlaComplianceReport
        for dep in self._deployments.values():
            sla = dep.slas.get(sla_id)
            if sla is not None:
                return SlaComplianceReport(
                    sla_id=sla_id,
                    name=sla.name,
                    compliance_rate=1.0,
                    breach_count=0,
                    total_evaluations=1,
                    period_start=datetime.utcnow() - timedelta(days=30),
                    period_end=datetime.utcnow(),
                )
        return None

    async def get_sla_dashboard(self) -> list[SlaComplianceReport]:
        from engines.document.models.bam_models import SlaComplianceReport
        reports: list[SlaComplianceReport] = []
        for dep in self._deployments.values():
            for sla_id in dep.slas:
                report = await self.track_sla_compliance(sla_id)
                if report:
                    reports.append(report)
        return reports

    async def evaluate_alerts(self) -> list[AlertNotification]:
        from engines.document.models.bam_models import AlertNotification
        notifications: list[AlertNotification] = []
        for dep in self._deployments.values():
            for rid, rule in dep.alert_rules.items():
                if rule.metric_ref and rule.metric_ref in self._metric_history:
                    history = self._metric_history[rule.metric_ref]
                    if history:
                        latest = history[-1]
                        notifications.append(AlertNotification(
                            alert_id=f"{rid}_{int(time.time())}",
                            rule_id=rid,
                            name=rule.name,
                            severity=rule.severity,
                            state=AlertState.ACTIVE,
                            message=f"Alert triggered for {rule.name}",
                            triggered_at=datetime.utcnow(),
                            metric_value=latest.value,
                        ))
        return notifications

    async def acknowledge_alert(self, alert_id: str) -> None:
        pass

    async def run_monitoring_agents(self) -> list[AgentReport]:
        from engines.document.models.bam_models import AgentReport
        reports: list[AgentReport] = []
        for dep in self._deployments.values():
            for aid, agent_def in dep.monitoring_agents.items():
                reports.append(AgentReport(
                    agent_id=aid,
                    name=agent_def.name,
                    executed_at=datetime.utcnow(),
                    status="success",
                ))
        return reports

    async def get_agent_status(self, agent_id: str) -> dict[str, Any] | None:
        return None

    async def get_dashboard_data(self, dashboard_id: str) -> dict[str, Any] | None:
        for dep in self._deployments.values():
            dash = dep.dashboards.get(dashboard_id)
            if dash is not None:
                return {
                    "dashboard_id": dash.dashboard_id,
                    "name": dash.name,
                    "widgets": [
                        {"widget_id": w.widget_id, "type": w.type, "title": w.title}
                        for w in dash.widgets
                    ],
                }
        return None

    async def get_widget_data(self, widget_id: str) -> dict[str, Any] | None:
        return None

    async def _flush_metrics(self) -> None:
        async with self._metric_lock:
            self._metric_buffer.clear()

    def _parse_window(self, window: str) -> datetime:
        now = datetime.utcnow()
        unit = window[-1]
        value = int(window[:-1])
        if unit == "h":
            return now - timedelta(hours=value)
        elif unit == "m":
            return now - timedelta(minutes=value)
        elif unit == "d":
            return now - timedelta(days=value)
        return now - timedelta(hours=1)
```

- [ ] **Step 6: Run test to verify it passes**

Run: `pytest tests/orchestration/test_bam/test_bam_engine.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add tests/orchestration/test_bam/ engines/orchestration/bam/
git commit -m "feat(bam): add BamEngine skeleton with lifecycle, load, parse, deploy, basic metrics"
```

---

### Task 10: MetricCollector and KpiEvaluator

**Files:**
- Create: `engines/orchestration/bam/collector/metric_collector.py`
- Create: `engines/orchestration/bam/collector/kpi_evaluator.py`
- Test: `tests/orchestration/test_bam/test_collector.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/orchestration/test_bam/test_collector.py
import pytest
from datetime import datetime
from engines.orchestration.bam.collector.metric_collector import MetricCollector
from engines.orchestration.bam.collector.kpi_evaluator import KpiEvaluator
from engines.document.models.bam_models import (
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/orchestration/test_bam/test_collector.py -v`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Create `engines/orchestration/bam/collector/metric_collector.py`**

```python
# engines/orchestration/bam/collector/metric_collector.py
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

from engines.document.models.bam_models import MetricValue


class MetricCollector:
    def __init__(self) -> None:
        self._history: dict[str, list[MetricValue]] = defaultdict(list)

    def record(
        self,
        metric_id: str,
        value: float,
        dimensions: dict[str, str] | None = None,
    ) -> None:
        mv = MetricValue(
            timestamp=datetime.utcnow(),
            metric_id=metric_id,
            value=value,
            dimensions=dimensions or {},
        )
        self._history[metric_id].append(mv)

    def get_history(self, metric_id: str) -> list[MetricValue]:
        return list(self._history.get(metric_id, []))

    def average(self, metric_id: str) -> float | None:
        values = self._history.get(metric_id, [])
        if not values:
            return None
        return sum(v.value for v in values) / len(values)

    def stats(self, metric_id: str) -> dict[str, Any]:
        values = self._history.get(metric_id, [])
        if not values:
            return {"count": 0, "avg": 0, "min": 0, "max": 0}
        vals = [v.value for v in values]
        return {
            "count": len(vals),
            "avg": sum(vals) / len(vals),
            "min": min(vals),
            "max": max(vals),
        }

    def clear(self, metric_id: str | None = None) -> None:
        if metric_id:
            self._history.pop(metric_id, None)
        else:
            self._history.clear()
```

- [ ] **Step 4: Create `engines/orchestration/bam/collector/kpi_evaluator.py`**

```python
# engines/orchestration/bam/collector/kpi_evaluator.py
from __future__ import annotations

from datetime import datetime

from engines.document.models.bam_models import (
    KPI, KpiResult, KpiStatus, TrendDirection,
)

from .metric_collector import MetricCollector


class KpiEvaluator:
    def __init__(self, collector: MetricCollector) -> None:
        self._collector = collector

    def evaluate(self, kpi: KPI) -> KpiResult:
        avg = self._collector.average(kpi.metric_ref) or 0.0
        if avg >= kpi.target_value:
            status = KpiStatus.ON_TRACK
        elif avg >= kpi.threshold_warning:
            status = KpiStatus.WARNING
        else:
            status = KpiStatus.CRITICAL
        return KpiResult(
            kpi_id=kpi.kpi_id,
            name=kpi.name,
            current_value=avg,
            target_value=kpi.target_value,
            status=status,
            trend=TrendDirection.STABLE,
            evaluated_at=datetime.utcnow(),
        )

    def evaluate_batch(self, kpis: list[KPI]) -> list[KpiResult]:
        return [self.evaluate(k) for k in kpis]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/orchestration/test_bam/test_collector.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add tests/orchestration/test_bam/test_collector.py engines/orchestration/bam/collector/
git commit -m "feat(bam): add MetricCollector and KpiEvaluator"
```

---

### Task 11: Metric and Alert Persistence

**Files:**
- Create: `engines/orchestration/bam/persistence/metric_repository.py`
- Create: `engines/orchestration/bam/persistence/alert_repository.py`
- Test: `tests/orchestration/test_bam/test_persistence.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/orchestration/test_bam/test_persistence.py
import pytest
from datetime import datetime
from engines.orchestration.bam.persistence.metric_repository import MetricRepository
from engines.orchestration.bam.persistence.alert_repository import AlertRepository
from engines.document.models.bam_models import (
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/orchestration/test_bam/test_persistence.py -v`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Create `engines/orchestration/bam/persistence/metric_repository.py`**

```python
# engines/orchestration/bam/persistence/metric_repository.py
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

from engines.document.models.bam_models import MetricValue


class MetricRepository:
    def __init__(self) -> None:
        self._store_impl: list[MetricValue] = []

    async def store(self, mv: MetricValue) -> None:
        self._store_impl.append(mv)

    def _store(self, mv: MetricValue) -> None:
        self._store_impl.append(mv)

    async def query(self, metric_id: str) -> list[MetricValue]:
        return [v for v in self._store_impl if v.metric_id == metric_id]

    async def query_range(
        self,
        metric_id: str,
        start: datetime,
        end: datetime,
    ) -> list[MetricValue]:
        return [
            v for v in self._store_impl
            if v.metric_id == metric_id and start <= v.timestamp <= end
        ]

    async def latest(self, metric_id: str) -> MetricValue | None:
        matches = [v for v in self._store_impl if v.metric_id == metric_id]
        return max(matches, key=lambda v: v.timestamp) if matches else None

    async def clear(self) -> None:
        self._store_impl.clear()
```

- [ ] **Step 4: Create `engines/orchestration/bam/persistence/alert_repository.py`**

```python
# engines/orchestration/bam/persistence/alert_repository.py
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
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/orchestration/test_bam/test_persistence.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add tests/orchestration/test_bam/test_persistence.py engines/orchestration/bam/persistence/
git commit -m "feat(bam): add MetricRepository and AlertRepository"
```

---

### Task 12: AlertManager

**Files:**
- Create: `engines/orchestration/bam/alerting/alert_manager.py`
- Test: `tests/orchestration/test_bam/test_alerting.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/orchestration/test_bam/test_alerting.py
import pytest
from datetime import datetime, timedelta
from engines.orchestration.bam.alerting.alert_manager import AlertManager
from engines.document.models.bam_models import (
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
    assert len(n2) == 0  # within cooldown


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/orchestration/test_bam/test_alerting.py -v`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Create `engines/orchestration/bam/alerting/alert_manager.py`**

```python
# engines/orchestration/bam/alerting/alert_manager.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/orchestration/test_bam/test_alerting.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/orchestration/test_bam/test_alerting.py engines/orchestration/bam/alerting/alert_manager.py
git commit -m "feat(bam): add AlertManager with cooldown, acknowledge, resolve"
```

---

### Task 13: CepBridge and RingBuffer

**Files:**
- Create: `engines/orchestration/bam/realtime/cep_bridge.py`
- Create: `engines/orchestration/bam/realtime/ring_buffer.py`
- Test: `tests/orchestration/test_bam/test_realtime.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/orchestration/test_bam/test_realtime.py
import pytest
from engines.orchestration.bam.realtime.ring_buffer import RingBuffer
from engines.orchestration.bam.realtime.cep_bridge import CepBridge


def test_ring_buffer_push_and_get():
    buf = RingBuffer(capacity=5)
    buf.push("a")
    buf.push("b")
    buf.push("c")
    items = buf.get_all()
    assert items == ["a", "b", "c"]


def test_ring_buffer_capacity():
    buf = RingBuffer(capacity=3)
    buf.push(1)
    buf.push(2)
    buf.push(3)
    buf.push(4)
    items = buf.get_all()
    assert items == [2, 3, 4]
    assert len(items) == 3


def test_ring_buffer_clear():
    buf = RingBuffer(capacity=10)
    buf.push("a")
    buf.push("b")
    buf.clear()
    assert buf.get_all() == []


def test_ring_buffer_empty():
    buf = RingBuffer(capacity=5)
    assert buf.get_all() == []


@pytest.mark.asyncio
async def test_cep_bridge():
    bridge = CepBridge()
    bridge.register_rule("cpu_high", {"metric": "cpu", "operator": "gt", "value": 90})
    alert = bridge.evaluate("cpu", 95.0)
    assert alert is not None
    assert alert["rule_id"] == "cpu_high"


@pytest.mark.asyncio
async def test_cep_bridge_no_match():
    bridge = CepBridge()
    bridge.register_rule("cpu_high", {"metric": "cpu", "operator": "gt", "value": 90})
    alert = bridge.evaluate("cpu", 50.0)
    assert alert is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/orchestration/test_bam/test_realtime.py -v`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Create `engines/orchestration/bam/realtime/ring_buffer.py`**

```python
# engines/orchestration/bam/realtime/ring_buffer.py
from __future__ import annotations

from typing import Any, TypeVar

T = TypeVar("T")


class RingBuffer:
    def __init__(self, capacity: int = 100000) -> None:
        self._capacity = capacity
        self._buffer: list[T] = []
        self._head = 0

    def push(self, item: T) -> None:
        if len(self._buffer) < self._capacity:
            self._buffer.append(item)
        else:
            self._buffer[self._head] = item
            self._head = (self._head + 1) % self._capacity

    def get_all(self) -> list[T]:
        if len(self._buffer) < self._capacity:
            return list(self._buffer)
        return self._buffer[self._head:] + self._buffer[:self._head]

    def clear(self) -> None:
        self._buffer.clear()
        self._head = 0

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def size(self) -> int:
        return len(self._buffer)
```

- [ ] **Step 4: Create `engines/orchestration/bam/realtime/cep_bridge.py`**

```python
# engines/orchestration/bam/realtime/cep_bridge.py
from __future__ import annotations

from typing import Any


class CepBridge:
    def __init__(self) -> None:
        self._rules: dict[str, dict[str, Any]] = {}

    def register_rule(self, rule_id: str, condition: dict[str, Any]) -> None:
        self._rules[rule_id] = condition

    def evaluate(
        self,
        metric_id: str,
        value: float,
    ) -> dict[str, Any] | None:
        for rule_id, condition in self._rules.items():
            if condition.get("metric") != metric_id:
                continue
            operator = condition.get("operator", "gt")
            threshold = condition.get("value", 0)
            if self._compare(value, operator, threshold):
                return {
                    "rule_id": rule_id,
                    "metric": metric_id,
                    "value": value,
                    "threshold": threshold,
                }
        return None

    def evaluate_batch(
        self,
        metrics: dict[str, float],
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for metric_id, value in metrics.items():
            result = self.evaluate(metric_id, value)
            if result:
                results.append(result)
        return results

    def remove_rule(self, rule_id: str) -> None:
        self._rules.pop(rule_id, None)

    def _compare(self, value: float, operator: str, threshold: float) -> bool:
        operators = {
            "gt": lambda v, t: v > t,
            "gte": lambda v, t: v >= t,
            "lt": lambda v, t: v < t,
            "lte": lambda v, t: v <= t,
            "eq": lambda v, t: v == t,
            "neq": lambda v, t: v != t,
        }
        op_func = operators.get(operator)
        if op_func is None:
            return False
        return op_func(value, threshold)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/orchestration/test_bam/test_realtime.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add tests/orchestration/test_bam/test_realtime.py engines/orchestration/bam/realtime/
git commit -m "feat(bam): add RingBuffer and CepBridge"
```

---

### Task 14: Monitoring Agents (Threshold + Predictive + Anomaly + Advisory)

**Files:**
- Create: `engines/orchestration/bam/agents/monitoring_orchestrator.py`
- Create: `engines/orchestration/bam/agents/threshold_agent.py`
- Create: `engines/orchestration/bam/agents/predictive_agent.py`
- Create: `engines/orchestration/bam/agents/anomaly_agent.py`
- Create: `engines/orchestration/bam/agents/advisory_agent.py`
- Test: `tests/orchestration/test_bam/test_agents.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/orchestration/test_bam/test_agents.py
import pytest
from datetime import datetime
from typing import Any

from engines.orchestration.bam.agents.threshold_agent import ThresholdAgent
from engines.orchestration.bam.agents.monitoring_orchestrator import (
    MonitoringOrchestrator,
)
from engines.document.models.bam_models import (
    MonitoringAgentDefinition, MonitoringAgentType,
    AgentReport, MetricValue,
)


@pytest.mark.asyncio
async def test_threshold_agent_below_threshold():
    agent = ThresholdAgent("t1", "CPU Agent", threshold=90.0)
    agent.set_value(50.0)
    report = await agent.execute()
    assert report.status == "success"
    assert len(report.findings) == 0


@pytest.mark.asyncio
async def test_threshold_agent_above_threshold():
    agent = ThresholdAgent("t1", "CPU Agent", threshold=90.0)
    agent.set_value(95.0)
    report = await agent.execute()
    assert report.status == "success"
    assert len(report.findings) > 0
    assert "95.0" in report.findings[0]


@pytest.mark.asyncio
async def test_orchestrator_run_agents():
    class MockCollector:
        def average(self, metric_id: str) -> float | None:
            return 85.0

    t_agent = ThresholdAgent("t1", "Test Agent", threshold=80.0)
    t_agent.set_value(85.0)
    t_agent_def = MonitoringAgentDefinition(
        agent_id="t1", name="Test Agent",
        input_metrics=["cpu"],
    )
    orchestrator = MonitoringOrchestrator(MockCollector())  # type: ignore
    orchestrator.register(t_agent_def, t_agent)
    reports = await orchestrator.run_all()
    assert len(reports) == 1
    assert reports[0].agent_id == "t1"


def test_orchestrator_register_and_unregister():
    class MockCollector:
        def average(self, metric_id: str) -> float | None:
            return 50.0

    agent_def = MonitoringAgentDefinition(
        agent_id="a1", name="Agent 1",
        input_metrics=["cpu"],
    )
    t_agent = ThresholdAgent("a1", "Agent 1", threshold=90.0)
    orchestrator = MonitoringOrchestrator(MockCollector())  # type: ignore
    orchestrator.register(agent_def, t_agent)
    assert orchestrator.get("a1") is not None
    orchestrator.unregister("a1")
    assert orchestrator.get("a1") is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/orchestration/test_bam/test_agents.py -v`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Create `engines/orchestration/bam/agents/monitoring_orchestrator.py`**

```python
# engines/orchestration/bam/agents/monitoring_orchestrator.py
from __future__ import annotations

from datetime import datetime
from typing import Any

from engines.document.models.bam_models import (
    AgentReport, MonitoringAgentDefinition,
)

from ..collector.metric_collector import MetricCollector


class BaseMonitoringAgent:
    def __init__(self, agent_id: str, name: str) -> None:
        self.agent_id = agent_id
        self.name = name

    async def execute(self) -> AgentReport:
        raise NotImplementedError


class MonitoringOrchestrator:
    def __init__(self, collector: MetricCollector) -> None:
        self._collector = collector
        self._agents: dict[str, BaseMonitoringAgent] = {}
        self._definitions: dict[str, MonitoringAgentDefinition] = {}

    def register(
        self,
        definition: MonitoringAgentDefinition,
        agent: BaseMonitoringAgent,
    ) -> None:
        self._definitions[definition.agent_id] = definition
        self._agents[definition.agent_id] = agent

    def unregister(self, agent_id: str) -> None:
        self._definitions.pop(agent_id, None)
        self._agents.pop(agent_id, None)

    def get(self, agent_id: str) -> BaseMonitoringAgent | None:
        return self._agents.get(agent_id)

    async def run_all(self) -> list[AgentReport]:
        reports: list[AgentReport] = []
        for agent_id, agent in self._agents.items():
            report = await agent.execute()
            reports.append(report)
        return reports

    async def run(self, agent_id: str) -> AgentReport | None:
        agent = self._agents.get(agent_id)
        if agent is None:
            return None
        return await agent.execute()
```

- [ ] **Step 4: Create `engines/orchestration/bam/agents/threshold_agent.py`**

```python
# engines/orchestration/bam/agents/threshold_agent.py
from __future__ import annotations

from datetime import datetime
from typing import Any

from engines.document.models.bam_models import AgentReport

from .monitoring_orchestrator import BaseMonitoringAgent


class ThresholdAgent(BaseMonitoringAgent):
    def __init__(
        self,
        agent_id: str,
        name: str,
        threshold: float = 90.0,
    ) -> None:
        super().__init__(agent_id, name)
        self._threshold = threshold
        self._value: float | None = None

    def set_value(self, value: float) -> None:
        self._value = value

    async def execute(self) -> AgentReport:
        findings: list[str] = []
        recommendations: list[str] = []
        status = "success"

        if self._value is not None and self._value > self._threshold:
            findings.append(
                f"Value {self._value} exceeds threshold {self._threshold}"
            )
            recommendations.append(f"Consider investigating metric above {self._threshold}")
            status = "warning"

        return AgentReport(
            agent_id=self.agent_id,
            name=self.name,
            executed_at=datetime.utcnow(),
            status=status,
            findings=findings,
            recommendations=recommendations,
            metrics={"threshold": self._threshold} if self._value is not None else {},
        )
```

- [ ] **Step 5: Create `engines/orchestration/bam/agents/predictive_agent.py`**

```python
# engines/orchestration/bam/agents/predictive_agent.py
from __future__ import annotations

from datetime import datetime
from typing import Any

from engines.document.models.bam_models import AgentReport

from .monitoring_orchestrator import BaseMonitoringAgent


class PredictiveAgent(BaseMonitoringAgent):
    def __init__(
        self,
        agent_id: str,
        name: str,
    ) -> None:
        super().__init__(agent_id, name)
        self._values: list[float] = []

    def set_values(self, values: list[float]) -> None:
        self._values = values

    async def execute(self) -> AgentReport:
        findings: list[str] = []
        recommendations: list[str] = []
        status = "success"

        if len(self._values) >= 2:
            trend = self._values[-1] - self._values[0]
            if trend > 0:
                findings.append(f"Upward trend detected: +{trend:.1f} over {len(self._values)} samples")
                recommendations.append("Investigate cause of increasing metric")
                status = "warning"
            elif trend < 0:
                findings.append(f"Downward trend: {trend:.1f} over {len(self._values)} samples")

        return AgentReport(
            agent_id=self.agent_id,
            name=self.name,
            executed_at=datetime.utcnow(),
            status=status,
            findings=findings,
            recommendations=recommendations,
            metrics={"sample_count": len(self._values)},
        )
```

- [ ] **Step 6: Create `engines/orchestration/bam/agents/anomaly_agent.py`**

```python
# engines/orchestration/bam/agents/anomaly_agent.py
from __future__ import annotations

from datetime import datetime
from typing import Any

from engines.document.models.bam_models import AgentReport

from .monitoring_orchestrator import BaseMonitoringAgent


class AnomalyAgent(BaseMonitoringAgent):
    def __init__(
        self,
        agent_id: str,
        name: str,
        stddev_multiplier: float = 2.0,
    ) -> None:
        super().__init__(agent_id, name)
        self._stddev_mult = stddev_multiplier
        self._values: list[float] = []

    def set_values(self, values: list[float]) -> None:
        self._values = values

    async def execute(self) -> AgentReport:
        findings: list[str] = []
        recommendations: list[str] = []
        status = "success"

        if len(self._values) >= 3:
            import statistics
            try:
                mean = statistics.mean(self._values)
                stdev = statistics.stdev(self._values) if len(self._values) >= 2 else 0
                threshold = stdev * self._stddev_mult
                anomalies = [v for v in self._values if abs(v - mean) > threshold]
                if anomalies:
                    findings.append(f"Detected {len(anomalies)} anomalous values (>{self._stddev_mult}σ)")
                    recommendations.append("Review anomaly detection parameters")
                    status = "warning"
            except statistics.StatisticsError:
                pass

        return AgentReport(
            agent_id=self.agent_id,
            name=self.name,
            executed_at=datetime.utcnow(),
            status=status,
            findings=findings,
            recommendations=recommendations,
            metrics={"stddev_multiplier": self._stddev_mult},
        )
```

- [ ] **Step 7: Create `engines/orchestration/bam/agents/advisory_agent.py`**

```python
# engines/orchestration/bam/agents/advisory_agent.py
from __future__ import annotations

from datetime import datetime
from typing import Any

from engines.document.models.bam_models import AgentReport

from .monitoring_orchestrator import BaseMonitoringAgent


class AdvisoryAgent(BaseMonitoringAgent):
    def __init__(
        self,
        agent_id: str,
        name: str,
    ) -> None:
        super().__init__(agent_id, name)
        self._context: dict[str, Any] = {}

    def set_context(self, context: dict[str, Any]) -> None:
        self._context = context

    async def execute(self) -> AgentReport:
        findings: list[str] = []
        recommendations: list[str] = []

        for key, value in self._context.items():
            findings.append(f"{key}: {value}")

        if self._context.get("load_avg", 0) > 80:
            recommendations.append("Consider scaling up resources")
        if self._context.get("error_rate", 0) > 5:
            recommendations.append("Investigate error sources")

        return AgentReport(
            agent_id=self.agent_id,
            name=self.name,
            executed_at=datetime.utcnow(),
            status="success",
            findings=findings,
            recommendations=recommendations,
            metrics={"context_keys": len(self._context)},
        )
```

- [ ] **Step 8: Run test to verify it passes**

Run: `pytest tests/orchestration/test_bam/test_agents.py -v`
Expected: PASS

- [ ] **Step 9: Commit**

```bash
git add tests/orchestration/test_bam/test_agents.py engines/orchestration/bam/agents/
git commit -m "feat(bam): add 4 monitoring agent types + orchestrator"
```

---

### Task 15: DashboardManager

**Files:**
- Create: `engines/orchestration/bam/dashboard/dashboard_manager.py`
- Test: `tests/orchestration/test_bam/test_dashboard.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/orchestration/test_bam/test_dashboard.py
import pytest
from datetime import datetime
from engines.orchestration.bam.dashboard.dashboard_manager import DashboardManager
from engines.document.models.bam_models import (
    Dashboard, DashboardWidget, BusinessMetric, KPI,
    MetricValue,
)


@pytest.mark.asyncio
async def test_dashboard_manager_register():
    mgr = DashboardManager()
    dash = Dashboard(
        dashboard_id="d1", name="Operations",
        widgets=[
            DashboardWidget(widget_id="w1", type="gauge", title="CPU", data_source="metric:cpu"),
            DashboardWidget(widget_id="w2", type="chart", title="Latency", data_source="metric:latency"),
        ],
    )
    mgr.register(dash)
    assert mgr.get("d1") is not None
    assert len(mgr.list_all()) == 1


@pytest.mark.asyncio
async def test_dashboard_manager_resolve_widget_data():
    mgr = DashboardManager()
    dash = Dashboard(
        dashboard_id="d1", name="Ops",
        widgets=[
            DashboardWidget(widget_id="w1", type="gauge", title="CPU", data_source="metric:cpu"),
        ],
    )
    mgr.register(dash)

    mgr.set_metric_value("cpu", 42.5)
    data = mgr.resolve_widget("w1")
    assert data is not None
    assert data["value"] == 42.5
    assert data["widget_id"] == "w1"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/orchestration/test_bam/test_dashboard.py -v`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Create `engines/orchestration/bam/dashboard/dashboard_manager.py`**

```python
# engines/orchestration/bam/dashboard/dashboard_manager.py
from __future__ import annotations

from datetime import datetime
from typing import Any

from engines.document.models.bam_models import Dashboard


class DashboardManager:
    def __init__(self) -> None:
        self._dashboards: dict[str, Dashboard] = {}
        self._metric_values: dict[str, float] = {}

    def register(self, dashboard: Dashboard) -> None:
        self._dashboards[dashboard.dashboard_id] = dashboard

    def unregister(self, dashboard_id: str) -> None:
        self._dashboards.pop(dashboard_id, None)

    def get(self, dashboard_id: str) -> Dashboard | None:
        return self._dashboards.get(dashboard_id)

    def list_all(self) -> list[Dashboard]:
        return list(self._dashboards.values())

    def set_metric_value(self, metric_id: str, value: float) -> None:
        self._metric_values[metric_id] = value

    def resolve_widget(self, widget_id: str) -> dict[str, Any] | None:
        for dash in self._dashboards.values():
            for widget in dash.widgets:
                if widget.widget_id == widget_id:
                    data_source = widget.data_source
                    value = None
                    if data_source.startswith("metric:"):
                        metric_id = data_source.split(":", 1)[1]
                        value = self._metric_values.get(metric_id)
                    return {
                        "widget_id": widget.widget_id,
                        "type": widget.type,
                        "title": widget.title,
                        "value": value,
                        "data_source": data_source,
                    }
        return None

    def resolve_dashboard(self, dashboard_id: str) -> dict[str, Any] | None:
        dash = self._dashboards.get(dashboard_id)
        if dash is None:
            return None
        return {
            "dashboard_id": dash.dashboard_id,
            "name": dash.name,
            "widgets": [
                self.resolve_widget(w.widget_id) for w in dash.widgets
            ],
        }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/orchestration/test_bam/test_dashboard.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/orchestration/test_bam/test_dashboard.py engines/orchestration/bam/dashboard/
git commit -m "feat(bam): add DashboardManager"
```

---

### Task 16: SlaTracker

**Files:**
- Create: `engines/orchestration/bam/slas/sla_tracker.py`
- Test: `tests/orchestration/test_bam/test_slas.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/orchestration/test_bam/test_slas.py
import pytest
from datetime import datetime, timedelta
from engines.orchestration.bam.slas.sla_tracker import SlaTracker
from engines.document.models.bam_models import (
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/orchestration/test_bam/test_slas.py -v`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Create `engines/orchestration/bam/slas/sla_tracker.py`**

```python
# engines/orchestration/bam/slas/sla_tracker.py
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from engines.document.models.bam_models import (
    MetricValue, SlaComplianceReport, SlaDefinition,
)


class SlaTracker:
    def __init__(self) -> None:
        self._slas: dict[str, SlaDefinition] = {}
        self._evaluations: dict[str, list[float]] = {}

    def register(self, sla: SlaDefinition) -> None:
        self._slas[sla.sla_id] = sla
        self._evaluations.setdefault(sla.sla_id, [])

    def unregister(self, sla_id: str) -> None:
        self._slas.pop(sla_id, None)
        self._evaluations.pop(sla_id, None)

    def record_evaluation(self, sla_id: str, value: float) -> None:
        if sla_id in self._evaluations:
            self._evaluations[sla_id].append(value)

    def get_report(self, sla_id: str) -> SlaComplianceReport | None:
        sla = self._slas.get(sla_id)
        if sla is None:
            return None
        values = self._evaluations.get(sla_id, [])
        if not values:
            return SlaComplianceReport(
                sla_id=sla_id,
                name=sla.name,
                compliance_rate=1.0,
                breach_count=0,
                total_evaluations=0,
                period_start=datetime.utcnow() - timedelta(days=30),
                period_end=datetime.utcnow(),
            )
        threshold = self._parse_condition_threshold(sla.condition)
        breaches = sum(1 for v in values if v > threshold) if threshold is not None else 0
        total = len(values)
        rate = (total - breaches) / total if total > 0 else 1.0
        return SlaComplianceReport(
            sla_id=sla_id,
            name=sla.name,
            compliance_rate=rate,
            breach_count=breaches,
            total_evaluations=total,
            period_start=datetime.utcnow() - timedelta(days=30),
            period_end=datetime.utcnow(),
        )

    def get_all_reports(self) -> list[SlaComplianceReport]:
        return [r for sid in self._slas if (r := self.get_report(sid)) is not None]

    def _parse_condition_threshold(self, condition: str) -> float | None:
        if " < " in condition:
            _, val = condition.rsplit(" < ", 1)
            try:
                return float(val.strip())
            except ValueError:
                return None
        if " > " in condition:
            _, val = condition.rsplit(" > ", 1)
            try:
                return float(val.strip())
            except ValueError:
                return None
        if " <= " in condition:
            _, val = condition.rsplit(" <= ", 1)
            try:
                return float(val.strip())
            except ValueError:
                return None
        if " >= " in condition:
            _, val = condition.rsplit(" >= ", 1)
            try:
                return float(val.strip())
            except ValueError:
                return None
        return None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/orchestration/test_bam/test_slas.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/orchestration/test_bam/test_slas.py engines/orchestration/bam/slas/
git commit -m "feat(bam): add SlaTracker with compliance computation"
```

---

### Task 17: Integration with OrchestrationEngine

**Files:**
- Modify: `engines/orchestration/bam/engine.py` (update to accept OrchestrationEngine ref)
- Test: `tests/orchestration/test_bam/test_orchestration_integration.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/orchestration/test_bam/test_orchestration_integration.py
import pytest
from engines.orchestration.core.engine import OrchestrationEngine, EngineConfig
from engines.orchestration.bam.engine import BamEngine


@pytest.mark.asyncio
async def test_orchestration_has_bam_flag():
    config = EngineConfig()
    assert hasattr(config, "enable_bam")


@pytest.mark.asyncio
async def test_bam_engine_receives_orchestration_ref():
    config = EngineConfig(enable_bam=True, enable_persistence=False)
    engine = OrchestrationEngine(config)
    await engine.start()
    assert engine._bam_engine is not None
    assert isinstance(engine._bam_engine, BamEngine)
    await engine.stop()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/orchestration/test_bam/test_orchestration_integration.py -v`
Expected: FAIL — `EngineConfig` lacks `enable_bam`, `OrchestrationEngine` lacks `_bam_engine`

- [ ] **Step 3: Add `enable_bam` to EngineConfig**

In `engines/orchestration/core/engine.py`, add to `EngineConfig`:
```python
enable_bam: bool = True
bam_metric_buffer_size: int = 100000
bam_persistence_interval: int = 60
bam_enable_predictive: bool = True
```

- [ ] **Step 4: Add BAM engine initialization to OrchestrationEngine**

In `engines/orchestration/core/engine.py`, in `__init__` (after `self._config = config`):
```python
from ..bam.engine import BamEngine
self._bam_engine: BamEngine | None = None
if self._config.enable_bam:
    self._bam_engine = BamEngine(engine=self)
```

In `start()`:
```python
if self._bam_engine:
    await self._bam_engine.start()
```

In `stop()`:
```python
if self._bam_engine:
    await self._bam_engine.stop()
```

In `_detect_definition_type()`:
```python
if name.endswith(".bam.json") or name.endswith(".bam.yaml") or name.endswith(".bam.yml"):
    return "bam"
```

In `_get_handler()`:
```python
"bam": "BamEngine",
```

- [ ] **Step 5: Enable handler dispatch for BAM**

In `_get_handler()` after the `engine_handlers` dict:
```python
"bam": self._bam_engine,
```

- [ ] **Step 6: Run test to verify it passes**

Run: `pytest tests/orchestration/test_bam/test_orchestration_integration.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add tests/orchestration/test_bam/test_orchestration_integration.py engines/orchestration/core/engine.py
git commit -m "feat(bam): integrate BamEngine into OrchestrationEngine"
```

---

### Task 18: Run All BAM Tests

- [ ] **Step 1: Run all BAM tests**

Run: `python3 -m pytest tests/document/test_bam_media_types.py tests/document/test_bam_models.py tests/document/test_bam_json_parser.py tests/document/test_bam_yaml_parser.py tests/document/test_bam_json_writer.py tests/document/test_bam_yaml_writer.py tests/document/test_bam_roundtrip.py tests/orchestration/test_bam/ -v`

Expected: All PASS

- [ ] **Step 2: Commit if any remaining**

```bash
git add -A && git commit -m "test(bam): verify all BAM tests pass"
```
