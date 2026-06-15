from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from engines.tools.models.core.core_models import Tool, ToolKind


@dataclass
class ApigeeTool(Tool):
    kind: ToolKind = ToolKind.APIGEE
    api_hub_url: str = ""
    action: str = "search"
    query: str = ""
    api_id: str = ""
