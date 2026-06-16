from __future__ import annotations

from engines.tools.base_executor import BaseToolExecutor
from engines.tools.base_executor import ToolResult
from engines.tools.models.tools_def_models import ArgName, ParameterName, ToolKind
from engines.tools.models.tools_def_models import ToolParameter


@BaseToolExecutor.register(ToolKind.COMPOSITE)
class CompositeExecutor(BaseToolExecutor):
    """Composite pattern — runs multiple executors in sequence."""

    def _apply_params(self) -> None:
        self._executors: list[BaseToolExecutor] = []

    def add(self, executor: BaseToolExecutor) -> None:
        self._executors.append(executor)

    @property
    def name(self) -> str:
        return "composite"

    @property
    def description(self) -> str:
        return "Run multiple tools in sequence"

    async def execute(self, args: list[ToolParameter]) -> ToolResult:
        results: list[dict[str, object]] = []
        for executor in self._executors:
            result = await executor.execute(args)
            results.append({"executor": executor.name, "success": result.success, "data": result.data})
            if not result.success:
                return ToolResult(False, data=results, error=f"Step '{executor.name}' failed")
        return ToolResult(True, data=results)
