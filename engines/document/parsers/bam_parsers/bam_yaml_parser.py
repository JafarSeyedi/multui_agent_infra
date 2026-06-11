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
    name = "bam_yaml"
    supported_extensions = (".bam.yaml", ".bam.yml")

    async def parse_bytes(
        self,
        data: bytes,
        document_id: str,
        source_name: str = "",
        metadata: dict[str, Any] | None = None,
        options: Any | None = None,
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
        options: Any | None = None,
    ) -> BaseDocument:
        p = Path(path)
        data = p.read_bytes()
        return await self.parse_bytes(data, document_id or p.stem, str(p), metadata, options)

    async def parse_stream(
        self,
        stream: AsyncIterator[bytes],
        document_id: str,
        source_name: str = "",
        metadata: dict[str, Any] | None = None,
        options: Any | None = None,
    ) -> BaseDocument:
        chunks = [chunk async for chunk in stream]
        data = b"".join(chunks)
        return await self.parse_bytes(data, document_id, source_name, metadata, options)

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
