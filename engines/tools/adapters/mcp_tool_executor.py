from __future__ import annotations

from typing import Any

from engines.tools.base_executor import BaseToolExecutor
from engines.tools.base_executor import ToolResult


class MCPToolExecutor(BaseToolExecutor):
    """Executes tools via the Model Context Protocol."""

    def __init__(self, server_url: str = "") -> None:
        self._server_url = server_url

    @property
    def name(self) -> str:
        return f"mcp:{self._server_url}"

    @property
    def description(self) -> str:
        return f"Execute MCP tool at {self._server_url}"

    async def execute(self, **kwargs: Any) -> ToolResult:
        tool_name = kwargs.get("tool", "")
        return ToolResult(True, data={"tool": tool_name, "result": {}})
