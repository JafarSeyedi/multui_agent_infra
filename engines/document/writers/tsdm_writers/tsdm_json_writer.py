# engines/document/writers/tsdm_writers/tsdm_json_writer.py
import json
import uuid
from typing import Any

from ...models.tsdm_models import (
    AiModelTool,
    CliTool,
    CompositeTool,
    DbQueryTool,
    DbStatementTool,
    FileReadTool,
    FileWriteTool,
    GraphQLTool,
    GrpcServiceTool,
    HttpMethod,
    HttpServiceTool,
    LoadBalanceStrategy,
    MCPTool,
    MessageBusTool,
    MibSnmpTool,
    NetconfProtocol,
    ParameterSource,
    ParameterType,
    PythonFunctionTool,
    SnmpVersion,
    TcpSocketTool,
    Tool,
    ToolKind,
    ToolOutput,
    ToolParameter,
    TSDMDocument,
    YangNetconfTool,
)
from .base_tsdm_writer import BaseTSDMWriter


class TsdmJsonWriter(BaseTSDMWriter):
    name = "tsdm_json"
    supported_extensions = (".tsdm.json", ".tools.json")

    async def _write_design(self, document: TSDMDocument) -> bytes:
        tools = [self._tool_to_dict(t) for t in document.tools]
        output = {"tools": tools}
        json_str = json.dumps(output, indent=2, ensure_ascii=False)
        return json_str.encode(getattr(self.options, "encoding", "utf-8") or "utf-8")

    def _tool_to_dict(self, tool: Tool) -> dict[str, Any]:
        base = {
            "id": tool.id,
            "name": tool.name,
            "description": tool.description,
            "version": tool.version,
            "kind": tool.kind.value,
            "parameters": [self._param_to_dict(p) for p in tool.parameters],
            "outputs": [self._output_to_dict(o) for o in tool.outputs],
            "tags": tool.tags,
            "annotations": tool.annotations,
            "retry_policy": tool.retry_policy,
            "timeout_ms": tool.timeout_ms,
        }

        # Use isinstance for type‑safe access to subclass attributes
        if isinstance(tool, DbQueryTool):
            base["connection_string"] = tool.connection_string
            base["query_template"] = tool.query_template

        elif isinstance(tool, DbStatementTool):
            base["connection_string"] = tool.connection_string
            base["statement_template"] = tool.statement_template

        elif isinstance(tool, HttpServiceTool):
            base.update({
                "endpoint_url": tool.endpoint_url,
                "http_method": tool.http_method.value,
                "headers": tool.headers,
                "body_template": tool.body_template,
                "auth": tool.auth,
                "load_balance": tool.load_balance.value,
                "endpoints": tool.endpoints,
            })

        elif isinstance(tool, GrpcServiceTool):
            base.update({
                "host": tool.host,
                "port": tool.port,
                "service_name": tool.service_name,
                "method_name": tool.method_name,
                "proto_file_path": tool.proto_file_path,
                "tls_config": tool.tls_config,
            })

        elif isinstance(tool, GraphQLTool):
            base.update({
                "endpoint_url": tool.endpoint_url,
                "query_template": tool.query_template,
                "variables": tool.variables,
            })

        elif isinstance(tool, TcpSocketTool):
            base.update({
                "host": tool.host,
                "port": tool.port,
                "request_template": tool.request_template,
                "expect_response": tool.expect_response,
                "connection_timeout_ms": tool.connection_timeout_ms,
            })

        elif isinstance(tool, MessageBusTool):
            base.update({
                "transport": tool.transport,
                "topic": tool.topic,
                "message_template": tool.message_template,
                "publish": tool.publish,
            })

        elif isinstance(tool, CliTool):
            base.update({
                "command": tool.command,
                "args": tool.args,
                "working_directory": tool.working_directory,
                "env_vars": tool.env_vars,
            })

        elif isinstance(tool, PythonFunctionTool):
            base.update({
                "module_path": tool.module_path,
                "function_name": tool.function_name,
                "import_type": tool.import_type,
            })

        elif isinstance(tool, MCPTool):
            base.update({
                "server_command": tool.server_command,
                "server_url": tool.server_url,
                "tool_name": tool.tool_name,
                "transport": tool.transport,
            })

        elif isinstance(tool, YangNetconfTool):
            base.update({
                "host": tool.host,
                "port": tool.port,
                "username": tool.username,
                "password": tool.password,
                "netconf_protocol": tool.netconf_protocol.value,
                "rpc_template": tool.rpc_template,
            })

        elif isinstance(tool, MibSnmpTool):
            base.update({
                "host": tool.host,
                "port": tool.port,
                "community": tool.community,
                "snmp_version": tool.snmp_version.value,
                "oid": tool.oid,
                "operation": tool.operation,
                "value": tool.value,
            })

        elif isinstance(tool, FileReadTool):
            base.update({
                "file_path_template": tool.file_path_template,
                "encoding": tool.encoding,
            })

        elif isinstance(tool, FileWriteTool):
            base.update({
                "file_path_template": tool.file_path_template,
                "content_template": tool.content_template,
                "encoding": tool.encoding,
            })

        elif isinstance(tool, AiModelTool):
            base.update({
                "endpoint_url": tool.endpoint_url,
                "model_name": tool.model_name,
                "prompt_template": tool.prompt_template,
                "api_key_env": tool.api_key_env,
            })

        elif isinstance(tool, CompositeTool):
            base.update({
                "steps": tool.steps,
                "data_flow": tool.data_flow,
            })

        # If none of the above, it's a base Tool with no extra fields (fallback)
        return base

    def _param_to_dict(self, p: ToolParameter) -> dict[str, Any]:
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

    def _output_to_dict(self, o: ToolOutput) -> dict[str, Any]:
        return {
            "name": o.name,
            "type": o.type.value,
            "description": o.description,
            "mapping_from": o.mapping_from,
        }