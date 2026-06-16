from __future__ import annotations

import os
import tempfile

from engines.tools.base_executor import BaseToolExecutor, ToolResult
from engines.tools.models.tools_def_models import ArgName, ParameterName, ToolKind
from engines.tools.models.tools_def_models import ToolParameter


@BaseToolExecutor.register(ToolKind.CODE_EXECUTION)
class CodeExecutionExecutor(BaseToolExecutor):
    def _apply_params(self) -> None:
        self._language = self.param(self._params, ParameterName.LANGUAGE, "python")

    @property
    def name(self) -> str:
        return "code_execution"

    @property
    def description(self) -> str:
        return "Execute code in a sandboxed environment"

    async def execute(self, args: list[ToolParameter]) -> ToolResult:
        import asyncio
        source = self.arg(args, ArgName.CODE, "")
        timeout_s = 30

        if not source:
            return ToolResult(success=False, error="Source code is required")

        with tempfile.NamedTemporaryFile(mode="w", suffix=self._suffix(self._language), delete=False) as f:
            f.write(source)
            fpath = f.name

        try:
            cmd = self._command(self._language, fpath)
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_s)
                return ToolResult(
                    success=proc.returncode == 0,
                    data={
                        "stdout": stdout.decode() if stdout else "",
                        "stderr": stderr.decode() if stderr else "",
                        "return_code": proc.returncode,
                    },
                )
            except asyncio.TimeoutError:
                proc.kill()
                return ToolResult(success=False, error="Execution timed out")
        finally:
            os.unlink(fpath)

    def _suffix(self, language: str) -> str:
        return {"python": ".py", "javascript": ".js", "typescript": ".ts"}.get(language, ".py")

    def _command(self, language: str, fpath: str) -> list[str]:
        return {"python": ["python3", fpath], "javascript": ["node", fpath], "typescript": ["npx", "tsx", fpath]}.get(
            language, ["python3", fpath]
        )
