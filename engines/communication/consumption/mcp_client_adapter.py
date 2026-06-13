from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class MCPClientAdapter:
    """Adapter pattern — wraps MCP stdio/SSE transport as a unified client.

    Provides a consistent interface for calling MCP tools regardless
    of the underlying transport (stdio, SSE, HTTP).
    """

    def __init__(self, command: str = "", args: list[str] | None = None) -> None:
        self._command = command
        self._args = args or []
        self._process: asyncio.subprocess.Process | None = None
        self._request_id = 0

    async def connect(self) -> None:
        if not self._command:
            raise ValueError("MCP command not configured")
        self._process = await asyncio.create_subprocess_exec(
            self._command,
            *self._args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

    async def disconnect(self) -> None:
        if self._process is not None:
            self._process.kill()
            await self._process.wait()
        self._process = None

    async def list_tools(self) -> list[dict[str, Any]]:
        result = await self._send_request("list_tools", {})
        return result.get("tools", [])

    async def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self._send_request("call_tool", {"name": name, "arguments": arguments or {}})

    async def _send_request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        if self._process is None or self._process.stdin is None:
            raise RuntimeError("MCP client not connected")

        self._request_id += 1
        request = json.dumps({"jsonrpc": "2.0", "id": self._request_id, "method": method, "params": params})
        self._process.stdin.write((request + "\n").encode())
        await self._process.stdin.drain()

        stdout = self._process.stdout
        if stdout is None:
            raise RuntimeError("MCP client stdout not available")
        line = await stdout.readline()
        response = json.loads(line.decode())
        if "error" in response:
            raise RuntimeError(f"MCP error: {response['error']}")
        return response.get("result", {})

    @property
    def is_connected(self) -> bool:
        return self._process is not None and self._process.returncode is None


class MCPClientProxy:
    """Proxy pattern — lazy-init wrapper for MCPClientAdapter.

    Defers connection until first tool call. Automatically connects
    on demand and disconnects when used as a context manager.
    """

    def __init__(self, command: str, args: list[str] | None = None) -> None:
        self._command = command
        self._args = args or []
        self._client: MCPClientAdapter | None = None

    async def _ensure(self) -> MCPClientAdapter:
        if self._client is None:
            self._client = MCPClientAdapter(self._command, self._args)
            await self._client.connect()
        return self._client

    async def list_tools(self) -> list[dict[str, Any]]:
        client = await self._ensure()
        return await client.list_tools()

    async def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        client = await self._ensure()
        return await client.call_tool(name, arguments)

    async def disconnect(self) -> None:
        if self._client is not None:
            await self._client.disconnect()
        self._client = None
