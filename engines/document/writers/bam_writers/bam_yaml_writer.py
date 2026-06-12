from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from ...models.base import BaseDocument
from ...models.bam_models import MonitoringDashboardDocument
from ..base import BaseDocumentWriter


_yaml: Any = None
try:
    import yaml as _yaml
except ImportError:
    pass


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
                mid: m.model_dump(mode="json", exclude_none=True)
                for mid, m in doc.metrics.items()
            }
        if doc.kpis:
            result["kpis"] = {
                kid: k.model_dump(mode="json", exclude_none=True)
                for kid, k in doc.kpis.items()
            }
        if doc.slas:
            result["slas"] = {
                sid: s.model_dump(mode="json", exclude_none=True)
                for sid, s in doc.slas.items()
            }
        if doc.alert_rules:
            result["alert_rules"] = {
                rid: r.model_dump(mode="json", exclude_none=True)
                for rid, r in doc.alert_rules.items()
            }
        if doc.dashboards:
            result["dashboards"] = {
                did: d.model_dump(mode="json", exclude_none=True)
                for did, d in doc.dashboards.items()
            }
        if doc.monitoring_agents:
            result["monitoring_agents"] = {
                aid: a.model_dump(mode="json", exclude_none=True)
                for aid, a in doc.monitoring_agents.items()
            }
        if doc.metadata:
            result["metadata"] = doc.metadata
        return result
