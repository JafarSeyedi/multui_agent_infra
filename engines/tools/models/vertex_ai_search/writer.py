from __future__ import annotations

from typing import Any

from .vertex_ai_search_models import VertexAiSearchTool


def write_vertex_ai_search_tool(tool: VertexAiSearchTool) -> dict[str, Any]:
    return {
        "id": tool.id,
        "name": tool.name,
        "description": tool.description,
        "kind": tool.kind.value,
        "query": tool.query,
        "data_store_id": tool.data_store_id,
        "serving_config": tool.serving_config,
        "location": tool.location,
        "parameters": [
            {"name": p.name, "type": p.type.value, "required": p.required}
            for p in tool.parameters
        ],
        "outputs": [
            {"name": o.name, "type": o.type.value}
            for o in tool.outputs
        ],
        "tags": tool.tags,
        "annotations": tool.annotations,
    }
