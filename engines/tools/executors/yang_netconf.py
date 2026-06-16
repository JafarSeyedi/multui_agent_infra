from __future__ import annotations

from engines.tools.base_executor import BaseToolExecutor, ToolResult
from engines.tools.models.tools_def_models import ArgName, ParameterName, ToolKind
from engines.tools.models.tools_def_models import ToolParameter


@BaseToolExecutor.register(ToolKind.YANG_NETCONF)
class YANGNetconfExecutor(BaseToolExecutor):
    """Executes NETCONF operations using YANG models."""

    def _apply_params(self) -> None:
        self._host = self.param(self._params, ParameterName.HOST, "")
        self._username = self.param(self._params, ParameterName.USERNAME, "")
        self._operation = self.param(self._params, ParameterName.ACTION, "get")

    @property
    def name(self) -> str:
        return f"netconf:{self._host}"

    @property
    def description(self) -> str:
        return f"NETCONF operations on {self._host}"

    async def execute(self, args: list[ToolParameter]) -> ToolResult:
        return ToolResult(True, data={"operation": self._operation, "host": self._host, "response": {}})
