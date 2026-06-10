from __future__ import annotations

from collections.abc import AsyncIterator

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from engines.document.parsers.base import BaseDocumentParser, ParseOptions, ParseResult
from engines.document.models.media_types import MEDIA_TYPES
from engines.document.models.ksdm_models import (
    UnifiedBiAggregationDocument,
    AggregationSource,
    Dimension,
    DimensionAttribute,
    DimensionHierarchy,
    DimensionLevel,
    Measure,
)


class AwxmlParser(BaseDocumentParser):
    name = "awxml_bi"
    supported_extensions = (".aw.xml",)

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
        if isinstance(source, str) and source.endswith((".aw.xml", ".awxml")):
            return True
        try:
            data = Path(source).read_bytes()[:200]
            return b"AWManifest" in data or b"analyticWorkspace" in data or b"AWXML" in data
        except Exception:
            return False

    def _parse_xml(self, root: ET.Element, name: str) -> UnifiedBiAggregationDocument:
        doc_name = root.get("name", root.get("workspaceName", name))

        sources: list[AggregationSource] = []
        dimensions: list[Dimension] = []
        measures: list[Measure] = []

        for cube_elem in root.findall(".//cube"):
            cname = cube_elem.get("name", "")
            sources.append(AggregationSource(
                name=cname,
                source_type="cube",
                description=f"Oracle AW cube: {cname}",
            ))

            for dim_elem in cube_elem.findall(".//dimension") + root.findall(".//dimension"):
                dim_name = dim_elem.get("name", "")
                hier_elems = dim_elem.findall(".//hierarchy") + dim_elem.findall(".//levelHierarchy")
                hierarchies: list[DimensionHierarchy] = []
                attrs: list[DimensionAttribute] = []

                if hier_elems:
                    h = hier_elems[0]
                    levels: list[DimensionLevel] = []
                    for lvl_elem in h.findall(".//level"):
                        lvl_name = lvl_elem.get("name", "")
                        lvl = DimensionLevel(name=lvl_name)
                        levels.append(lvl)
                        attrs.append(DimensionAttribute(
                            name=lvl_name,
                            source_column=lvl_name,
                        ))
                    hierarchies.append(DimensionHierarchy(
                        name="Default",
                        levels=levels,
                        has_all=True,
                    ))

                dimensions.append(Dimension(
                    name=dim_name,
                    dimension_type="standard",
                    hierarchies=hierarchies,
                    attributes=attrs,
                ))

            for meas_elem in cube_elem.findall(".//measure") + root.findall(".//measure"):
                measures.append(Measure(
                    name=meas_elem.get("name", ""),
                    source_column=meas_elem.get("column", meas_elem.get("expression", "")),
                    aggregator=meas_elem.get("aggregator", meas_elem.get("formula", "sum")),
                ))

        return UnifiedBiAggregationDocument(
            name=doc_name,
            description=f"Oracle Analytic Workspace: {doc_name}",
            sources=sources,
            dimensions=dimensions,
            measures=measures,
            title=name,
            document_id=name,
            media_type=MEDIA_TYPES["awxml"],
        )
