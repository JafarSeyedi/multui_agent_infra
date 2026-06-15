from __future__ import annotations

from .apigee_models import ApigeeTool


def write_apigee_tool(tool: ApigeeTool) -> dict:
    return {k: getattr(tool, k) for k in tool.__dataclass_fields__}
