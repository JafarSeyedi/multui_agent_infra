from __future__ import annotations

from engines.tools.base_executor import BaseToolExecutor
from engines.tools.base_executor import ToolResult
from engines.tools.models.tools_def_models import ArgName
from engines.tools.models.tools_def_models import ParameterName
from engines.tools.models.tools_def_models import ToolKind
from engines.tools.models.tools_def_models import ToolParameter


@BaseToolExecutor.register(ToolKind.GRPC_SERVICE)
class GrpcToolExecutor(BaseToolExecutor):

    def _apply_params(self) -> None:
        self._target = self.param(self._params, "target", "")
        self._method = self.param(self._params, ParameterName.METHOD, "")

    @property
    def name(self) -> str:
        return f"grpc:{self._target}"

    @property
    def description(self) -> str:
        return f"Invoke gRPC service at {self._target}"

    async def execute(self, args: list[ToolParameter]) -> ToolResult:
        return ToolResult(True, data={"target": self._target, "method": self._method, "response": {}})
