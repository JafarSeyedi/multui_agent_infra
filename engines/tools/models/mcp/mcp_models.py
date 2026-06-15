from __future__ import annotations

from dataclasses import dataclass, field

from engines.tools.models.core.core_models import Tool
from engines.tools.models.core.core_models import ToolKind


@dataclass
class MCPTool(Tool):
    kind: ToolKind = ToolKind.MCP
    server_command: list[str] = field(default_factory=list)
    server_url: str = ""
    tool_name: str = ""
    transport: str = "stdio"
    args: list[str] = field(default_factory=list)
    env_vars: dict[str, str] = field(default_factory=dict)
