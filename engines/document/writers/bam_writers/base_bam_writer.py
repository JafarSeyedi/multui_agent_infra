from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from ...models.base import BaseDocument
from ...models.bam_models import MonitoringDashboardDocument
from ..base import BaseDocumentWriter


class BaseBAMWriter(BaseDocumentWriter):
    media_type = ""
    supported_extensions: tuple[str, ...] = ()

    async def write(self, document: BaseDocument) -> bytes:
        assert isinstance(document, MonitoringDashboardDocument)
        raw = self._to_dict(document)
        return self._serialize(raw)

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
        return [self.media_type] if self.media_type else []

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    def _serialize(self, raw: dict[str, Any]) -> bytes:
        raise NotImplementedError

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
