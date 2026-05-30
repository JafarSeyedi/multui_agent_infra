"""Minimal MCP client adapter for tools exposed over STDIO or SSE/HTTP endpoints."""

from __future__ import annotations

import asyncio
import json
import shlex
from typing import Any

from ....document.models.ssdm_models import Transport
from .base import TransportRequest


class MCPAdapterError(RuntimeError):
    """Raised when MCP transport cannot execute the requested tool call."""


class MCPAdapter:
    """Small transport adapter for MCP server interaction.

    The implementation is intentionally generic: when `transport=STDIO`, a command
    is executed and line-oriented JSON RPC messages are exchanged. When `transport`
    is SSE/HTTPS, a JSON-over-HTTP contract is attempted.
    """

    def __init__(
        self,
        *,
        transport: Transport = Transport.STDIO,
        command: str | None = None,
        server_url: str | None = None,
        timeout_ms: int = 30000,
    ) -> None:
        self.transport = transport
        self.command = command
        self.server_url = server_url
        self.timeout_ms = timeout_ms
        self._proc = None
        self._reader_task = None
        self._next_id = 0
        self._pending: dict[int, asyncio.Future] = {}

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if self.transport == Transport.STDIO:
            return await self._call_via_stdio(tool_name, arguments)
        if self.transport == Transport.SSE:
            return await self._call_via_sse(tool_name, arguments)
        raise MCPAdapterError(f"Unsupported MCP transport '{self.transport.value}'")

    async def close(self) -> None:
        if self._reader_task is not None:
            self._reader_task.cancel()
            self._reader_task = None
        if self._proc is not None:
            proc = self._proc
            self._proc = None
            if proc.returncode is None:
                proc.terminate()
            try:
                await proc.wait()
            except Exception:
                pass

    async def _call_via_stdio(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if not self.command:
            raise MCPAdapterError("STDIO transport requires a command")

        proc = await self._ensure_stdio_process()
        request_id = self._next_request_id()

        future: asyncio.Future = asyncio.get_running_loop().create_future()
        self._pending[request_id] = future

        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments,
            },
        }
        proc.stdin.write((json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8"))
        await proc.stdin.drain()

        try:
            result = await asyncio.wait_for(future, timeout=self.timeout_ms / 1000)
        except asyncio.TimeoutError as exc:
            del self._pending[request_id]
            raise MCPAdapterError(f"Timeout calling MCP tool '{tool_name}'") from exc
        return _normalize_tool_result(result)

    async def _call_via_sse(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if not self.server_url:
            raise MCPAdapterError("SSE/HTTP MCP transport requires server_url")

        try:
            import aiohttp  # type: ignore[import-not-found]
        except Exception as exc:
            raise MCPAdapterError("aiohttp is required for SSE/HTTP MCP calls") from exc

        transport = self.server_url.rstrip("/")
        endpoints = ["tools/call", "tool/call", ""]

        request_payload = {"tool": tool_name, "arguments": arguments}
        last_err: Exception | None = None
        for suffix in endpoints:
            url = f"{transport}/{suffix}" if suffix else transport
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        url,
                        json=request_payload,
                        timeout=aiohttp.ClientTimeout(total=self.timeout_ms / 1000),
                    ) as response:
                        if response.status >= 400:
                            text = await response.text()
                            raise MCPAdapterError(f"MCP endpoint {url} returned {response.status}: {text}")
                        data = await response.json()
                        return _normalize_tool_result(data)
            except MCPAdapterError:
                raise
            except Exception as exc:
                last_err = exc
                continue

        raise MCPAdapterError(f"Unable to call MCP SSE endpoint {self.server_url}") from last_err

    def _next_request_id(self) -> int:
        self._next_id += 1
        return self._next_id

    async def _ensure_stdio_process(self):
        if self._proc is not None and self._proc.returncode is None:
            return self._proc

        if self._reader_task is not None:
            self._reader_task.cancel()
            self._reader_task = None

        try:
            import asyncio.subprocess
        except Exception as exc:
            raise MCPAdapterError("Asyncio subprocess support not available") from exc

        args = shlex.split(self.command)
        self._proc = await asyncio.create_subprocess_exec(
            *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        if self._proc.stdout is None or self._proc.stdin is None:
            raise MCPAdapterError("MCP process is missing stdio pipes")
        self._reader_task = asyncio.create_task(self._stdout_reader(self._proc.stdout))
        return self._proc

    async def _stdout_reader(self, stream):
        while True:
            line = await stream.readline()
            if not line:
                break
            text = line.decode("utf-8", errors="ignore").strip()
            if not text:
                continue
            try:
                data = json.loads(text)
            except Exception:
                continue
            message_id = data.get("id")
            if message_id is None:
                continue
            request_id = int(message_id)
            future = self._pending.pop(request_id, None)
            if future is not None and not future.done():
                future.set_result(data)


def _normalize_tool_result(payload: dict[str, Any]) -> dict[str, Any]:
    if isinstance(payload, dict):
        if "result" in payload:
            result = payload["result"]
            if isinstance(result, dict):
                return result
            return {"result": result}
        if "error" in payload:
            return {"error": payload.get("error")}
    return payload


class MCPTransport(TransportRequest):
    """Backward-compatible compatibility alias retained for simple typing."""

    ...


def _noop() -> None:
    return None
