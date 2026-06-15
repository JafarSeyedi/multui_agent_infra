from __future__ import annotations

from .gemini_code_exec_models import GeminiCodeExecutionTool


def write_gemini_code_exec_tool(tool: GeminiCodeExecutionTool) -> dict:
    return {k: getattr(tool, k) for k in tool.__dataclass_fields__}
