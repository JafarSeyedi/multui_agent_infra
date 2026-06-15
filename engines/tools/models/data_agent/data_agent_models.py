from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from engines.tools.models.core.core_models import Tool, ToolKind


@dataclass
class DataAgentTool(Tool):
    kind: ToolKind = ToolKind.DATA_AGENT
    query: str = ""
    data_source: str = ""
    agent_id: str = ""
