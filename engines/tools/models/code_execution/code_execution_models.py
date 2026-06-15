from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from engines.tools.models.core.core_models import Tool


@dataclass
class CodeExecutionTool(Tool):
    kind: str = "code_execution"
    language: str = "python"
    source: str = ""
    timeout_ms: int = 30000
    sandbox_type: str = "subprocess"
