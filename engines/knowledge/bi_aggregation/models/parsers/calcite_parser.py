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
    Measure,
)


class CalciteParser(BaseDocumentParser):
    name = "calcite_bi"
    supported_extensions = (".calcite.json", ".model.json")

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
        if isinstance(source, str) and (source.endswith((".calcite.json", ".model.json"))):
            return True
        try:
            data = json.loads(Path(source).read_bytes()[:4096])
            return "schemas" in data or "defaultSchema" in data
        except Exception:
            return False

    def _parse_model(self, raw: dict, name: str) -> UnifiedBiAggregationDocument:
        sources: list[AggregationSource] = []
        dimensions: list[Dimension] = []
        measures: list[Measure] = []

        default_schema = raw.get("defaultSchema", "")
        schemas = raw.get("schemas", [])
        for schema in schemas:
            schema_name = schema.get("name", default_schema or name)
            for tbl in schema.get("tables", []):
                tname = tbl.get("name", "")
                sources.append(AggregationSource(
                    name=tname,
                    source_type=tbl.get("type", "view"),
                    description=f"Calcite table in schema {schema_name}: {tname}",
                ))

                columns = tbl.get("columns", tbl.get("operand", {}).get("columns", []))
                attrs = [
                    DimensionAttribute(
                        name=c.get("name", ""),
                        source_column=c.get("name", ""),
                        data_type=c.get("type", c.get("dataType")),
                    )
                    for c in columns
                ]
                if attrs:
                    dimensions.append(Dimension(
                        name=tname,
                        source_table=schema_name,
                        dimension_type="standard",
                        attributes=attrs,
                    ))

        # Calcite models may define views with SQL — extract measure hints
        for schema in schemas:
            for tbl in schema.get("tables", []):
                sql = tbl.get("sql", tbl.get("operand", {}).get("sql", ""))
                if sql and ("SUM" in sql or "COUNT" in sql or "AVG" in sql):
                    measures.append(Measure(
                        name=f"{tbl.get('name', 'view')}_aggregation",
                        source_column=sql,
                        aggregator="custom",
                    ))

        return UnifiedBiAggregationDocument(
            name=default_schema or name,
            description=f"Apache Calcite model: {default_schema or name}",
            sources=sources,
            dimensions=dimensions,
            measures=measures,
            title=name,
            document_id=name,
            media_type=MEDIA_TYPES["calcite_json"],
        )
