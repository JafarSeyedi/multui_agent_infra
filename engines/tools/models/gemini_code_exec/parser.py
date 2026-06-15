from __future__ import annotations

from .gemini_code_exec_models import GeminiCodeExecutionTool


def parse_gemini_code_exec_tool(data: dict) -> GeminiCodeExecutionTool:
    return GeminiCodeExecutionTool(**{k: v for k, v in data.items() if k in GeminiCodeExecutionTool.__dataclass_fields__})
