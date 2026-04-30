# API/Service Structured Document Model (SSDM)
# Purpose: Represent HTTP APIs, SOAP services, network management interfaces, and RPC protocols.

# Formats to support
# Format	                            File extensions	        Notes
# OpenAPI (Swagger)	                    .yaml, .json	        REST API specification
# SOAP / WSDL	                        .wsdl	                XML‑based service description
# YANG	                                .yang	                Network device modelling (RFC 7950)
# MIB (SNMP)	                        .mib	                Management Information Base
# AsyncAPI	                            .yaml, .json	        Event‑driven API specification
# GraphQL Schema	                    .graphql	            (Overlaps with MSDM)
# gRPC / Protobuf	                    .proto	                (Overlaps with MSDM)
# RAML	                                .raml	                RESTful API Modeling Language
# API Blueprint	                        .apib	                Markdown‑based API description
# Web IDL	                            .webidl	                Browser API definitions
# Postman Collections	                .json	                Exported API collections
# CDDL (CBOR Data Definition Language)	.cddl	                IoT / CBOR schema


# engines/document/models/ssdm_models.py
"""
SSDM – Service Standard Definition Model
===========================================
Format‑independent representation of service / API definitions.
Supports REST, SOAP, GraphQL, AsyncAPI, YANG, MIB, Protobuf/GRPC, etc.
All types and messages are described via MSDM entities.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Union
from ..base import BaseDocument
from ..media_types import DocumentStandard
from ..msdm_models import MSDMDocument, Entity


# ============================================================
# Enums
# ============================================================

class HttpMethod(str, Enum):
    GET     = "GET"
    POST    = "POST"
    PUT     = "PUT"
    DELETE  = "DELETE"
    PATCH   = "PATCH"
    HEAD    = "HEAD"
    OPTIONS = "OPTIONS"
    TRACE   = "TRACE"


class ParameterLocation(str, Enum):
    PATH    = "path"
    QUERY   = "query"
    HEADER  = "header"
    COOKIE  = "cookie"
    BODY    = "body"


class SecurityType(str, Enum):
    HTTP_BASIC      = "httpBasic"
    HTTP_BEARER     = "httpBearer"
    API_KEY         = "apiKey"
    OAUTH2          = "oauth2"
    OPENID_CONNECT  = "openIdConnect"
    MUTUAL_TLS      = "mutualTLS"


class OAuth2Flow(str, Enum):
    IMPLICIT        = "implicit"
    PASSWORD        = "password"
    CLIENT_CREDENTIALS = "clientCredentials"
    AUTHORIZATION_CODE = "authorizationCode"


class ApiKeyLocation(str, Enum):
    HEADER  = "header"
    QUERY   = "query"
    COOKIE  = "cookie"


class OperationType(str, Enum):
    """High‑level operation kind; maps to different format specifics."""
    REQUEST_RESPONSE = "requestResponse"
    PUBLISH          = "publish"       # AsyncAPI publish
    SUBSCRIBE        = "subscribe"     # AsyncAPI subscribe
    ONE_WAY          = "oneWay"        # SOAP one‑way
    NOTIFICATION     = "notification"  # SOAP notification


class YangStatement(str, Enum):
    """Key YANG statement names."""
    MODULE          = "module"
    CONTAINER       = "container"
    LIST            = "list"
    LEAF            = "leaf"
    LEAF_LIST       = "leaf-list"
    CHOICE          = "choice"
    CASE            = "case"
    AUGMENT         = "augment"
    USES            = "uses"
    REFINE          = "refine"
    DEVIATION       = "deviation"
    NOTIFICATION    = "notification"
    RPC             = "rpc"


class SnmpAccess(str, Enum):
    """SNMP access permissions."""
    READ_ONLY       = "read-only"
    READ_WRITE      = "read-write"
    NOT_ACCESSIBLE  = "not-accessible"


class SnmpStatus(str, Enum):
    CURRENT         = "current"
    DEPRECATED      = "deprecated"
    OBSOLETE        = "obsolete"


# ============================================================
# Service‑wide definitions
# ============================================================

@dataclass
class ContactInfo:
    name: Optional[str] = None
    url: Optional[str] = None
    email: Optional[str] = None


@dataclass
class LicenseInfo:
    name: str
    url: Optional[str] = None


@dataclass
class Server:
    url: str
    description: Optional[str] = None
    variables: Dict[str, str] = field(default_factory=dict)  # variable name → default value


# ============================================================
# Security Schemes
# ============================================================

@dataclass
class SecurityScheme:
    name: str
    type: SecurityType
    description: Optional[str] = None
    # API key
    api_key_location: Optional[ApiKeyLocation] = None
    api_key_param_name: Optional[str] = None
    # OAuth2
    oauth2_flows: List[OAuth2FlowInfo] = field(default_factory=list)
    # OpenID
    open_id_connect_url: Optional[str] = None
    # Mutual TLS
    mutual_tls_subject_dn: Optional[str] = None


@dataclass
class OAuth2FlowInfo:
    flow: OAuth2Flow
    authorization_url: Optional[str] = None
    token_url: Optional[str] = None
    refresh_url: Optional[str] = None
    scopes: Dict[str, str] = field(default_factory=dict)   # name → description


# ============================================================
# Parameter & Body definitions – refer to MSDM entities
# ============================================================

@dataclass
class Parameter:
    name: str
    location: ParameterLocation
    required: bool = False
    description: Optional[str] = None
    # Reference to an MSDM Entity that describes the parameter type.
    # For simple types, the entity will have a single attribute.
    type_entity: Optional[Entity] = None
    # Alternatively, a plain string type if no Entity needed.
    type_string: Optional[str] = None


@dataclass
class RequestBody:
    description: Optional[str] = None
    required: bool = False
    # The request body is always described by an MSDM Entity.
    content_entity: Optional[Entity] = None
    # Multiple content types with different schemas
    content_type_entities: Dict[str, Entity] = field(default_factory=dict)
    is_binary: bool = False
    
@dataclass
class Link:
    operation_id: str
    parameters: Dict[str, str] = field(default_factory=dict)
    description: Optional[str] = None
    request_body: Optional[Any] = None   # can be a raw expression or a reference
    
@dataclass
class Response:
    status_code: str                       # "200", "404", etc.
    description: Optional[str] = None
    # Response body schema
    content_entity: Optional[Entity] = None
    content_type_entities: Dict[str, Entity] = field(default_factory=dict)
    headers: List[Parameter] = field(default_factory=list)
    links: Dict[str, Link] = field(default_factory=dict)
    is_binary: bool = False
    
# ============================================================
# Operation – REST endpoint, SOAP operation, AsyncAPI channel
# ============================================================

@dataclass
class Operation:
    name: str                              # operationId or method name
    type: OperationType = OperationType.REQUEST_RESPONSE
    description: Optional[str] = None

    # HTTP binding
    http_method: Optional[HttpMethod] = None
    path: Optional[str] = None

    # SOAP binding
    soap_action: Optional[str] = None

    # AsyncAPI binding
    channel: Optional[str] = None          # channel name for publish/subscribe
    message_entity: Optional[Entity] = None

    # Input/output
    parameters: List[Parameter] = field(default_factory=list)
    request_body: Optional[RequestBody] = None
    responses: List[Response] = field(default_factory=list)

    # Security (list of security scheme names that apply to this operation)
    security: List[str] = field(default_factory=list)

    # Additional protocol‑specific attributes
    tags: List[str] = field(default_factory=list)
    deprecated: bool = False
    
    callbacks: Dict[str, List[Operation]] = field(default_factory=dict)
    
    servers: List[Server] = field(default_factory=list)
    external_docs: Optional[dict] = None

    extensions: Dict[str, Any] = field(default_factory=dict)

# ============================================================
# YANG specific structures 
# ============================================================

@dataclass
class YangType:
    """A YANG type statement."""
    name: str
    description: Optional[str] = None
    base_type: Optional[str] = None          # e.g., "string", "int32"
    pattern: Optional[str] = None
    length: Optional[str] = None
    range: Optional[str] = None
    enum_values: List[str] = field(default_factory=list)


@dataclass
class YangLeaf:
    name: str
    type: YangType
    description: Optional[str] = None
    default: Optional[str] = None
    mandatory: bool = False


@dataclass
class YangContainer:
    name: str
    description: Optional[str] = None
    children: List[Union[YangContainer, YangLeaf]] = field(default_factory=list)


# ============================================================
# MIB specific structures
# ============================================================

@dataclass
class MibObjectType:
    name: str
    oid: str
    syntax: str                          # "INTEGER", "OCTET STRING", etc.
    access: SnmpAccess
    status: SnmpStatus
    description: Optional[str] = None
    index: Optional[str] = None          # index of table entry


@dataclass
class MibModule:
    name: str
    description: Optional[str] = None
    imports: List[str] = field(default_factory=list)
    objects: List[MibObjectType] = field(default_factory=list)


# ============================================================
# GraphQL / AsyncAPI / CDDL specific structures
# ============================================================

@dataclass
class GraphQLService:
    """GraphQL schema already modelled in MSDM; this is a placeholder."""
    schema_entity: Entity              # the root Query/Mutation/Subscription type


@dataclass
class AsyncAPIInfo:
    asyncapi_version: str = "2.5.0"
    servers: Dict[str, str] = field(default_factory=dict)  # name → url
    channels: List[Operation] = field(default_factory=list) # each channel is an Operation


# ============================================================
# Top‑level SSDM Document
# ============================================================

@dataclass
class SSDM_DOCUMENT(BaseDocument):
    """
    A service definition document, supporting REST, SOAP, AsyncAPI,
    YANG, MIB, GraphQL, and more.
    """
    kind: DocumentStandard = DocumentStandard.SSDM
    title: str
    version: str
    description: Optional[str] = None
    contact: Optional[ContactInfo] = None
    license: Optional[LicenseInfo] = None
    servers: List[Server] = field(default_factory=list)

    # Security schemes (global)
    security_schemes: List[SecurityScheme] = field(default_factory=list)

    # Operations – the core of every service
    operations: List[Operation] = field(default_factory=list)

    # Reusable type definitions – uses MSDM
    type_definitions: Optional[MSDMDocument] = None

    # Format‑specific extensions (strongly typed)
    yang_module: Optional[YangContainer] = None      # top‑level YANG container
    mib_module: Optional[MibModule] = None           # MIB module
    asyncapi_info: Optional[AsyncAPIInfo] = None     # AsyncAPI specifics
    graphql_service: Optional[GraphQLService] = None # GraphQL

    reusable_parameters: Dict[str, Parameter] = field(default_factory=dict)
    reusable_responses: Dict[str, Response] = field(default_factory=dict)
    reusable_request_bodies: Dict[str, RequestBody] = field(default_factory=dict)
    reusable_headers: Dict[str, Parameter] = field(default_factory=dict)

    extensions: Dict[str, Any] = field(default_factory=dict)
    # RAML / API Blueprint / Postman / Web IDL / CDDL can be represented
    # through the core operations + type_definitions, no extra fields needed.
    
    
# engines/document/models/ssdm_models.py
# Additional dataclasses – replace any previous stubs with these.
# (Place after the existing SSDM_DOCUMENT definition)

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Set, Union

# ── Enums ─────────────────────────────────────────────────────────
class Transport(str, Enum):
    HTTP          = "HTTP"
    HTTPS         = "HTTPS"
    HTTP2         = "HTTP2"
    GRPC          = "gRPC"
    AMQP          = "AMQP"
    MQTT          = "MQTT"
    KAFKA         = "KAFKA"
    NATS          = "NATS"
    SOCKET        = "SOCKET"
    STDIO         = "STDIO"
    SSE           = "SSE"

class AuthMethod(str, Enum):
    NONE           = "none"
    API_KEY        = "apiKey"
    HTTP_BASIC     = "httpBasic"
    BEARER_TOKEN   = "bearerToken"
    OAUTH2         = "oauth2"
    MUTUAL_TLS     = "mutualTLS"
    JWT            = "jwt"
    OPENID_CONNECT = "openIdConnect"
    CUSTOM_HEADER  = "customHeader"
    HMAC           = "hmac"

class ApiKeyLocation(str, Enum):
    HEADER = "header"
    QUERY  = "query"
    COOKIE = "cookie"

class ValueSource(str, Enum):
    STATIC   = "static"
    ENV_VAR  = "envVar"
    FILE     = "file"
    VAULT    = "vault"
    DYNAMIC  = "dynamic"       # obtained via a callback or script

class OAuth2Flow(str, Enum):
    IMPLICIT          = "implicit"
    PASSWORD          = "password"
    CLIENT_CREDENTIALS= "clientCredentials"
    AUTHORIZATION_CODE= "authorizationCode"
    DEVICE_CODE       = "deviceCode"

class RetryPolicy(str, Enum):
    NONE                = "none"
    FIXED_DELAY         = "fixedDelay"
    EXPONENTIAL_BACKOFF= "exponentialBackoff"
    CIRCUIT_BREAKER     = "circuitBreaker"

class PortProtocol(str, Enum):
    TCP  = "TCP"
    UDP  = "UDP"
    SCTP = "SCTP"

class HealthProbeType(str, Enum):
    HTTP_GET   = "httpGet"
    TCP_SOCKET = "tcpSocket"
    EXEC       = "exec"
    GRPC       = "grpc"

class PerformedBy(str, Enum):
    ORCHESTRATOR      = "orchestrator"       # Kubernetes, Consul
    EXTERNAL_MONITOR  = "externalMonitor"
    SELF              = "self"

class DiscoveryBackend(str, Enum):
    NONE       = "none"
    KUBERNETES = "kubernetes"
    CONSUL     = "consul"
    DNS        = "dns"
    EUREKA     = "eureka"
    ETCD       = "etcd"
    ZOOKEEPER  = "zookeeper"
    STATIC     = "static"

class ServiceType(str, Enum):
    CLUSTER_IP    = "ClusterIP"
    NODE_PORT     = "NodePort"
    LOAD_BALANCER = "LoadBalancer"
    EXTERNAL_NAME = "ExternalName"

# ── AuthConfig ────────────────────────────────────────────────────
@dataclass
class JWTValidation:
    issuer: Optional[str] = None
    audience: Optional[str] = None
    jwks_uri: Optional[str] = None
    algorithms: List[str] = field(default_factory=lambda: ["RS256"])

@dataclass
class AuthConfig:
    method: AuthMethod = AuthMethod.NONE
    # For API key
    location: Optional[ApiKeyLocation] = None
    param_name: Optional[str] = None       # header or query parameter name
    # Credential source
    value: Optional[str] = None            # static value
    value_source: ValueSource = ValueSource.STATIC
    # OAuth2 / OIDC
    oauth2_flow: Optional[OAuth2Flow] = None
    oauth2_token_url: Optional[str] = None
    oauth2_authorization_url: Optional[str] = None
    oauth2_client_id: Optional[str] = None
    oauth2_client_secret: Optional[str] = None
    oauth2_scopes: List[str] = field(default_factory=list)
    oauth2_pkce: bool = False
    oauth2_device_auth_endpoint: Optional[str] = None
    # JWT
    jwt_validation: Optional[JWTValidation] = None
    # mTLS
    tls_cert: Optional[str] = None         # inline PEM
    tls_key: Optional[str] = None          # inline PEM
    tls_ca: Optional[str] = None
    tls_cert_file: Optional[str] = None
    tls_key_file: Optional[str] = None
    tls_ca_file: Optional[str] = None

# ── Gateway / SLA / Rate Limit ────────────────────────────────────
@dataclass
class SlAPolicy:
    max_latency_ms: int = 1000
    availability_pct: float = 99.9
    error_budget_pct: float = 0.1

@dataclass
class RateLimit:
    requests_per_second: int = 100
    burst_size: int = 200
    period_seconds: int = 1

@dataclass
class CORSConfig:
    allowed_origins: List[str] = field(default_factory=list)
    allowed_methods: List[str] = field(default_factory=lambda: ["GET", "POST", "PUT", "DELETE"])
    allowed_headers: List[str] = field(default_factory=lambda: ["*"])
    exposed_headers: List[str] = field(default_factory=list)
    max_age_seconds: int = 3600
    allow_credentials: bool = False

@dataclass
class GatewayRule:
    path: str
    methods: List[str] = field(default_factory=lambda: ["GET"])
    upstream: str                         # internal service URL
    host: Optional[str] = None            # optional host matching
    rewrite_path: Optional[str] = None
    strip_path: bool = False
    auth: Optional[AuthConfig] = None
    rate_limit: Optional[RateLimit] = None
    cors: Optional[CORSConfig] = None
    request_size_limit_bytes: Optional[int] = None
    timeout_ms: int = 30000
    plugins: Dict[str, Any] = field(default_factory=dict)   # middleware‑specific config

# ── PortMapping ───────────────────────────────────────────────────
@dataclass
class PortMapping:
    container_port: int
    service_port: Optional[int] = None     # auto‑generated if None
    node_port: Optional[int] = None
    host_port: Optional[int] = None
    protocol: PortProtocol = PortProtocol.TCP
    app_protocol: Optional[Transport] = None   # e.g., HTTP, gRPC
    name: Optional[str] = None

# ── HealthCheck ──────────────────────────────────────────────────
@dataclass
class HTTPGetProbe:
    path: str = "/health"
    port: int = 80
    scheme: str = "HTTP"
    http_headers: Dict[str, str] = field(default_factory=dict)

@dataclass
class TCPSocketProbe:
    port: int

@dataclass
class ExecProbe:
    command: List[str] = field(default_factory=list)

@dataclass
class GRPCProbe:
    port: int
    service: Optional[str] = None

@dataclass
class HealthCheck:
    type: HealthProbeType
    performed_by: PerformedBy = PerformedBy.ORCHESTRATOR
    timeout_seconds: int = 5
    initial_delay_seconds: int = 10
    period_seconds: int = 30
    failure_threshold: int = 3
    success_threshold: int = 1
    http_get: Optional[HTTPGetProbe] = None
    tcp_socket: Optional[TCPSocketProbe] = None
    exec: Optional[ExecProbe] = None
    grpc: Optional[GRPCProbe] = None

# ── Discovery ────────────────────────────────────────────────────
@dataclass
class DiscoveryConfig:
    backend: DiscoveryBackend = DiscoveryBackend.NONE
    # Kubernetes
    service_name: Optional[str] = None
    namespace: Optional[str] = None
    port: Optional[int] = None
    path: Optional[str] = None
    # Consul
    consul_tags: List[str] = field(default_factory=list)
    consul_datacenter: Optional[str] = None
    # DNS
    dns_name: Optional[str] = None
    # Static
    static_hosts: List[str] = field(default_factory=list)   # "host:port"
    # Etcd/Zookeeper
    etcd_key: Optional[str] = None
    zk_path: Optional[str] = None

# ── MeshRule ─────────────────────────────────────────────────────
class MeshRuleType(str, Enum):
    CIRCUIT_BREAKER = "circuitBreaker"
    RETRY           = "retry"
    TIMEOUT         = "timeout"
    RATE_LIMIT      = "rateLimit"
    HEADER_MODIFY   = "headerModify"
    TRAFFIC_SHIFT   = "trafficShift"

@dataclass
class MeshRule:
    type: MeshRuleType
    config: Dict[str, str] = field(default_factory=dict)

# ── ServiceExposure (external access) ────────────────────────────
@dataclass
class IngressRule:
    host: str
    paths: List[GatewayRule] = field(default_factory=list)   # reuse gateway rules for ingress
    tls_secret: Optional[str] = None

@dataclass
class LoadBalancerConfig:
    source_ranges: List[str] = field(default_factory=list)
    external_traffic_policy: Optional[str] = None   # "Cluster" or "Local"
    session_affinity: Optional[str] = None
    health_check_node_port: Optional[int] = None

@dataclass
class ServiceExposure:
    type: ServiceType = ServiceType.CLUSTER_IP
    ingress: Optional[IngressRule] = None
    load_balancer: Optional[LoadBalancerConfig] = None
    reverse_proxy_rules: List[GatewayRule] = field(default_factory=list)   # internal proxying

# ── DeploymentDescriptor ─────────────────────────────────────────
@dataclass
class DeploymentDescriptor:
    service_name: str
    replicas: int = 1
    container_image: Optional[str] = None
    command: Optional[List[str]] = None
    args: Optional[List[str]] = None
    ports: List[PortMapping] = field(default_factory=list)
    environment: Dict[str, str] = field(default_factory=dict)
    config_maps: List[str] = field(default_factory=list)
    secrets: List[str] = field(default_factory=list)
    volumes: List[str] = field(default_factory=list)           # volume names or descriptions
    resources: Dict[str, str] = field(default_factory=dict)    # CPU/mem
    health_check: Optional[HealthCheck] = None
    discovery: Optional[DiscoveryConfig] = None
    mesh_rules: List[MeshRule] = field(default_factory=list)
    service_exposure: ServiceExposure = field(default_factory=ServiceExposure)
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    service_account: Optional[str] = None

# ── Message binding (for transports like Kafka, AMQP) ────────────
class MessageFormat(str, Enum):
    JSON     = "JSON"
    AVRO     = "AVRO"
    PROTOBUF = "PROTOBUF"
    XML      = "XML"
    PLAIN    = "PLAIN"

class SubscriptionType(str, Enum):
    PUB_SUB   = "pubSub"
    QUEUE     = "queue"
    PUSH      = "push"
    PULL      = "pull"

@dataclass
class MessageBinding:
    transport: Transport
    topic: Optional[str] = None              # for Kafka, Pulsar, AMQP topic
    queue: Optional[str] = None              # for AMQP, SQS
    message_format: MessageFormat = MessageFormat.JSON
    subscription_type: SubscriptionType = SubscriptionType.PUB_SUB
    group_id: Optional[str] = None           # consumer group
    routing_key: Optional[str] = None        # AMQP routing key
    reply_to: Optional[str] = None

# ── Service binding (south‑bound) ────────────────────────────────
@dataclass
class ServiceBinding:
    operation_id: str
    transport: Transport = Transport.HTTP
    endpoint_url: Optional[str] = None         # HTTP/HTTPS endpoint
    http_method: Optional[str] = None
    auth_config: Optional[AuthConfig] = None
    timeout_ms: int = 30000
    retry_policy: RetryPolicy = RetryPolicy.NONE
    max_retries: int = 3
    headers: Dict[str, str] = field(default_factory=dict)
    # If transport is message‑based, this binding overrides the generic MessageBinding
    message_binding: Optional[MessageBinding] = None
    # MCP specific
    mcp_tools: Optional[List[MCPClientToolBinding]] = None


@dataclass
class MCPToolBinding:
    """Internal binding for a single MCP tool."""
    tool_name: str                           # MCP tool name as exposed to clients
    internal: InternalServiceBinding         # how this tool is served internally

@dataclass
class MCPResourceBinding:
    """Internal binding for a single MCP resource."""
    uri: str                                 # resource URI pattern exposed to clients
    internal: InternalServiceBinding

@dataclass
class MCPPromptBinding:
    """Internal binding for a single MCP prompt."""
    prompt_name: str
    internal: InternalServiceBinding

@dataclass
class MCPNorthBoundBinding:
    """Complete north‑bound MCP server specification."""
    server_name: str
    transport: Transport = Transport.STDIO    # STDIO or SSE
    server_url: Optional[str] = None          # for SSE transport
    tools: List[MCPToolBinding] = field(default_factory=list)
    resources: List[MCPResourceBinding] = field(default_factory=list)
    prompts: List[MCPPromptBinding] = field(default_factory=list)
    server_auth: Optional[AuthConfig] = None  # auth for clients calling this MCP server


class InternalComponentType(str, Enum):
    TOOL      = "tool"
    AGENT     = "agent"
    WORKFLOW  = "workflow"
    ACTIVITY  = "activity"
    WF_MSG    = "workflow_message"
    WF_TASK   = "workflow_task"
    WF_WI     = "workflow_work_item"
    TASK      = "task"
    FUNCTION  = "function"
    MODULE    = "module"
    SERVICE   = "service"          # another internal micro‑service

class CoordinationProtocol(str, Enum):
    DIRECT_CALL  = "directCall"    # in‑process or direct HTTP/gRPC
    MESSAGE_BUS  = "messageBus"    # async via Kafka / AMQP
    AGENT_FRAMEWORK = "agentFramework"
    WORKFLOW_ENGINE = "workflowEngine"
    TOOL_DISPATCHER = "toolDispatcher"

@dataclass
class ParameterMapping:
    """
    Defines how an incoming request parameter is passed to an internal component.
    """
    source: str                               # e.g., "body.userId", "query.page", "header.Authorization"
    target: str                               # internal parameter name
    transform: Optional[str] = None           # optional expression (e.g., "int(value)")

@dataclass
class ResponseMapping:
    """
    Defines how an internal component's output maps back to the client response.
    """
    source: str                               # internal output field
    target: str                               # e.g., "body", "header.X-Custom"
    transform: Optional[str] = None
    status_code_on_error: Optional[int] = 500

@dataclass
class InternalServiceBinding:
    """
    Complete specification for how a north‑bound operation is served
    by an internal component (tool, agent, workflow, function, etc.).
    """
    component_type: InternalComponentType
    coordination: CoordinationProtocol = CoordinationProtocol.DIRECT_CALL
    address: str                              # e.g., "agent://invoice-processor",
                                              # "module://orders.create",
                                              # "workflow://ord456"
    timeout_ms: int = 30000
    retry_policy: RetryPolicy = RetryPolicy.NONE
    max_retries: int = 3
    config: Dict[str, str] = field(default_factory=dict)   # extra coordination params
    parameter_mappings: List[ParameterMapping] = field(default_factory=list)
    response_mappings: List[ResponseMapping] = field(default_factory=list)
    internal_auth: Optional[AuthConfig] = None



# ── North‑bound binding (our exposure) ────────────────────────────
@dataclass
class NorthBoundBinding(ServiceBinding):
    internal_binding: Optional[InternalServiceBinding] = None
    sla: Optional[SlAPolicy] = None
    rate_limit: Optional[RateLimit] = None
    gateway_rules: List[GatewayRule] = field(default_factory=list)
    mcp_binding: MCPNorthBoundBinding = None
    
    

@dataclass
class MCPClientToolBinding:
    """Describes how we call a specific tool on an external MCP server."""
    tool_name: str
    # Optional: how the tool's input parameters map to our internal calling code
    parameter_mappings: List[ParameterMapping] = field(default_factory=list)
    response_mappings: List[ResponseMapping] = field(default_factory=list)
    # Timeout / retry overrides for this specific tool
    timeout_ms: Optional[int] = None
    retry_policy: Optional[RetryPolicy] = None

@dataclass
class MCPSouthBoundBinding:
    """Client configuration for calling an external MCP server."""
    server_name: str
    transport: Transport = Transport.STDIO
    endpoint_url: Optional[str] = None       # for SSE
    command: Optional[str] = None            # for STDIO (e.g., "python my_server.py")
    auth_config: Optional[AuthConfig] = None
    tools: List[MCPClientToolBinding] = field(default_factory=list)
    # Services we call on this MCP server map to our SSDM Operations
    operation_bindings: Dict[str, str] = field(default_factory=dict)  # operation_id → tool_name    
    
@dataclass
class MCPSouthBoundBinding:
    """
    Convenience model for defining consumption of an external MCP server.
    Generates a standard ServiceBinding with transport=STDIO/SSE and the
    appropriate mcp_tools list.
    """
    server_name: str
    transport: Transport = Transport.STDIO
    endpoint_url: Optional[str] = None
    command: Optional[str] = None
    auth_config: Optional[AuthConfig] = None
    tools: List[MCPClientToolBinding] = field(default_factory=list)
    operation_bindings: Dict[str, str] = field(default_factory=dict)  # op_id → tool_name

    def to_service_binding(self, operation_id: str) -> ServiceBinding:
        """Convert to a unified ServiceBinding for a specific operation."""
        # Filter tools that are used by this operation
        op_tools = [t for t in self.tools
                    if self.operation_bindings.get(operation_id) == t.tool_name]
        return ServiceBinding(
            operation_id=operation_id,
            transport=self.transport,
            endpoint_url=self.endpoint_url,
            auth_config=self.auth_config,
            mcp_tools=op_tools if op_tools else None,
        )
