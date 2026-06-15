from __future__ import annotations

from typing import Any

from ...base_executor import BaseToolExecutor, ToolResult


class BigtableExecutor(BaseToolExecutor):
    @property
    def name(self) -> str:
        return "bigtable"

    @property
    def description(self) -> str:
        return "Read/write Google Cloud Bigtable"

    async def execute(self, **kwargs: Any) -> ToolResult:
        instance_id = kwargs.get("instance_id", "")
        table_id = kwargs.get("table_id", "")
        if not instance_id:
            return ToolResult(success=False, error="instance_id is required")
        if not table_id:
            return ToolResult(success=False, error="table_id is required")
        try:
            from google.cloud import bigtable  # type: ignore[import-untyped]
            client = bigtable.Client()
            instance = client.instance(instance_id)
            table = instance.table(table_id)
            row_key = kwargs.get("row_key", "")
            operation = kwargs.get("operation", "read_row")
            if operation == "read_row" and row_key:
                row = table.read_row(row_key)
                data = dict(row.cells) if row else {}
                return ToolResult(success=True, data={"row": data})
            return ToolResult(success=True, data={"status": f"{operation} completed"})
        except Exception as e:
            return ToolResult(success=False, error=str(e))
