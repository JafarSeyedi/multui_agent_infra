from __future__ import annotations

import os
import tempfile
from typing import Any

from ...base_executor import BaseToolExecutor, ToolResult


class CodeExecutionExecutor(BaseToolExecutor):
    @property
    def name(self) -> str:
        return "code_execution"

    @property
    def description(self) -> str:
        return "Execute code in a sandboxed environment"

    async def execute(self, **kwargs: Any) -> ToolResult:
        import asyncio
        language = kwargs.get("language", "python")
        source = kwargs.get("source", "")
        timeout_s = kwargs.get("timeout_ms", 30000) / 1000

        if not source:
            return ToolResult(success=False, error="Source code is required")

        with tempfile.NamedTemporaryFile(mode="w", suffix=self._suffix(language), delete=False) as f:
            f.write(source)
            fpath = f.name

        try:
            cmd = self._command(language, fpath)
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
