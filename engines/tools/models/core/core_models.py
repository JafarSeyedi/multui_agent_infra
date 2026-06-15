from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from engines.document.models.base import BaseDocument
from engines.document.models.standard import DocumentStandard
from engines.document.models.ssdm_models import HttpMethod


class ToolKind(str, Enum):
    DB_QUERY = "dbQuery"
    DB_STATEMENT = "dbStatement"
    HTTP_SERVICE = "httpService"
    GRPC_SERVICE = "grpcService"
    GRAPHQL = "graphql"
    TCP_SOCKET = "tcpSocket"
    MESSAGE_BUS = "messageBus"
    CLI = "cli"
    PYTHON_FUNCTION = "pythonFunction"
    MCP = "mcp"
    YANG_NETCONF = "yangNetconf"
    MIB_SNMP = "mibSnmp"
    FILE_READ = "fileRead"
    FILE_WRITE = "fileWrite"
    AI_MODEL = "aiModel"
    COMPOSITE = "composite"


class ParameterSource(str, Enum):
    CALLER_ARG = "callerArg"
    ENV_VAR = "envVar"
    CONFIG = "config"
    SECRET = "secret"
    CONTEXT_PATH = "contextPath"


class ParameterType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    JSON = "json"
    BINARY = "binary"


class LoadBalanceStrategy(str, Enum):
    ROUND_ROBIN = "roundRobin"
    RANDOM = "random"
    LEAST_CONN = "leastConnections"


class SnmpVersion(str, Enum):
    SNMPv1 = "v1"
    SNMPv2c = "v2c"
    SNMPv3 = "v3"


class NetconfProtocol(str, Enum):
    SSH = "ssh"
    TLS = "tls"


@dataclass
class ToolParameter:
    name: str
    type: ParameterType = ParameterType.STRING
    required: bool = False
    default: str | None = None
    description: str | None = None
    source: ParameterSource = ParameterSource.CALLER_ARG
    source_path: str | None = None
    mapping_target: str | None = None


@dataclass
class ToolOutput:
    name: str
    type: ParameterType = ParameterType.JSON
    description: str | None = None
    mapping_from: str | None = None


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


class TSDMDocument(BaseDocument):
    kind: DocumentStandard = DocumentStandard.TSDM
    tools: list[Tool] = field(default_factory=list)
