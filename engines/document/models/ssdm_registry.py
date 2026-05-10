# engines/document/models/ssdm_registry.py
# Registry populated at module level
from .media_types import DocumentFormat
from .ssdm_capabilities import BodyMediaType
from .ssdm_capabilities import FormatCapability
from .ssdm_capabilities import OperationModel
from .ssdm_capabilities import ParameterNesting
from .ssdm_capabilities import SchemaKind
from .ssdm_capabilities import SecurityFeature
from .ssdm_capabilities import TransportBinding



FORMAT_CAPABILITY_REGISTRY: dict[DocumentFormat, FormatCapability] = {}


def _reg(cap: FormatCapability):
    FORMAT_CAPABILITY_REGISTRY[cap.format] = cap


# ── OpenAPI JSON ────────────────────────────────────────────────
_reg(FormatCapability(
    format=DocumentFormat.OPENAPI_JSON,
    description="OpenAPI (Swagger) JSON",
    operation_model=OperationModel.EXPLICIT,
    supports_crud=True,
    supports_explicit_operations=True,
    parameter_nesting=ParameterNesting.FLAT_OBJECT,
    supports_query_params=True,
    supports_path_params=True,
    supports_header_params=True,
    supports_cookie_params=True,
    request_body_supported=True,
    response_body_supported=True,
    request_media_types=[BodyMediaType.JSON, BodyMediaType.XML,
                         BodyMediaType.FORM, BodyMediaType.MULTIPART],
    response_media_types=[BodyMediaType.JSON, BodyMediaType.XML, BodyMediaType.PLAIN, BodyMediaType.BINARY],
    security_features=[SecurityFeature.HTTP_BASIC, SecurityFeature.HTTP_BEARER,
                       SecurityFeature.API_KEY, SecurityFeature.OAUTH2,
                       SecurityFeature.OPENID_CONNECT, SecurityFeature.MUTUAL_TLS],
    transport_bindings=[TransportBinding.HTTP, TransportBinding.HTTPS],
    schema_kind=SchemaKind.REFERENCE,
    references_msdm=True,
    supports_streaming=False,
))

# ── OpenAPI YAML ────────────────────────────────────────────────
_reg(FormatCapability(
    format=DocumentFormat.OPENAPI_YAML,
    description="OpenAPI (Swagger) YAML",
    operation_model=OperationModel.EXPLICIT,
    supports_crud=True,
    supports_explicit_operations=True,
    parameter_nesting=ParameterNesting.FLAT_OBJECT,
    supports_query_params=True,
    supports_path_params=True,
    supports_header_params=True,
    supports_cookie_params=True,
    request_body_supported=True,
    response_body_supported=True,
    request_media_types=[BodyMediaType.JSON, BodyMediaType.XML,
                         BodyMediaType.FORM, BodyMediaType.MULTIPART],
    response_media_types=[BodyMediaType.JSON, BodyMediaType.XML, BodyMediaType.PLAIN, BodyMediaType.BINARY],
    security_features=[SecurityFeature.HTTP_BASIC, SecurityFeature.HTTP_BEARER,
                       SecurityFeature.API_KEY, SecurityFeature.OAUTH2,
                       SecurityFeature.OPENID_CONNECT, SecurityFeature.MUTUAL_TLS],
    transport_bindings=[TransportBinding.HTTP, TransportBinding.HTTPS],
    schema_kind=SchemaKind.REFERENCE,
    references_msdm=True,
    supports_streaming=False,
))

# ── WSDL ────────────────────────────────────────────────────────
_reg(FormatCapability(
    format=DocumentFormat.WSDL,
    description="WSDL (SOAP) Service Definition",
    operation_model=OperationModel.RPC,
    supports_crud=False,
    supports_explicit_operations=True,
    parameter_nesting=ParameterNesting.DEEP_NESTED,
    supports_query_params=False,
    supports_path_params=False,
    supports_header_params=False,   # header handled via SOAP headers, but not common
    supports_cookie_params=False,
    request_body_supported=True,
    response_body_supported=True,
    request_media_types=[BodyMediaType.XML],
    response_media_types=[BodyMediaType.XML],
    security_features=[],            # usually WS‑Security, which is an extension
    transport_bindings=[TransportBinding.SOAP, TransportBinding.HTTP, TransportBinding.HTTPS],
    schema_kind=SchemaKind.REFERENCE,
    references_msdm=True,
    supports_streaming=False,
))

# ── YANG ────────────────────────────────────────────────────────
_reg(FormatCapability(
    format=DocumentFormat.YANG,
    description="YANG Data Model (RFC 7950)",
    operation_model=OperationModel.RPC,
    supports_crud=False,                # YANG can do configuration via RPCs, not REST CRUD
    supports_explicit_operations=True,
    parameter_nesting=ParameterNesting.DEEP_NESTED,
    supports_query_params=False,
    supports_path_params=False,
    supports_header_params=False,
    supports_cookie_params=False,
    request_body_supported=True,        # RPC input
    response_body_supported=True,       # RPC output
    request_media_types=[BodyMediaType.XML],   # typically XML encoding
    response_media_types=[BodyMediaType.XML],
    security_features=[],
    transport_bindings=[TransportBinding.NETCONF, TransportBinding.RESTCONF, TransportBinding.HTTPS],
    schema_kind=SchemaKind.REFERENCE,
    references_msdm=True,
    supports_streaming=False,
))

# ── AsyncAPI ────────────────────────────────────────────────────
_reg(FormatCapability(
    format=DocumentFormat.ASYNCAPI,
    description="AsyncAPI Event‑driven API",
    operation_model=OperationModel.PUBLISH_SUBSCRIBE,
    supports_crud=False,
    supports_explicit_operations=False,
    parameter_nesting=ParameterNesting.FLAT_OBJECT,
    supports_query_params=False,
    supports_path_params=False,
    supports_header_params=True,            # message headers
    supports_cookie_params=False,
    request_body_supported=True,            # message payload
    response_body_supported=False,          # typically one‑way, but can have reply channels
    request_media_types=[BodyMediaType.JSON, BodyMediaType.XML, BodyMediaType.BINARY],
    response_media_types=[],
    security_features=[],
    transport_bindings=[TransportBinding.AMQP, TransportBinding.MQTT, TransportBinding.HTTP, TransportBinding.WEBSOCKET],
    schema_kind=SchemaKind.REFERENCE,
    references_msdm=True,
    supports_streaming=True,
))

# ── GraphQL Schema ──────────────────────────────────────────────
_reg(FormatCapability(
    format=DocumentFormat.GRAPHQL_SCHEMA,
    description="GraphQL Schema",
    operation_model=OperationModel.QUERY_SCHEMA,
    supports_crud=False,
    supports_explicit_operations=False,
    parameter_nesting=ParameterNesting.DEEP_NESTED,
    supports_query_params=True,             # via arguments
    supports_path_params=False,
    supports_header_params=False,
    supports_cookie_params=False,
    request_body_supported=True,            # query variables
    response_body_supported=True,
    request_media_types=[BodyMediaType.JSON],
    response_media_types=[BodyMediaType.JSON],
    security_features=[],
    transport_bindings=[TransportBinding.HTTP, TransportBinding.HTTPS],
    schema_kind=SchemaKind.REFERENCE,
    references_msdm=True,
    supports_streaming=False,
))

# ── Protobuf ────────────────────────────────────────────────────
_reg(FormatCapability(
    format=DocumentFormat.PROTOBUF,
    description="Protobuf IDL (gRPC service definitions)",
    operation_model=OperationModel.RPC,
    supports_crud=False,
    supports_explicit_operations=True,
    parameter_nesting=ParameterNesting.DEEP_NESTED,
    supports_query_params=False,
    supports_path_params=False,
    supports_header_params=False,
    supports_cookie_params=False,
    request_body_supported=True,
    response_body_supported=True,
    request_media_types=[BodyMediaType.BINARY],
    response_media_types=[BodyMediaType.BINARY],
    security_features=[],
    transport_bindings=[TransportBinding.GRPC],
    schema_kind=SchemaKind.REFERENCE,
    references_msdm=True,
    supports_streaming=True,
))
