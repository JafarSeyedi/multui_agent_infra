# engines/document/models/msdm_capabilities.py
"""
MSDM Format Capability Profiles – describes what each MSDM format can express.
"""
from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from enum import auto
from enum import Enum
from enum import Flag

from .media_types import DocumentFormat

# ============================================================
# Enums for schema expressiveness
# ============================================================

class ScalarSupport(str, Enum):
    """Which scalar types a format natively supports."""
    STRING = "string"
    INT = "int"
    LONG = "long"
    FLOAT = "float"
    DOUBLE = "double"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    DATE = "date"
    TIME = "time"
    TIMESTAMP = "timestamp"
    DURATION = "duration"
    UUID = "uuid"
    BINARY = "binary"
    JSON = "json"
    XML = "xml"

class CompositeSupport(str, Enum):
    """Which composite types are allowed."""
    ARRAY = "array"
    MAP = "map"
    STRUCT = "struct"           # nested object / record
    REF = "ref"                 # reference to another entity
    ENUM = "enum"
    UNION = "union"             # sum types

class ConstraintCapability(str, Enum):
    """Which constraint types can be expressed."""
    PRIMARY_KEY = "primary_key"
    FOREIGN_KEY = "foreign_key"
    UNIQUE = "unique"
    NOT_NULL = "not_null"
    CHECK = "check"
    DEFAULT = "default"

class IndexCapability(str, Enum):
    """Index‑related features."""
    UNIQUE_INDEX = "unique_index"
    NON_UNIQUE_INDEX = "non_unique_index"
    COMPOSITE_INDEX = "composite_index"

class NestingDepth(str, Enum):
    NONE = "none"               # flat scalar fields only
    SINGLE_LEVEL = "single"     # one level of nesting (e.g., simple array of scalars)
    DEEP = "deep"               # arbitrary nesting (arrays of objects, nested structs)

class InheritanceSupport(str, Enum):
    NONE = "none"
    SINGLE = "single"           # single inheritance (extends)
    MULTIPLE = "multiple"       # multiple inheritance / implements

class RelationshipModel(str, Enum):
    """How relationships between entities are expressed."""
    NONE = "none"               # standalone entities only
    FOREIGN_KEY = "foreign_key" # implicit via FK constraints
    EXPLICIT = "explicit"       # dedicated relationship definitions (ERD)
    NAVIGATION = "navigation"   # graph‑style navigation (e.g., GraphQL edges)

class AnnotationSupport(str, Enum):
    """What kind of annotations / comments are available."""
    NONE = "none"
    SIMPLE_COMMENT = "simple"   # plain text description
    KEY_VALUE = "key_value"     # structured key‑value pairs
    DIRECTIVES = "directives"   # special directives (e.g., Protobuf options, GraphQL directives)

class TimeSeriesSupport(Flag):
    NONE = 0
    TIMESTAMP_FIELD = auto()
    TAG_FIELDS = auto()
    VALUE_FIELDS = auto()
    RETENTION_POLICY = auto()

class NamespaceSupport(str, Enum):
    """Support for namespacing / packaging."""
    NONE = "none"
    FLAT = "flat"               # single namespace (e.g., package name)
    HIERARCHICAL = "hierarchical" # nested namespaces

class EnumCapability(Flag):
    NONE = 0
    STRING_ENUM = auto()  # enum with named values
    INT_ENUM = auto()        # enum with integer values


@dataclass
class MSDM_FormatCapability:
    """Describes the structural abilities of a schema‑definition format."""
    format: DocumentFormat
    description: str

    # Scalar types supported
    scalar_types: list[ScalarSupport] = field(default_factory=list)
    # Composite types supported
    composite_types: list[CompositeSupport] = field(default_factory=list)
    # Nesting depth allowed
    nesting_depth: NestingDepth = NestingDepth.NONE

    # Constraints
    constraints: list[ConstraintCapability] = field(default_factory=list)
    # Indexes
    indexes: list[IndexCapability] = field(default_factory=list)

    # Inheritance
    inheritance: InheritanceSupport = InheritanceSupport.NONE

    # Relationship modelling
    relationship_model: RelationshipModel = RelationshipModel.NONE

    # Annotations
    annotations: AnnotationSupport = AnnotationSupport.NONE

    # Time‑series semantics
    time_series: TimeSeriesSupport = TimeSeriesSupport.NONE

    # Namespace / package
    namespace: NamespaceSupport = NamespaceSupport.NONE

    # Enum support
    enum_support: EnumCapability = EnumCapability.NONE

    # Additional: whether the format has a concept of a table/collection vs free‑form
    has_entity_concept: bool = True
    # Whether the format supports schema reuse (imports, includes)
    supports_reuse: bool = False
    # Whether the format is designed for streaming / event schemas
    supports_streaming: bool = False
    # Whether the format is a binary format (vs text)
    is_binary: bool = False
