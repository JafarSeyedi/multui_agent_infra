from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from engines.tools.models.core.core_models import Tool


@dataclass
class GeminiCodeExecutionTool(Tool):
    kind: str = "gemini_code_exec"
    code: str = ""
    language: str = "python"
    files: list[dict[str, Any]] = field(default_factory=list)
