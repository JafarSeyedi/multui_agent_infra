# engines/document/models/msdm_models.py

# Metadata of data Structure Definition Model (SDM)
# MSDM is about metadata describing structure. Whether you're defining a relational table, 
# a JSON schema, or a time‑series measurement, you're essentially listing fields with types 
# and constraints. The kind field simply gives a hint to the parser/writer about what format 
# to expect (e.g., .cql for Cassandra, .sql for TimescaleDB, or direct InfluxQL)

# Purpose: Describe data schemas, database tables, class hierarchies, and type systems in a format‑independent way.

# Formats to support
# Format	                File extensions	        Notes
# JSON Schema	            .schema.json, .json	    Declarative validation rules for JSON
# XSD (XML Schema)	        .xsd	                XML structure definition
# SQL DDL	                .sql, .ddl	            CREATE TABLE, ALTER, etc.
# ERD / Entity‑Relationship	.erd, .xml, .json	    Database modelling
# UML Class Diagram	        .uml, .xmi, .plantuml   Object‑oriented design
# Protobuf / gRPC IDL	    .proto	                Language‑neutral interface definitions
# Avro Schema	            .avsc	                Apache Avro schema format
# Thrift IDL	            .thrift	                Apache Thrift interface definitions
# GraphQL Schema	        .graphql, .gql	        Type system and query definitions
# OWL / RDF Schema	        .owl, .rdf	            Semantic web ontologies
# CUE	                    .cue	                Data constraint language
# Pydantic / dataclass	    .py                     (Python code) Direct extraction from Python classes
# TypeScript interfaces	    .ts	Static              type definitions

# Typical NoSQL schemas:

# Type	            Example formats	            Schema description
# Document	        MongoDB, Couchbase	        JSON Schema / Mongoose schemas
# Wide‑column	    Cassandra, HBase	        CQL table definitions
# Key‑value	        Redis, DynamoDB	            Often schema‑less, but key/value type info possible
# Graph	            Neo4j, ArangoDB	            Node/Edge type definitions
# Search	        Elasticsearch	            Index mappings (JSON)

# How MSDM handles them:
# - Entity represents a collection, table, or node label.
# - Attribute fields map to document properties, columns, or key fields. The type can be a complex string like "array<string>" or "map<string, int>" for nested structures.
# - Constraint can capture uniqueness, required, indexing, or text‑search options.
# - Annotation stores engine‑specific hints (e.g., shard keys, TTL).
# - Add an optional Entity.kind field ("document", "column_family", "graph_node", "timeseries") to inform downstream tools.

# Time‑based data - Typical time‑series / event schemas:

# Type	            Example formats	                    Schema description
# Time‑series DB	InfluxDB, TimescaleDB, Prometheus	Measurement/table with timestamp, fields, tags
# Event sourcing	Kafka, EventStore	                Event schema (Avro/JSON) with timestamp
# Temporal tables	SQL:2011	                        System‑versioned tables

# How MSDM handles them:
# - A time‑series measurement is an Entity with a kind="timeseries".
# - The timestamp column is simply an Attribute with type="timestamp" and primary_key=True.
# - Tags (dimensions) and fields (metrics) are regular attributes; we can use annotations to mark which are tags/fields.
# - Retention policies, down‑sampling, and continuous queries become Constraint or Annotation objects.

# CQL (Cassandra) – engines/document/parsers/msdm/cql_parser.py
# MongoDB validator schema – engines/document/parsers/msdm/mongo_schema_parser.py
# InfluxDB – engines/document/parsers/msdm/influx_schema_parser.py
# Kafka Avro schemas (already covered by proto/avsc parsers)


# engines/document/models/msdm_models.py
"""
MSDM – Metadata Standard Definition Model
===========================================
Format‑independent representation of data schemas, database tables,
class hierarchies, type systems, and time‑series / NoSQL definitions.
Every structural detail is captured in strictly‑typed fields.
Annotations are reserved for human‑oriented text without semantic weight.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any, Literal, Union
from .base import BaseDocument
from .media_types import DocumentStandard

# ============================================================
# Enums
# ============================================================

class EntityKind(str, Enum):
    TABLE           = "table"
    DOCUMENT        = "document"
    COLUMN_FAMILY   = "column_family"
    GRAPH_NODE      = "graph_node"
    GRAPH_EDGE      = "graph_edge"
    TIMESERIES      = "timeseries"
    STREAM          = "stream"
    VIEW            = "view"
    OBJECT          = "object"          # UML class, Pydantic model, TypeScript type


class Cardinality(str, Enum):
    ONE              = "1"
    MANY             = "*"
    ZERO_OR_ONE      = "0..1"
    ONE_OR_MANY      = "1..*"


class ConstraintType(str, Enum):
    PRIMARY_KEY     = "primary_key"
    FOREIGN_KEY     = "foreign_key"
    UNIQUE          = "unique"
    NOT_NULL        = "not_null"
    CHECK           = "check"
    DEFAULT         = "default"
    INDEX           = "index"           # used when attached to an attribute rather than entity

    MIN_LENGTH       = "minLength"
    MAX_LENGTH       = "maxLength"
    LENGTH           = "length"
    PATTERN          = "pattern"
    MIN_INCLUSIVE    = "minInclusive"
    MAX_INCLUSIVE    = "maxInclusive"
    MIN_EXCLUSIVE    = "minExclusive"
    MAX_EXCLUSIVE    = "maxExclusive"
    TOTAL_DIGITS     = "totalDigits"
    FRACTION_DIGITS  = "fractionDigits"
    ENUMERATION      = "enumeration"   # distinct from CHECK
    WHITESPACE       = "whiteSpace"

class ScalarType(str, Enum):
    STRING          = "string"
    INT             = "int"
    LONG            = "long"
    FLOAT           = "float"
    DOUBLE          = "double"
    DECIMAL         = "decimal"
    BOOLEAN         = "boolean"
    DATE            = "date"
    TIME            = "time"
    TIMESTAMP       = "timestamp"
    DURATION        = "duration"
    UUID            = "uuid"
    BINARY          = "binary"
    JSON            = "json"
    XML             = "xml"
    ANY             = "any"
    ARRAY           = "array"
    MAP             = "map"
    STRUCT          = "struct"
    REF             = "ref"             # reference to another Entity


class XSDFacet(str, Enum):
    """Facets used in XSD simple type restrictions."""
    LENGTH          = "length"
    MIN_LENGTH      = "minLength"
    MAX_LENGTH      = "maxLength"
    PATTERN         = "pattern"
    MIN_INCLUSIVE   = "minInclusive"
    MAX_INCLUSIVE   = "maxInclusive"
    MIN_EXCLUSIVE   = "minExclusive"
    MAX_EXCLUSIVE   = "maxExclusive"
    TOTAL_DIGITS    = "totalDigits"
    FRACTION_DIGITS = "fractionDigits"
    ENUMERATION     = "enumeration"


class ProtobufOption(str, Enum):
    """Common Protobuf options."""
    PACKED          = "packed"
    DEPRECATED      = "deprecated"
    JSON_NAME       = "json_name"
    OPTIONAL        = "optional"
    REQUIRED        = "required"
    REPEATED        = "repeated"


class AvroLogicalType(str, Enum):
    """Logical types defined by Avro."""
    DECIMAL         = "decimal"
    DATE            = "date"
    TIME_MILLIS     = "time-millis"
    TIME_MICROS     = "time-micros"
    TIMESTAMP_MILLIS= "timestamp-millis"
    TIMESTAMP_MICROS= "timestamp-micros"
    DURATION        = "duration"
    UUID            = "uuid"


class GraphQLDirective(str, Enum):
    """Built‑in GraphQL directives."""
    SKIP            = "skip"
    INCLUDE         = "include"
    DEPRECATED      = "deprecated"
    SPECIFIED_BY    = "specifiedBy"


# ============================================================
# Explicit type representation (no Any)
# ============================================================

@dataclass
class DataType:
    base: ScalarType
    # Complex type parameters
    element_type: Optional[DataType] = None       # for ARRAY
    key_type: Optional[DataType] = None           # for MAP
    value_type: Optional[DataType] = None         # for MAP
    ref_entity: Optional[str] = None              # for REF
    precision: Optional[int] = None               # for DECIMAL
    scale: Optional[int] = None
    max_length: Optional[int] = None              # for STRING/BINARY


# ============================================================
# Annotation – human‑readable text only (no semantic meaning)
# ============================================================

@dataclass
class Annotation:
    """Purely descriptive text, e.g., a comment or implementation hint."""
    key: str        # e.g., "comment", "ui_label"
    value: str


# ============================================================
# Constraints and Indices (fully typed)
# ============================================================

@dataclass
class Constraint:
    type: ConstraintType
    name: Optional[str] = None                     # optional constraint name
    expression: Optional[str] = None               # CHECK expression, or unique column list
    referenced_entity: Optional[str] = None         # for FOREIGN KEY
    referenced_attributes: List[str] = field(default_factory=list)
    on_delete: Optional[str] = None
    on_update: Optional[str] = None

    # XSD facets (only relevant for XSD simple types)
    facets: List[XSDFacet] = field(default_factory=list)
    facet_values: Dict[str, str] = field(default_factory=dict)   # e.g., {"minLength": "5"}


@dataclass
class Index:
    name: Optional[str] = None
    attributes: List[str] = field(default_factory=list)
    unique: bool = False
    method: Optional[str] = None                  # e.g., "btree", "hash", "gin"
    annotations: List[Annotation] = field(default_factory=list)


# ============================================================
# Attribute – a field / column / property
# ============================================================

@dataclass
class Attribute:
    name: str
    data_type: DataType
    required: bool = False
    description: Optional[str] = None
    default_value: Optional[str] = None             # literal value as string

    # Key and time‑series markers
    primary_key: bool = False
    is_tag: bool = False                            # time‑series dimension
    is_field: bool = False                          # time‑series metric

    # Nested attributes for STRUCT data_type
    nested_attributes: List[Attribute] = field(default_factory=list)

    # Constraints applicable to this attribute
    constraints: List[Constraint] = field(default_factory=list)

    # Annotations – only human‑oriented text
    annotations: List[Annotation] = field(default_factory=list)

    # Optional: Protobuf‑specific options (strongly typed)
    protobuf_options: List[ProtobufOption] = field(default_factory=list)

    # Avro logical type (if different from base ScalarType)
    avro_logical_type: Optional[AvroLogicalType] = None

    # GraphQL directives (list of applied directives)
    graphql_directives: List[GraphQLDirective] = field(default_factory=list)

    # OWL restrictions (e.g., someValuesFrom, allValuesFrom) – stored as a small typed map
    owl_restrictions: Dict[str, str] = field(default_factory=dict)
    extensions: Dict[str, Any] = field(default_factory=dict)
    deprecated: bool = False
    xml: Optional[Dict[str, Any]] = None    # OpenAPI's xml object
# ============================================================
# Entity – table, collection, node, measurement, etc.
# ============================================================

@dataclass
class Entity:
    name: str
    kind: EntityKind = EntityKind.TABLE
    description: Optional[str] = None
    attributes: List[Attribute] = field(default_factory=list)
    constraints: List[Constraint] = field(default_factory=list)
    indexes: List[Index] = field(default_factory=list)
    annotations: List[Annotation] = field(default_factory=list)

    # Inheritance for object models
    extends: Optional[str] = None                    # name of base entity
    implements: List[str] = field(default_factory=list)  # interfaces / traits

    # GraphQL specific: list of interface names this type implements
    graphql_interfaces: List[str] = field(default_factory=list)

    # Avro namespace (optional)
    namespace: Optional[str] = None
    composition: Optional[CompositionEntity] = None
    discriminator: Optional[Attribute] = None
    discriminator_mapping: Dict[str, Entity] = field(default_factory=dict)
    extensions: Dict[str, Any] = field(default_factory=dict)
    
@dataclass
class CompositionEntity:
    """
    Represents a schema composition keyword (allOf, oneOf, anyOf).
    The actual type definitions are referenced via entity names or inline entities.
    """
    composition_type: Literal["allOf", "oneOf", "anyOf"]
    members: List[Entity] = field(default_factory=list)
    description: Optional[str] = None

# ============================================================
# Relationship – explicit ERD/UML association
# ============================================================

@dataclass
class Relationship:
    from_entity: str
    to_entity: str
    name: Optional[str] = None
    cardinality_from: Cardinality = Cardinality.ONE
    cardinality_to: Cardinality = Cardinality.MANY
    foreign_key_attributes: List[str] = field(default_factory=list)   # attributes in from_entity
    description: Optional[str] = None
    annotations: List[Annotation] = field(default_factory=list)


# ============================================================
# Top‑level MSDM Document
# ============================================================

@dataclass
class MSDMDocument(BaseDocument):
    """
    A document holding one or more data structure definitions.
    This is the root object of the MSDM standard.
    """
    kind: DocumentStandard = DocumentStandard.MSDM
    entities: List[Entity] = field(default_factory=list)
    relationships: List[Relationship] = field(default_factory=list)
    schema_name: Optional[str] = None
    namespace: Optional[str] = None