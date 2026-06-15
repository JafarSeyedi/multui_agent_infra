from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from engines.tools.models.core.core_models import Tool, ToolKind


@dataclass
class BigQueryTool(Tool):
    kind: str = "bigquery"
    project_id: str = ""
    dataset_id: str = ""
    query: str = ""
    location: str = "US"
    max_results: int = 1000
    use_query_cache: bool = True
