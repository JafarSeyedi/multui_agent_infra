from __future__ import annotations

from collections.abc import AsyncIterator

import json
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
    DaxQuery,
    RestTransport,
    FlatTableResult,
    QueryColumn,
)


_DAX_TABLE_REF_RE = re.compile(r"'([^']+)'\[([^\]]+)\]", re.IGNORECASE)
_DAX_MEASURE_REF_RE = re.compile(r"\[([^\]]+)\]", re.IGNORECASE)
_DAX_FUNCTION_RE = re.compile(r"(CALCULATE|FILTER|ALL|CALCULATETABLE|SUMX|ADDCOLUMNS|SUMMARIZE)\s*\(", re.IGNORECASE)
_DAX_VAR_RE = re.compile(r"VAR\s+(?P<name>\w+)\s*=\s*(?P<expr>.+?)(?=RETURN|VAR\s+\w+\s*=)", re.IGNORECASE | re.DOTALL)


class DaxParser(BaseDocumentParser):
    name = "dax_query"
    supported_extensions = (".dax",)

    async def parse_bytes(self, data: bytes, document_id: str, source_name: str, metadata: dict[str, Any] | None = None, options: ParseOptions | None = None) -> UnifiedQueryDocument:
        raw = data.decode("utf-8", errors="replace")

        if data.strip().startswith(b"{"):
            return self._parse_rest_json(json.loads(data), source_name)
        return self._parse_text(raw, source_name)

    async def parse_path(self, path: str | Path, document_id: str, metadata: dict[str, Any] | None = None, options: ParseOptions | None = None) -> UnifiedQueryDocument:
        p = Path(path)
        return await self.parse_bytes(p.read_bytes(), document_id, p.name, metadata, options)

    async def parse_stream(self, stream: AsyncIterator[bytes], document_id: str, source_name: str, metadata: dict[str, Any] | None = None, options: ParseOptions | None = None) -> UnifiedQueryDocument:
        chunks = [chunk async for chunk in stream]
        data = b"".join(chunks)
        return await self.parse_bytes(data, document_id, source_name, metadata, options)

    def can_parse(self, source: str | Path) -> bool:
        if isinstance(source, str) and source.endswith((".dax", ".dax.json")):
            return True
        try:
            text = Path(source).read_text(errors="replace")[:300]
            if "EVALUATE" in text.upper() and "SUMMARIZE" not in text.upper():
                return True
            return bool(re.search(r"'[^']+'\[", text)) or bool(re.search(r"CALCULATE\s*\(", text, re.IGNORECASE))
        except Exception:
            return False

    def _parse_text(self, text: str, name: str) -> UnifiedQueryDocument:
        table_refs = _DAX_TABLE_REF_RE.findall(text)
        measure_refs = [m[0] for m in _DAX_MEASURE_REF_RE.findall(text) if m[0] not in [r[1] for r in table_refs]]
        functions = [m[0] for m in _DAX_FUNCTION_RE.finditer(text)]

        primary_table = table_refs[0][0] if table_refs else None

        variables: dict[str, str] = {}
        for m in _DAX_VAR_RE.finditer(text):
            variables[m.group("name").strip()] = m.group("expr").strip()

        dax = DaxQuery(
            table_name=primary_table,
            expression=text,
            measures=list(set(measure_refs)),
            filter="; ".join(functions) if functions else None,
            variables=variables,
        )

        source = QuerySource(name=primary_table or name, source_type="table")
        query_def = QueryDefinition(
            language=QueryLanguage.DAX,
            source=primary_table or name,
            text=text,
        )

        return UnifiedQueryDocument(
            language=QueryLanguage.DAX,
            source=source,
            query_definition=query_def,
            dax=dax,
            title=name,
            document_id=name,
            media_type=MEDIA_TYPES["dax_query_text"],
        )

    def _parse_rest_json(self, data: dict, name: str) -> UnifiedQueryDocument:
        queries = data.get("queries", [data])
        first = queries[0] if queries else {}
        expression = first.get("Expression", first.get("expression", ""))

        dax = DaxQuery(expression=expression)
        rest = RestTransport(
            endpoint=data.get("endpoint", ""),
            method="POST",
            body=json.dumps(data),
        )

        source = QuerySource(name=name, source_type="table")
        query_def = QueryDefinition(
            language=QueryLanguage.DAX,
            source=name,
            text=expression,
        )

        doc = UnifiedQueryDocument(
            language=QueryLanguage.DAX,
            transport=QueryTransport.REST_JSON,
            source=source,
            query_definition=query_def,
            dax=dax,
            rest_transport=rest,
            title=name,
            document_id=name,
            media_type=MEDIA_TYPES["dax_rest_json"],
        )

        results = data.get("results", [])
        if results:
            tables = results[0].get("tables", [])
            if tables:
                rows = tables[0].get("rows", [])
                columns = tables[0].get("columns", [])
                doc.resultset_format = ResultsetFormat.FLAT_TABLE
                doc.table = FlatTableResult(
                    columns=[QueryColumn(name=c.get("name", ""), data_type=c.get("dataType")) for c in columns],
                    rows=[[r.get(c.get("name", ""), "") for c in columns] for r in rows],
                    row_count=len(rows),
                )

        return doc
