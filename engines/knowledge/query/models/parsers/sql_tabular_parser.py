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
    SqlTabularQuery,
)


_SQL_SELECT_RE = re.compile(r"SELECT\s+(?P<cols>.+?)\s+FROM", re.IGNORECASE | re.DOTALL)
_SQL_FROM_RE = re.compile(r"FROM\s+(?:\[(?P<cat>[^\]]+)\]\.)?(?:\[?(?P<schema>[^\]]+)\]?\.)?\[?(?P<table>[^\]\s;]+)\]?", re.IGNORECASE)
_SQL_DMV_RE = re.compile(r"\$SYSTEM\.(?P<dmv>[A-Z_]+)", re.IGNORECASE)
_SQL_WHERE_RE = re.compile(r"WHERE\s+(?P<condition>.+?)(?:GROUP|ORDER|$)", re.IGNORECASE | re.DOTALL)
_SQL_EVALUATE_RE = re.compile(r"EVALUATE\s+(?P<expr>.+)", re.IGNORECASE | re.DOTALL)
_SQL_MEASURE_RE = re.compile(r"\[(?P<measure>[^\]]+)\]", re.IGNORECASE)


class SqlTabularParser(BaseDocumentParser):
    name = "sql_tabular_query"
    supported_extensions = (".sql.tabular",)

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
        if isinstance(source, str) and (source.endswith((".sql.tabular", ".tsql"))):
            return True
        try:
            text = Path(source).read_text(errors="replace")[:500]
            return bool(re.search(r"\$SYSTEM\.(MDSCHEMA|DISCOVER)", text, re.IGNORECASE)) or bool(re.search(r"EVALUATE\s", text, re.IGNORECASE))
        except Exception:
            return False

    def _parse_text(self, text: str, name: str) -> UnifiedQueryDocument:
        is_evaluate = bool(_SQL_EVALUATE_RE.search(text))

        if is_evaluate:
            tables = _SQL_MEASURE_RE.findall(text)
            sql = SqlTabularQuery(
                dialect="dax_evaluate",
                statement=text.strip(),
                tables=list(set(tables)),
                columns=list(set(tables)),
            )
        else:
            cols_m = _SQL_SELECT_RE.search(text)
            columns = []
            if cols_m:
                columns = [c.strip().strip("[]") for c in cols_m.group("cols").split(",")]
                columns = [re.sub(r"\s+AS\s+.*", "", c, flags=re.IGNORECASE) for c in columns]

            from_m = _SQL_FROM_RE.search(text)
            catalog = None
            schema = None
            table = None
            if from_m:
                catalog = from_m.group("cat")
                schema = from_m.group("schema")
                table = from_m.group("table")

            dmv_m = _SQL_DMV_RE.search(text)
            dmv_name = dmv_m.group("dmv").upper() if dmv_m else None

            tables = [t for t in [table] if t]

            sql = SqlTabularQuery(
                dialect="tsql",
                catalog=catalog,
                schema_name=schema,
                dmv_name=dmv_name,
                statement=text.strip(),
                tables=tables,
                columns=columns,
            )

        source = QuerySource(name=name, source_type="table")
        query_def = QueryDefinition(
            language=QueryLanguage.SQL_TABULAR,
            source=name,
            text=text,
        )

        return UnifiedQueryDocument(
            language=QueryLanguage.SQL_TABULAR,
            source=source,
            query_definition=query_def,
            sql=sql,
            title=name,
            document_id=name,
            media_type=MEDIA_TYPES["sql_tabular_text"],
        )
