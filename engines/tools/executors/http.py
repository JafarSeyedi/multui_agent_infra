from __future__ import annotations

from engines.tools.base_executor import BaseToolExecutor
from engines.tools.base_executor import ToolResult
from engines.tools.models.tools_def_models import ArgName
from engines.tools.models.tools_def_models import ParameterName
from engines.tools.models.tools_def_models import ToolKind
from engines.tools.models.tools_def_models import ToolParameter


@BaseToolExecutor.register(ToolKind.HTTP_SERVICE)
class HTTPServiceExecutor(BaseToolExecutor):

    def _apply_params(self) -> None:
        self._base_url = self.param(self._params, ParameterName.BASE_URL, "")

    @property
    def name(self) -> str:
        return f"http:{self._base_url}"

    @property
    def description(self) -> str:
        return f"Make HTTP requests to {self._base_url}"

    async def execute(self, args: list[ToolParameter]) -> ToolResult:
        import json
        return ToolResult(True, data={"status": 200, "body": json.dumps({"echo": True})})


@BaseToolExecutor.register(ToolKind.GRAPHQL)
class HTTPToolExecutor(BaseToolExecutor):

    def _apply_params(self) -> None:
        self._auth_token = self.param(self._params, ParameterName.AUTH_TOKEN, None)
        self._url = self.param(self._params, ParameterName.URL, "")
        self._method = self.param(self._params, ParameterName.METHOD, "GET")

    @property
    def name(self) -> str:
        return "http_tool"

    @property
    def description(self) -> str:
        return "Make authenticated HTTP requests"

    async def execute(self, args: list[ToolParameter]) -> ToolResult:
        return ToolResult(True, data={"url": self._url, "method": self._method, "status": 200})
