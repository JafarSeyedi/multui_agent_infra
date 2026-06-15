from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from engines.tools.models.core.core_models import Tool, ToolKind


@dataclass
class BigtableTool(Tool):
    kind: ToolKind = ToolKind.BIGTABLE
    instance_id: str = ""
    table_id: str = ""
    row_key: str = ""
    column_family: str = ""
    filter: str = ""
    operation: str = "read_row"
    columns: dict[str, Any] = field(default_factory=dict)
