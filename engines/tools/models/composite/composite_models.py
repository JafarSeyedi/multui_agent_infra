from __future__ import annotations

from dataclasses import dataclass, field

from engines.tools.models.core.core_models import Tool
from engines.tools.models.core.core_models import ToolKind


@dataclass
class CompositeTool(Tool):
    kind: ToolKind = ToolKind.COMPOSITE
    steps: list[Tool] = field(default_factory=list)
    data_flow: str = "sequential"
