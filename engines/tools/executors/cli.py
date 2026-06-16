from __future__ import annotations

import asyncio

from engines.tools.base_executor import BaseToolExecutor
from engines.tools.base_executor import ToolResult
from engines.tools.models.tools_def_models import ArgName
from engines.tools.models.tools_def_models import ParameterName
from engines.tools.models.tools_def_models import ToolKind
from engines.tools.models.tools_def_models import ToolParameter


@BaseToolExecutor.register(ToolKind.CLI)
class CLIExecutor(BaseToolExecutor):

    def _apply_params(self) -> None:
        self._command = self.param(self._params, ParameterName.COMMAND, "")

    @property
    def name(self) -> str:
        return "cli"

    @property
    def description(self) -> str:
        return "Execute a command-line program"

    async def execute(self, args: list[ToolParameter]) -> ToolResult:
        if not self._command:
            return ToolResult(False, error="No command provided")
        proc = await asyncio.create_subprocess_shell(
            self._command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        return ToolResult(
            proc.returncode == 0,
            data={"stdout": stdout.decode(), "stderr": stderr.decode()},
        )
