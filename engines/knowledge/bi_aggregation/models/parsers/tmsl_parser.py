from __future__ import annotations

from collections.abc import AsyncIterator

import json
from pathlib import Path
from typing import Any

from engines.document.parsers.base import BaseDocumentParser, ParseOptions, ParseResult
from engines.document.models.media_types import MEDIA_TYPES
from engines.knowledge.bi_aggregation.models import (
    UnifiedBiAggregationDocument,
    AggregationSource,
    Dimension,
    DimensionAttribute,
    DimensionHierarchy,
    DimensionLevel,
    Measure,
    AggregationRelationship,
)


class TmslParser(BaseDocumentParser):
    name = "tmsl_bi"
    supported_extensions = (".bim",)

    async def parse_bytes(self, data: bytes, document_id: str, source_name: str, metadata: dict[str, Any] | None = None, options: ParseOptions | None = None) -> UnifiedBiAggregationDocument:
        raw = json.loads(data)
        return self._parse_model(raw, source_name)

    async def parse_path(self, path: str | Path, document_id: str, metadata: dict[str, Any] | None = None, options: ParseOptions | None = None) -> UnifiedBiAggregationDocument:
        p = Path(path)
        data = p.read_bytes()
        return await self.parse_bytes(data, document_id, p.name, metadata, options)

    async def parse_stream(self, stream: AsyncIterator[bytes], document_id: str, source_name: str, metadata: dict[str, Any] | None = None, options: ParseOptions | None = None) -> UnifiedBiAggregationDocument:
        chunks = [chunk async for chunk in stream]
        data = b"".join(chunks)
        return await self.parse_bytes(data, document_id, source_name, metadata, options)

    def can_parse(self, source: str | Path) -> bool:
        if isinstance(source, str) and source.endswith(".bim"):
            return True
        try:
            data = json.loads(Path(source).read_bytes()[:4096])
            return "model" in data
        except Exception:
            return False

    def _parse_model(self, raw: dict, name: str) -> UnifiedBiAggregationDocument:
        model = raw.get("model", raw)
        model_name = model.get("name", name)

        sources: list[AggregationSource] = []
        dimensions: list[Dimension] = []
        measures: list[Measure] = []
        relationships: list[AggregationRelationship] = []

        tables = model.get("tables", [])
        for table in tables:
            tname = table.get("name", "")
            sources.append(AggregationSource(
                name=tname,
                source_type="table",
                description=table.get("description", ""),
            ))

            columns = table.get("columns", [])
            attrs = [
                DimensionAttribute(
                    name=c.get("name", ""),
                    source_column=c.get("sourceColumn", c.get("name", "")),
                    data_type=c.get("dataType"),
                )
                for c in columns
            ]

            if attrs:
                dimensions.append(Dimension(
                    name=tname,
                    source_table=tname,
                    dimension_type="standard",
                    attributes=attrs,
                ))

            table_measures = table.get("measures", [])
            for m in table_measures:
                measures.append(Measure(
                    name=m.get("name", ""),
                    source_column=m.get("expression", ""),
                    aggregator="custom",
                    format_string=m.get("formatString"),
                ))

        for rel in model.get("relationships", []):
            relationships.append(AggregationRelationship(
                name=rel.get("name", ""),
                source_table=rel.get("fromTable", ""),
                target_table=rel.get("toTable", ""),
                source_column=rel.get("fromColumn", ""),
                target_column=rel.get("toColumn", ""),
                cardinality=rel.get("cardinality", "many_to_one"),
            ))

        return UnifiedBiAggregationDocument(
            name=model_name,
            description=model.get("description"),
            sources=sources,
            dimensions=dimensions,
            measures=measures,
            relationships=relationships,
            title=name,
            document_id=name,
            media_type=MEDIA_TYPES["tmsl_json"],
        )
