from __future__ import annotations

import logging

from engines.tools.base_executor import BaseToolExecutor
from engines.tools.base_executor import ToolResult
from engines.tools.models.tools_def_models import ParameterName
from engines.tools.models.tools_def_models import Tool
from engines.tools.models.tools_def_models import ToolParameter

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

    async def execute_tool(self, tool: Tool) -> ToolResult:
        executor_cls = BaseToolExecutor.for_kind(tool.kind)
        if executor_cls is None:
            return ToolResult(
                False,
                error=f"No executor registered for tool kind '{tool.kind}'",
            )
        executor = executor_cls(tool.params)
        return await executor.execute(tool.args)

    async def execute(self, name: str, **kwargs: object) -> ToolResult:
        executor = self._executors.get(name)
        if executor is None:
            return ToolResult(False, error=f"Unknown tool '{name}'")
        try:
            args = _kwargs_to_tool_args(kwargs)
            return await executor.execute(args)
        except Exception as exc:
            logger.exception("Tool '%s' failed", name)
            return ToolResult(False, error=str(exc))


def _kwargs_to_tool_args(kwargs: dict[str, object]) -> list[ToolParameter]:
    result: list[ToolParameter] = []
    for k, v in kwargs.items():
        if isinstance(v, bool):
            param = ToolParameter(name=k, default=str(v).lower())
        elif isinstance(v, (int, float)):
            param = ToolParameter(name=k, default=str(v))
        elif isinstance(v, str):
            param = ToolParameter(name=k, default=v)
        else:
            import json
            param = ToolParameter(name=k, default=json.dumps(v))
        result.append(param)
    return result
