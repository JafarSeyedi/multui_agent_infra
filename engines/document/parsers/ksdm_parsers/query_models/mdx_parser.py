from __future__ import annotations

from collections.abc import AsyncIterator

import re
from pathlib import Path
from typing import Any

from engines.document.parsers.base import BaseDocumentParser, ParseOptions
from engines.document.models.media_types import MEDIA_TYPES
from engines.document.models.query_models import (
    UnifiedQueryDocument,
    QueryLanguage,
    QueryTransport,
    ResultsetFormat,
    QuerySource,
    QueryDefinition,
    MdxQuery,
    MdxAxis,
    MdxCalculatedMember,
    MdxCellset,
    CellAxis,
    CellValue,
    FlatTableResult,
    QueryColumn,
)


_MDX_AXIS_RE = re.compile(
    r"(?P<set>\{.*?\}|[A-Za-z0-9_\[\]\.]+\s*\.\s*[A-Za-z0-9_\[\]]+)\s+ON\s+(?P<axis>ROWS|COLUMNS|PAGES|CHAPTERS|SECTIONS)",
    re.IGNORECASE,
)
_MDX_FROM_RE = re.compile(r"FROM\s+\[?(?P<cube>[^\]]+)\]?", re.IGNORECASE)
_MDX_WHERE_RE = re.compile(r"WHERE\s+\(?(?P<slicer>[^)]+)\)?", re.IGNORECASE)
_MDX_WITH_MEMBER_RE = re.compile(
    r"MEMBER\s+\[?(?P<member>[^\]]+)\]?\s+AS\s+'(?P<expr>[^']+)'",
    re.IGNORECASE,
)
_MDX_CELL_PROPERTIES_RE = re.compile(
    r"CELL\s+PROPERTIES\s+(?P<props>.+?)(?:\s*$|\s*;)",
    re.IGNORECASE | re.DOTALL,
)


class MdxParser(BaseDocumentParser):
    name = "mdx_query"
    supported_extensions = (".mdx",)

    async def parse_bytes(self, data: bytes, document_id: str, source_name: str, metadata: dict[str, Any] | None = None, options: ParseOptions | None = None) -> UnifiedQueryDocument:
        text = data.decode("utf-8", errors="replace")
        return self._parse_text(text, source_name)

    async def parse_path(self, path: str | Path, document_id: str, metadata: dict[str, Any] | None = None, options: ParseOptions | None = None) -> UnifiedQueryDocument:
        p = Path(path)
        return await self.parse_bytes(p.read_bytes(), document_id, p.name, metadata, options)

    async def parse_stream(self, stream: AsyncIterator[bytes], document_id: str, source_name: str, metadata: dict[str, Any] | None = None, options: ParseOptions | None = None) -> UnifiedQueryDocument:
        chunks = [chunk async for chunk in stream]
        data = b"".join(chunks)
        return await self.parse_bytes(data, document_id, source_name, metadata, options)

    def can_parse(self, source: str | Path) -> bool:
        if isinstance(source, str) and (source.endswith((".mdx", ".mdx.xml"))):
            return True
        try:
            text = Path(source).read_text(errors="replace")[:500]
            return bool(re.search(r"SELECT\s+.*ON\s+(ROWS|COLUMNS)", text, re.IGNORECASE))
        except Exception:
            return False

    def _parse_text(self, text: str, name: str) -> UnifiedQueryDocument:
        cube_name = ""
        cube_m = _MDX_FROM_RE.search(text)
        if cube_m:
            cube_name = cube_m.group("cube").strip()

        axes: list[MdxAxis] = []
        for m in _MDX_AXIS_RE.finditer(text):
            axes.append(MdxAxis(
                axis=m.group("axis").upper(),
                set_expression=m.group("set").strip(),
            ))

        slicer = ""
        where_m = _MDX_WHERE_RE.search(text)
        if where_m:
            slicer = where_m.group("slicer").strip()

        calculated_members: list[MdxCalculatedMember] = []
        for m in _MDX_WITH_MEMBER_RE.finditer(text):
            calculated_members.append(MdxCalculatedMember(
                name=m.group("member").strip(),
                expression=m.group("expr").strip(),
            ))

        cell_properties: list[str] = []
        cp_m = _MDX_CELL_PROPERTIES_RE.search(text)
        if cp_m:
            cell_properties = [p.strip() for p in cp_m.group("props").split(",")]

        measures: list[str] = []
        non_empty = "NON EMPTY" in text.upper()

        mdx = MdxQuery(
            cube_name=cube_name,
            axes=axes,
            measures=measures,
            calculated_members=calculated_members,
            slicer=slicer,
            non_empty=non_empty,
            cell_properties=cell_properties,
            query_text=text,
        )

        source = QuerySource(name=cube_name or name, source_type="cube")
        query_def = QueryDefinition(
            language=QueryLanguage.MDX,
            source=cube_name or name,
            text=text,
        )

        return UnifiedQueryDocument(
            language=QueryLanguage.MDX,
            transport=QueryTransport.XMLA_SOAP,
            source=source,
            query_definition=query_def,
            mdx=mdx,
            title=name,
            document_id=name,
            media_type=MEDIA_TYPES["mdx_query_text"],
        )
