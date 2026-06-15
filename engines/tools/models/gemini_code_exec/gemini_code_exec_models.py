from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from engines.tools.models.core.core_models import Tool, ToolKind


@dataclass
class GeminiCodeExecutionTool(Tool):
    kind: ToolKind = ToolKind.GEMINI_CODE_EXEC
    code: str = ""
    language: str = "python"
    files: list[dict[str, Any]] = field(default_factory=list)
