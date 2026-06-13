"""MCP invocation service — handles MCP tool calls and argument mapping."""

from __future__ import annotations

from typing import Any

from ...document.models.ssdm_models import ServiceBinding, ServiceOperation, Transport
from ..._types import MessagePayload, Metadata, RawData
from ..common.transport.mcp_adapter import MCPAdapter
from ..consumption.models import InvocationResult


class MCPService:
    """Manages MCP adapter lifecycle and tool invocation."""

    def __init__(self) -> None:
        self._adapters: dict[str, MCPAdapter] = {}

    async def invoke(
        self,
        operation: ServiceOperation,
        payload: MessagePayload,
        binding: ServiceBinding,
    ) -> InvocationResult:
        tools = binding.mcp_tools or []
        if not tools:
            raise RuntimeError(f"MCP binding for operation '{operation.name}' has no tools")
        tool = tools[0]

        endpoint_key = binding.endpoint_url or binding.operation_id
        adapter = self._get_adapter(binding, endpoint_key)
        tool_payload = self._map_arguments(tool.parameter_mappings, payload)
        tool_result = await adapter.call_tool(tool.tool_name, tool_payload)
        mapped_result = self._map_response(tool.response_mappings, tool_result)

        return InvocationResult(
            operation_id=operation.name,
            transport=binding.transport,
            request=None,
            response=None,
            payload=mapped_result,
            metadata={"tool_name": tool.tool_name, "binding": binding.operation_id},
        )

    def _get_adapter(self, binding: ServiceBinding, endpoint_key: str) -> MCPAdapter:
        adapter = self._adapters.get(endpoint_key)
        if adapter is None:
            adapter = MCPAdapter(
                transport=binding.transport,
                command=getattr(binding, "command", None),
                server_url=binding.endpoint_url,
                timeout_ms=binding.timeout_ms,
            )
            self._adapters[endpoint_key] = adapter
        return adapter

    async def close_all(self) -> None:
        for adapter in self._adapters.values():
            await adapter.close()
        self._adapters.clear()

    @staticmethod
    def _map_arguments(mappings: list[Any], payload: MessagePayload) -> RawData:
        if not mappings:
            return payload
        result: RawData = {}
        for mapping in mappings:
            result[mapping.target] = _resolve_source(payload, mapping.source)
        return result

    @staticmethod
    def _map_response(mappings: list[Any], tool_result: RawData) -> Any:
        if not mappings:
            return tool_result
        body: RawData = {}
        headers: Metadata = {}
        for mapping in mappings:
            value = _resolve_source(tool_result, mapping.source)
            if mapping.target.startswith("header."):
                headers[mapping.target.split(".", 1)[1]] = value
            else:
                body[mapping.target] = value
        if headers:
            body["_headers"] = headers
        return body


def _resolve_source(payload: RawData, source: str) -> Any:
    current: Any = payload
    for part in source.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current
