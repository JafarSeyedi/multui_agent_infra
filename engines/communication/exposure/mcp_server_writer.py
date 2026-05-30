"""Generate MCP north-bound server configuration from SSDM bindings."""

from __future__ import annotations

from typing import Any

from ...document.models.ssdm_models import MCPNorthBoundBinding


class MCPServerWriter:
    """Serialize a north-bound MCP server definition."""

    def dump(self, binding: MCPNorthBoundBinding) -> dict[str, Any]:
        return {
            "server_name": binding.server_name,
            "transport": binding.transport.value,
            "server_url": binding.server_url,
            "tools": [self._dump_tool(tool) for tool in binding.tools],
            "resources": [self._dump_resource(resource) for resource in binding.resources],
            "prompts": [self._dump_prompt(prompt) for prompt in binding.prompts],
        }

    @staticmethod
    def _dump_tool(tool: Any) -> dict[str, Any]:
        return {
            "name": tool.tool_name,
            "component_type": tool.internal.component_type.value,
            "address": tool.internal.address,
            "coordination": tool.internal.coordination.value,
        }

    @staticmethod
    def _dump_resource(resource: Any) -> dict[str, Any]:
        return {
            "uri": resource.uri,
            "component_type": resource.internal.component_type.value,
            "address": resource.internal.address,
        }

    @staticmethod
    def _dump_prompt(prompt: Any) -> dict[str, Any]:
        return {
            "name": prompt.prompt_name,
            "component_type": prompt.internal.component_type.value,
            "address": prompt.internal.address,
        }
