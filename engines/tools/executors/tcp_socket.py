from __future__ import annotations

from engines.tools.base_executor import BaseToolExecutor
from engines.tools.base_executor import ToolResult
from engines.tools.models.tools_def_models import ArgName
from engines.tools.models.tools_def_models import ParameterName
from engines.tools.models.tools_def_models import ToolKind
from engines.tools.models.tools_def_models import ToolParameter


@BaseToolExecutor.register(ToolKind.TCP_SOCKET)
class TCPSocketExecutor(BaseToolExecutor):

    def _apply_params(self) -> None:
        self._host = self.param(self._params, ParameterName.HOST, "localhost")
        self._port = self.param(self._params, ParameterName.PORT, 0)

    @property
    def name(self) -> str:
        return f"tcp:{self._host}:{self._port}"

    @property
    def description(self) -> str:
        return f"TCP socket to {self._host}:{self._port}"

    async def execute(self, args: list[ToolParameter]) -> ToolResult:
        data = self.arg(args, ArgName.DATA, "")
        return ToolResult(True, data={"sent": len(data), "response": ""})
