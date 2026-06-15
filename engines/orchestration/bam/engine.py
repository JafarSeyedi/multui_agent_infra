from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)

from .models.bam_models import (
    AgentReport, AlertNotification, AlertState, KpiResult,
    KpiStatus, MetricValue, MonitoringDashboardDocument,
    SlaComplianceReport, TrendDirection,
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
        parser: Any
        p = Path(path)
        if p.suffix == ".json" or ".bam.json" in str(p):
            from .parsers.bam_json_parser import BamJsonParser
            parser = BamJsonParser()
        elif ".bam.yaml" in str(p) or ".bam.yml" in str(p):
            from .parsers.bam_yaml_parser import BamYamlParser
            parser = BamYamlParser()
        else:
            raise ValueError(f"Unsupported BAM file: {path}")
        doc = await parser.parse_path(p)
        assert isinstance(doc, MonitoringDashboardDocument)
        return doc

    async def parse(self, content: str, fmt: str) -> MonitoringDashboardDocument:
        parser: Any
        if fmt == "json":
            from .parsers.bam_json_parser import BamJsonParser
            parser = BamJsonParser()
            doc = await parser.parse_bytes(content.encode("utf-8"), "inline", "inline.bam.json")
        elif fmt == "yaml":
            from .parsers.bam_yaml_parser import BamYamlParser
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
        reports: list[SlaComplianceReport] = []
        for dep in self._deployments.values():
            for sla_id in dep.slas:
                report = await self.track_sla_compliance(sla_id)
                if report:
                    reports.append(report)
        return reports

    async def evaluate_alerts(self) -> list[AlertNotification]:
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

    async def execute_instance(self, instance: Any, definition: Any) -> None:
        if not self._running:
            await self.start()
        doc = await self.parse(
            definition.definition_xml,
            "json" if ".json" in definition.resource_name else "yaml",
        )
        doc.document_id = instance.id
        await self.deploy(doc)

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
