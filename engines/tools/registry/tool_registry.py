from __future__ import annotations

import logging
from typing import Any

from engines.tools.base_executor import BaseToolExecutor
from engines.tools.base_executor import ToolResult

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry + mediator for tool executors. Agents use this to discover
    and invoke tools without knowing the concrete executor classes."""

    def __init__(self) -> None:
        self._executors: dict[str, BaseToolExecutor] = {}

    def register(self, executor: BaseToolExecutor) -> None:
        name = executor.name
        if name in self._executors:
            logger.warning("Overwriting existing executor '%s'", name)
        self._executors[name] = executor

    def unregister(self, name: str) -> None:
        self._executors.pop(name, None)

    def get(self, name: str) -> BaseToolExecutor | None:
        return self._executors.get(name)

    def list_tools(self) -> list[dict[str, str]]:
        return [
            {"name": e.name, "description": e.description}
            for e in self._executors.values()
        ]

    async def execute(self, name: str, **kwargs: Any) -> ToolResult:
        executor = self._executors.get(name)
        if executor is None:
            return ToolResult(False, error=f"Unknown tool '{name}'")
        try:
            return await executor.execute(**kwargs)
        except Exception as exc:
            logger.exception("Tool '%s' failed", name)
            return ToolResult(False, error=str(exc))
