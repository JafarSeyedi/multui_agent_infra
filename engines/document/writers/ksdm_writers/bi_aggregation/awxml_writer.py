from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, BinaryIO, TextIO, cast

from engines.document.models.ksdm_models import UnifiedBiAggregationDocument
from engines.document.writers.base import BaseDocument, BaseDocumentWriter


class AwxmlWriter(BaseDocumentWriter):
    supported_format = None

    def can_write(self, document) -> bool:
        return isinstance(document, UnifiedBiAggregationDocument)

    async def write(self, document: BaseDocument, destination: str | Path | BinaryIO | TextIO | None = None, **options: Any) -> bytes:
        doc = cast(UnifiedBiAggregationDocument, document)
        root = ET.Element("AWManifest")
        root.set("name", doc.name or "aw_workspace")

        for src in doc.sources:
            cube = ET.SubElement(root, "cube")
            cube.set("name", src.name)

        for dim in doc.dimensions:
            dim_elem = ET.SubElement(root, "dimension")
            dim_elem.set("name", dim.name)
            if dim.hierarchies:
                h = dim.hierarchies[0]
                h_elem = ET.SubElement(dim_elem, "hierarchy")
                h_elem.set("name", h.name)
                for lvl in h.levels:
                    lvl_elem = ET.SubElement(h_elem, "level")
                    lvl_elem.set("name", lvl.name)

        for meas in doc.measures:
            meas_elem = ET.SubElement(root, "measure")
            meas_elem.set("name", meas.name)
            if meas.source_column:
                meas_elem.set("column", meas.source_column)
            meas_elem.set("aggregator", meas.aggregator)

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
        return [".aw.xml"]
