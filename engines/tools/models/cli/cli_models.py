from __future__ import annotations

from dataclasses import dataclass, field

from engines.tools.models.core.core_models import Tool
from engines.tools.models.core.core_models import ToolKind


@dataclass
class CliTool(Tool):
    kind: ToolKind = ToolKind.CLI
    command: str = ""
    args: list[str] = field(default_factory=list)
    working_directory: str | None = None
    env_vars: dict[str, str] = field(default_factory=dict)
