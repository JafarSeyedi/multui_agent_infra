# engines/document/models/msdm_models.py
# Metadata of data Structure Definition Model (SDM)
# MSDM is about metadata describing structure. Whether you're defining a relational table,
# a JSON schema, or a time-series measurement, you're essentially listing fields with types
# and constraints. The kind field simply gives a hint to the parser/writer about what format
# to expect (e.g., .cql for Cassandra, .sql for TimescaleDB, or direct InfluxQL)
# Purpose: Describe data schemas, database tables, class hierarchies, and type systems in a format-independent way.
# Formats to support
# Format                   File extensions         Notes
# JSON Schema              .schema.json, .json     Declarative validation rules for JSON
# XSD (XML Schema)         .xsd                    XML structure definition
# SQL DDL                  .sql, .ddl              CREATE TABLE, ALTER, etc.
# ERD / Entity-Relationship .erd, .xml, .json      Database modelling
# UML Class Diagram        .uml, .xmi, .plantuml   Object-oriented design
# Protobuf / gRPC IDL      .proto                  Language-neutral interface definitions
# Thrift IDL               .thrift                 Apache Thrift interface definitions
# GraphQL Schema           .graphql, .gql          Type system and query definitions
# OWL / RDF Schema         .owl, .rdf              Semantic web ontologies
# Pydantic / dataclass     .py                     (Python code) Direct extraction from Python classes
# TypeScript interfaces    .ts                     Static type definitions
# Typical NoSQL schemas:
# Type             Example formats            Schema description
# Document         MongoDB, Couchbase         JSON Schema / Mongoose schemas
# Wide-column      Cassandra, HBase           CQL table definitions
# Key-value        Redis, DynamoDB            Often schema-less, but key/value type info possible
# Graph            Neo4j, ArangoDB            Node/Edge type definitions
# Search           Elasticsearch              Index mappings (JSON)
# How MSDM handles them:
# - Entity represents a collection, table, or node label.
# - Attribute fields map to document properties, columns, or key fields. The type can be a complex string like "array<string>" or "map<string, int>" for nested structures.
# - Constraint can capture uniqueness, required, indexing, or text-search options.
# - Annotation stores engine-specific hints (e.g., shard keys, TTL).
# - Add an optional Entity.kind field ("document", "column_family", "graph_node", "timeseries") to inform downstream tools.
# Time-based data - Typical time-series / event schemas:
# Type             Example formats                    Schema description
# Time-series DB   InfluxDB, TimescaleDB, Prometheus   Measurement/table with timestamp, fields, tags
# Event sourcing   Kafka, EventStore                   Event schema (Avro/JSON) with timestamp
# Temporal tables  SQL:2011                            System-versioned tables
# How MSDM handles them:
# - A time-series measurement is an Entity with a kind="timeseries".
# - The timestamp column is simply an Attribute with type="timestamp" and primary_key=True.
# - Tags (dimensions) and fields (metrics) are regular attributes; we can use annotations to mark which are tags/fields.
# - Retention policies, down-sampling, and continuous queries become Constraint or Annotation objects.
# CQL (Cassandra) - engines/document/parsers/msdm_parsers/cql_parser.py
# MongoDB validator schema - engines/document/parsers/msdm_parsers/mongo_schema_parser.py
# InfluxDB - engines/document/parsers/msdm_parsers/influx_schema_parser.py
# Kafka Avro schemas (already covered by proto/avsc parsers)
# engines/document/models/msdm_models.py
"""
MSDM - Metadata Standard Definition Model
===========================================
Format-independent representation of data schemas, database tables,
class hierarchies, type systems, and time-series / NoSQL definitions.
Every structural detail is captured in strictly-typed fields.
Annotations are reserved for human-oriented text without semantic weight.
"""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, ConfigDict

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
    RANGE            = "range"

    MUST             = "must"
    WHEN             = "when"
    OWL_SOME_VALUES_FROM    = "owl_some_values_from"
    OWL_ALL_VALUES_FROM     = "owl_all_values_from"
    OWL_MIN_CARDINALITY     = "owl_min_cardinality"

class ScalarType(str, Enum):
    NULL            = "null"
    STRING          = "string"
    INT             = "int"
    LONG            = "long"
    FLOAT           = "float"
    DOUBLE          = "double"
    DECIMAL         = "decimal"
    BOOLEAN         = "boolean"
    DATETIME        = "datetime"
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
    NONE            = "none"
    YANG_ANYDATA    = "yang_any_data"            # YANG anydata / anyxml
    OBJECT_ID       = "object_id"  # MongoDB ObjectId
    REGEX           = "regex"  # Regular expression
    URI             = "uri"
    EMAIL           = "email"
    CUSTOM          = "custom"

class IndexMethod(str, Enum):
    BTREE           = "skip"
    HASH            = "include"
    GIN             = "deprecated"
    NOT_DEFINED     = "not_defined"
    UNKNOWN         = "unknown"

class CompositionType(str, Enum):
    ALL_OF           = "allOf"
    ONE_OF           = "oneOf"
    ANY_OF           = "anyOf"

class VersionStatus(str, Enum):
    CURRENT         = "current"
    DEPRECATED      = "deprecated"
    OBSOLETE        = "obsolete"

class VisibilityKind(str, Enum):
    PUBLIC = "+"
    PRIVATE = "-"
    PROTECTED = "#"
    PACKAGE = "~"

# ============================================================
# Explicit type representation
# ============================================================

class DataType(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    base: ScalarType
    element_type: DataType | None = None       # for ARRAY
    key_type: DataType | None = None           # for MAP
    value_type: DataType | None = None         # for MAP
    ref_entity: Entity | None = None           # for REF (forward ref, resolved at runtime)
    ref_entity_id: str | None = None           # for REF temporary id
    precision: int | None = None               # for DECIMAL
    scale: int | None = None
    max_length: int | None = None              # for STRING/BINARY

# ============================================================
# Annotation - human-readable text only (no semantic meaning)
# ============================================================

class Annotation(BaseModel):
    """Purely descriptive text, e.g., a comment or implementation hint."""
    key: str        # e.g., "comment", "ui_label"
    value: str


# ============================================================
# Constraints and Indices (fully typed)
# ============================================================

class Constraint(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    type: ConstraintType
    name: str | None = None                     # optional constraint name
    expression: str | None = None               # CHECK expression, or unique column list
    value: Any | None = None
    ref_entity: Entity | None = None         # for FOREIGN KEY (forward ref)
    ref_entity_id: str | None = None           # for REF temporary id
    ref_attr_ids: list[str] = Field(default_factory=list)
    on_delete: str | None = None
    on_update: str | None = None


class Index(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str | None = None
    attributes: list[Attribute] = Field(default_factory=list)
    unique: bool = False
    method: IndexMethod | None = None                  # e.g., "btree", "hash", "gin"
    annotations: list[Annotation] = Field(default_factory=list)


# ============================================================
# Attribute - a field / column / property
# ============================================================

class Attribute(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    data_type: DataType
    description: str | None = None
    default_value: str | None = None             # literal value as string
    required: bool = False

    # Key and time-series markers
    is_tag: bool = False                            # time-series dimension
    is_field: bool = False                          # time-series metric

    # Nested attributes for STRUCT data_type
    nested_attributes: list[Attribute] = Field(default_factory=list)

    # Constraints applicable to this attribute
    constraints: list[Constraint] = Field(default_factory=list)

    # Annotations - only human-oriented text
    annotations: list[Annotation] = Field(default_factory=list)

    # Optional: Protobuf-specific options (strongly typed)
    is_packed: bool = False

    extensions: dict[str, Any] = Field(default_factory=dict)
    template: Entity | None = None   # name of the template entity to expand (forward ref)
    template_id: str | None = None
    is_config: bool | None = None       # config (true/false), default true
    version_status: VersionStatus | None = None

    # UML specific (optional)
    is_static: bool = False
    is_derived: bool = False
    is_abstract: bool = False
    visibility: VisibilityKind | None = None

# ============================================================
# Entity - table, collection, node, measurement, etc.
# ===========================================================

class Namespace(BaseModel):
    uri: str                     # e.g., "http://example.com/schema"
    prefix: str | None = None    # e.g., "ex"
    is_default: bool = False     # whether this is the default namespace
    version: str | None = None

class EntityComposition(BaseModel):
    """
    Represents a schema composition keyword (allOf, oneOf, anyOf).
    The actual type definitions are referenced via entity names or inline entities.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    composition_type: CompositionType
    members: list[Entity] = Field(default_factory=list)
    member_ids: list[str] = Field(default_factory=list)
    description: str | None = None

class Entity(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    kind: EntityKind = EntityKind.TABLE
    description: str | None = None
    attributes: list[Attribute] = Field(default_factory=list)
    constraints: list[Constraint] = Field(default_factory=list)
    indexes: list[Index] = Field(default_factory=list)
    # Annotations - only human-oriented text
    annotations: list[Annotation] = Field(default_factory=list)

    # Inheritance for object models
    extends: Entity | None = None                    # self-reference, resolved at runtime
    extends_ref_id: str | None = None
    augments: Entity | None = None                    # self-reference
    augments_ref_id: str | None = None
    implements: list[Entity] = Field(default_factory=list)  # interfaces / traits
    implements_ref_ids: list[str] = Field(default_factory=list)

    namespace: Namespace | None = None
    composition: EntityComposition | None = None
    discriminator: Attribute | None = None
    discriminator_mapping: dict[str, Entity] = Field(default_factory=dict)
    is_template: bool = False
    list_key: str | None = None        # Attribute name key for YANG list entries
    is_config: bool | None = None       # config (true/false), default true
    version_status: VersionStatus | None = None        # "current", "deprecated", "obsolete"
    yang_deviate_targets: list[str] = Field(default_factory=list)   # deviation targets

    # UML specific (optional)
    is_interface: bool = False
    is_abstract: bool = False

# ============================================================
# EntityRelationship - explicit ERD/UML association
# ============================================================

class EntityRelationship(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    from_entity: Entity | None = None
    to_entity: Entity | None = None
    from_ref_id: str | None = None
    to_ref_id: str | None = None
    name: str | None = None
    cardinality_from: Cardinality = Cardinality.ONE
    cardinality_to: Cardinality = Cardinality.MANY
    foreign_key_attributes: list[str] = Field(default_factory=list)   # attributes in from_entity
    description: str | None = None
    annotations: list[Annotation] = Field(default_factory=list)


# ============================================================
# Top-level MSDM Document
# ============================================================

class MSDMDocument(BaseDocument):
    """
    A document holding one or more data structure definitions.
    This is the root object of the MSDM standard.
    """
    kind: DocumentStandard = DocumentStandard.MSDM
    entities: list[Entity] = Field(default_factory=list)
    relationships: list[EntityRelationship] = Field(default_factory=list)
    schema_name: str | None = None
    namespace: Namespace | None = None
    annotations: list[Annotation] = Field(default_factory=list)


# ============================================================
# Resolve forward references (needed for self- and circular refs)
# ============================================================
DataType.model_rebuild()
Constraint.model_rebuild()
Index.model_rebuild()
Attribute.model_rebuild()
EntityComposition.model_rebuild()
Entity.model_rebuild()
EntityRelationship.model_rebuild()
