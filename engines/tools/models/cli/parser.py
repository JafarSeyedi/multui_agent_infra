from __future__ import annotations

from engines.tools.models.core.core_models import ToolKind
from engines.tools.models.core.core_models import ToolParameter
from engines.tools.models.core.core_models import ParameterSource
from engines.tools.models.core.core_models import ParameterType
from engines.tools.models.core.core_models import ToolOutput
from engines.tools.models.cli.cli_models import CliTool


def parse_cli_tool(data: dict) -> CliTool:
    common = _common_fields(data)
    return CliTool(
        **common,
        command=data.get("command", ""),
        args=data.get("args", []),
        working_directory=data.get("working_directory"),
        env_vars=data.get("env_vars", {}),
    )


def _common_fields(data: dict) -> dict:
    return {
        "id": data.get("id", ""),
        "name": data.get("name", ""),
        "description": data.get("description"),
        "version": data.get("version", "1.0.0"),
        "kind": ToolKind(data.get("kind", "cli")),
        "parameters": [_parse_param(p) for p in data.get("parameters", [])],
        "outputs": [_parse_output(o) for o in data.get("outputs", [])],
        "tags": data.get("tags", []),
        "annotations": data.get("annotations", {}),
        "retry_policy": data.get("retry_policy"),
        "timeout_ms": data.get("timeout_ms", 30000),
    }


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
