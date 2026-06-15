from __future__ import annotations

from dataclasses import dataclass

from engines.tools.models.core.core_models import Tool, ToolKind


@dataclass
class GoogleSearchTool(Tool):
    kind: ToolKind = ToolKind.GOOGLE_SEARCH
    query: str = ""
    num_results: int = 10
    cx: str = ""
    api_key: str = ""
