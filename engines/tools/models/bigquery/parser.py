from __future__ import annotations

from .bigquery_models import BigQueryTool


def parse_bigquery_tool(data: dict) -> BigQueryTool:
    return BigQueryTool(**{k: v for k, v in data.items() if k in BigQueryTool.__dataclass_fields__})
