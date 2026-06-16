from __future__ import annotations

from engines.tools.base_executor import BaseToolExecutor, ToolResult
from engines.tools.models.tools_def_models import ArgName, ParameterName, ToolKind
from engines.tools.models.tools_def_models import ToolParameter


@BaseToolExecutor.register(ToolKind.APIGEE)
class ApigeeExecutor(BaseToolExecutor):
    def _apply_params(self) -> None:
        self._base_url = self.param(self._params, ParameterName.URL, "https://apihub.googleapis.com/v1")
        self._api_id = self.param(self._params, ParameterName.API_ID, "")
        self._action = self.param(self._params, ParameterName.ACTION, "search")

    @property
    def name(self) -> str:
        return "apigee"

    @property
    def description(self) -> str:
        return "Query Apigee API Hub for API discovery"

    async def execute(self, args: list[ToolParameter]) -> ToolResult:
        import aiohttp
        try:
            async with aiohttp.ClientSession() as session:
                if self._action == "search":
                    query = self.arg(args, ArgName.INPUT, "")
                    async with session.get(f"{self._base_url}/apis", params={"q": query}) as resp:
                        resp.raise_for_status()
                        data = await resp.json()
                        return ToolResult(success=True, data=data)
                elif self._action == "get":
                    async with session.get(f"{self._base_url}/apis/{self._api_id}") as resp:
                        resp.raise_for_status()
                        data = await resp.json()
                        return ToolResult(success=True, data=data)
                return ToolResult(success=True, data={"apis": []})
        except Exception as e:
            return ToolResult(success=False, error=str(e))
