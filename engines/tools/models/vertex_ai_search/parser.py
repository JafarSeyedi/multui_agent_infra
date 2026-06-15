from __future__ import annotations

from typing import Any

from .vertex_ai_search_models import VertexAiSearchTool


def parse_vertex_ai_search_tool(data: dict[str, Any]) -> VertexAiSearchTool:
    return VertexAiSearchTool(
        id=data.get("id", ""),
        name=data.get("name", "vertex_ai_search"),
        description=data.get("description", ""),
        query=data.get("query", ""),
        data_store_id=data.get("data_store_id", ""),
        serving_config=data.get("serving_config", "default_search"),
        location=data.get("location", "global"),
        parameters=data.get("parameters", []),
        outputs=data.get("outputs", []),
        tags=data.get("tags", []),
        annotations=data.get("annotations", {}),
    )
