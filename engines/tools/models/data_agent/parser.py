from __future__ import annotations

from .data_agent_models import DataAgentTool


def parse_data_agent_tool(data: dict) -> DataAgentTool:
    return DataAgentTool(**{k: v for k, v in data.items() if k in DataAgentTool.__dataclass_fields__})
