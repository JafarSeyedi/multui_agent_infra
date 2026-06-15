from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from engines.tools.models.core.core_models import Tool, ToolKind


@dataclass
class CodeExecutionTool(Tool):
    kind: ToolKind = ToolKind.CODE_EXECUTION
    language: str = "python"
    source: str = ""
    timeout_ms: int = 30000
    sandbox_type: str = "subprocess"
