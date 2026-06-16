from __future__ import annotations

import json

from engines.tools.base_executor import BaseToolExecutor, ToolResult
from engines.tools.models.tools_def_models import ArgName, ParameterName, ToolKind
from engines.tools.models.tools_def_models import ToolParameter

Metadata = dict


@BaseToolExecutor.register(ToolKind.VECTOR_DB)
class VectorDBExecutor(BaseToolExecutor):
    def _apply_params(self) -> None:
        self._backend = self.param(self._params, ParameterName.BACKEND, "memory")
        self._connection = self.param(self._params, ParameterName.CONNECTION, "")
        self._dimensions = int(self.param(self._params, ParameterName.DIMENSIONS, "128"))
        self._backend_instance = None

    async def _storage(self):
        if self._backend_instance is not None:
            return self._backend_instance
        from engines.storage.factories import create_storage
        try:
            if self._connection:
                self._backend_instance = create_storage("vector", backend=self._backend, connection_string=self._connection)
            else:
                self._backend_instance = create_storage("vector", backend=self._backend)
            if not getattr(self._backend_instance, "_connected", False):
                await self._backend_instance.connect()
        except Exception:
            self._backend_instance = None
        return self._backend_instance

    @property
    def name(self) -> str:
        return f"vector_db:{self._backend}"

    @property
    def description(self) -> str:
        return f"Vector database via {self._backend} backend"

    async def execute(self, args: list[ToolParameter]) -> ToolResult:
        action = self.arg(args, ArgName.ACTION, "query")
        vector_id = self.arg(args, ParameterName.NODE_ID, "")
        vector_str = self.arg(args, ParameterName.EMBEDDING, "[]")
        metadata_str = self.arg(args, ParameterName.METADATA, "{}")
        top_k_str = self.arg(args, ParameterName.TOP_K, "5")
        filters_str = self.arg(args, ArgName.FILTERS, "{}")

        try:
            store = await self._storage()
            if store is None:
                return ToolResult(success=True, data={"note": "no backend configured"})

            vector = json.loads(vector_str) if isinstance(vector_str, str) else vector_str
            metadata = json.loads(metadata_str) if isinstance(metadata_str, str) else metadata_str
            filters = json.loads(filters_str) if isinstance(filters_str, str) else filters_str
            top_k = int(top_k_str)

            if action == "upsert":
                await store.upsert(vector_id, vector, metadata=metadata or None)
                return ToolResult(success=True, data={"id": vector_id, "upserted": True})
            elif action == "query":
                results = await store.query(vector, top_k=top_k, filters=filters or None)
                return ToolResult(success=True, data={"results": results})
            elif action == "delete":
                await store.delete(vector_id)
                return ToolResult(success=True, data={"id": vector_id, "deleted": True})
            return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
