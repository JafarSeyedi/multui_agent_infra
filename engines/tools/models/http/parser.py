from __future__ import annotations

from engines.document.models.ssdm_models import HttpMethod
from engines.tools.models.core.core_models import ToolKind
from engines.tools.models.core.core_models import ToolParameter
from engines.tools.models.core.core_models import ParameterSource
from engines.tools.models.core.core_models import ParameterType
from engines.tools.models.core.core_models import ToolOutput
from engines.tools.models.core.core_models import LoadBalanceStrategy
from engines.tools.models.http.http_models import HttpServiceTool
from engines.tools.models.http.http_models import GraphQLTool


def parse_http_tool(data: dict) -> HttpServiceTool | GraphQLTool:
    kind = ToolKind(data.get("kind", "httpService"))
    common = _common_fields(data)
    if kind == ToolKind.GRAPHQL:
        return GraphQLTool(
            **common,
            endpoint_url=data.get("endpoint_url", ""),
            query_template=data.get("query_template", ""),
            variables=data.get("variables", {}),
        )
    return HttpServiceTool(
        **common,
        endpoint_url=data.get("endpoint_url", ""),
        http_method=HttpMethod(data.get("http_method", "GET")),
        headers=data.get("headers", {}),
        body_template=data.get("body_template"),
        auth=data.get("auth"),
        load_balance=LoadBalanceStrategy(data.get("load_balance", "roundRobin")),
        endpoints=data.get("endpoints", []),
    )


def _common_fields(data: dict) -> dict:
    return {
        "id": data.get("id", ""),
        "name": data.get("name", ""),
        "description": data.get("description"),
        "version": data.get("version", "1.0.0"),
        "kind": ToolKind(data.get("kind", "httpService")),
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
