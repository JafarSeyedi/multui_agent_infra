from __future__ import annotations

from .bigquery_models import BigQueryTool


def write_bigquery_tool(tool: BigQueryTool) -> dict:
    return {k: getattr(tool, k) for k in tool.__dataclass_fields__}
