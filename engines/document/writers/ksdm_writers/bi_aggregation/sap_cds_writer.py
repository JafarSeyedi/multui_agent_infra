from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, BinaryIO, TextIO, cast

from engines.document.models.ksdm_models import UnifiedBiAggregationDocument
from engines.document.writers.base import BaseDocument, BaseDocumentWriter


class SapCdsWriter(BaseDocumentWriter):
    supported_format = None

    def can_write(self, document) -> bool:
        return isinstance(document, UnifiedBiAggregationDocument)

    async def write(self, document: BaseDocument, destination: str | Path | BinaryIO | TextIO | None = None, **options: Any) -> bytes:
        doc = cast(UnifiedBiAggregationDocument, document)
        root = ET.Element("Schema")
        root.set("name", doc.name or "cds_schema")
        root.set("xmlns", "http://www.sap.com/cds")

        entity_names = {s.name for s in doc.sources}
        for ename in entity_names:
            entity = ET.SubElement(root, "Entity")
            entity.set("name", ename)

            for dim in doc.dimensions:
                if dim.source_table == ename:
                    for attr in dim.attributes:
                        elem = ET.SubElement(entity, "Element")
                        elem.set("name", attr.name)
                        if attr.data_type:
                            elem.set("type", attr.data_type)

            for meas in doc.measures:
                m = ET.SubElement(entity, "measure")
                m.set("name", meas.name)
                m.set("aggregation", meas.aggregator)

        for rel in doc.relationships:
            assoc = ET.SubElement(root, "Association")
            assoc.set("name", rel.name)
            assoc.set("source", rel.source_table)
            assoc.set("target", rel.target_table)
            assoc.set("sourceElement", rel.source_column)
            assoc.set("targetElement", rel.target_column)

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
        return [".cds.xml"]
