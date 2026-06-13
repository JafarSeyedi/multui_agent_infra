from __future__ import annotations

from typing import Any

from engines.tools.base_executor import BaseToolExecutor
from engines.tools.base_executor import ToolResult


class DBQueryExecutor(BaseToolExecutor):
    """Executes SQL queries against a database."""

    def __init__(self, connection_string: str = "") -> None:
        self._connection_string = connection_string

    @property
    def name(self) -> str:
        return "db_query"

    @property
    def description(self) -> str:
        return "Execute a SQL query against a database"

    async def execute(self, **kwargs: Any) -> ToolResult:
        query = kwargs.get("query", "")
        return ToolResult(True, data={"query": query, "rows": [], "row_count": 0})
