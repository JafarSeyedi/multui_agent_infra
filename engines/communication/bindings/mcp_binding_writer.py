"""Serialize MCP south-bound bindings for external clients."""

from __future__ import annotations

from typing import Any

import yaml

import json

from ...document.models.ssdm_models import MCPSouthBoundBinding, MCPClientToolBinding, MCPToolBinding


class MCPBindingWriter:
    """Write MCP binding definitions as MCP-compatible JSON/YAML documents."""

    def dump_tool(self, tool: MCPClientToolBinding | MCPToolBinding) -> dict[str, Any]:
        if isinstance(tool, MCPToolBinding):
            return {
                "name": tool.tool_name,
                "internal": {
                    "component_type": tool.internal.component_type.value,
                    "address": tool.internal.address,
                    "coordination": tool.internal.coordination.value,
                    "timeout_ms": tool.internal.timeout_ms,
                    "retry_policy": tool.internal.retry_policy.value,
                    "max_retries": tool.internal.max_retries,
                    "config": tool.internal.config,
                },
            }
        target = {
            "name": tool.tool_name,
            "parameters": [
                {
                    "source": m.source,
                    "target": m.target,
                    "transform": m.transform,
                }
                for m in tool.parameter_mappings
            ],
            "response_mappings": [
                {
                    "source": m.source,
                    "target": m.target,
                    "transform": m.transform,
                    "status_code_on_error": m.status_code_on_error,
                }
                for m in tool.response_mappings
            ],
            "timeout_ms": tool.timeout_ms,
            "retry_policy": tool.retry_policy.value if tool.retry_policy else None,
        }
        target = {k: v for k, v in target.items() if v not in (None, [], {})}
        return target

    def dump(self, binding: MCPSouthBoundBinding, *, output_format: str = "json") -> bytes:
        payload: dict[str, Any] = {
            "server_name": binding.server_name,
            "transport": binding.transport.value,
            "endpoint_url": binding.endpoint_url,
            "command": binding.command,
            "tools": [self.dump_tool(t) for t in binding.tools],
            "operation_bindings": dict(binding.operation_bindings),
        }
        payload = {k: v for k, v in payload.items() if v not in (None, [], {})}
        if output_format.lower() in {"json", ".json"}:
            return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        return yaml.safe_dump(payload, sort_keys=False).encode("utf-8")
