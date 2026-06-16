from __future__ import annotations

from engines.tools.base_executor import BaseToolExecutor, ToolResult
from engines.tools.models.tools_def_models import ArgName, ParameterName, ToolKind
from engines.tools.models.tools_def_models import ToolParameter


@BaseToolExecutor.register(ToolKind.MCP)
class MCPToolExecutor(BaseToolExecutor):

    def _apply_params(self) -> None:
        self._server_command = self.param(self._params, ParameterName.COMMAND, [])
        self._server_url = self.param(self._params, ParameterName.URL, "")
        self._name = self.param(self._params, "tool_name", "")
        if self._name and self._name.startswith(("http://", "https://")):
            self._server_url = self._name
            self._name = ""
        self._client = None
        if not self._server_command and not self._server_url:
            raise ValueError("MCPToolExecutor requires server_command or server_url")

    @property
    def name(self) -> str:
        return self._name or f"mcp:{self._server_url}"

    @property
    def description(self) -> str:
        return f"MCP tool: {self._name or self._server_url}"

    async def execute(self, args: list[ToolParameter]) -> ToolResult:
        try:
            arguments = {
                p.name.value if isinstance(p.name, ParameterName) else p.name: self.arg(args, p.name)
                for p in args
            }
            result = await self._call_mcp(arguments)
            return ToolResult(success=True, data={"result": result})
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def _call_mcp(self, arguments: dict) -> object:
        from engines.agent.skill.mcp_client import MCPClient

        if self._server_command:
            client = MCPClient(server_command=self._server_command)
        elif self._server_url:
            client = MCPClient(server_url=self._server_url)
        else:
            raise ValueError("MCPToolExecutor requires server_command or server_url")

        tool_name = arguments.pop("tool", self._name) if not self._name else self._name

        try:
            await client.connect()
            result = await client.call_tool(tool_name, arguments)
            return result
        finally:
            await client.disconnect()
