from __future__ import annotations

from .bigtable_models import BigtableTool


def write_bigtable_tool(tool: BigtableTool) -> dict:
    return {k: getattr(tool, k) for k in tool.__dataclass_fields__}
