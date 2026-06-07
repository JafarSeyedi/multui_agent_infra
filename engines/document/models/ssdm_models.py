# API/Service Structured Document Model (SSDM)
# Purpose: Represent HTTP APIs, SOAP services, network management interfaces, and RPC protocols.
# Formats to support
# Format	                            File extensions	        Notes
# OpenAPI (Swagger)	                    .yaml, .json	        REST API specification
# SOAP / WSDL	                        .wsdl	                XML‑based service description
# YANG	                                .yang	                Network device modelling (RFC 7950)
# AsyncAPI	                            .yaml, .json	        Event‑driven API specification
# GraphQL Schema	                    .graphql	            (Overlaps with MSDM)
# gRPC / Protobuf	                    .proto	                (Overlaps with MSDM)
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
from typing import Any

from .base import BaseDocument
from .media_types import DocumentStandard
from .msdm_models import Entity
from .msdm_models import MSDMDocument
from .msdm_models import VersionStatus, Annotation


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


class OAuth2Flow(str, Enum):
    IMPLICIT        = "implicit"
    PASSWORD        = "password"
    CLIENT_CREDENTIALS = "clientCredentials"
    AUTHORIZATION_CODE = "authorizationCode"
    DEVICE_CODE       = "deviceCode"


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


class ValueSource(str, Enum):
    STATIC   = "static"
    ENV_VAR  = "envVar"
    FILE     = "file"
    VAULT    = "vault"
    DYNAMIC  = "dynamic"       # obtained via a callback or script

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

class MeshRuleType(str, Enum):
    CIRCUIT_BREAKER = "circuitBreaker"
    RETRY           = "retry"
    TIMEOUT         = "timeout"
    RATE_LIMIT      = "rateLimit"
    HEADER_MODIFY   = "headerModify"
    TRAFFIC_SHIFT   = "trafficShift"

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


# class YangStatement(str, Enum):
#     """Key YANG statement names."""
#     MODULE          = "module"
#     CONTAINER       = "container"
#     LIST            = "list"
#     LEAF            = "leaf"
#     LEAF_LIST       = "leaf-list"
#     CHOICE          = "choice"
#     CASE            = "case"
#     AUGMENT         = "augment"
#     USES            = "uses"
#     REFINE          = "refine"
#     DEVIATION       = "deviation"
#     NOTIFICATION    = "notification"
#     RPC             = "rpc"


# class SnmpAccess(str, Enum):
#     """SNMP access permissions."""
#     READ_ONLY       = "read-only"
#     READ_WRITE      = "read-write"
#     NOT_ACCESSIBLE  = "not-accessible"

# ============================================================
# Service‑wide definitions
# ============================================================

@dataclass
class ContactInfo:
    name: str | None = None
    url: str | None = None
    email: str | None = None


@dataclass
class LicenseInfo:
    name: str
    url: str | None = None


@dataclass
class Server:
    url: str
    description: str | None = None
    variables: dict[str, str] = field(default_factory=dict)  # variable name → default value

# ============================================================
# Parameter & Body definitions – refer to MSDM entities
# ============================================================

@dataclass
class Parameter:
    name: str
    location: ParameterLocation
    required: bool = False
    description: str | None = None
    # Reference to an MSDM Entity that describes the parameter type.
    # For simple types, the entity will have a single attribute.
    type_entity: Entity | None = None
    # # Alternatively, a plain string type if no Entity needed.
    # type_string: str | None = None

    annotations: list[Annotation] = field(default_factory=list)   # for x-* and other non‑semantic data

@dataclass
class RequestBody:
    description: str | None = None
    required: bool = False
    # The request body is always described by an MSDM Entity.
    content_entity: Entity | None = None
    # Multiple content types with different schemas
    content_type_entities: dict[str, Entity] = field(default_factory=dict)
    is_binary: bool = False
    
    annotations: list[Annotation] = field(default_factory=list)

@dataclass
class Link:
    operation_id: str
    parameters: dict[str, str] = field(default_factory=dict)
    description: str | None = None
    request_body: RequestBody | None = None   # can be a raw expression or a reference

@dataclass
class Response:
    status_code: str                       # "200", "404", etc.
    description: str | None = None
    # Response body schema
    content_entity: Entity | None = None
    content_type_entities: dict[str, Entity] = field(default_factory=dict)
    headers: list[Parameter] = field(default_factory=list)
    links: dict[str, Link] = field(default_factory=dict)
    is_binary: bool = False
    
    annotations: list[Annotation] = field(default_factory=list)

# ============================================================
# ServiceOperation – REST endpoint, SOAP operation, AsyncAPI channel
# ============================================================
@dataclass
class YangMetadata:
    must: str | None = None
    when: str | None = None
    config: bool | None = None
    status: str | None = None
    deviation: str | None = None
    
@dataclass
class ServiceOperation:
    name: str                              # operationId or method name
    type: OperationType = OperationType.REQUEST_RESPONSE
    description: str | None = None

    # HTTP binding
    http_method: HttpMethod | None = None
    path: str | None = None

    # SOAP binding
    soap_action: str | None = None

    # AsyncAPI binding
    channel: str | None = None          # channel name for publish/subscribe
    message_entity: Entity | None = None

    # Input/output
    parameters: list[Parameter] = field(default_factory=list)
    request_body: RequestBody | None = None
    responses: list[Response] = field(default_factory=list)

    # Additional protocol‑specific attributes
    tags: list[str] = field(default_factory=list)
    version: str | None = None
    version_status: VersionStatus | None = None
    
    callbacks: dict[str, list[ServiceOperation]] = field(default_factory=dict)

    servers: list[Server] = field(default_factory=list)
    external_docs: dict | None = None

    extensions: dict[str, Any] = field(default_factory=dict)

    # YANG‑specific extensions
    yang: YangMetadata | None = None
    
    security_requirements: list[SecurityRequirement] = field(default_factory=list)
    annotations: list[Annotation] = field(default_factory=list)
# ============================================================
# MIB specific structures
# ============================================================

# @dataclass
# class MibObjectType:
#     name: str
#     oid: str
#     syntax: str                          # "INTEGER", "OCTET STRING", etc.
#     access: SnmpAccess
#     status: SnmpStatus
#     description: str | None = None
#     index: str | None = None          # index of table entry


# @dataclass
# class MibModule:
#     name: str
#     description: str | None = None
#     imports: list[str] = field(default_factory=list)
#     objects: list[MibObjectType] = field(default_factory=list)

# ============================================================
# Top‑level SSDM Document
# ============================================================

class SSDMDocument(BaseDocument):
    """
    A service definition document, supporting OpenAPI, REST, SOAP, AsyncAPI,
    YANG, MIB, GraphQL, and more.
    """
    version_status: VersionStatus | None = None

    kind: DocumentStandard = DocumentStandard.SSDM
    source_file: str | None = None
    description: str | None = None
    contact: ContactInfo | None = None
    license: LicenseInfo | None = None
    servers: list[Server] = field(default_factory=list)

    # Operations – the core of every service
    operations: list[ServiceOperation] = field(default_factory=list)

    # Reusable type definitions – uses MSDM
    type_definitions: MSDMDocument | None = None
    root_entity: Entity | None = None              # the root Query/Mutation/Subscription type

    security_schemes: list[AuthConfig] = field(default_factory=list)
    # Format‑specific extensions (strongly typed)
    # yang_module: YangContainer | None = None      # top‑level YANG container
    # asyncapi_info: AsyncAPIInfo | None = None     # AsyncAPI specifics
    # graphql_service: GraphQLService | None = None # GraphQL

    reusable_parameters: dict[str, Parameter] = field(default_factory=dict)
    reusable_responses: dict[str, Response] = field(default_factory=dict)
    reusable_request_bodies: dict[str, RequestBody] = field(default_factory=dict)
    reusable_headers: dict[str, Parameter] = field(default_factory=dict)

    annotations: list[Annotation] = field(default_factory=list)



# ── AuthConfig ────────────────────────────────────────────────────
@dataclass
class SecurityRequirement:
    """Type‑safe representation of OpenAPI security requirement."""
    name: str
    scopes: list[str] = field(default_factory=list)
    
@dataclass
class JWTValidation:
    issuer: str | None = None
    audience: str | None = None
    jwks_uri: str | None = None
    algorithms: list[str] = field(default_factory=lambda: ["RS256"])

@dataclass
class AuthConfig:
    method: AuthMethod = AuthMethod.NONE
    # For API key
    location: ApiKeyLocation | None = None
    param_name: str | None = None       # header or query parameter name
    # Credential source
    value: str | None = None            # static value
    value_source: ValueSource = ValueSource.STATIC
    # OAuth2 / OIDC
    oauth2_flow: OAuth2Flow | None = None
    oauth2_token_url: str | None = None
    oauth2_authorization_url: str | None = None
    oauth2_client_id: str | None = None
    oauth2_client_secret: str | None = None
    oauth2_scopes: list[str] = field(default_factory=list)
    oauth2_pkce: bool = False
    oauth2_device_auth_endpoint: str | None = None
    # JWT
    jwt_validation: JWTValidation | None = None
    # mTLS
    tls_cert: str | None = None         # inline PEM
    tls_key: str | None = None          # inline PEM
    tls_ca: str | None = None
    tls_cert_file: str | None = None
    tls_key_file: str | None = None
    tls_ca_file: str | None = None
    
    open_id_connect_url: str | None = None   # new field
    annotations: list[Annotation] = field(default_factory=list)


# ── Gateway / SLA / Rate Limit ────────────────────────────────────
@dataclass
class SlaPolicy:
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
    allowed_origins: list[str] = field(default_factory=list)
    allowed_methods: list[str] = field(default_factory=lambda: ["GET", "POST", "PUT", "DELETE"])
    allowed_headers: list[str] = field(default_factory=lambda: ["*"])
    exposed_headers: list[str] = field(default_factory=list)
    max_age_seconds: int = 3600
    allow_credentials: bool = False

@dataclass
class GatewayRule:
    path: str
    upstream: str                         # internal service URL
    methods: list[str] = field(default_factory=lambda: ["GET"])
    host: str | None = None            # optional host matching
    rewrite_path: str | None = None
    strip_path: bool = False
    auth: AuthConfig | None = None
    rate_limit: RateLimit | None = None
    cors: CORSConfig | None = None
    request_size_limit_bytes: int | None = None
    timeout_ms: int = 30000
    plugins: dict[str, Any] = field(default_factory=dict)   # middleware‑specific config

# ── PortMapping ───────────────────────────────────────────────────
@dataclass
class PortMapping:
    container_port: int
    service_port: int | None = None     # auto‑generated if None
    node_port: int | None = None
    host_port: int | None = None
    protocol: PortProtocol = PortProtocol.TCP
    app_protocol: Transport | None = None   # e.g., HTTP, gRPC
    name: str | None = None

# ── HealthCheck ──────────────────────────────────────────────────
@dataclass
class HTTPGetProbe:
    path: str = "/health"
    port: int = 80
    scheme: str = "HTTP"
    http_headers: dict[str, str] = field(default_factory=dict)

@dataclass
class TCPSocketProbe:
    port: int

@dataclass
class ExecProbe:
    command: list[str] = field(default_factory=list)

@dataclass
class GRPCProbe:
    port: int
    service: str | None = None

@dataclass
class HealthCheck:
    type: HealthProbeType
    performed_by: PerformedBy = PerformedBy.ORCHESTRATOR
    timeout_seconds: int = 5
    initial_delay_seconds: int = 10
    period_seconds: int = 30
    failure_threshold: int = 3
    success_threshold: int = 1
    http_get: HTTPGetProbe | None = None
    tcp_socket: TCPSocketProbe | None = None
    exec: ExecProbe | None = None
    grpc: GRPCProbe | None = None

# ── Discovery ────────────────────────────────────────────────────
@dataclass
class DiscoveryConfig:
    backend: DiscoveryBackend = DiscoveryBackend.NONE
    # Kubernetes
    service_name: str | None = None
    namespace: str | None = None
    port: int | None = None
    path: str | None = None
    # Consul
    consul_tags: list[str] = field(default_factory=list)
    consul_datacenter: str | None = None
    # DNS
    dns_name: str | None = None
    # Static
    static_hosts: list[str] = field(default_factory=list)   # "host:port"
    # Etcd/Zookeeper
    etcd_key: str | None = None
    zk_path: str | None = None

# ── MeshRule ─────────────────────────────────────────────────────

@dataclass
class MeshRule:
    type: MeshRuleType
    config: dict[str, str] = field(default_factory=dict)

# ── ServiceExposure (external access) ────────────────────────────
@dataclass
class IngressRule:
    host: str
    paths: list[GatewayRule] = field(default_factory=list)   # reuse gateway rules for ingress
    tls_secret: str | None = None

@dataclass
class LoadBalancerConfig:
    source_ranges: list[str] = field(default_factory=list)
    external_traffic_policy: str | None = None   # "Cluster" or "Local"
    session_affinity: str | None = None
    health_check_node_port: int | None = None

@dataclass
class ServiceExposure:
    type: ServiceType = ServiceType.CLUSTER_IP
    ingress: IngressRule | None = None
    load_balancer: LoadBalancerConfig | None = None
    reverse_proxy_rules: list[GatewayRule] = field(default_factory=list)   # internal proxying

# ── DeploymentDescriptor ─────────────────────────────────────────
@dataclass
class DeploymentDescriptor:
    service_name: str
    replicas: int = 1
    container_image: str | None = None
    command: list[str] | None = None
    args: list[str] | None = None
    ports: list[PortMapping] = field(default_factory=list)
    environment: dict[str, str] = field(default_factory=dict)
    config_maps: list[str] = field(default_factory=list)
    secrets: list[str] = field(default_factory=list)
    volumes: list[str] = field(default_factory=list)           # volume names or descriptions
    resources: dict[str, str] = field(default_factory=dict)    # CPU/mem
    health_check: HealthCheck | None = None
    discovery: DiscoveryConfig | None = None
    mesh_rules: list[MeshRule] = field(default_factory=list)
    service_exposure: ServiceExposure = field(default_factory=ServiceExposure)
    labels: dict[str, str] = field(default_factory=dict)
    annotations: dict[str, str] = field(default_factory=dict)
    service_account: str | None = None

@dataclass
class MessageBinding:
    transport: Transport
    topic: str | None = None              # for Kafka, Pulsar, AMQP topic
    queue: str | None = None              # for AMQP, SQS
    message_format: MessageFormat = MessageFormat.JSON
    subscription_type: SubscriptionType = SubscriptionType.PUB_SUB
    group_id: str | None = None           # consumer group
    routing_key: str | None = None        # AMQP routing key
    reply_to: str | None = None

# ── Service binding (south‑bound) ────────────────────────────────
@dataclass
class ServiceBinding:
    operation_id: str
    transport: Transport = Transport.HTTP
    endpoint_url: str | None = None         # HTTP/HTTPS endpoint
    http_method: str | None = None
    auth_config: AuthConfig | None = None
    timeout_ms: int = 30000
    retry_policy: RetryPolicy = RetryPolicy.NONE
    max_retries: int = 3
    headers: dict[str, str] = field(default_factory=dict)
    # If transport is message‑based, this binding overrides the generic MessageBinding
    message_binding: MessageBinding | None = None
    # MCP specific
    mcp_tools: list[MCPClientToolBinding] | None = None


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
    server_url: str | None = None          # for SSE transport
    tools: list[MCPToolBinding] = field(default_factory=list)
    resources: list[MCPResourceBinding] = field(default_factory=list)
    prompts: list[MCPPromptBinding] = field(default_factory=list)
    server_auth: AuthConfig | None = None  # auth for clients calling this MCP server


@dataclass
class ParameterMapping:
    """
    Defines how an incoming request parameter is passed to an internal component.
    """
    source: str                               # e.g., "body.userId", "query.page", "header.Authorization"
    target: str                               # internal parameter name
    transform: str | None = None           # optional expression (e.g., "int(value)")

@dataclass
class ResponseMapping:
    """
    Defines how an internal component's output maps back to the client response.
    """
    source: str                               # internal output field
    target: str                               # e.g., "body", "header.X-Custom"
    transform: str | None = None
    status_code_on_error: int | None = 500

@dataclass
class InternalServiceBinding:
    """
    Complete specification for how a north‑bound operation is served
    by an internal component (tool, agent, workflow, function, etc.).
    """
    component_type: InternalComponentType
    address: str                              # e.g., "agent://invoice-processor",
                                              # "module://orders.create",
                                              # "workflow://ord456"
    coordination: CoordinationProtocol = CoordinationProtocol.DIRECT_CALL
    timeout_ms: int = 30000
    retry_policy: RetryPolicy = RetryPolicy.NONE
    max_retries: int = 3
    config: dict[str, str] = field(default_factory=dict)   # extra coordination params
    parameter_mappings: list[ParameterMapping] = field(default_factory=list)
    response_mappings: list[ResponseMapping] = field(default_factory=list)
    internal_auth: AuthConfig | None = None



# ── North‑bound binding (our exposure) ────────────────────────────
@dataclass
class NorthBoundBinding(ServiceBinding):
    internal_binding: InternalServiceBinding | None = None
    sla: SlaPolicy | None = None
    rate_limit: RateLimit | None = None
    gateway_rules: list[GatewayRule] = field(default_factory=list)
    mcp_binding: MCPNorthBoundBinding | None = None



@dataclass
class MCPClientToolBinding:
    """Describes how we call a specific tool on an external MCP server."""
    tool_name: str
    # Optional: how the tool's input parameters map to our internal calling code
    parameter_mappings: list[ParameterMapping] = field(default_factory=list)
    response_mappings: list[ResponseMapping] = field(default_factory=list)
    # Timeout / retry overrides for this specific tool
    timeout_ms: int | None = None
    retry_policy: RetryPolicy | None = None

@dataclass
class MCPSouthBoundBinding:
    """
    Convenience model for defining consumption of an external MCP server.
    Generates a standard ServiceBinding with transport=STDIO/SSE and the
    appropriate mcp_tools list.
    """
    server_name: str
    transport: Transport = Transport.STDIO
    endpoint_url: str | None = None
    command: str | None = None
    auth_config: AuthConfig | None = None
    tools: list[MCPClientToolBinding] = field(default_factory=list)
    operation_bindings: dict[str, str] = field(default_factory=dict)  # op_id → tool_name

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
