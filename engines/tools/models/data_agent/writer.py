from __future__ import annotations

from .data_agent_models import DataAgentTool


def write_data_agent_tool(tool: DataAgentTool) -> dict:
    return {k: getattr(tool, k) for k in tool.__dataclass_fields__}
