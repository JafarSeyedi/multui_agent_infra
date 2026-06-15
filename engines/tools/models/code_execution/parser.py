from __future__ import annotations

from .code_execution_models import CodeExecutionTool


def parse_code_execution_tool(data: dict) -> CodeExecutionTool:
    return CodeExecutionTool(**{k: v for k, v in data.items() if k in CodeExecutionTool.__dataclass_fields__})
