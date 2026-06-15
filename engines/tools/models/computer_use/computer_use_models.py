from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from engines.tools.models.core.core_models import Tool


@dataclass
class ComputerUseTool(Tool):
    kind: str = "computer_use"
    action: str = "navigate"
    url: str = ""
    selector: str = ""
    value: str = ""
    headless: bool = True
