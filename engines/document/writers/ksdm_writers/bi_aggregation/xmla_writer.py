from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, BinaryIO, TextIO, cast

from engines.document.models.ksdm_models import (
    BiAggregationDocument,
    BiAggregationKind,
    XmlaDiscoverRequest,
    XmlaDiscoverResponse,
)
from engines.document.writers.base import BaseDocument, BaseDocumentWriter


class XmlaDiscoverWriter(BaseDocumentWriter):
    supported_format = None

    def can_write(self, document) -> bool:
        return isinstance(document, BiAggregationDocument) and document.bi_aggregation_kind == BiAggregationKind.XMLA_CUBE

    async def write(self, document: BaseDocument, destination: str | Path | BinaryIO | TextIO | None = None, **options: Any) -> bytes:
        getattr(document, 'xmla_discover_request', XmlaDiscoverRequest())
        resp = getattr(document, 'xmla_discover_response', XmlaDiscoverResponse())
        envelope = ET.Element('{http://schemas.xmlsoap.org/soap/envelope/}Envelope')
        body = ET.SubElement(envelope, '{http://schemas.xmlsoap.org/soap/envelope/}Body')
        dr = ET.SubElement(body, 'DiscoverResponse')
        dr.set('xmlns', 'urn:schemas-microsoft-com:xml-analysis')
        if resp.request_type:
            ET.SubElement(dr, 'RequestType').text = resp.request_type
        if resp.rows:
            for row in resp.rows:
                row_elem = ET.SubElement(dr, 'row')
                for k, v in row.items():
                    ET.SubElement(row_elem, k).text = str(v)
        tree = ET.ElementTree(envelope)
        ET.indent(tree, space='  ')
        xml_bytes = ET.tostring(envelope, encoding='unicode').encode('utf-8')
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
