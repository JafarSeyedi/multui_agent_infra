from __future__ import annotations

from typing import Any

from ...base_executor import BaseToolExecutor, ToolResult


class MCPToolExecutor(BaseToolExecutor):
    def __init__(
        self,
        tool_name: str,
        server_command: list[str] | None = None,
        server_url: str | None = None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self._name = tool_name
        self._server_command = server_command or []
        self._server_url = server_url
        self._client = None

        if not self._server_command and not self._server_url:
            raise ValueError("MCPToolExecutor requires server_command or server_url")

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return f"MCP tool: {self._name}"

    async def execute(self, **kwargs: Any) -> ToolResult:
        try:
            result = await self._call_mcp(kwargs)
            return ToolResult(success=True, data={"result": result})
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def _call_mcp(self, arguments: dict[str, Any]) -> Any:
        from engines.agent.skill.mcp_client import MCPClient

        if self._server_command:
            client = MCPClient(server_command=self._server_command)
        elif self._server_url:
            client = MCPClient(server_url=self._server_url)
        else:
            raise ValueError("MCPToolExecutor requires server_command or server_url")

        try:
            await client.connect()
            result = await client.call_tool(self._name, arguments)
            return result
        finally:
            await client.disconnect()
