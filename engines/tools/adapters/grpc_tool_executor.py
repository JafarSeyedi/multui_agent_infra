from __future__ import annotations

from typing import Any

from engines.tools.base_executor import BaseToolExecutor
from engines.tools.base_executor import ToolResult


class GrpcToolExecutor(BaseToolExecutor):
    """Invokes a gRPC service method."""

    def __init__(self, target: str = "") -> None:
        self._target = target

    @property
    def name(self) -> str:
        return f"grpc:{self._target}"

    @property
    def description(self) -> str:
        return f"Invoke gRPC service at {self._target}"

    async def execute(self, **kwargs: Any) -> ToolResult:
        method = kwargs.get("method", "")
        return ToolResult(True, data={"target": self._target, "method": method, "response": {}})
