from __future__ import annotations

from dataclasses import dataclass

from engines.tools.models.core.core_models import Tool, ToolKind


@dataclass
class VertexAiSearchTool(Tool):
    kind: ToolKind = ToolKind.VERTEX_AI_SEARCH
    query: str = ""
    data_store_id: str = ""
    serving_config: str = "default_search"
    location: str = "global"
