from __future__ import annotations

from typing import Any
from collections.abc import Callable

from engines.tools.base_executor import BaseToolExecutor
from engines.tools.base_executor import ToolResult


class PythonFunctionExecutor(BaseToolExecutor):
    """Executes a registered Python function by name."""

    def __init__(self) -> None:
        self._functions: dict[str, Callable[..., Any]] = {}

    def register_function(self, name: str, fn: Callable[..., Any]) -> None:
        self._functions[name] = fn

    @property
    def name(self) -> str:
        return "python_function"

    @property
    def description(self) -> str:
        return "Execute a registered Python function"

    async def execute(self, **kwargs: Any) -> ToolResult:
        fn_name = kwargs.get("function", "")
        fn = self._functions.get(fn_name)
        if fn is None:
            return ToolResult(False, error=f"Unknown function '{fn_name}'")
        fn_args = kwargs.get("args", ())
        fn_kwargs = kwargs.get("kwargs", {})
        try:
            result = fn(*fn_args, **fn_kwargs)
            return ToolResult(True, data={"function": fn_name, "result": result})
        except Exception as exc:
            return ToolResult(False, error=str(exc))
