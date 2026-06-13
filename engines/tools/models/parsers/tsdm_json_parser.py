# engines/document/parsers/tsdm_parsers/tsdm_json_parser.py
import json
import uuid

from engines.document.models.media_types import MEDIA_TYPES
from engines.tools.models.tsdm_models import AiModelTool
from engines.tools.models.tsdm_models import CliTool
from engines.tools.models.tsdm_models import CompositeTool
from engines.tools.models.tsdm_models import DbQueryTool
from engines.tools.models.tsdm_models import DbStatementTool
from engines.tools.models.tsdm_models import FileReadTool
from engines.tools.models.tsdm_models import FileWriteTool
from engines.tools.models.tsdm_models import GraphQLTool
from engines.tools.models.tsdm_models import GrpcServiceTool
from engines.tools.models.tsdm_models import HttpMethod
from engines.tools.models.tsdm_models import HttpServiceTool
from engines.tools.models.tsdm_models import LoadBalanceStrategy
from engines.tools.models.tsdm_models import MCPTool
from engines.tools.models.tsdm_models import MessageBusTool
from engines.tools.models.tsdm_models import MibSnmpTool
from engines.tools.models.tsdm_models import NetconfProtocol
from engines.tools.models.tsdm_models import ParameterSource
from engines.tools.models.tsdm_models import ParameterType
from engines.tools.models.tsdm_models import PythonFunctionTool
from engines.tools.models.tsdm_models import SnmpVersion
from engines.tools.models.tsdm_models import TcpSocketTool
from engines.tools.models.tsdm_models import Tool
from engines.tools.models.tsdm_models import ToolKind
from engines.tools.models.tsdm_models import ToolOutput
from engines.tools.models.tsdm_models import ToolParameter
from engines.tools.models.tsdm_models import TSDMDocument
from engines.tools.models.tsdm_models import YangNetconfTool
from engines.document.parsers.base import ParseOptions
from .base_tsdm_parser import BaseTSDMParser

_KIND_CLASS_MAP = {
    ToolKind.DB_QUERY: DbQueryTool,
    ToolKind.DB_STATEMENT: DbStatementTool,
    ToolKind.HTTP_SERVICE: HttpServiceTool,
    ToolKind.GRPC_SERVICE: GrpcServiceTool,
    ToolKind.GRAPHQL: GraphQLTool,
    ToolKind.TCP_SOCKET: TcpSocketTool,
    ToolKind.MESSAGE_BUS: MessageBusTool,
    ToolKind.CLI: CliTool,
    ToolKind.PYTHON_FUNCTION: PythonFunctionTool,
    ToolKind.MCP: MCPTool,
    ToolKind.YANG_NETCONF: YangNetconfTool,
    ToolKind.MIB_SNMP: MibSnmpTool,
    ToolKind.FILE_READ: FileReadTool,
    ToolKind.FILE_WRITE: FileWriteTool,
    ToolKind.AI_MODEL: AiModelTool,
    ToolKind.COMPOSITE: CompositeTool,
}

class TsdmJsonParser(BaseTSDMParser):
    name = "tsdm_json"
    supported_extensions = (".tsdm.json", ".tools.json")

    async def _parse_to_tsdm(self, data: bytes, source_name: str, options: ParseOptions) -> TSDMDocument:
        encoding = options.encoding or "utf-8"
        text = data.decode(encoding)
        raw = json.loads(text)
        doc = TSDMDocument(
            title=source_name,
            document_id=f"tsdm_json_{uuid.uuid4().hex[:16]}",
            media_type=MEDIA_TYPES["tsdm_json"],
        )
        
        tools_data = raw.get("tools", [])
        for td in tools_data:
            tool = self._parse_tool(td)
            doc.tools.append(tool)
        return doc

    def _parse_tool(self, data: dict) -> Tool:
        kind_str = data.get("kind", "cli")
        kind = ToolKind(kind_str)
        cls = _KIND_CLASS_MAP.get(kind, CliTool)

        # Common fields
        common_fields = {
            "id": data.get("id", ""),
            "name": data.get("name", ""),
            "description": data.get("description"),
            "version": data.get("version", "1.0.0"),
            "parameters": self._parse_parameters(data.get("parameters", [])),
            "outputs": self._parse_outputs(data.get("outputs", [])),
            "tags": data.get("tags", []),
            "annotations": data.get("annotations", {}),
            "retry_policy": data.get("retry_policy"),
            "timeout_ms": data.get("timeout_ms", 30000),
            "kind": kind,
        }

        # Specific fields per kind
        specific = {}
        if kind == ToolKind.DB_QUERY or kind == ToolKind.DB_STATEMENT:
            specific = {
                "connection_string": data.get("connection_string", ""),
                "query_template": data.get("query_template", ""),
            } if kind == ToolKind.DB_QUERY else {
                "connection_string": data.get("connection_string", ""),
                "statement_template": data.get("statement_template", ""),
            }
        elif kind == ToolKind.HTTP_SERVICE:
            specific = {
                "endpoint_url": data.get("endpoint_url", ""),
                "http_method": HttpMethod(data.get("http_method", "GET")),
                "headers": data.get("headers", {}),
                "body_template": data.get("body_template"),
                "auth": data.get("auth"),
                "load_balance": LoadBalanceStrategy(data.get("load_balance", "roundRobin")),
                "endpoints": data.get("endpoints", []),
            }
        elif kind == ToolKind.GRPC_SERVICE:
            specific = {
                "host": data.get("host", "localhost"),
                "port": data.get("port", 50051),
                "service_name": data.get("service_name", ""),
                "method_name": data.get("method_name", ""),
                "proto_file_path": data.get("proto_file_path"),
                "tls_config": data.get("tls_config"),
            }
        elif kind == ToolKind.GRAPHQL:
            specific = {
                "endpoint_url": data.get("endpoint_url", ""),
                "query_template": data.get("query_template", ""),
                "variables": data.get("variables", {}),
            }
        elif kind == ToolKind.TCP_SOCKET:
            specific = {
                "host": data.get("host", "localhost"),
                "port": data.get("port", 8080),
                "request_template": data.get("request_template", ""),
                "expect_response": data.get("expect_response", True),
                "connection_timeout_ms": data.get("connection_timeout_ms", 5000),
            }
        elif kind == ToolKind.MESSAGE_BUS:
            specific = {
                "transport": data.get("transport", "kafka"),
                "topic": data.get("topic", ""),
                "message_template": data.get("message_template", ""),
                "publish": data.get("publish", True),
            }
        elif kind == ToolKind.CLI:
            specific = {
                "command": data.get("command", ""),
                "args": data.get("args", []),
                "working_directory": data.get("working_directory"),
                "env_vars": data.get("env_vars", {}),
            }
        elif kind == ToolKind.PYTHON_FUNCTION:
            specific = {
                "module_path": data.get("module_path", ""),
                "function_name": data.get("function_name", ""),
                "import_type": data.get("import_type", "direct"),
            }
        elif kind == ToolKind.MCP:
            specific = {
                "server_command": data.get("server_command"),
                "server_url": data.get("server_url"),
                "tool_name": data.get("tool_name", ""),
                "transport": data.get("transport", "stdio"),
            }
        elif kind == ToolKind.YANG_NETCONF:
            specific = {
                "host": data.get("host", "localhost"),
                "port": data.get("port", 830),
                "username": data.get("username", ""),
                "password": data.get("password"),
                "netconf_protocol": NetconfProtocol(data.get("netconf_protocol", "ssh")),
                "rpc_template": data.get("rpc_template", ""),
            }
        elif kind == ToolKind.MIB_SNMP:
            specific = {
                "host": data.get("host", "localhost"),
                "port": data.get("port", 161),
                "community": data.get("community"),
                "snmp_version": SnmpVersion(data.get("snmp_version", "v2c")),
                "oid": data.get("oid", ""),
                "operation": data.get("operation", "get"),
                "value": data.get("value"),
            }
        elif kind == ToolKind.FILE_READ:
            specific = {
                "file_path_template": data.get("file_path_template", ""),
                "encoding": data.get("encoding", "utf-8"),
            }
        elif kind == ToolKind.FILE_WRITE:
            specific = {
                "file_path_template": data.get("file_path_template", ""),
                "content_template": data.get("content_template", ""),
                "encoding": data.get("encoding", "utf-8"),
            }
        elif kind == ToolKind.AI_MODEL:
            specific = {
                "endpoint_url": data.get("endpoint_url", ""),
                "model_name": data.get("model_name", ""),
                "prompt_template": data.get("prompt_template", ""),
                "api_key_env": data.get("api_key_env"),
            }
        elif kind == ToolKind.COMPOSITE:
            specific = {
                "steps": data.get("steps", []),
                "data_flow": data.get("data_flow", {}),
            }
        # Combine
        tool_data = {**common_fields, **specific}
        tool = cls(**tool_data)
        return tool

    def _parse_parameters(self, params: list) -> list[ToolParameter]:
        return [ToolParameter(
            name=p.get("name", ""),
            type=ParameterType(p.get("type", "string")),
            required=p.get("required", False),
            default=p.get("default"),
            description=p.get("description"),
            source=ParameterSource(p.get("source", "callerArg")),
            source_path=p.get("source_path"),
            mapping_target=p.get("mapping_target"),
        ) for p in params]

    def _parse_outputs(self, outputs: list) -> list[ToolOutput]:
        return [ToolOutput(
            name=o.get("name", ""),
            type=ParameterType(o.get("type", "json")),
            description=o.get("description"),
            mapping_from=o.get("mapping_from"),
        ) for o in outputs]
