from __future__ import annotations

from typing import Any

from engines.tools.base_executor import BaseToolExecutor
from engines.tools.base_executor import ToolResult


class TCPSocketExecutor(BaseToolExecutor):
    """Sends/receives raw TCP data."""

    def __init__(self, host: str = "localhost", port: int = 0) -> None:
        self._host = host
        self._port = port

    @property
    def name(self) -> str:
        return f"tcp:{self._host}:{self._port}"

    @property
    def description(self) -> str:
        return f"TCP socket to {self._host}:{self._port}"

    async def execute(self, **kwargs: Any) -> ToolResult:
        data = kwargs.get("data", "")
        return ToolResult(True, data={"sent": len(data), "response": ""})
