from __future__ import annotations

from typing import Any

from .google_search_models import GoogleSearchTool


def write_google_search_tool(tool: GoogleSearchTool) -> dict[str, Any]:
    return {
        "id": tool.id,
        "name": tool.name,
        "description": tool.description,
        "kind": tool.kind.value,
        "query": tool.query,
        "num_results": tool.num_results,
        "cx": tool.cx,
        "api_key": tool.api_key,
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
