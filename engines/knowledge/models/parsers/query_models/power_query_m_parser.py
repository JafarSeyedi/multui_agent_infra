from __future__ import annotations

from collections.abc import AsyncIterator

import re
from pathlib import Path
from typing import Any

from engines.document.parsers.base import BaseDocumentParser, ParseOptions
from engines.document.models.media_types import MEDIA_TYPES
from engines.knowledge.models.query_models import (
    UnifiedQueryDocument,
    QueryLanguage,
    QuerySource,
    QueryDefinition,
    PowerQueryM,
    QueryParameter,
)


_M_LET_RE = re.compile(r"let\s+(?P<let_body>.+?)\s+in", re.IGNORECASE | re.DOTALL)
_M_OUTPUT_RE = re.compile(r"in\s+(?P<output>.+?)$", re.IGNORECASE | re.DOTALL)
_M_VAR_RE = re.compile(r"(?P<name>\w+)\s*=\s*(?P<expr>.+?),?\s*$", re.MULTILINE)
_M_FUNCTION_RE = re.compile(r"(Table\.\w+|#\".+?\"|Source|Navigation|Excel\.|Csv\.|Odbc\.|OData\.)", re.IGNORECASE)
_M_PARAM_RE = re.compile(r"(?P<name>#[A-Za-z]\w*|Function\.Parameter)", re.IGNORECASE)


class PowerQueryMParser(BaseDocumentParser):
    name = "m_query"
    supported_extensions = (".m",)

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
        if isinstance(source, str) and source.endswith((".m", ".pq")):
            return True
        try:
            text = Path(source).read_text(errors="replace")[:300]
            return bool(re.search(r"\blet\b.*\bin\b", text, re.IGNORECASE | re.DOTALL))
        except Exception:
            return False

    def _parse_text(self, text: str, name: str) -> UnifiedQueryDocument:
        let_m = _M_LET_RE.search(text)
        out_m = _M_OUTPUT_RE.search(text)

        variables: dict[str, str] = {}
        if let_m:
            let_body = let_m.group("let_body")
            for line in let_body.split("\n"):
                line = line.strip()
                var_m = _M_VAR_RE.match(line)
                if var_m:
                    vname = var_m.group("name").strip()
                    vexpr = var_m.group("expr").strip().rstrip(",")
                    variables[vname] = vexpr

        output = out_m.group("output").strip() if out_m else ""
        _ = list(set(_M_FUNCTION_RE.findall(text)))
        parameters: list[QueryParameter] = []
        for p in _M_PARAM_RE.finditer(text):
            parameters.append(QueryParameter(name=p.group("name")))

        m = PowerQueryM(
            let_expression=text,
            variables=variables,
            output=output,
            parameters=parameters,
        )

        source = QuerySource(name=name, source_type="table")
        query_def = QueryDefinition(
            language=QueryLanguage.M_POWER_QUERY,
            source=name,
            text=text,
        )

        return UnifiedQueryDocument(
            language=QueryLanguage.M_POWER_QUERY,
            source=source,
            query_definition=query_def,
            m_query=m,
            title=name,
            document_id=name,
            media_type=MEDIA_TYPES["m_power_query_text"],
        )
