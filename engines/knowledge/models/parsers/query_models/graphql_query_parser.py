from __future__ import annotations

from collections.abc import AsyncIterator

import json
import re
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
    GraphqlQueryDocument,
    GraphqlOperation,
    GraphqlField,
    GraphqlFragment,
    GraphqlError,
    FlatTableResult,
    QueryColumn,
)


_GQL_OP_RE = re.compile(
    r"(?P<kind>query|mutation|subscription)\s+(?P<name>\w+)?\s*"
    r"(\((?P<vars>[^)]*)\))?\s*\{",
    re.IGNORECASE,
)
_GQL_FIELD_RE = re.compile(r"(?P<alias>\w+)\s*:\s*(?P<name>\w+)|(?P<bare>\w+)")
_GQL_VAR_DEF_RE = re.compile(r"\$(?P<name>\w+)\s*:\s*(?P<type>[!\w\[\]]+)")
_GQL_FRAG_RE = re.compile(r"fragment\s+(?P<name>\w+)\s+on\s+(?P<type>\w+)\s*\{", re.IGNORECASE)


class GraphqlQueryParser(BaseDocumentParser):
    name = "graphql_query"
    supported_extensions = (".gql.query",)

    async def parse_bytes(self, data: bytes, document_id: str, source_name: str, metadata: dict[str, Any] | None = None, options: ParseOptions | None = None) -> UnifiedQueryDocument:
        raw = data.decode("utf-8", errors="replace")

        if data.strip().startswith(b"{"):
            try:
                return self._parse_response(json.loads(data), source_name)
            except json.JSONDecodeError:
                pass

        return self._parse_text(raw, source_name)

    async def parse_path(self, path: str | Path, document_id: str, metadata: dict[str, Any] | None = None, options: ParseOptions | None = None) -> UnifiedQueryDocument:
        p = Path(path)
        return await self.parse_bytes(p.read_bytes(), document_id, p.name, metadata, options)

    async def parse_stream(self, stream: AsyncIterator[bytes], document_id: str, source_name: str, metadata: dict[str, Any] | None = None, options: ParseOptions | None = None) -> UnifiedQueryDocument:
        chunks = [chunk async for chunk in stream]
        data = b"".join(chunks)
        return await self.parse_bytes(data, document_id, source_name, metadata, options)

    def can_parse(self, source: str | Path) -> bool:
        if isinstance(source, str) and source.endswith((".gql.query", ".graphql")):
            return True
        try:
            text = Path(source).read_text(errors="replace")[:300]
            return bool(re.search(r"(query|mutation|subscription)\s+\w+\s*[\({]", text, re.IGNORECASE))
        except Exception:
            return False

    def _parse_text(self, text: str, name: str) -> UnifiedQueryDocument:
        operations: list[GraphqlOperation] = []
        fragments: list[GraphqlFragment] = []

        for m in _GQL_FRAG_RE.finditer(text):
            fragments.append(GraphqlFragment(
                name=m.group("name"),
                on_type=m.group("type"),
            ))

        for m in _GQL_OP_RE.finditer(text):
            kind = m.group("kind").lower()
            op_name = m.group("name")
            vars_str = m.group("vars") or ""

            var_defs: dict[str, str] = {}
            for v in _GQL_VAR_DEF_RE.finditer(vars_str):
                var_defs[v.group("name")] = v.group("type")

            operations.append(GraphqlOperation(
                kind=kind,
                name=op_name,
                variable_definitions=var_defs,
            ))

        gql = GraphqlQueryDocument(
            operations=operations,
            fragments=fragments,
            query_text=text,
        )

        source = QuerySource(name=name, source_type="service")
        query_def = QueryDefinition(
            language=QueryLanguage.GRAPHQL,
            source=name,
            text=text,
        )

        return UnifiedQueryDocument(
            language=QueryLanguage.GRAPHQL,
            transport=QueryTransport.REST_JSON,
            source=source,
            query_definition=query_def,
            graphql=gql,
            title=name,
            document_id=name,
            media_type=MEDIA_TYPES["graphql_query_text"],
        )

    def _parse_response(self, data: dict, name: str) -> UnifiedQueryDocument:
        gql = GraphqlQueryDocument()

        if "data" in data:
            gql.response_data = data["data"]

        if "errors" in data:
            for err in data["errors"]:
                gql.response_errors.append(GraphqlError(
                    message=err.get("message", ""),
                    locations=err.get("locations", []),
                    path=err.get("path", []),
                    extensions=err.get("extensions", {}),
                ))

        source = QuerySource(name=name, source_type="service")
        query_def = QueryDefinition(
            language=QueryLanguage.GRAPHQL,
            source=name,
            text=json.dumps(data),
        )

        doc = UnifiedQueryDocument(
            language=QueryLanguage.GRAPHQL,
            transport=QueryTransport.REST_JSON,
            resultset_format=ResultsetFormat.JSON_API,
            source=source,
            query_definition=query_def,
            graphql=gql,
            title=name,
            document_id=name,
            media_type=MEDIA_TYPES["graphql_query_text"],
        )

        if gql.response_data:
            rows = [gql.response_data]
            columns = [QueryColumn(name=k) for k in gql.response_data.keys()]
            doc.table = FlatTableResult(
                columns=columns,
                rows=[[gql.response_data.get(c.name, "") for c in columns] for r in rows],
                row_count=1,
            )

        return doc
