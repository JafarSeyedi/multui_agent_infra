# engines/document/models/tsdm_models.py
"""
TSDM – Tools Standard Definition Model
========================================
Format‑independent description of executable tools.
Covers:
  - DB Query / Statement
  - South‑bound Service Calls (HTTP, gRPC, GraphQL, TCP socket, load‑balanced)
  - Message‑bus Tools (Kafka, AMQP, NATS)
  - CLI Commands
  - Python Functions
  - MCP Tools
  - YANG / NETCONF Operations
  - MIB / SNMP Operations
  - Composite / Pipeline Tools
  - File Tools (read/write)
  - AI / ML Model Invocation

All fields are strongly typed.  Metadata not required for execution is stored
in annotations.
"""
from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from enum import Enum

from .base import BaseDocument
from .media_types import DocumentStandard
from .ssdm_models import HttpMethod

# ── Enums ─────────────────────────────────────────────────────────
class ToolKind(str, Enum):
    DB_QUERY        = "dbQuery"
    DB_STATEMENT    = "dbStatement"
    HTTP_SERVICE    = "httpService"
    GRPC_SERVICE    = "grpcService"
    GRAPHQL         = "graphql"
    TCP_SOCKET      = "tcpSocket"
    MESSAGE_BUS     = "messageBus"
    CLI             = "cli"
    PYTHON_FUNCTION = "pythonFunction"
    MCP             = "mcp"
    YANG_NETCONF    = "yangNetconf"
    MIB_SNMP        = "mibSnmp"
    FILE_READ       = "fileRead"
    FILE_WRITE      = "fileWrite"
    AI_MODEL        = "aiModel"
    COMPOSITE       = "composite"

class ParameterSource(str, Enum):
    CALLER_ARG   = "callerArg"       # explicit argument from caller
    ENV_VAR      = "envVar"
    CONFIG       = "config"
    SECRET       = "secret"
    CONTEXT_PATH = "contextPath"     # e.g., "workflow.variables.x"

class ParameterType(str, Enum):
    STRING   = "string"
    INTEGER  = "integer"
    FLOAT    = "float"
    BOOLEAN  = "boolean"
    JSON     = "json"
    BINARY   = "binary"

class LoadBalanceStrategy(str, Enum):
    ROUND_ROBIN = "roundRobin"
    RANDOM      = "random"
    LEAST_CONN  = "leastConnections"

class SnmpVersion(str, Enum):
    SNMPv1  = "v1"
    SNMPv2c = "v2c"
    SNMPv3  = "v3"

class NetconfProtocol(str, Enum):
    SSH  = "ssh"
    TLS  = "tls"


# ── Parameter & Output ───────────────────────────────────────────
@dataclass
class ToolParameter:
    name: str
    type: ParameterType = ParameterType.STRING
    required: bool = False
    default: str | None = None
    description: str | None = None
    source: ParameterSource = ParameterSource.CALLER_ARG
    source_path: str | None = None       # env var name, config key, etc.
    mapping_target: str | None = None    # where in the tool request this value is placed (e.g., "query.page")

@dataclass
class ToolOutput:
    name: str
    type: ParameterType = ParameterType.JSON
    description: str | None = None
    mapping_from: str | None = None      # path in raw response to extract


# ── Base Tool ────────────────────────────────────────────────────
@dataclass
class Tool:
    id: str
    name: str
    description: str | None = None
    version: str = "1.0.0"
    kind: ToolKind = ToolKind.CLI
    parameters: list[ToolParameter] = field(default_factory=list)
    outputs: list[ToolOutput] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    annotations: dict[str, str] = field(default_factory=dict)
    retry_policy: str | None = None
    timeout_ms: int = 30000


# ── Concrete tool types ──────────────────────────────────────────

@dataclass
class DbQueryTool(Tool):
    """Execute a read‑only query against a database."""
    connection_string: str = ""
    query_template: str = ""                # SQL with named parameters

@dataclass
class DbStatementTool(Tool):
    """Execute a DML/DDL statement."""
    connection_string: str = ""
    statement_template: str = ""

@dataclass
class HttpServiceTool(Tool):
    """Call an HTTP/HTTPS endpoint (south‑bound service)."""
    endpoint_url: str = ""
    http_method: HttpMethod = HttpMethod.GET
    headers: dict[str, str] = field(default_factory=dict)
    body_template: str | None = None     # JSON template with placeholders
    auth: str | None = None              # reference to an AuthConfig id
    load_balance: LoadBalanceStrategy = LoadBalanceStrategy.ROUND_ROBIN
    endpoints: list[str] = field(default_factory=list)   # multiple URLs for LB

@dataclass
class GrpcServiceTool(Tool):
    """Call a gRPC service."""
    host: str = "localhost"
    port: int = 50051
    service_name: str = ""
    method_name: str = ""
    proto_file_path: str | None = None
    tls_config: str | None = None

@dataclass
class GraphQLTool(Tool):
    endpoint_url: str = ""
    query_template: str = ""
    variables: dict[str, str] = field(default_factory=dict)

@dataclass
class TcpSocketTool(Tool):
    """Low‑level TCP socket communication."""
    host: str = "localhost"
    port: int = 8080
    request_template: str = ""              # raw bytes / text template
    expect_response: bool = True
    connection_timeout_ms: int = 5000

@dataclass
class MessageBusTool(Tool):
    """Publish or subscribe to a message broker."""
    transport: str = "kafka"                # "kafka", "amqp", "nats"
    topic: str = ""
    message_template: str = ""
    publish: bool = True                     # True = publish, False = subscribe

@dataclass
class CliTool(Tool):
    """Execute a command‑line program."""
    command: str = ""
    args: list[str] = field(default_factory=list)
    working_directory: str | None = None
    env_vars: dict[str, str] = field(default_factory=dict)

@dataclass
class PythonFunctionTool(Tool):
    """Call a Python function (module.function)."""
    module_path: str = ""                    # fully qualified, e.g., "mypackage.mymodule"
    function_name: str = ""
    import_type: str = "direct"             # "direct" or "importlib"

@dataclass
class MCPTool(Tool):
    """Call a tool on an MCP server (south‑bound)."""
    server_command: str | None = None      # for STDIO transport
    server_url: str | None = None          # for SSE transport
    tool_name: str = ""
    transport: str = "stdio"                 # "stdio" or "sse"

@dataclass
class YangNetconfTool(Tool):
    """Execute a YANG / NETCONF operation."""
    host: str = "localhost"
    port: int = 830
    username: str = ""
    password: str | None = None
    netconf_protocol: NetconfProtocol = NetconfProtocol.SSH
    rpc_template: str = ""                   # XML RPC body with placeholders

@dataclass
class MibSnmpTool(Tool):
    """Perform an SNMP GET / SET / WALK operation."""
    host: str = "localhost"
    port: int = 161
    community: str | None = None          # for v1/v2c
    snmp_version: SnmpVersion = SnmpVersion.SNMPv2c
    oid: str = ""
    operation: str = "get"                   # "get", "set", "walk"
    value: str | None = None              # for set

@dataclass
class FileReadTool(Tool):
    """Read content from a file."""
    file_path_template: str = ""
    encoding: str = "utf-8"

@dataclass
class FileWriteTool(Tool):
    """Write content to a file."""
    file_path_template: str = ""
    content_template: str = ""               # template for the file content
    encoding: str = "utf-8"

@dataclass
class AiModelTool(Tool):
    """Invoke an AI / ML model (e.g., via REST)."""
    endpoint_url: str = ""
    model_name: str = ""
    prompt_template: str = ""
    api_key_env: str | None = None

@dataclass
class CompositeTool(Tool):
    """Pipeline / chain of other tools."""
    steps: list[str] = field(default_factory=list)   # tool IDs in execution order
    data_flow: dict[str, str] = field(default_factory=dict)  # step → output mapping to next step input


# ── Top‑level TSDM Document ──────────────────────────────────────
@dataclass
class TSDMDocument(BaseDocument):
    """A document describing a set of tools (for discovery / configuration)."""
    kind: DocumentStandard = DocumentStandard.TSDM    # add TSDM to your enum
    tools: list[Tool] = field(default_factory=list)
