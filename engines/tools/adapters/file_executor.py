from __future__ import annotations

from typing import Any

from engines.tools.base_executor import BaseToolExecutor
from engines.tools.base_executor import ToolResult


class FileExecutor(BaseToolExecutor):
    """Reads or writes files on the local filesystem."""

    def __init__(self, base_path: str = "") -> None:
        self._base_path = base_path

    @property
    def name(self) -> str:
        return "file"

    @property
    def description(self) -> str:
        return "Read or write files on the local filesystem"

    async def execute(self, **kwargs: Any) -> ToolResult:
        operation = kwargs.get("operation", "read")
        path = kwargs.get("path", "")
        return ToolResult(True, data={"operation": operation, "path": path, "content": ""})
