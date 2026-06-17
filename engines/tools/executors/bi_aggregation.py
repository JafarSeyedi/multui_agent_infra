from __future__ import annotations

import json

from engines.tools.base_executor import BaseToolExecutor, ToolResult
from engines.tools.models.tools_def_models import ArgName, ParameterName, ToolKind
from engines.tools.models.tools_def_models import ToolParameter


@BaseToolExecutor.register(ToolKind.KNOWLEDGE_BI_AGGREGATION)
class BiAggregationKnowledgeExecutor(BaseToolExecutor):
    def _apply_params(self) -> None:
        self._engine = None

    async def _get_engine(self):
        if self._engine is not None:
            return self._engine
        from engines.knowledge.bi_aggregation import BiAggregationEngine
        self._engine = BiAggregationEngine()
        return self._engine

    @property
    def name(self) -> str:
        return "knowledge_bi_aggregation"

    @property
    def description(self) -> str:
        return "BI aggregation engine — load, query, and convert BI semantic models (CWM, Mondrian, TMSL, CDM, etc.)"

    async def execute(self, args: list[ToolParameter]) -> ToolResult:
        action = self.arg(args, ArgName.ACTION, "get_cubes")
        source_path = self.arg(args, ParameterName.SOURCE, "")
        parser_name = self.arg(args, ParameterName.PARSER_NAME, "")
        target_format = self.arg(args, ParameterName.TARGET_FORMAT, "")
        cube_name = self.arg(args, ParameterName.CUBE_NAME, "")
        group_by_str = self.arg(args, ParameterName.GROUP_BY, "[]")
        measures_str = self.arg(args, ParameterName.MEASURES, "[]")
        filter_expr = self.arg(args, ParameterName.FILTER_EXPR, "")
        materialized_str = self.arg(args, ParameterName.MATERIALIZED, "false")

        try:
            engine = await self._get_engine()

            if action == "load":
                if source_path:
                    doc = await engine.async_load(source_path, parser_name=parser_name or None)
                    return ToolResult(success=True, data={"document_id": doc.document_id if hasattr(doc, "document_id") else "", "title": doc.title if hasattr(doc, "title") else ""})
                return ToolResult(success=False, error="source_path required")

            elif action == "get_cubes":
                cubes = engine.get_cubes()
                return ToolResult(success=True, data={"cubes": [str(c) for c in cubes]})

            elif action == "get_dimensions":
                dims = engine.get_dimensions(cube_name=cube_name or None)
                return ToolResult(success=True, data={"dimensions": [str(d) for d in dims]})

            elif action == "get_measures":
                measures = engine.get_measures(cube_name=cube_name or None)
                return ToolResult(success=True, data={"measures": [str(m) for m in measures]})

            elif action == "get_relationships":
                rels = engine.get_relationships()
                return ToolResult(success=True, data={"relationships": [str(r) for r in rels]})

            elif action == "get_aggregations":
                aggs = engine.get_aggregations()
                return ToolResult(success=True, data={"aggregations": [str(a) for a in aggs]})

            elif action == "aggregate":
                group_by = json.loads(group_by_str)
                measures = json.loads(measures_str)
                materialized = materialized_str.lower() in ("true", "1", "yes")
                agg = engine.aggregate(
                    group_by=group_by,
                    measures=measures,
                    source=cube_name or None,
                    filter_expr=filter_expr or None,
                    materialized=materialized,
                )
                return ToolResult(success=True, data={"aggregation": str(agg)})

            elif action == "convert":
                if target_format:
                    result = await engine.async_convert(target_format)
                    return ToolResult(success=True, data={"result": result.decode("utf-8", errors="replace")})
                return ToolResult(success=False, error="target_format required")

            return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
