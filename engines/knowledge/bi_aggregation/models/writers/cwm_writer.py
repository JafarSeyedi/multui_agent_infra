from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, BinaryIO, TextIO, cast

from engines.knowledge.bi_aggregation.models import UnifiedBiAggregationDocument
from engines.document.writers.base import BaseDocument, BaseDocumentWriter


class CwmWriter(BaseDocumentWriter):
    supported_format = None

    def can_write(self, document) -> bool:
        return isinstance(document, UnifiedBiAggregationDocument)

    async def write(self, document: BaseDocument, destination: str | Path | BinaryIO | TextIO | None = None, **options: Any) -> bytes:
        doc = cast(UnifiedBiAggregationDocument, document)
        root = ET.Element("XMI")
        root.set("xmlns:xmi", "http://www.omg.org/XMI")
        root.set("xmlns:cwm", "http://www.omg.org/spec/CWM/")
        root.set("name", doc.name or "UnifiedModel")

        for dim in doc.dimensions:
            cls_elem = ET.SubElement(root, "Class")
            cls_elem.set("name", dim.name)
            for attr in dim.attributes:
                attr_elem = ET.SubElement(cls_elem, "Attribute")
                attr_elem.set("name", attr.name)
                attr_elem.set("type", attr.data_type or "String")

        for src in doc.sources:
            if src.name not in {d.name for d in doc.dimensions}:
                cls_elem = ET.SubElement(root, "Class")
                cls_elem.set("name", src.name)
                cls_elem.set("package", src.source_type)

        for rel in doc.relationships:
            assoc_elem = ET.SubElement(root, "Association")
            assoc_elem.set("name", rel.name)
            assoc_elem.set("sourceClass", rel.source_table)
            assoc_elem.set("targetClass", rel.target_table)
            assoc_elem.set("multiplicity", rel.cardinality)

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
        return [".xmi", ".cwm"]
