from __future__ import annotations

from collections.abc import AsyncIterator

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from engines.document.parsers.base import BaseDocumentParser, ParseOptions
from engines.document.models.media_types import MEDIA_TYPES
from engines.knowledge.models.query_models import (
    UnifiedQueryDocument,
    QueryLanguage,
    QueryTransport,
    ResultsetFormat,
    QuerySource,
    QueryDefinition,
    QueryColumn,
    XmlaTransport,
    FlatTableResult,
)


class XmlaQueryParser(BaseDocumentParser):
    name = "xmla_query"
    supported_extensions = (".xml",)

    async def parse_bytes(self, data: bytes, document_id: str, source_name: str, metadata: dict[str, Any] | None = None, options: ParseOptions | None = None) -> UnifiedQueryDocument:
        root = ET.fromstring(data)
        ns = {
            "soap": "http://schemas.xmlsoap.org/soap/envelope/",
            "xmla": "urn:schemas-microsoft-com:xml-analysis",
        }

        body_elem = root.find(".//soap:Body", ns)
        if body_elem is None:
            body_elem = root

        discover_resp = body_elem.find(".//DiscoverResponse", ns)
        execute_resp = body_elem.find(".//ExecuteResponse", ns)

        if execute_resp is not None:
            response = execute_resp
            is_execute = True
        elif discover_resp is not None:
            response = discover_resp
            is_execute = False
        else:
            response = body_elem
            is_execute = b"Execute" in data

        request_type = ""
        rows: list[dict[str, str]] = []

        rt_elem = response.find(".//xmla:RequestType", ns) if response is not None else None
        if rt_elem is None:
            rt_elem = response.find(".//RequestType", ns) if response is not None else None
        if rt_elem is not None and rt_elem.text:
            request_type = rt_elem.text

        row_elems = response.findall(".//row") if response is not None else []
        for row in row_elems:
            row_data: dict[str, str] = {}
            for child in row:
                tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                row_data[tag] = child.text or ""
            rows.append(row_data)

        transport = XmlaTransport(
            request_type=request_type,
            rows=rows,
        )

        source = QuerySource(name=source_name, source_type="cube")

        query_def = QueryDefinition(
            language=QueryLanguage.MDX if is_execute else QueryLanguage.SQL_TABULAR,
            source=source_name,
            text="",
        )

        doc = UnifiedQueryDocument(
            language=query_def.language,
            transport=QueryTransport.XMLA_SOAP,
            source=source,
            query_definition=query_def,
            xmla_transport=transport,
            title=source_name,
            document_id=source_name,
            media_type=MEDIA_TYPES["xmla_execute_xml"] if is_execute else MEDIA_TYPES["xmla_discover_xml"],
        )

        if is_execute and rows:
            doc.resultset_format = ResultsetFormat.FLAT_TABLE
            columns = [QueryColumn(name=k) for k in rows[0].keys()] if rows else []
            doc.table = FlatTableResult(
                columns=columns,
                rows=[[r.get(c.name, "") for c in columns] for r in rows],
                row_count=len(rows),
            )

        return doc

    async def parse_path(self, path: str | Path, document_id: str, metadata: dict[str, Any] | None = None, options: ParseOptions | None = None) -> UnifiedQueryDocument:
        p = Path(path)
        data = p.read_bytes()
        return await self.parse_bytes(data, document_id, p.name, metadata, options)

    async def parse_stream(self, stream: AsyncIterator[bytes], document_id: str, source_name: str, metadata: dict[str, Any] | None = None, options: ParseOptions | None = None) -> UnifiedQueryDocument:
        chunks = [chunk async for chunk in stream]
        data = b"".join(chunks)
        return await self.parse_bytes(data, document_id, source_name, metadata, options)

    def can_parse(self, source: str | Path) -> bool:
        if isinstance(source, str) and source.endswith((".xmla.xml", ".xml")):
            return True
        try:
            data = Path(source).read_bytes()[:300]
            return b"<DiscoverResponse" in data or b"<ExecuteResponse" in data or b"<Envelope" in data
        except Exception:
            return False
