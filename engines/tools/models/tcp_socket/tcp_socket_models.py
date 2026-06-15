from __future__ import annotations

from dataclasses import dataclass

from engines.tools.models.core.core_models import Tool
from engines.tools.models.core.core_models import ToolKind


@dataclass
class TcpSocketTool(Tool):
    kind: ToolKind = ToolKind.TCP_SOCKET
    host: str = "localhost"
    port: int = 8080
    request_template: str = ""
    expect_response: bool = True
    connection_timeout_ms: int = 5000
