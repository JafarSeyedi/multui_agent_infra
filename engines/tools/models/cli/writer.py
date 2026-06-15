from __future__ import annotations

from typing import Any

from engines.tools.models.core.core_models import Tool
from engines.tools.models.core.core_models import ToolParameter
from engines.tools.models.core.core_models import ToolOutput
from engines.tools.models.cli.cli_models import CliTool


def write_cli_tool(tool: Tool) -> dict[str, Any]:
    base = _base_dict(tool)
    if isinstance(tool, CliTool):
        base["command"] = tool.command
        base["args"] = tool.args
        base["working_directory"] = tool.working_directory
        base["env_vars"] = tool.env_vars
    return base


def _base_dict(tool: Tool) -> dict[str, Any]:
    return {
        "id": tool.id,
        "name": tool.name,
        "description": tool.description,
        "version": tool.version,
        "kind": tool.kind.value,
        "parameters": [_param_dict(p) for p in tool.parameters],
        "outputs": [_output_dict(o) for o in tool.outputs],
        "tags": tool.tags,
        "annotations": tool.annotations,
        "retry_policy": tool.retry_policy,
        "timeout_ms": tool.timeout_ms,
    }


def _param_dict(p: ToolParameter) -> dict[str, Any]:
    return {
        "name": p.name,
        "type": p.type.value,
        "required": p.required,
        "default": p.default,
        "description": p.description,
        "source": p.source.value,
        "source_path": p.source_path,
        "mapping_target": p.mapping_target,
    }


def _output_dict(o: ToolOutput) -> dict[str, Any]:
    return {
        "name": o.name,
        "type": o.type.value,
        "description": o.description,
        "mapping_from": o.mapping_from,
    }
