from __future__ import annotations

from typing import Any

from engines.tools.base_executor import BaseToolExecutor
from engines.tools.base_executor import ToolResult


class CompositeExecutor(BaseToolExecutor):
    """Composite pattern — runs multiple executors in sequence."""

    def __init__(self, executors: list[BaseToolExecutor] | None = None) -> None:
        self._executors = executors or []

    def add(self, executor: BaseToolExecutor) -> None:
        self._executors.append(executor)

    @property
    def name(self) -> str:
        return "composite"

    @property
    def description(self) -> str:
        return "Run multiple tools in sequence"

    async def execute(self, **kwargs: Any) -> ToolResult:
        results: list[dict[str, Any]] = []
        for executor in self._executors:
            result = await executor.execute(**kwargs)
            results.append({"executor": executor.name, "success": result.success, "data": result.data})
            if not result.success:
                return ToolResult(False, data=results, error=f"Step '{executor.name}' failed")
        return ToolResult(True, data=results)
