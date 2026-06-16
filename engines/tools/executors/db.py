from __future__ import annotations

from engines.tools.base_executor import BaseToolExecutor, ToolResult
from engines.tools.models.tools_def_models import ArgName, ParameterName, ToolKind
from engines.tools.models.tools_def_models import ToolParameter


@BaseToolExecutor.register(ToolKind.DB_STATEMENT)
@BaseToolExecutor.register(ToolKind.DB_QUERY)
class DBQueryExecutor(BaseToolExecutor):
    def _apply_params(self) -> None:
        self._connection_string = self.param(self._params, ParameterName.CONNECTION, "")
        self._backend = self.param(self._params, ParameterName.BACKEND, "sqlite")
        self._backend_instance = None

    async def _storage(self):
        if self._backend_instance is not None:
            return self._backend_instance
        from engines.storage.factories import create_storage
        if self._connection_string:
            self._backend_instance = create_storage("relational", backend=self._backend, connection_string=self._connection_string)
        else:
            if self._backend == "sqlite":
                self._backend_instance = create_storage("relational", backend=self._backend, db_path=":memory:")
            else:
                self._backend_instance = None
        if self._backend_instance is not None and not self._backend_instance._connected:
            await self._backend_instance.connect()
        return self._backend_instance

    @property
    def name(self) -> str:
        return "db_query"

    @property
    def description(self) -> str:
        return "Execute SQL against a relational database"

    async def execute(self, args: list[ToolParameter]) -> ToolResult:
        query = self.arg(args, ArgName.INPUT, "")

        try:
            store = await self._storage()
            if store is None:
                return ToolResult(success=True, data={"query": query, "rows": [], "row_count": 0})
            rows = await store.fetch_all(query)
            return ToolResult(success=True, data={"rows": rows, "row_count": len(rows)})
        except Exception as e:
            return ToolResult(success=False, error=str(e))
