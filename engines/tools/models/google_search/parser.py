from __future__ import annotations

from typing import Any

from .google_search_models import GoogleSearchTool


def parse_google_search_tool(data: dict[str, Any]) -> GoogleSearchTool:
    return GoogleSearchTool(
        id=data.get("id", ""),
        name=data.get("name", "google_search"),
        description=data.get("description", ""),
        query=data.get("query", ""),
        num_results=data.get("num_results", 10),
        cx=data.get("cx", ""),
        api_key=data.get("api_key", ""),
        parameters=data.get("parameters", []),
        outputs=data.get("outputs", []),
        tags=data.get("tags", []),
        annotations=data.get("annotations", {}),
    )
