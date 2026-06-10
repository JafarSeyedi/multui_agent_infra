from __future__ import annotations

import re
from typing import Any

from engines.document.models.query_models import (
    CellAxis,
    CellValue,
    DaxQuery,
    FlatTableResult,
    GraphqlField,
    GraphqlOperation,
    GraphqlQueryDocument,
    JpqlQuery,
    MdxAxis,
    MdxCalculatedMember,
    MdxCellset,
    MdxQuery,
    OqlQuery,
    PowerQueryM,
    QueryColumn,
    QueryDefinition,
    QueryLanguage,
    QueryParameter,
    QuerySource,
    QueryTransport,
    RestTransport,
    ResultsetFormat,
    SqlTabularQuery,
    UnifiedQueryDocument,
    XmlaTransport,
)
from engines.document.parsers.base import BaseDocumentParser
from engines.document.parsers.ksdm_parsers.query_models import (
    DaxParser,
    GraphqlQueryParser,
    JpqlParser,
    MdxParser,
    OqlParser,
    PowerQueryMParser,
    SqlTabularParser,
    XmlaQueryParser,
)
from engines.document.writers.base import BaseDocumentWriter
from engines.document.writers.ksdm_writers.query_models import (
    DaxWriter,
    GraphqlQueryWriter,
    JpqlWriter,
    MdxWriter,
    OqlWriter,
    PowerQueryMWriter,
    SqlTabularWriter,
    XmlaQueryWriter,
)


_PARSER_MAP: dict[str, type[BaseDocumentParser]] = {
    "xmla": XmlaQueryParser,
    "mdx": MdxParser,
    "dax": DaxParser,
    "dax_rest": DaxParser,
    "sql_tabular": SqlTabularParser,
    "m_power_query": PowerQueryMParser,
    "jpql": JpqlParser,
    "oql": OqlParser,
    "graphql_query": GraphqlQueryParser,
}

_WRITER_MAP: dict[str, type[BaseDocumentWriter]] = {
    "xmla": XmlaQueryWriter,
    "mdx": MdxWriter,
    "dax": DaxWriter,
    "dax_rest": DaxWriter,
    "sql_tabular": SqlTabularWriter,
    "m_power_query": PowerQueryMWriter,
    "jpql": JpqlWriter,
    "oql": OqlWriter,
    "graphql_query": GraphqlQueryWriter,
}

_LANGUAGE_KEYWORDS: dict[str, QueryLanguage] = {
    "WITH": QueryLanguage.MDX,
    "NON EMPTY": QueryLanguage.MDX,
    "ON COLUMNS": QueryLanguage.MDX,
    "ON ROWS": QueryLanguage.MDX,
    "EVALUATE": QueryLanguage.DAX,
    "CALCULATE": QueryLanguage.DAX,
    "SUMMARIZE": QueryLanguage.DAX,
    "let": QueryLanguage.M_POWER_QUERY,
    "in": QueryLanguage.M_POWER_QUERY,
    "query": QueryLanguage.GRAPHQL,
    "mutation": QueryLanguage.GRAPHQL,
    "subscription": QueryLanguage.GRAPHQL,
    "$SYSTEM": QueryLanguage.SQL_TABULAR,
}


class QueryEngine:
    def __init__(self, doc: UnifiedQueryDocument | None = None):
        self._doc = doc

    def detect_language(self, text: str) -> QueryLanguage:
        for keyword, lang in _LANGUAGE_KEYWORDS.items():
            if keyword in text:
                return lang
        if re.search(r"FETCH\s+\d+", text, re.IGNORECASE):
            return QueryLanguage.OQL
        if re.search(r"ON\s+(COLUMNS|ROWS)", text, re.IGNORECASE):
            return QueryLanguage.MDX
        if re.search(r"\[[^\]]+\]", text):
            return QueryLanguage.MDX
        m = re.search(r"SELECT\s+(\w+)\s+FROM\s+(\w+)", text)
        if m:
            alias, entity = m.groups()
            if alias != "*":
                return QueryLanguage.JPQL
        if re.search(r"SELECT\s+\*\s+FROM\s+[A-Z]\w+", text):
            return QueryLanguage.MDX
        if re.search(r"FROM\s+\w+", text):
            m_alias = re.search(r"SELECT\s+(\w+)\s+FROM", text)
            if m_alias and m_alias.group(1) != "*":
                return QueryLanguage.JPQL
            return QueryLanguage.MDX
        return QueryLanguage.MDX

    async def async_load(
        self,
        source: str | bytes,
        parser_name: str | None = None,
        **options: Any,
    ) -> UnifiedQueryDocument:
        if parser_name and parser_name in _PARSER_MAP:
            parser = _PARSER_MAP[parser_name]()
        else:
            parser = self._detect_parser(source)
        if isinstance(source, str):
            from pathlib import Path
            result = await parser.parse_path(Path(source), str(source))
        else:
            result = await parser.parse_bytes(source, "load", "load")
        assert isinstance(result, UnifiedQueryDocument)
        self._doc = result
        return self._doc

    def load(
        self,
        source: str | bytes,
        parser_name: str | None = None,
        **options: Any,
    ) -> UnifiedQueryDocument:
        import asyncio
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.async_load(source, parser_name, **options))
        raise RuntimeError(
            "Cannot call load() synchronously in async context. "
            "Use await engine.async_load()."
        )

    async def async_parse(
        self,
        text: str,
        language: QueryLanguage | None = None,
    ) -> UnifiedQueryDocument:
        if language is None:
            language = self.detect_language(text)
        parser = _PARSER_MAP.get(language.value, MdxParser)()
        data = text.encode("utf-8")
        result = await parser.parse_bytes(data, "query", "query")
        assert isinstance(result, UnifiedQueryDocument)
        self._doc = result
        return self._doc

    async def async_convert(self, target_language: QueryLanguage) -> str:
        if self._doc is None:
            raise ValueError("No document loaded.")
        writer_cls = _WRITER_MAP.get(target_language.value)
        if writer_cls is None:
            raise ValueError(f"No writer for {target_language}")
        writer = writer_cls()
        result = await writer.write(self._doc)
        return result.decode("utf-8")

    async def async_execute(self, connection: Any = None) -> UnifiedQueryDocument:
        if self._doc is None:
            raise ValueError("No document loaded.")
        return self._doc

    def to_flat_table(self) -> FlatTableResult:
        if self._doc is None or self._doc.table is None:
            return FlatTableResult()
        return self._doc.table

    def to_mdx_cellset(self) -> MdxCellset:
        if self._doc is None or self._doc.cellset is None:
            return MdxCellset()
        return self._doc.cellset

    async def async_write(
        self,
        destination: str,
        format_name: str | None = None,
    ) -> bytes:
        if self._doc is None:
            raise ValueError("No document loaded.")
        if format_name and format_name in _WRITER_MAP:
            writer = _WRITER_MAP[format_name]()
        else:
            from pathlib import Path
            ext = Path(destination).suffix.lower()
            matched: list[BaseDocumentWriter] = []
            for cls in _WRITER_MAP.values():
                w = cls()
                if any(ext.endswith(e) for e in w.get_supported_extensions()):
                    matched.append(w)
            writer = matched[0] if matched else MdxWriter()
        result = await writer.write(self._doc)
        Path(destination).write_bytes(result)
        return result

    def write(self, destination: str, format_name: str | None = None) -> bytes:
        import asyncio
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.async_write(destination, format_name))
        raise RuntimeError("Cannot call write() synchronously in async context.")

    def _detect_parser(self, source: str | bytes) -> BaseDocumentParser:
        if isinstance(source, str):
            from pathlib import Path
            path = Path(source)
            ext = path.suffix.lower()
            ext_map: dict[str, type[BaseDocumentParser]] = {
                ".mdx": MdxParser,
                ".dax": DaxParser,
                ".m": PowerQueryMParser,
                ".jpql": JpqlParser,
                ".oql": OqlParser,
                ".gql": GraphqlQueryParser,
            }
            if ext in ext_map:
                return ext_map[ext]()
        src = source if isinstance(source, str) else source.decode("utf-8", errors="replace")
        for p_cls in _PARSER_MAP.values():
            p = p_cls()
            try:
                if p.can_parse(src):
                    return p
            except Exception:
                continue
        raise ValueError(
            f"Cannot auto-detect parser. Specify parser_name: {list(_PARSER_MAP.keys())}"
        )
