from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, BinaryIO, TextIO, cast

from engines.knowledge.models.ksdm_models import UnifiedBiAggregationDocument
from engines.document.writers.base import BaseDocument, BaseDocumentWriter


class CognosFmfWriter(BaseDocumentWriter):
    supported_format = None

    def can_write(self, document) -> bool:
        return isinstance(document, UnifiedBiAggregationDocument)

    async def write(self, document: BaseDocument, destination: str | Path | BinaryIO | TextIO | None = None, **options: Any) -> bytes:
        doc = cast(UnifiedBiAggregationDocument, document)
        root = ET.Element("FrameworkManager")
        root.set("name", doc.name or "cognos_model")

        for src in doc.sources:
            subj = ET.SubElement(root, "QuerySubject")
            subj.set("name", src.name)
            if src.description:
                subj.set("description", src.description)

        for dim in doc.dimensions:
            subj = ET.SubElement(root, "QuerySubject")
            subj.set("name", dim.name)
            for attr in dim.attributes:
                item = ET.SubElement(subj, "QueryItem")
                item.set("name", attr.name)

        for meas in doc.measures:
            m = ET.SubElement(root, "QueryItem")
            m.set("name", meas.name)
            m.set("aggregation", meas.aggregator)
            if meas.source_column:
                m.set("expression", meas.source_column)

        for rel in doc.relationships:
            r = ET.SubElement(root, "Relationship")
            r.set("name", rel.name)
            r.set("source", rel.source_table)
            r.set("target", rel.target_table)

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
        return [".fmf.xml"]
