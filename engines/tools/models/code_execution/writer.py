from __future__ import annotations

from .code_execution_models import CodeExecutionTool


def write_code_execution_tool(tool: CodeExecutionTool) -> dict:
    return {k: getattr(tool, k) for k in tool.__dataclass_fields__}
