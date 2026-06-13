from __future__ import annotations

from collections.abc import AsyncIterator

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from engines.document.parsers.base import BaseDocumentParser, ParseOptions, ParseResult
from engines.document.models.media_types import MEDIA_TYPES
from engines.knowledge.models.ksdm_models import (
    UnifiedBiAggregationDocument,
    AggregationSource,
    Dimension,
    DimensionAttribute,
    DimensionHierarchy,
    DimensionLevel,
    Measure,
    AggregationRelationship,
)


class CognosFmfParser(BaseDocumentParser):
    name = "cognos_fmf_bi"
    supported_extensions = (".fmf.xml",)

    async def parse_bytes(self, data: bytes, document_id: str, source_name: str, metadata: dict[str, Any] | None = None, options: ParseOptions | None = None) -> UnifiedBiAggregationDocument:
        root = ET.fromstring(data)
        return self._parse_xml(root, source_name)

    async def parse_path(self, path: str | Path, document_id: str, metadata: dict[str, Any] | None = None, options: ParseOptions | None = None) -> UnifiedBiAggregationDocument:
        p = Path(path)
        data = p.read_bytes()
        return await self.parse_bytes(data, document_id, p.name, metadata, options)

    async def parse_stream(self, stream: AsyncIterator[bytes], document_id: str, source_name: str, metadata: dict[str, Any] | None = None, options: ParseOptions | None = None) -> UnifiedBiAggregationDocument:
        chunks = [chunk async for chunk in stream]
        data = b"".join(chunks)
        return await self.parse_bytes(data, document_id, source_name, metadata, options)

    def can_parse(self, source: str | Path) -> bool:
        if isinstance(source, str) and source.endswith((".fmf.xml", ".fmf")):
            return True
        try:
            data = Path(source).read_bytes()[:300]
            return b"FrameworkManager" in data or b"cognos" in data.lower() or b"fmf" in data.lower()
        except Exception:
            return False

    def _parse_xml(self, root: ET.Element, name: str) -> UnifiedBiAggregationDocument:
        doc_name = root.get("name", root.get("modelName", name))

        sources: list[AggregationSource] = []
        dimensions: list[Dimension] = []
        measures: list[Measure] = []
        relationships: list[AggregationRelationship] = []

        for subj in root.findall(".//QuerySubject") + root.findall(".//querySubject") + root.findall(".//subject"):
            sname = subj.get("name", "")
            sources.append(AggregationSource(
                name=sname,
                source_type="query_subject",
                description=subj.get("description", ""),
            ))

            items = subj.findall(".//QueryItem") + subj.findall(".//queryItem") + subj.findall(".//item")
            attrs: list[DimensionAttribute] = []
            subj_measures: list[Measure] = []

            for item in items:
                iname = item.get("name", "")
                iagg = item.get("aggregation", item.get("rollup", "")).lower()
                if iagg in ("sum", "count", "avg", "min", "max", "distinct_count"):
                    subj_measures.append(Measure(
                        name=iname,
                        source_column=item.get("expression", item.get("source", iname)),
                        aggregator=iagg,
                    ))
                elif iname:
                    attrs.append(DimensionAttribute(
                        name=iname,
                        source_column=iname,
                        data_type=item.get("dataType", item.get("type")),
                    ))

            if attrs:
                dimensions.append(Dimension(
                    name=sname,
                    source_table=sname,
                    dimension_type="standard",
                    attributes=attrs,
                ))
            measures.extend(subj_measures)

        for rel in root.findall(".//Relationship") + root.findall(".//relationship"):
            relationships.append(AggregationRelationship(
                name=rel.get("name", ""),
                source_table=rel.get("source", rel.get("fromSubject", "")),
                target_table=rel.get("target", rel.get("toSubject", "")),
                source_column=rel.get("sourceCardinality", rel.get("from", "")),
                target_column=rel.get("targetCardinality", rel.get("to", "")),
            ))

        return UnifiedBiAggregationDocument(
            name=doc_name,
            description=f"IBM Cognos Framework Manager: {doc_name}",
            sources=sources,
            dimensions=dimensions,
            measures=measures,
            relationships=relationships,
            title=name,
            document_id=name,
            media_type=MEDIA_TYPES["cognos_fmf_xml"],
        )
