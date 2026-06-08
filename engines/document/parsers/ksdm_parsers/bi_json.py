from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from engines.document.models.ksdm_models import (
    BIAggregation,
    BIAggregatorModel,
)
from engines.document.models.media_types import MediaType, MEDIA_TYPES
from ..base import BaseDocumentParser, ParseOptions


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
