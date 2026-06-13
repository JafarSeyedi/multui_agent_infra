from __future__ import annotations

import asyncio
from typing import Any

from engines.tools.base_executor import BaseToolExecutor
from engines.tools.base_executor import ToolResult


class CLIExecutor(BaseToolExecutor):
    """Runs a command-line program and captures output."""

    @property
    def name(self) -> str:
        return "cli"

    @property
    def description(self) -> str:
        return "Execute a command-line program"

    async def execute(self, **kwargs: Any) -> ToolResult:
        command = kwargs.get("command", "")
        if not command:
            return ToolResult(False, error="No command provided")
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        return ToolResult(
            proc.returncode == 0,
            data={"stdout": stdout.decode(), "stderr": stderr.decode()},
        )
