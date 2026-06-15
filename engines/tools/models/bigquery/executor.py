from __future__ import annotations

from typing import Any

from ...base_executor import BaseToolExecutor, ToolResult


class BigQueryExecutor(BaseToolExecutor):
    @property
    def name(self) -> str:
        return "bigquery"

    @property
    def description(self) -> str:
        return "Execute SQL queries on Google BigQuery"

    async def execute(self, **kwargs: Any) -> ToolResult:
        query = kwargs.get("query", "")
        project_id = kwargs.get("project_id", "")
        if not query:
            return ToolResult(success=False, error="Query cannot be empty")
        try:
            from google.cloud import bigquery
            client = bigquery.Client(project=project_id or None)
            job = client.query(query)
            rows = [dict(row) for row in job.result(max_results=kwargs.get("max_results", 1000))]
            return ToolResult(success=True, data={"rows": rows, "total_rows": len(rows)})
        except Exception as e:
            return ToolResult(success=False, error=str(e))
