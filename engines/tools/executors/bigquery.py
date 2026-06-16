from __future__ import annotations

from engines.tools.base_executor import BaseToolExecutor, ToolResult
from engines.tools.models.tools_def_models import ArgName, ParameterName, ToolKind
from engines.tools.models.tools_def_models import ToolParameter


@BaseToolExecutor.register(ToolKind.BIGQUERY)
class BigQueryExecutor(BaseToolExecutor):
    def _apply_params(self) -> None:
        self._project_id = self.param(self._params, ParameterName.PROJECT, "")
        self._max_results = self.param(self._params, ParameterName.MAX_RESULTS, 1000)

    @property
    def name(self) -> str:
        return "bigquery"

    @property
    def description(self) -> str:
        return "Execute SQL queries on Google BigQuery"

    async def execute(self, args: list[ToolParameter]) -> ToolResult:
        query = self.arg(args, ArgName.INPUT, "")
        if not query:
            return ToolResult(success=False, error="Query cannot be empty")
        try:
            from google.cloud import bigquery  # type: ignore[import-untyped]
            client = bigquery.Client(project=self._project_id or None)
            job = client.query(query)
            rows = [dict(row) for row in job.result(max_results=self._max_results)]
            return ToolResult(success=True, data={"rows": rows, "total_rows": len(rows)})
        except Exception as e:
            return ToolResult(success=False, error=str(e))
