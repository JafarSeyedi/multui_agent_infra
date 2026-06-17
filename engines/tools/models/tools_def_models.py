from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from engines.document.models.base import BaseDocument
from engines.document.models.standard import DocumentStandard


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
    BIGQUERY = "bigquery"
    BIGTABLE = "bigtable"
    DATA_AGENT = "dataAgent"
    APIGEE = "apigee"
    CODE_EXECUTION = "codeExecution"
    COMPUTER_USE = "computerUse"
    GEMINI_CODE_EXEC = "geminiCodeExec"
    GOOGLE_SEARCH = "googleSearch"
    VERTEX_AI_SEARCH = "vertexAiSearch"

    CACHE = "cache"
    KEY_VALUE = "keyValue"
    OBJECT_STORAGE = "objectStorage"
    STREAM = "stream"
    EVENT_LOG = "eventLog"
    TIME_SERIES = "timeSeries"
    VECTOR_DB = "vectorDb"
    GRAPH_STORAGE = "graphStorage"
    SERVICE_INVOCATION = "serviceInvocation"
    SERVICE_DISCOVERY = "serviceDiscovery"
    AUTH = "auth"
    BINDING = "binding"

    # ── Knowledge engine kinds ──────────────────────────────────────
    KNOWLEDGE_RAG = "knowledgeRag"
    KNOWLEDGE_SEMANTIC_GRAPH = "knowledgeSemanticGraph"
    KNOWLEDGE_ML_MINING = "knowledgeMlMining"
    KNOWLEDGE_BI_AGGREGATION = "knowledgeBiAggregation"
    KNOWLEDGE_PROCESS_MINING = "knowledgeProcessMining"
    KNOWLEDGE_QUERY = "knowledgeQuery"


class ParameterName(str, Enum):
    HOST = "host"
    PORT = "port"
    URL = "url"
    BASE_URL = "base_url"
    TIMEOUT_MS = "timeout_ms"
    TLS = "tls"
    TRANSPORT = "transport"

    METHOD = "method"
    HEADERS = "headers"
    LOAD_BALANCE = "load_balance"
    ENDPOINTS = "endpoints"
    SERVICE = "service"
    PROTO_FILE = "proto_file"

    AUTH_TOKEN = "auth_token"
    USERNAME = "username"
    PASSWORD = "password"
    API_KEY = "api_key"

    COMMAND = "command"
    WORK_DIR = "work_dir"
    ENV = "env"
    LANGUAGE = "language"
    HEADLESS = "headless"
    SANDBOX = "sandbox"
    ENCODING = "encoding"

    MODEL = "model"
    TEMPERATURE = "temperature"
    MAX_TOKENS = "max_tokens"

    CONNECTION = "connection"
    PROJECT = "project"
    DATASET = "dataset"
    LOCATION = "location"
    INSTANCE = "instance"
    TABLE = "table"
    CACHE = "cache"
    ROW_KEY = "row_key"
    COLUMNS = "columns"
    COLUMN_FAMILY = "column_family"
    FILTER = "filter"
    MAX_RESULTS = "max_results"

    CX = "cx"
    DATA_STORE = "data_store"
    SERVING_CONFIG = "serving_config"
    AGENT_ID = "agent_id"
    API_ID = "api_id"
    FUNCTION = "function"
    MODULE = "module"
    IMPORT = "import"

    SNMP_VERSION = "snmp_version"
    COMMUNITY = "community"
    NETCONF_PROTOCOL = "netconf_protocol"
    OID = "oid"

    TOPIC = "topic"
    SELECTOR = "selector"
    FILE_PATH = "file_path"

    ACTION = "action"
    VARIABLES = "variables"
    EXTRA = "extra"
    BACKEND = "backend"
    KEY = "key"
    BUCKET = "bucket"
    CONTENT_TYPE = "content_type"
    MEASUREMENT = "measurement"
    FIELDS = "fields"
    TAGS = "tags"
    EMBEDDING = "embedding"
    NODE_ID = "node_id"
    SOURCE_NODE = "source_node"
    TARGET_NODE = "target_node"
    RELATION = "relation"
    RECIPIENT = "recipient"
    BUS_TYPE = "bus_type"
    BINDING_DATA = "binding_data"
    EVENT_TYPE = "event_type"
    DIMENSIONS = "dimensions"
    TOP_K = "top_k"
    START = "start"
    END = "end"
    GROUP = "group"
    METADATA = "metadata"
    PROPERTIES = "properties"
    MESSAGE_TYPE = "message_type"
    FORMAT = "format"
    PARSER_NAME = "parser_name"
    TARGET_FORMAT = "target_format"
    SOURCE = "source"
    DESTINATION = "destination"
    QUERY_TEXT = "query_text"
    RETRIEVER = "retriever"
    CHUNK_SIZE = "chunk_size"
    CHUNK_OVERLAP = "chunk_overlap"
    EXTRA_ARGS = "extra_args"
    GRAPH_NODES = "graph_nodes"
    GRAPH_EDGES = "graph_edges"
    FEATURES = "features"
    MAX_DEPTH = "max_depth"
    NODE_LABEL = "node_label"
    NODE_TYPE = "node_type"
    OP_TYPE = "op_type"
    FIELD_NAME = "field_name"
    GROUP_BY = "group_by"
    MEASURES = "measures"
    FILTER_EXPR = "filter_expr"
    MATERIALIZED = "materialized"
    CUBE_NAME = "cube_name"
    ACTIVITY_KEY = "activity_key"
    DECISION_POINT_ID = "decision_point_id"


class ArgName(str, Enum):
    ACTION = "action"
    INPUT = "input"
    MESSAGES = "messages"
    CODE = "code"
    SOURCE = "source"
    CONTENT = "content"
    DATA = "data"
    HEADERS = "headers"
    BODY = "body"
    KEY = "key"
    VALUE = "value"
    QUERY = "query"
    PAYLOAD = "payload"
    OPERATION = "operation"
    ARGUMENTS = "arguments"
    FILTERS = "filters"
    PARAMS = "params"
    MODEL_FORMAT = "model_format"
    X_DATA = "x_data"
    Y_DATA = "y_data"
    METRICS = "metrics"
    DOCUMENT_ID = "document_id"
    RETRIEVER_NAME = "retriever_name"
    RERANK_TOP_K = "rerank_top_k"


class RetryPolicy(str, Enum):
    NONE = "none"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    FIXED_INTERVAL = "fixed_interval"
    LINEAR_BACKOFF = "linear_backoff"


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
    params: list[ToolParameter] = field(default_factory=list)
    args: list[ToolParameter] = field(default_factory=list)
    outputs: list[ToolOutput] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    annotations: dict[str, str] = field(default_factory=dict)
    retry_policy: RetryPolicy | None = None
    timeout_ms: int = 30000


class TSDMDocument(BaseDocument):
    kind: DocumentStandard = DocumentStandard.TSDM
    tools: list[Tool] = field(default_factory=list)
