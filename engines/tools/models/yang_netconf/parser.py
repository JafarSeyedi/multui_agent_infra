from __future__ import annotations

from engines.tools.models.core.core_models import ToolKind
from engines.tools.models.core.core_models import ToolParameter
from engines.tools.models.core.core_models import ParameterSource
from engines.tools.models.core.core_models import ParameterType
from engines.tools.models.core.core_models import ToolOutput
from engines.tools.models.core.core_models import NetconfProtocol
from engines.tools.models.yang_netconf.yang_netconf_models import YangNetconfTool


def parse_yang_netconf_tool(data: dict) -> YangNetconfTool:
    return YangNetconfTool(
        id=data.get("id", ""),
        name=data.get("name", ""),
        description=data.get("description"),
        version=data.get("version", "1.0.0"),
        kind=ToolKind.YANG_NETCONF,
        parameters=[_parse_param(p) for p in data.get("parameters", [])],
        outputs=[_parse_output(o) for o in data.get("outputs", [])],
        tags=data.get("tags", []),
        annotations=data.get("annotations", {}),
        retry_policy=data.get("retry_policy"),
        timeout_ms=data.get("timeout_ms", 30000),
        host=data.get("host", "localhost"),
        port=data.get("port", 830),
        username=data.get("username", ""),
        password=data.get("password"),
        netconf_protocol=NetconfProtocol(data.get("netconf_protocol", "ssh")),
        rpc_template=data.get("rpc_template", ""),
    )


def _parse_param(p: dict) -> ToolParameter:
    return ToolParameter(
        name=p.get("name", ""),
        type=ParameterType(p.get("type", "string")),
        required=p.get("required", False),
        default=p.get("default"),
        description=p.get("description"),
        source=ParameterSource(p.get("source", "callerArg")),
        source_path=p.get("source_path"),
        mapping_target=p.get("mapping_target"),
    )


def _parse_output(o: dict) -> ToolOutput:
    return ToolOutput(
        name=o.get("name", ""),
        type=ParameterType(o.get("type", "json")),
        description=o.get("description"),
        mapping_from=o.get("mapping_from"),
    )
