from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, BinaryIO, TextIO, cast

from engines.knowledge.models.query_models import UnifiedQueryDocument, XmlaTransport, QueryLanguage
from engines.document.writers.base import BaseDocument, BaseDocumentWriter


class XmlaQueryWriter(BaseDocumentWriter):
    supported_format = None

    def can_write(self, document) -> bool:
        return isinstance(document, UnifiedQueryDocument)

    async def write(self, document: BaseDocument, destination: str | Path | BinaryIO | TextIO | None = None, **options: Any) -> bytes:
        doc = cast(UnifiedQueryDocument, document)
        xt = doc.xmla_transport or XmlaTransport()

        envelope = ET.Element("{http://schemas.xmlsoap.org/soap/envelope/}Envelope")
        body = ET.SubElement(envelope, "{http://schemas.xmlsoap.org/soap/envelope/}Body")

        is_execute = doc.language == QueryLanguage.MDX
        response_tag = "ExecuteResponse" if is_execute else "DiscoverResponse"
        resp = ET.SubElement(body, response_tag)
        resp.set("xmlns", "urn:schemas-microsoft-com:xml-analysis")

        ET.SubElement(resp, "RequestType").text = xt.request_type or "MDSCHEMA_CUBES"

        for row in xt.rows:
            row_elem = ET.SubElement(resp, "row")
            for key, val in row.items():
                ET.SubElement(row_elem, key).text = val

        if doc.table:
            for row_vals in doc.table.rows:
                row_elem = ET.SubElement(resp, "row")
                for i, col in enumerate(doc.table.columns):
                    ET.SubElement(row_elem, col.name).text = str(row_vals[i]) if i < len(row_vals) else ""

        xml_bytes = ET.tostring(envelope, encoding="unicode").encode("utf-8")
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
        return [".xml"]
