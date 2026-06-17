from __future__ import annotations

import json

from engines.tools.base_executor import BaseToolExecutor, ToolResult
from engines.tools.models.tools_def_models import ArgName, ParameterName, ToolKind
from engines.tools.models.tools_def_models import ToolParameter


@BaseToolExecutor.register(ToolKind.KNOWLEDGE_SEMANTIC_GRAPH)
class SemanticGraphKnowledgeExecutor(BaseToolExecutor):
    def _apply_params(self) -> None:
        self._engine = None

    async def _get_engine(self):
        if self._engine is not None:
            return self._engine
        from engines.knowledge.semantic_graph import SemanticGraphEngine
        self._engine = SemanticGraphEngine()
        return self._engine

    @property
    def name(self) -> str:
        return "knowledge_semantic_graph"

    @property
    def description(self) -> str:
        return "Semantic graph engine — load, query, traverse, and convert RDF/knowledge graphs"

    async def execute(self, args: list[ToolParameter]) -> ToolResult:
        action = self.arg(args, ArgName.ACTION, "query")
        node_id = self.arg(args, ParameterName.NODE_ID, "")
        source_id = self.arg(args, ParameterName.SOURCE_NODE, "")
        target_id = self.arg(args, ParameterName.TARGET_NODE, "")
        relation = self.arg(args, ParameterName.RELATION, "")
        label = self.arg(args, ParameterName.NODE_LABEL, "")
        node_type = self.arg(args, ParameterName.NODE_TYPE, "")
        max_depth_str = self.arg(args, ParameterName.MAX_DEPTH, "1")
        parser_name = self.arg(args, ParameterName.PARSER_NAME, "")
        source_path = self.arg(args, ParameterName.SOURCE, "")
        target_format = self.arg(args, ParameterName.TARGET_FORMAT, "")
        query_text = self.arg(args, ParameterName.QUERY_TEXT, "")
        extra_args_str = self.arg(args, ParameterName.EXTRA_ARGS, "{}")

        try:
            engine = await self._get_engine()

            if action == "load":
                if source_path:
                    doc = await engine.async_load(source_path, parser_name=parser_name or None)
                elif query_text:
                    doc = await engine.async_parse(query_text, model_format=parser_name or None)
                else:
                    return ToolResult(success=False, error="source or query_text required")
                return ToolResult(success=True, data={"document_id": doc.document_id if hasattr(doc, "document_id") else ""})

            elif action == "get_node":
                node = engine.get_node(node_id)
                if node:
                    return ToolResult(success=True, data={"node": str(node)})
                return ToolResult(success=False, error=f"Node '{node_id}' not found")

            elif action == "find_nodes":
                nodes = engine.find_nodes(label=label or None, node_type=node_type or None)
                return ToolResult(success=True, data={"nodes": [str(n) for n in nodes]})

            elif action == "get_edges":
                edges = engine.get_edges()
                return ToolResult(success=True, data={"edges": [str(e) for e in edges]})

            elif action == "find_edges":
                edges = engine.find_edges(source=source_id or None, target=target_id or None, relation=relation or None)
                return ToolResult(success=True, data={"edges": [str(e) for e in edges]})

            elif action == "neighbors":
                max_depth = int(max_depth_str)
                neighbors = engine.neighbors(node_id, max_depth=max_depth)
                return ToolResult(success=True, data={"neighbors": [(str(n), str(e), d) for n, e, d in neighbors]})

            elif action == "shortest_path":
                path = engine.shortest_path(source_id, target_id)
                if path:
                    return ToolResult(success=True, data={"path": [str(n) for n in path]})
                return ToolResult(success=False, error="No path found")

            elif action == "subgraph":
                node_ids = json.loads(extra_args_str) if extra_args_str else []
                kg = engine.subgraph(node_ids)
                return ToolResult(success=True, data={"nodes": len(kg.nodes), "edges": len(kg.edges)})

            elif action == "statistics":
                stats = engine.get_statistics()
                return ToolResult(success=True, data=stats)

            elif action == "validate":
                warnings = engine.validate()
                return ToolResult(success=True, data={"warnings": warnings})

            elif action == "convert":
                if target_format:
                    result = await engine.async_convert(target_format)
                    return ToolResult(success=True, data={"result": result.decode("utf-8", errors="replace")})
                return ToolResult(success=False, error="target_format required")

            return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
