# engines/document/models/ssdm_capabilities.py
"""
Format Capability Profiles – describes what each SSDM format can express.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Set
from .media_types import DocumentFormat


class ParameterNesting(str, Enum):
    SCALAR_ONLY = "scalar_only"          # e.g., query strings limited to atomic types
    FLAT_OBJECT = "flat_object"          # single‑level object, no deep nesting
    DEEP_NESTED = "deep_nested"          # arbitrary JSON / XML trees


class BodyMediaType(str, Enum):
    JSON = "application/json"
    XML  = "application/xml"
    FORM = "application/x-www-form-urlencoded"
    MULTIPART = "multipart/form-data"
    PLAIN = "text/plain"
    BINARY = "application/octet-stream"


class SecurityFeature(str, Enum):
    HTTP_BASIC      = "httpBasic"
    HTTP_BEARER     = "httpBearer"
    API_KEY         = "apiKey"
    OAUTH2          = "oauth2"
    OPENID_CONNECT  = "openIdConnect"
    MUTUAL_TLS      = "mutualTLS"


class TransportBinding(str, Enum):
    HTTP            = "HTTP"
    HTTPS           = "HTTPS"
    SOAP            = "SOAP"
    SNMP            = "SNMP"
    NETCONF         = "NETCONF"
    RESTCONF        = "RESTCONF"
    GRPC            = "gRPC"
    WEBSOCKET       = "WebSocket"
    AMQP            = "AMQP"
    MQTT            = "MQTT"


class SchemaKind(str, Enum):
    EMBEDDED_ONLY   = "embedded_only"     # types defined inline, no reuse
    REFERENCE       = "reference"         # separate schema sections, reusable
    NONE            = "none"              # format doesn't have user‑defined types


class OperationModel(str, Enum):
    """How operations are expressed."""
    CRUD_AUTO = "crud_auto"              # e.g., a collection exposed as CRUD endpoints
    EXPLICIT = "explicit"                # explicit operations with parameters
    RPC = "rpc"                          # SOAP‑style remote procedure calls
    PUBLISH_SUBSCRIBE = "pubsub"         # AsyncAPI event channels
    QUERY_SCHEMA = "query_schema"        # GraphQL schema‑defined queries


@dataclass
class FormatCapability:
    """Describes the structural abilities of a service‑definition format."""
    format: DocumentFormat
    description: str

    # Operations
    operation_model: OperationModel
    supports_crud: bool                      # e.g., REST CRUD on resources
    supports_explicit_operations: bool       # named operations with custom logic

    # Parameter constraints
    parameter_nesting: ParameterNesting
    supports_query_params: bool
    supports_path_params: bool
    supports_header_params: bool
    supports_cookie_params: bool

    # Request & response bodies
    request_body_supported: bool
    response_body_supported: bool
    request_media_types: List[BodyMediaType] = field(default_factory=list)
    response_media_types: List[BodyMediaType] = field(default_factory=list)

    # Security
    security_features: List[SecurityFeature] = field(default_factory=list)

    # Transport
    transport_bindings: List[TransportBinding] = field(default_factory=list)

    # Schema / type system
    schema_kind: SchemaKind = SchemaKind.NONE
    references_msdm: bool = False            # whether the format's type system maps to MSDM entities
    supports_streaming: bool = False