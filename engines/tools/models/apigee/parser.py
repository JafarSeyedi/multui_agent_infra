from __future__ import annotations

from .apigee_models import ApigeeTool


def parse_apigee_tool(data: dict) -> ApigeeTool:
    return ApigeeTool(**{k: v for k, v in data.items() if k in ApigeeTool.__dataclass_fields__})
