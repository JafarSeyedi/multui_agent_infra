from __future__ import annotations

from collections.abc import Callable

from engines.tools.base_executor import BaseToolExecutor, ToolResult
from engines.tools.models.tools_def_models import ArgName, ParameterName, ToolKind
from engines.tools.models.tools_def_models import ToolParameter


@BaseToolExecutor.register(ToolKind.PYTHON_FUNCTION)
class PythonFunctionExecutor(BaseToolExecutor):
    """Executes a registered Python function by name."""

    def _apply_params(self) -> None:
        self._functions: dict[str, Callable[..., object]] = {}
        self._fn_name = self.param(self._params, ParameterName.FUNCTION, "")

    def register_function(self, name: str, fn: Callable[..., object]) -> None:
        self._functions[name] = fn

    @property
    def name(self) -> str:
        return "python_function"

    @property
    def description(self) -> str:
        return "Execute a registered Python function"

    async def execute(self, args: list[ToolParameter]) -> ToolResult:
        fn = self._functions.get(self._fn_name)
        if fn is None:
            return ToolResult(False, error=f"Unknown function '{self._fn_name}'")
        fn_args = self.arg(args, "args", ())
        fn_kwargs = self.arg(args, "kwargs", {})
        try:
            result = fn(*fn_args, **fn_kwargs)
            return ToolResult(True, data={"function": self._fn_name, "result": result})
        except Exception as exc:
            return ToolResult(False, error=str(exc))
