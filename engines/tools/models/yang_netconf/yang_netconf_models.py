from __future__ import annotations

from dataclasses import dataclass

from engines.tools.models.core.core_models import Tool
from engines.tools.models.core.core_models import ToolKind
from engines.tools.models.core.core_models import NetconfProtocol


@dataclass
class YangNetconfTool(Tool):
    kind: ToolKind = ToolKind.YANG_NETCONF
    host: str = "localhost"
    port: int = 830
    username: str = ""
    password: str | None = None
    netconf_protocol: NetconfProtocol = NetconfProtocol.SSH
    rpc_template: str = ""
