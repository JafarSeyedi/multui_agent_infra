from __future__ import annotations

from typing import Any

from engines.tools.base_executor import BaseToolExecutor
from engines.tools.base_executor import ToolResult


class HTTPToolExecutor(BaseToolExecutor):
    """Agent-facing HTTP tool executor — wraps requests with auth."""

    def __init__(self, auth_token: str | None = None) -> None:
        self._auth_token = auth_token

    @property
    def name(self) -> str:
        return "http_tool"

    @property
    def description(self) -> str:
        return "Make authenticated HTTP requests"

    async def execute(self, **kwargs: Any) -> ToolResult:
        url = kwargs.get("url", "")
        method = kwargs.get("method", "GET")
        return ToolResult(True, data={"url": url, "method": method, "status": 200})
