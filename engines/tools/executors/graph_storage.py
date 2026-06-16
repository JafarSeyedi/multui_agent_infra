from __future__ import annotations

import json

from engines.tools.base_executor import BaseToolExecutor, ToolResult
from engines.tools.models.tools_def_models import ArgName, ParameterName, ToolKind
from engines.tools.models.tools_def_models import ToolParameter

Metadata = dict


@BaseToolExecutor.register(ToolKind.GRAPH_STORAGE)
class GraphStorageExecutor(BaseToolExecutor):
    def _apply_params(self) -> None:
        self._backend = self.param(self._params, ParameterName.BACKEND, "neo4j")
        self._connection = self.param(self._params, ParameterName.CONNECTION, "")
        self._backend_instance = None

    async def _storage(self):
        if self._backend_instance is not None:
            return self._backend_instance
        from engines.storage.factories import create_storage
        try:
            if self._connection:
                self._backend_instance = create_storage("graph", backend=self._backend, url=self._connection)
            else:
                self._backend_instance = create_storage("graph", backend=self._backend)
            if not getattr(self._backend_instance, "_connected", False):
                await self._backend_instance.connect()
        except Exception:
            self._backend_instance = None
        return self._backend_instance

    @property
    def name(self) -> str:
        return f"graph:{self._backend}"

    @property
    def description(self) -> str:
        return f"Graph storage via {self._backend} backend"

    async def execute(self, args: list[ToolParameter]) -> ToolResult:
        action = self.arg(args, ArgName.ACTION, "query")
        node_id = self.arg(args, ParameterName.NODE_ID, "")
        source = self.arg(args, ParameterName.SOURCE_NODE, "")
        target = self.arg(args, ParameterName.TARGET_NODE, "")
        relation = self.arg(args, ParameterName.RELATION, "")
        properties_str = self.arg(args, ParameterName.PROPERTIES, "{}")
        cypher = self.arg(args, ArgName.QUERY, "")

        try:
            store = await self._storage()
            if store is None:
                return ToolResult(success=True, data={"note": "no backend configured"})

            properties = json.loads(properties_str) if isinstance(properties_str, str) else properties_str

            if action == "add_node":
                await store.add_node(node_id, properties)
                return ToolResult(success=True, data={"node_id": node_id, "added": True})
            elif action == "add_edge":
                await store.add_edge(source, target, relation, properties=properties or None)
                return ToolResult(success=True, data={"edge": f"{source}-[{relation}]->{target}", "added": True})
            elif action == "query":
                results = await store.query(cypher)
                return ToolResult(success=True, data={"results": results})
            return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
