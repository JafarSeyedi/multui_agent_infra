from __future__ import annotations

from engines.tools.base_executor import BaseToolExecutor, ToolResult
from engines.tools.models.tools_def_models import ArgName, ParameterName, ToolKind
from engines.tools.models.tools_def_models import ToolParameter


@BaseToolExecutor.register(ToolKind.GEMINI_CODE_EXEC)
class GeminiCodeExecutionExecutor(BaseToolExecutor):

    def _apply_params(self) -> None:
        self._language = self.param(self._params, ParameterName.LANGUAGE, "python")

    @property
    def name(self) -> str:
        return "gemini_code_exec"

    @property
    def description(self) -> str:
        return "Execute code via Gemini API's built-in code execution"

    async def execute(self, args: list[ToolParameter]) -> ToolResult:
        code = self.arg(args, ArgName.CODE, "")
        if not code:
            return ToolResult(success=False, error="Code is required")
        try:
            import google.generativeai as genai
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = await model.generate_content_async(
                f"Execute this code and return the output:\n```{self._language}\n{code}\n```",
            )
            return ToolResult(success=True, data={"output": response.text})
        except ImportError:
            return ToolResult(success=False, error="google-generativeai not installed")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
