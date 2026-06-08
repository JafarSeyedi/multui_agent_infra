from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from engines.document.models.ksdm_models import (
    KSDMMetricsDocument,
    Metric,
    MetricType,
    TimeGranularity,
)
from engines.document.models.media_types import MediaType, MEDIA_TYPES
from ..base import BaseDocumentParser, ParseOptions


class KSDMMetricsJSONParser(BaseDocumentParser):
    name = "ksdm_metrics_json"
    supported_extensions = [".ksdm_metrics.json", ".isfm.json"]

    async def parse_bytes(
        self, data: bytes, document_id: str, source_name: str,
        metadata: dict[str, Any] | None = None,
        options: ParseOptions | None = None,
    ) -> KSDMMetricsDocument:
        raw = json.loads(data.decode("utf-8"))
        return self._decode(raw, document_id)

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

    def _decode(self, raw: dict[str, Any], document_id: str) -> KSDMMetricsDocument:
        metrics_data = raw.get("metrics", [])
        metrics = []
        for m in metrics_data:
            metric_type = MetricType.GAUGE if m.get("type") == "gauge" else MetricType.COUNTER
            ts = datetime.fromisoformat(m["timestamp"]) if isinstance(m.get("timestamp"), str) else None
            metrics.append(Metric(
                name=m["name"],
                type=metric_type,
                value=m["value"],
                labels=m.get("labels"),
                timestamp=ts,
                buckets=m.get("buckets"),
                bucket_counts=m.get("bucket_counts"),
            ))
        source_info = raw.get("source_info", {})
        if not isinstance(source_info, dict):
            source_info = {}
        return KSDMMetricsDocument(
            document_id=document_id,
            kind=document_id,  # will be overridden by DocumentStandard.KSDM
            start_time=datetime.fromisoformat(raw["start_time"]) if isinstance(raw.get("start_time"), str) else None,
            end_time=datetime.fromisoformat(raw["end_time"]) if isinstance(raw.get("end_time"), str) else None,
            granularity=TimeGranularity(raw["granularity"]) if raw.get("granularity") else TimeGranularity.DAY,
            dimensions=raw.get("dimensions", []),
            metrics=metrics,
            data_rows=raw.get("data_rows", []),
            source_info=source_info,
            media_type=cast(MediaType, MEDIA_TYPES.get("json")),
        )
