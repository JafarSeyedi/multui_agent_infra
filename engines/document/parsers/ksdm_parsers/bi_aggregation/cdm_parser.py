from __future__ import annotations

from collections.abc import AsyncIterator

import json
from pathlib import Path
from typing import Any

from engines.document.parsers.base import BaseDocumentParser, ParseOptions, ParseResult
from engines.document.models.media_types import MEDIA_TYPES
from engines.document.models.ksdm_models import (
    UnifiedBiAggregationDocument,
    AggregationSource,
    Dimension,
    DimensionAttribute,
    Measure,
    AggregationRelationship,
)


class CdmParser(BaseDocumentParser):
    name = "cdm_bi"
    supported_extensions = (".cdm.json",)

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
        if isinstance(source, str) and source.endswith(".cdm.json"):
            return True
        try:
            data = json.loads(Path(source).read_bytes()[:4096])
            return "entities" in data or "definitions" in data
        except Exception:
            return False

    def _parse_model(self, raw: dict, name: str) -> UnifiedBiAggregationDocument:
        model_name = raw.get("name", raw.get("ModelName", name))

        sources: list[AggregationSource] = []
        dimensions: list[Dimension] = []
        measures: list[Measure] = []
        relationships: list[AggregationRelationship] = []

        entities = raw.get("entities", [])
        for entity in entities:
            ename = entity.get("name", "")
            sources.append(AggregationSource(
                name=ename,
                source_type="entity",
                description=entity.get("description", ""),
            ))

            attrs = [
                DimensionAttribute(
                    name=a.get("name", ""),
                    source_column=a.get("name", ""),
                    data_type=a.get("dataType", a.get("dataTypeName")),
                )
                for a in entity.get("attributes", [])
            ]

            if attrs:
                dimensions.append(Dimension(
                    name=ename,
                    source_table=ename,
                    dimension_type="standard",
                    attributes=attrs,
                ))

        for rel in raw.get("relationships", []):
            relationships.append(AggregationRelationship(
                name=rel.get("name", ""),
                source_table=rel.get("fromEntity", "").split("/")[-1],
                target_table=rel.get("toEntity", "").split("/")[-1] if "/" in rel.get("toEntity", "") else rel.get("toEntity", ""),
                source_column=rel.get("fromAttribute", ""),
                target_column=rel.get("toAttribute", ""),
            ))

        return UnifiedBiAggregationDocument(
            name=model_name,
            description=raw.get("description"),
            sources=sources,
            dimensions=dimensions,
            measures=measures,
            relationships=relationships,
            title=name,
            document_id=name,
            media_type=MEDIA_TYPES["cdm_json"],
        )
