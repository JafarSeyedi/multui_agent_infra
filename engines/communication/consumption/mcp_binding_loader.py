"""Load MCP south-bound bindings and materialize operation call bindings."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ...document.models.ssdm_models import MCPSouthBoundBinding, ServiceBinding


def load_mcp_binding(source: str | Path | dict[str, Any]) -> MCPSouthBoundBinding:
    """Load a MCP binding from YAML/JSON/dict payload."""
    if isinstance(source, dict):
        payload = source
    else:
        raw = Path(source).read_text(encoding="utf-8")
        if raw.strip().startswith("{") or raw.strip().startswith("["):
            import json
            payload = json.loads(raw)
        else:
            import yaml
            payload = yaml.safe_load(raw)

    command = payload.get("command")
    transport = payload.get("transport", "stdio")
    if transport == "stdIO":
        transport = "stdio"
    if payload.get("transport") == "sse" and not payload.get("server_url") and command:
        pass

    return MCPSouthBoundBinding(
        server_name=str(payload.get("server_name", payload.get("name", ""))),
        transport=payload.get("transport", "stdio"),
        endpoint_url=payload.get("endpoint_url") or payload.get("server_url"),
        command=command,
        auth_config=payload.get("auth_config"),
        # auth_config is expected to be AuthConfig-compatible dict for parser usage here.
        tools=[
            _dict_to_mcp_tool(tool)
            for tool in (payload.get("tools") or [])
        ],
        operation_bindings=dict(payload.get("operation_bindings") or {}),
    )


def _dict_to_mcp_tool(raw: dict[str, Any]):
    from ...document.models.ssdm_models import MCPClientToolBinding, ParameterMapping, ResponseMapping, RetryPolicy

    parameter_mappings = [
        ParameterMapping(
            source=m["source"],
            target=m["target"],
            transform=m.get("transform"),
        )
        for m in (raw.get("parameter_mappings") or [])
        if isinstance(m, dict) and "source" in m and "target" in m
    ]
    response_mappings = [
        ResponseMapping(
            source=m["source"],
            target=m["target"],
            transform=m.get("transform"),
            status_code_on_error=m.get("status_code_on_error"),
        )
        for m in (raw.get("response_mappings") or [])
        if isinstance(m, dict) and "source" in m and "target" in m
    ]

    rp = raw.get("retry_policy")
    if rp is not None:
        try:
            rp = RetryPolicy(rp)
        except Exception:
            rp = None

    return MCPClientToolBinding(
        tool_name=raw["name"] if "name" in raw else raw.get("tool_name", ""),
        parameter_mappings=parameter_mappings,
        response_mappings=response_mappings,
        timeout_ms=raw.get("timeout_ms"),
        retry_policy=rp,
    )


def load_service_bindings(source: str | Path | dict[str, Any]) -> list[ServiceBinding]:
    binding = load_mcp_binding(source)
    if not binding.tools:
        return []

    # Operation mapping is explicit when operation_bindings exists, else one tool per op.
    operations = binding.operation_bindings or {}
    if not operations:
        operations = {tool.tool_name: tool.tool_name for tool in binding.tools}

    result: list[ServiceBinding] = []
    for op_id, tool_name in operations.items():
        tool = next((t for t in binding.tools if t.tool_name == tool_name), None)
        if tool is None:
            continue
        svc = binding.to_service_binding(op_id)
        if svc.mcp_tools:
            svc.mcp_tools = [tool]
        result.append(svc)
    return result


def load_service_binding_from_ssdm(ssdm_doc) -> list[ServiceBinding]:
    payload = ssdm_doc.metadata.get("mcp", {}) if hasattr(ssdm_doc, "metadata") else {}
    binding = payload.get("binding") if isinstance(payload, dict) else None
    if binding is None:
        return []

    # If parser stored an actual MCPSouthBoundBinding instance, return direct operations.
    if isinstance(binding, MCPSouthBoundBinding):
        result = []
        for idx, op in enumerate(ssdm_doc.operations):
            service_tool = next((t for t in binding.tools if t.tool_name == idx), None)
            if service_tool is None:
                service_tool = binding.tools[0] if binding.tools else None
            sb = binding.to_service_binding(op.name)
            if service_tool:
                sb.mcp_tools = [service_tool]
            result.append(sb)
        return result

    # Otherwise parse payload as plain dict and materialize.
    return load_service_bindings(binding if isinstance(binding, dict) else {"operation_bindings": {}})
