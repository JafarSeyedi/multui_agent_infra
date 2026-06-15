from __future__ import annotations

from typing import Any

from ...base_executor import BaseToolExecutor, ToolResult


class GeminiCodeExecutionExecutor(BaseToolExecutor):
    @property
    def name(self) -> str:
        return "gemini_code_exec"

    @property
    def description(self) -> str:
        return "Execute code via Gemini API's built-in code execution"

    async def execute(self, **kwargs: Any) -> ToolResult:
        code = kwargs.get("code", "")
        if not code:
            return ToolResult(success=False, error="Code is required")
        try:
            import google.generativeai as genai
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = await model.generate_content_async(
                f"Execute this code and return the output:\n```{kwargs.get('language', 'python')}\n{code}\n```",
            )
            return ToolResult(success=True, data={"output": response.text})
        except ImportError:
            return ToolResult(success=False, error="google-generativeai not installed")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
