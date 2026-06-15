from __future__ import annotations

from .bigtable_models import BigtableTool


def parse_bigtable_tool(data: dict) -> BigtableTool:
    return BigtableTool(**{k: v for k, v in data.items() if k in BigtableTool.__dataclass_fields__})
