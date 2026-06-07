from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, ConfigDict

from .base import BaseDocument
from .media_types import MediaType
from .standard import DocumentStandard


# ==========================================================
# Enums
# ==========================================================

class EntityType(str, Enum):
    """High-level entity categories."""
    PERSON = "Person"
    ORGANIZATION = "Organization"
    LOCATION = "Location"
    EVENT = "Event"
    WORK = "Work"
    CONCEPT = "Concept"
    # Generic
    ITEM = "Item"
    UNKNOWN = "Unknown"


class RelationType(str, Enum):
    """Common relation types."""
    WORKS_FOR = "worksFor"
    LOCATED_IN = "locatedIn"
    PART_OF = "partOf"
    FRIEND_OF = "friendOf"
    FOLLOWS = "follows"
    BASED_ON = "basedOn"
    # Generic
    RELATED_TO = "relatedTo"


class Domain(str, Enum):
    """Knowledge graph domain/source context."""
    KNOWLEDGE = "knowledge"
    FINANCE = "finance"
    HEALTHCARE = "healthcare"
    ECOMMERCE = "ecommerce"
    LEGAL = "legal"
    SCIENTIFIC = "scientific"
    OTHER = "other"


# ==========================================================
# KSDM Document
# ==========================================================

@dataclass
class Entity:
    id: str
    type: EntityType = EntityType.ITEM
    label: str | None = None
    properties: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] = field(default_factory=list)


@dataclass
class Relation:
    id: str
    source_id: str
    target_id: str
    type: RelationType = RelationType.RELATED_TO
    properties: dict[str, Any] = field(default_factory=dict)
    weight: float = field(default=1.0)
    timestamp: datetime | None = None


class KSDMDocument(BaseDocument):
    """
    A knowledge graph document containing entities and relations.
    """
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        json_encoders={
            # Add any custom encoders if needed
        }
    )

    kind: DocumentStandard = Field(default=DocumentStandard.KSDM)
    title: str = ""
    document_id: str = ""
    ontology: dict[str, Any] = Field(default_factory=dict)
    entities: list[Entity] = Field(default_factory=list)
    relations: list[Relation] = Field(default_factory=list)
    attributes: dict[str, Any] = Field(default_factory=dict)


# ==========================================================
# RDF Triples
# ==========================================================

class RdfTriple(BaseModel):
    subject: str
    predicate: str
    object_: str
    graph: str | None = None  # named graph


class RdfGraph(BaseModel):
    graph_name: str | None = None
    triples: list[RdfTriple] = field(default_factory=list)


# ==========================================================
# RML Mapping
# ==========================================================

class RmlLogicalSource(BaseModel):
    source_name: str | None = None
    iterator: str | None = None
    reference_formulation: str | None = None
    query: str | None = None
    table_name: str | None = None


class RmlSubjectMap(BaseModel):
    class_type: str | None = None
    graph_map: str | None = None
    uri_template: str | None = None
    prefix_iri: str | None = None


class RmlPredicateObjectMap(BaseModel):
    predicate: str | None = None
    object_map: str | None = None
    datatype: str | None = None
    language: str | None = None
    parent_triples_map: str | None = None


class RmlSubjectMapRef(BaseModel):
    parent_triples_map: str


class RmlMapping(BaseModel):
    base_iri: str | None = None
    prefixes: dict[str, str] = field(default_factory=dict)
    logical_sources: list[RmlLogicalSource] = field(default_factory=list)
    subject_maps: list[RmlSubjectMap] = field(default_factory=list)
    predicate_object_maps: list[RmlPredicateObjectMap] = field(default_factory=list)
    references: list[RmlSubjectMapRef] = field(default_factory=list)


# ==========================================================
# GQL Schema
# ==========================================================

class GqlProperty(BaseModel):
    name: str
    type_name: str
    cardinality: Literal["REQUIRED", "OPTIONAL", "ONE", "MANY"] = "OPTIONAL"
    default_value: Any | None = None


class GqlNodeType(BaseModel):
    name: str
    properties: list[GqlProperty] = field(default_factory=list)
    key: str | None = None


class GqlEdgeType(BaseModel):
    name: str
    source: str
    target: str
    properties: list[GqlProperty] = field(default_factory=list)


class GqlSchema(BaseModel):
    node_types: list[GqlNodeType] = field(default_factory=list)
    edge_types: list[GqlEdgeType] = field(default_factory=list)


# ==========================================================
# Unified Graph Engine entities
# ==========================================================

class GraphNode(BaseModel):
    id: str
    label: str
    type: str
    url: str | None = None
    properties: dict[str, Any] = field(default_factory=dict)


class GraphEdge(BaseModel):
    source: str
    target: str
    relation: str
    properties: dict[str, Any] = field(default_factory=dict)


class KnowledgeGraph(BaseModel):
    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)


# ==========================================================
# KSDM Composite Documents
# ==========================================================

class KsdDocument(BaseDocument):
    title: str = ""
    document_id: str = ""
    media_type: MediaType | None = None
    rdf_graphs: list[RdfGraph] = Field(default_factory=list)
    rml_mappings: list[RmlMapping] = Field(default_factory=list)
    gql_schemas: list[GqlSchema] = Field(default_factory=list)
    knowledge_graph: KnowledgeGraph | None = None

    model_config = ConfigDict(
        populate_by_name=True,
    )


class KnowledgeGraphDocument(KSDMDocument):
    rdf_graphs: list[RdfGraph] = Field(default_factory=list)
    rml_mappings: list[RmlMapping] = Field(default_factory=list)
    gql_schemas: list[GqlSchema] = Field(default_factory=list)
    knowledge_graph: KnowledgeGraph | None = None


# Rebuild model
KSDMDocument.model_rebuild()
KsdDocument.model_rebuild()
KnowledgeGraphDocument.model_rebuild()