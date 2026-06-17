from __future__ import annotations

from engines.tools.base_executor import BaseToolExecutor, ToolResult
from engines.tools.models.tools_def_models import ArgName, ParameterName, ToolKind
from engines.tools.models.tools_def_models import ToolParameter


@BaseToolExecutor.register(ToolKind.KNOWLEDGE_QUERY)
class QueryEngineKnowledgeExecutor(BaseToolExecutor):
    def _apply_params(self) -> None:
        self._engine = None

    async def _get_engine(self):
        if self._engine is not None:
            return self._engine
        from engines.knowledge.query import QueryEngine
        self._engine = QueryEngine()
        return self._engine

    @property
    def name(self) -> str:
        return "knowledge_query"

    @property
    def description(self) -> str:
        return "Query engine — detect, parse, convert, and write query languages (MDX, DAX, JPQL, OQL, GraphQL, Power Query M)"

    async def execute(self, args: list[ToolParameter]) -> ToolResult:
        action = self.arg(args, ArgName.ACTION, "detect")
        source_path = self.arg(args, ParameterName.SOURCE, "")
        query_text = self.arg(args, ParameterName.QUERY_TEXT, "")
        parser_name = self.arg(args, ParameterName.PARSER_NAME, "")
        target_format = self.arg(args, ParameterName.TARGET_FORMAT, "")
        language_str = self.arg(args, ParameterName.LANGUAGE, "")
        source_content = self.arg(args, ArgName.INPUT, "")

        try:
            engine = await self._get_engine()

            if action == "detect":
                text = query_text or source_content
                if not text:
                    return ToolResult(success=False, error="query_text or input required")
                lang = engine.detect_language(text)
                return ToolResult(success=True, data={"language": lang.value})

            elif action == "load":
                if source_path:
                    doc = await engine.async_load(source_path, parser_name=parser_name or None)
                elif source_content:
                    doc = await engine.async_parse(source_content)
                else:
                    return ToolResult(success=False, error="source_path or input required")
                return ToolResult(success=True, data={"document_id": doc.document_id if hasattr(doc, "document_id") else ""})

            elif action == "parse":
                text = query_text or source_content
                if not text:
                    return ToolResult(success=False, error="query_text or input required")
                from engines.knowledge.query.models import QueryLanguage
                lang = QueryLanguage(language_str) if language_str else None
                doc = await engine.async_parse(text, language=lang)
                return ToolResult(success=True, data={"document_id": doc.document_id if hasattr(doc, "document_id") else ""})

            elif action == "convert":
                if target_format:
                    from engines.knowledge.query.models import QueryLanguage
                    result = await engine.async_convert(QueryLanguage(target_format))
                    return ToolResult(success=True, data={"result": result})
                return ToolResult(success=False, error="target_format required")

            elif action == "to_table":
                table = engine.to_flat_table()
                return ToolResult(success=True, data={"table": str(table)})

            elif action == "to_cellset":
                cellset = engine.to_mdx_cellset()
                return ToolResult(success=True, data={"cellset": str(cellset)})

            return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
