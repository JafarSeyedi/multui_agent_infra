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
    DimensionLevel,
    DimensionHierarchy,
    Measure,
)


class MondrianSchemaParser(BaseDocumentParser):
    name = "mondrian_bi"
    supported_extensions = (".mondrian.xml",)

    async def parse_bytes(self, data: bytes, document_id: str, source_name: str, metadata: dict[str, Any] | None = None, options: ParseOptions | None = None) -> UnifiedBiAggregationDocument:
        root = ET.fromstring(data)
        schema_name = root.get("name", root.get("schemaName", source_name))
        schema_table = root.get("table")

        sources: list[AggregationSource] = []
        all_dims: list[Dimension] = []
        all_measures: list[Measure] = []

        for cube_elem in root.findall(".//Cube") + root.findall(".//cube"):
            cube_name = cube_elem.get("name", schema_name)
            sources.append(
                AggregationSource(
                    name=cube_name,
                    source_type="cube",
                    description=f"Mondrian cube: {cube_name}",
                )
            )

            for dim_elem in cube_elem.findall(".//Dimension") + cube_elem.findall(
                ".//dimension"
            ):
                dim_name = dim_elem.get("name", "")
                dim_type = dim_elem.get("type", "StandardDimension")
                hier_elems = dim_elem.findall(".//Hierarchy") + dim_elem.findall(
                    ".//hierarchy"
                )
                hierarchies: list[DimensionHierarchy] = []
                attrs: list[DimensionAttribute] = []

                if hier_elems:
                    h = hier_elems[0]
                    has_all = h.get("hasAll", "true").lower() != "false"
                    levels: list[DimensionLevel] = []
                    for lvl_elem in h.findall(".//Level") + h.findall(".//level"):
                        lvl_name = lvl_elem.get("name", "")
                        lvl_col = lvl_elem.get("column", "")
                        lvl = DimensionLevel(
                            name=lvl_name,
                            source_column=lvl_col,
                        )
                        levels.append(lvl)
                        attrs.append(
                            DimensionAttribute(
                                name=lvl_name,
                                source_column=lvl_col,
                            )
                        )
                    hierarchies.append(
                        DimensionHierarchy(
                            name="Default",
                            levels=levels,
                            has_all=has_all,
                        )
                    )

                all_dims.append(
                    Dimension(
                        name=dim_name,
                        source_table=schema_table or dim_name,
                        dimension_type="standard"
                        if dim_type == "StandardDimension"
                        else dim_type.lower(),
                        hierarchies=hierarchies,
                        attributes=attrs,
                    )
                )

            for meas_elem in cube_elem.findall(".//Measure") + cube_elem.findall(
                ".//measure"
            ):
                all_measures.append(
                    Measure(
                        name=meas_elem.get("name", ""),
                        source_column=meas_elem.get("column", ""),
                        aggregator=meas_elem.get("aggregator", "sum"),
                        visible=meas_elem.get("visible", "true").lower() != "false",
                    )
                )

        return UnifiedBiAggregationDocument(
            name=schema_name,
            description=f"Mondrian OLAP schema: {schema_name}",
            sources=sources,
            dimensions=all_dims,
            measures=all_measures,
            title=source_name,
            document_id=source_name,
            media_type=MEDIA_TYPES["mondrian_schema"],
        )

    async def parse_path(self, path: str | Path, document_id: str, metadata: dict[str, Any] | None = None, options: ParseOptions | None = None) -> UnifiedBiAggregationDocument:
        p = Path(path)
        data = p.read_bytes()
        return await self.parse_bytes(data, document_id, p.name, metadata, options)

    async def parse_stream(self, stream: AsyncIterator[bytes], document_id: str, source_name: str, metadata: dict[str, Any] | None = None, options: ParseOptions | None = None) -> UnifiedBiAggregationDocument:
        chunks = [chunk async for chunk in stream]
        data = b"".join(chunks)
        return await self.parse_bytes(data, document_id, source_name, metadata, options)

    def can_parse(self, source: str | Path) -> bool:
        if isinstance(source, str) and source.endswith(
            (".mondrian.xml", ".schema.xml", ".xml")
        ):
            return True
        try:
            data = Path(source).read_bytes()[:200] if Path(source).exists() else b""
            return b"mondrian" in data.lower() or b"<Schema" in data
        except Exception:
            return False
