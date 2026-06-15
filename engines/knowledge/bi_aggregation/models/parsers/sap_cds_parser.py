from __future__ import annotations

from collections.abc import AsyncIterator

import xml.etree.ElementTree as ET
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


class SapCdsParser(BaseDocumentParser):
    name = "sap_cds_bi"
    supported_extensions = (".cds.xml",)

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
        if isinstance(source, str) and source.endswith((".cds.xml", ".hdbcalculationview")):
            return True
        try:
            data = Path(source).read_bytes()[:500]
            return b"CDS" in data or (b"CalculationView" in data) or (b"calculationView" in data)
        except Exception:
            return False

    def _parse_xml(self, root: ET.Element, name: str) -> UnifiedBiAggregationDocument:
        doc_name = root.get("name", root.get("schemaName", root.get("id", name)))

        sources: list[AggregationSource] = []
        dimensions: list[Dimension] = []
        measures: list[Measure] = []
        relationships: list[AggregationRelationship] = []

        for entity_elem in root.findall(".//Entity") + root.findall(".//entity") + root.findall(".//CalculationView"):
            ename = entity_elem.get("name", entity_elem.get("id", ""))
            sources.append(AggregationSource(
                name=ename,
                source_type="calculation_view" if entity_elem.tag == "CalculationView" else "entity",
                description=entity_elem.get("description", ""),
            ))

            elements = entity_elem.findall(".//Element") + entity_elem.findall(".//element") + entity_elem.findall(".//measure")
            attrs: list[DimensionAttribute] = []
            entity_measures: list[Measure] = []

            for elem in elements:
                elem_name = elem.get("name", "")
                elem_type = elem.get("type", elem.get("dataType", ""))
                is_measure = elem.get("aggregation", elem.get("aggregateFunction", "")).lower() in (
                    "sum", "count", "avg", "min", "max"
                ) or elem.tag == "measure"

                if is_measure:
                    entity_measures.append(Measure(
                        name=elem_name,
                        source_column=elem.get("column", elem_name),
                        aggregator=elem.get("aggregation", elem.get("aggregateFunction", "sum")),
                    ))
                else:
                    attrs.append(DimensionAttribute(
                        name=elem_name,
                        source_column=elem_name,
                        data_type=elem_type,
                    ))

            if attrs:
                dimensions.append(Dimension(
                    name=ename,
                    source_table=ename,
                    dimension_type="standard",
                    attributes=attrs,
                ))
            measures.extend(entity_measures)

            for assoc in entity_elem.findall(".//Association") + entity_elem.findall(".//association"):
                relationships.append(AggregationRelationship(
                    name=assoc.get("name", ""),
                    source_table=ename,
                    target_table=assoc.get("target", assoc.get("refEntity", "")),
                    source_column=assoc.get("sourceElement", assoc.get("key", "")),
                    target_column=assoc.get("targetElement", ""),
                ))

        return UnifiedBiAggregationDocument(
            name=doc_name,
            description=f"SAP CDS / Calculation View: {doc_name}",
            sources=sources,
            dimensions=dimensions,
            measures=measures,
            relationships=relationships,
            title=name,
            document_id=name,
            media_type=MEDIA_TYPES["sap_cds_xml"],
        )
