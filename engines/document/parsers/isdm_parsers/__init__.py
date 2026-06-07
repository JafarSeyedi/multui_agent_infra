from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import yaml

from ...models.isdm_models import ISDMDocument, Metric, MetricType, TimeGranularity, BIAggregatorModel, BIAggregation
from ...models.media_types import MEDIA_TYPES, MediaType
from ...models.standard import DocumentStandard
from ..base import BaseDocumentParser, ParseOptions


class ISDMJSONParser(BaseDocumentParser):
    name = "isdm_json"
    supported_extensions = [".isdm.json", ".isfm.json"]

    async def parse_bytes(
        self, data: bytes, document_id: str, source_name: str,
        metadata: dict[str, Any] | None = None,
        options: ParseOptions | None = None,
    ) -> ISDMDocument:
        raw = json.loads(data.decode("utf-8"))
        return self._decode(raw, document_id)

    async def parse_path(
        self, path: str | Path, document_id: str,
        metadata: dict[str, Any] | None = None,
        options: ParseOptions | None = None,
    ) -> ISDMDocument:
        p = Path(path)
        return await self.parse_bytes(p.read_bytes(), document_id, p.name)

    async def parse_stream(self, stream, document_id: str,
                           source_name: str, metadata=None, options=None) -> ISDMDocument:
        data = b"".join([chunk async for chunk in stream])
        return await self.parse_bytes(data, document_id, source_name)

    def _decode(self, raw: dict[str, Any], document_id: str) -> ISDMDocument:
        from datetime import datetime
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
        return ISDMDocument(
            document_id=document_id,
            kind=DocumentStandard.ISDM,
            start_time=datetime.fromisoformat(raw["start_time"]) if isinstance(raw.get("start_time"), str) else None,
            end_time=datetime.fromisoformat(raw["end_time"]) if isinstance(raw.get("end_time"), str) else None,
            granularity=TimeGranularity(raw["granularity"]) if raw.get("granularity") else TimeGranularity.DAY,
            dimensions=raw.get("dimensions", []),
            metrics=metrics,
            data_rows=raw.get("data_rows", []),
            source_info=source_info,
            media_type=cast(MediaType, MEDIA_TYPES.get("json")),
        )


class ISDMYAMLParser(BaseDocumentParser):
    name = "isdm_yaml"
    supported_extensions = [".isdm.yaml", ".isfm.yaml"]

    async def parse_bytes(
        self, data: bytes, document_id: str, source_name: str,
        metadata: dict[str, Any] | None = None,
        options: ParseOptions | None = None,
    ) -> ISDMDocument:
        raw = yaml.safe_load(data.decode("utf-8"))
        return ISDMJSONParser()._decode(raw, document_id)

    async def parse_path(
        self, path: str | Path, document_id: str,
        metadata: dict[str, Any] | None = None,
        options: ParseOptions | None = None,
    ) -> ISDMDocument:
        p = Path(path)
        return await self.parse_bytes(p.read_bytes(), document_id, p.name)

    async def parse_stream(self, stream, document_id: str,
                           source_name: str, metadata=None, options=None) -> ISDMDocument:
        data = b"".join([chunk async for chunk in stream])
        return await self.parse_bytes(data, document_id, source_name)


class BIAggregatorJSONParser(BaseDocumentParser):
    name = "bi_aggregator_json"
    supported_extensions = [".bi.json"]

    async def parse_bytes(
        self, data: bytes, document_id: str, source_name: str,
        metadata: dict[str, Any] | None = None,
        options: ParseOptions | None = None,
    ) -> BIAggregatorModel:
        raw = json.loads(data.decode("utf-8"))
        aggs = []
        for a in raw.get("aggregations", []):
            aggs.append(BIAggregation(
                name=a["name"],
                metric=a["metric"],
                window=a["window"],
                output=a["output"],
                dimensions=a.get("dimensions", []),
                output_config=a.get("output_config"),
            ))
        return BIAggregatorModel(
            document_id=document_id,
            title=raw.get("title", ""),
            version=str(raw.get("version", "1.0")),
            schedule=str(raw.get("schedule", "")),
            sources=raw.get("sources", []),
            aggregations=aggs,
            targets=raw.get("targets", []),
            media_type=cast(MediaType, MEDIA_TYPES.get("json")),
        )

    async def parse_path(
        self, path: str | Path, document_id: str,
        metadata: dict[str, Any] | None = None,
        options: ParseOptions | None = None,
    ) -> BIAggregatorModel:
        p = Path(path)
        return await self.parse_bytes(p.read_bytes(), document_id, p.name)

    async def parse_stream(self, stream, document_id: str,
                           source_name: str, metadata=None, options=None) -> BIAggregatorModel:
        data = b"".join([chunk async for chunk in stream])
        return await self.parse_bytes(data, document_id, source_name)


class BIAggregatorYAMLParser(BaseDocumentParser):
    name = "bi_aggregator_yaml"
    supported_extensions = [".bi.yaml"]

    async def parse_bytes(
        self, data: bytes, document_id: str, source_name: str,
        metadata: dict[str, Any] | None = None,
        options: ParseOptions | None = None,
    ) -> BIAggregatorModel:
        raw = yaml.safe_load(data.decode("utf-8"))
        return await BIAggregatorJSONParser().parse_bytes(
            json.dumps(raw).encode("utf-8"), document_id, source_name
        )

    async def parse_path(
        self, path: str | Path, document_id: str,
        metadata: dict[str, Any] | None = None,
        options: ParseOptions | None = None,
    ) -> BIAggregatorModel:
        p = Path(path)
        return await self.parse_bytes(p.read_bytes(), document_id, p.name)

    async def parse_stream(self, stream, document_id: str,
                           source_name: str, metadata=None, options=None) -> BIAggregatorModel:
        data = b"".join([chunk async for chunk in stream])
        return await self.parse_bytes(data, document_id, source_name)
