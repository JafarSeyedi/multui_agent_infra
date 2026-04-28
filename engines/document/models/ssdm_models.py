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
from engines.document.models.base import BaseDocument
from engines.document.models.media_types import DocumentStandard
from engines.document.models.msdm_models import (
    MSDMDocument, Entity,
)

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


@dataclass
class Response:
    status_code: str                       # "200", "404", etc.
    description: Optional[str] = None
    # Response body schema
    content_entity: Optional[Entity] = None
    content_type_entities: Dict[str, Entity] = field(default_factory=dict)
    headers: List[Parameter] = field(default_factory=list)


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


# ============================================================
# YANG specific structures – represented without Any
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

    # Format‑specific extensions (strongly typed, no Any)
    yang_module: Optional[YangContainer] = None      # top‑level YANG container
    mib_module: Optional[MibModule] = None           # MIB module
    asyncapi_info: Optional[AsyncAPIInfo] = None     # AsyncAPI specifics
    graphql_service: Optional[GraphQLService] = None # GraphQL

    # RAML / API Blueprint / Postman / Web IDL / CDDL can be represented
    # through the core operations + type_definitions, no extra fields needed.