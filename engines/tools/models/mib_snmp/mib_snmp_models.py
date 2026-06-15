from __future__ import annotations

from dataclasses import dataclass

from engines.tools.models.core.core_models import Tool
from engines.tools.models.core.core_models import ToolKind
from engines.tools.models.core.core_models import SnmpVersion


@dataclass
class MibSnmpTool(Tool):
    kind: ToolKind = ToolKind.MIB_SNMP
    host: str = "localhost"
    port: int = 161
    community: str | None = None
    snmp_version: SnmpVersion = SnmpVersion.SNMPv2c
    oid: str = ""
    operation: str = "get"
    value: str | None = None
