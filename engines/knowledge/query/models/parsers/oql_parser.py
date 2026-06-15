from __future__ import annotations

from collections.abc import AsyncIterator

import re
from pathlib import Path
from typing import Any

from engines.document.parsers.base import BaseDocumentParser, ParseOptions
from engines.document.models.media_types import MEDIA_TYPES
from engines.knowledge.query.models import (
    UnifiedQueryDocument,
    QueryLanguage,
    QuerySource,
    QueryDefinition,
    OqlQuery,
    QueryParameter,
)


_OQL_SELECT_RE = re.compile(r"SELECT\s*(?P<cols>[\w\s,]*)\s+FROM\s+(?P<entity>[A-Za-z]\w+)", re.IGNORECASE)
_OQL_FETCH_RE = re.compile(r"FETCH\s+(?P<depth>\d+)", re.IGNORECASE)
_OQL_PARAM_RE = re.compile(r":(?P<name>\w+)|(?P<pos>\?\d)")


class OqlParser(BaseDocumentParser):
    name = "oql_query"
    supported_extensions = (".oql",)

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
        if isinstance(source, str) and source.endswith(".oql"):
            return True
        try:
            text = Path(source).read_text(errors="replace")[:500]
            return bool(_OQL_SELECT_RE.search(text)) and ("FETCH" in text.upper() or "DISTINCT" in text.upper())
        except Exception:
            return False

    def _parse_text(self, text: str, name: str) -> UnifiedQueryDocument:
        m = _OQL_SELECT_RE.search(text)
        entity_name = m.group("entity") if m else None

        fields: list[str] = []
        if m:
            raw_cols = (m.group("cols") or "").strip()
            if raw_cols and raw_cols != "*":
                fields = [f.strip() for f in raw_cols.split(",")]

        fetch_m = _OQL_FETCH_RE.search(text)
        _ = int(fetch_m.group("depth")) if fetch_m else None

        params: list[QueryParameter] = []
        for p in _OQL_PARAM_RE.finditer(text):
            pname = p.group("name") or p.group("pos") or ""
            params.append(QueryParameter(name=pname))

        oql = OqlQuery(
            entity_name=entity_name,
            statement=text.strip(),
            fields=fields,
            parameters=params,
        )

        source = QuerySource(name=entity_name or name, source_type="entity")
        query_def = QueryDefinition(
            language=QueryLanguage.OQL,
            source=entity_name or name,
            text=text,
        )

        return UnifiedQueryDocument(
            language=QueryLanguage.OQL,
            source=source,
            query_definition=query_def,
            oql=oql,
            title=name,
            document_id=name,
            media_type=MEDIA_TYPES["oql_text"],
        )
