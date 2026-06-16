# engines/communication/transport/backends/stdio/stdio_transport.py
from __future__ import annotations

import asyncio
import shlex

from ...plugin import BaseTransport


class StdioTransport(BaseTransport):
    """STDIO transport — spawns a subprocess and communicates via stdin/stdout."""

    name = "stdio"

    def __init__(self, command: str) -> None:
        self._command = command
        self._process: asyncio.subprocess.Process | None = None

    async def connect(self, endpoint: str | None = None) -> None:
        args = shlex.split(self._command)
        self._process = await asyncio.create_subprocess_exec(
            *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

    async def send_bytes(self, data: bytes, endpoint: str | None = None) -> bytes:
        if self._process is None or self._process.stdin is None or self._process.stdout is None:
            raise RuntimeError("Process not connected")
        self._process.stdin.write(data + b"\n")
        await self._process.stdin.drain()
        line = await self._process.stdout.readline()
        return line

    async def close(self) -> None:
        if self._process is not None:
            self._process.kill()
            await self._process.wait()
            self._process = None
