from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from engines.tools.models.core.core_models import Tool, ToolKind


@dataclass
class ComputerUseTool(Tool):
    kind: ToolKind = ToolKind.COMPUTER_USE
    action: str = "navigate"
    url: str = ""
    selector: str = ""
    value: str = ""
    headless: bool = True
