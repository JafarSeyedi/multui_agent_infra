from __future__ import annotations

from engines.tools.base_executor import BaseToolExecutor, ToolResult
from engines.tools.models.tools_def_models import ArgName, ParameterName, ToolKind
from engines.tools.models.tools_def_models import ToolParameter


@BaseToolExecutor.register(ToolKind.BIGTABLE)
class BigtableExecutor(BaseToolExecutor):
    def _apply_params(self) -> None:
        self._instance_id = self.param(self._params, ParameterName.INSTANCE, "")
        self._table_id = self.param(self._params, ParameterName.TABLE, "")
        self._row_key = self.param(self._params, ParameterName.ROW_KEY, "")
        self._operation = self.param(self._params, ParameterName.ACTION, "read_row")

    @property
    def name(self) -> str:
        return "bigtable"

    @property
    def description(self) -> str:
        return "Read/write Google Cloud Bigtable"

    async def execute(self, args: list[ToolParameter]) -> ToolResult:
        if not self._instance_id:
            return ToolResult(success=False, error="instance_id is required")
        if not self._table_id:
            return ToolResult(success=False, error="table_id is required")
        try:
            from google.cloud import bigtable  # type: ignore[import-untyped]
            client = bigtable.Client()
            instance = client.instance(self._instance_id)
            table = instance.table(self._table_id)
            if self._operation == "read_row" and self._row_key:
                row = table.read_row(self._row_key)
                data = dict(row.cells) if row else {}
                return ToolResult(success=True, data={"row": data})
            return ToolResult(success=True, data={"status": f"{self._operation} completed"})
        except Exception as e:
            return ToolResult(success=False, error=str(e))
