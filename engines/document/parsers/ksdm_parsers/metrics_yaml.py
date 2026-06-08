from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from engines.document.models.ksdm_models import KSDMMetricsDocument
from ..base import BaseDocumentParser, ParseOptions
from .metrics_json import KSDMMetricsJSONParser


class KSDMMetricsYAMLParser(BaseDocumentParser):
    name = "ksdm_metrics_yaml"
    supported_extensions = [".ksdm_metrics.yaml", ".isfm.yaml"]

    async def parse_bytes(
        self, data: bytes, document_id: str, source_name: str,
        metadata: dict[str, Any] | None = None,
        options: ParseOptions | None = None,
    ) -> KSDMMetricsDocument:
        raw = yaml.safe_load(data.decode("utf-8"))
        return KSDMMetricsJSONParser()._decode(raw, document_id)

    async def parse_path(
        self, path: str | Path, document_id: str,
        metadata: dict[str, Any] | None = None,
        options: ParseOptions | None = None,
    ) -> KSDMMetricsDocument:
        p = Path(path)
        return await self.parse_bytes(p.read_bytes(), document_id, p.name)

    async def parse_stream(self, stream, document_id: str,
                           source_name: str, metadata=None, options=None) -> KSDMMetricsDocument:
        data = b"".join([chunk async for chunk in stream])
        return await self.parse_bytes(data, document_id, source_name)
