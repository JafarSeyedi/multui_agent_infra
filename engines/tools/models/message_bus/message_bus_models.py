from __future__ import annotations

from dataclasses import dataclass

from engines.tools.models.core.core_models import Tool
from engines.tools.models.core.core_models import ToolKind


@dataclass
class MessageBusTool(Tool):
    kind: ToolKind = ToolKind.MESSAGE_BUS
    transport: str = "kafka"
    topic: str = ""
    message_template: str = ""
    publish: bool = True
