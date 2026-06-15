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
    AggregationRelationship,
    Measure,
)


class CwmParser(BaseDocumentParser):
    name = "cwm_bi"
    supported_extensions = (".xmi", ".cwm")

    async def parse_bytes(self, data: bytes, document_id: str, source_name: str, metadata: dict[str, Any] | None = None, options: ParseOptions | None = None) -> UnifiedBiAggregationDocument:
        root = ET.fromstring(data)
        ns = self._resolve_ns(root)
        schema_name = root.get("name", source_name)

        sources: list[AggregationSource] = []
        dimensions: list[Dimension] = []
        relationships: list[AggregationRelationship] = []
        all_measures: list[Measure] = []

        # Support two CWM styles:
        #   1. Warehouse format: <Cube>, <Dimension>, <Measure> elements
        #   2. Metamodel format: <Class>, <Association> elements
        cwm_ns_val = ns.get("cwm", "")
        cube_tag = f"{{{cwm_ns_val}}}Cube" if cwm_ns_val else ".//Cube"
        dim_tag = f"{{{cwm_ns_val}}}Dimension" if cwm_ns_val else ".//Dimension"
        meas_tag = f"{{{cwm_ns_val}}}Measure" if cwm_ns_val else ".//Measure"

        for cube_elem in root.findall(f".//{cube_tag}"):
            cname = cube_elem.get("name", schema_name)
            sources.append(AggregationSource(
                name=cname,
                source_type="cube",
                description=f"CWM cube: {cname}",
            ))

        for dim_elem in root.findall(f".//{dim_tag}"):
            dim_name = dim_elem.get("name", "")
            dim_type = dim_elem.get("type", "StandardDimension")
            dimensions.append(Dimension(
                name=dim_name,
                dimension_type="standard" if dim_type == "StandardDimension" else dim_type.lower(),
            ))

        for meas_elem in root.findall(f".//{meas_tag}"):
            all_measures.append(Measure(
                name=meas_elem.get("name", ""),
                source_column=meas_elem.get("column", ""),
                aggregator=meas_elem.get("aggregator", meas_elem.get("formula", "sum")),
            ))

        # Metamodel format: Class-level decomposition
        for cls_elem in root.findall(".//cwm:Class", ns) + root.findall(".//Class"):
            cls_name = cls_elem.get("name", "")
            attrs: list[DimensionAttribute] = []
            is_fact = False

            for child in cls_elem:
                tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                if tag == "Attribute" or child.tag in (
                    f'{{{ns["cwm"]}}}Attribute',
                    "Attribute",
                ):
                    attr_name = child.get("name", "")
                    data_type = child.get("type", child.get("dataType", ""))
                    is_key = child.get("isKey", "false").lower() == "true"
                    attrs.append(
                        DimensionAttribute(
                            name=attr_name,
                            source_column=attr_name,
                            data_type=data_type,
                        )
                    )
                    if is_key:
                        is_fact = True

            if is_fact or cls_name.lower().endswith("fact"):
                sources.append(
                    AggregationSource(
                        name=cls_name,
                        source_type="table",
                        description=f"CWM class: {cls_name}",
                    )
                )
                for attr in attrs:
                    all_measures.append(
                        Measure(
                            name=attr.name,
                            source_column=attr.source_column,
                            aggregator="sum",
                        )
                    )
            else:
                hierarchy = DimensionHierarchy(
                    name="Default",
                    levels=[
                        DimensionLevel(
                            name=attr.name,
                            source_column=attr.source_column,
                            attributes=[attr],
                        )
                        for attr in attrs
                    ],
                )
                dimensions.append(
                    Dimension(
                        name=cls_name,
                        source_table=cls_name,
                        dimension_type="standard",
                        hierarchies=[hierarchy],
                        attributes=attrs,
                    )
                )

        for assoc_elem in root.findall(".//cwm:Association", ns) + root.findall(
            ".//Association"
        ):
            source_cls = assoc_elem.get("sourceClass", assoc_elem.get("source", ""))
            target_cls = assoc_elem.get("targetClass", assoc_elem.get("target", ""))
            if source_cls and target_cls:
                relationships.append(
                    AggregationRelationship(
                        name=assoc_elem.get("name", f"{source_cls}_to_{target_cls}"),
                        source_table=source_cls,
                        target_table=target_cls,
                        source_column="",
                        target_column="",
                        cardinality=assoc_elem.get("multiplicity", "many_to_one"),
                    )
                )

        return UnifiedBiAggregationDocument(
            name=schema_name,
            description=f"CWM warehouse: {schema_name}",
            sources=sources,
            dimensions=dimensions,
            measures=all_measures,
            relationships=relationships,
            title=source_name,
            document_id=source_name,
            media_type=MEDIA_TYPES["cwm_xmi"],
        )

    async def parse_path(self, path: str | Path, document_id: str, metadata: dict[str, Any] | None = None, options: ParseOptions | None = None) -> UnifiedBiAggregationDocument:
        p = Path(path)
        data = p.read_bytes()
        return await self.parse_bytes(data, document_id, p.name, metadata, options)

    async def parse_stream(self, stream: AsyncIterator[bytes], document_id: str, source_name: str, metadata: dict[str, Any] | None = None, options: ParseOptions | None = None) -> UnifiedBiAggregationDocument:
        chunks = [chunk async for chunk in stream]
        data = b"".join(chunks)
        return await self.parse_bytes(data, document_id, source_name, metadata, options)

    def _resolve_ns(self, root: ET.Element) -> dict[str, str]:
        ns: dict[str, str] = {"xmi": "http://www.omg.org/XMI"}
        for attr, val in (root.attrib or {}).items():
            if attr.startswith("xmlns"):
                prefix = attr.split("xmlns")[-1].lstrip(":")
                if prefix:
                    ns[prefix] = val
                else:
                    ns["cwm"] = val or "http://www.omg.org/cwm"
        if "cwm" not in ns:
            for _, val in ns.items():
                if "cwm" in val.lower() or "CWM" in val:
                    ns["cwm"] = val
                    break
            else:
                ns["cwm"] = "http://www.omg.org/cwm"
        return ns

    def can_parse(self, source: str | Path) -> bool:
        if isinstance(source, str) and source.endswith((".cwm", ".cwm.xml", ".xmi")):
            return True
        try:
            data = Path(source).read_bytes()[:200] if Path(source).exists() else b""
            return b"CWM" in data or b"cwm:" in data
        except Exception:
            return False
