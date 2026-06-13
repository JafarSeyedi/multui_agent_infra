from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, BinaryIO, TextIO, cast

from engines.knowledge.models.ksdm_models import UnifiedBiAggregationDocument
from engines.document.writers.base import BaseDocument, BaseDocumentWriter


class MondrianSchemaWriter(BaseDocumentWriter):
    supported_format = None

    def can_write(self, document) -> bool:
        return isinstance(document, UnifiedBiAggregationDocument)

    async def write(self, document: BaseDocument, destination: str | Path | BinaryIO | TextIO | None = None, **options: Any) -> bytes:
        doc = cast(UnifiedBiAggregationDocument, document)
        root = ET.Element("Schema")
        root.set("name", doc.name or "mondrian_schema")

        for src in doc.sources:
            cube_elem = ET.SubElement(root, "Cube")
            cube_elem.set("name", src.name)

            for dim in doc.dimensions:
                dim_elem = ET.SubElement(cube_elem, "Dimension")
                dim_elem.set("name", dim.name)
                if dim.dimension_type != "standard":
                    dim_elem.set("type", dim.dimension_type.capitalize() + "Dimension")

                for hier in dim.hierarchies:
                    h_elem = ET.SubElement(dim_elem, "Hierarchy")
                    h_elem.set("hasAll", "true" if hier.has_all else "false")
                    for lvl in hier.levels:
                        lvl_elem = ET.SubElement(h_elem, "Level")
                        lvl_elem.set("name", lvl.name)
                        if lvl.source_column:
                            lvl_elem.set("column", lvl.source_column)

            for meas in doc.measures:
                m_elem = ET.SubElement(cube_elem, "Measure")
                m_elem.set("name", meas.name)
                if meas.source_column:
                    m_elem.set("column", meas.source_column)
                m_elem.set("aggregator", meas.aggregator)
                m_elem.set("visible", "true" if meas.visible else "false")

            if not doc.dimensions and not doc.measures:
                pass  # empty cube

        ET.indent(ET.ElementTree(root), space="  ")
        xml_bytes = ET.tostring(root, encoding="unicode").encode("utf-8")
        if destination is not None:
            if isinstance(destination, (str, Path)):
                Path(destination).write_bytes(xml_bytes)
            else:
                cast(BinaryIO, destination).write(xml_bytes)
        return xml_bytes

    async def write_stream(self, document: BaseDocument) -> AsyncIterator[bytes]:
        yield await self.write(document)

    async def write_to_file(self, document: BaseDocument, target: Path, options: dict[str, Any] | None = None) -> None:
        target.write_bytes(await self.write(document))

    def get_supported_media_types(self) -> list[str]:
        return ["application/xml"]

    def get_supported_extensions(self) -> list[str]:
        return [".mondrian.xml"]
