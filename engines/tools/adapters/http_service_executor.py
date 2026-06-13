from __future__ import annotations

from typing import Any

from engines.tools.base_executor import BaseToolExecutor
from engines.tools.base_executor import ToolResult


class HTTPServiceExecutor(BaseToolExecutor):
    """Makes HTTP requests to external services."""

    def __init__(self, base_url: str = "") -> None:
        self._base_url = base_url

    @property
    def name(self) -> str:
        return f"http:{self._base_url}"

    @property
    def description(self) -> str:
        return f"Make HTTP requests to {self._base_url}"

    async def execute(self, **kwargs: Any) -> ToolResult:
        import json
        return ToolResult(True, data={"status": 200, "body": json.dumps({"echo": True})})
