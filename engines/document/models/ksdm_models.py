from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, ConfigDict

from .base import BaseDocument, BinaryPayload
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


# ============================================================
# Enums (from ISDM)
# ============================================================

class MetricType(str, Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class Aggregation(str, Enum):
    SUM = "sum"
    COUNT = "count"
    AVG = "average"
    MIN = "min"
    MAX = "max"
    PCTILE = "percentile"
    STDDEV = "stddev"


class TimeGranularity(str, Enum):
    SECOND = "second"
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


# ============================================================
# BI Aggregator Model Definition
# ============================================================

@dataclass
class BIAggregation:
    name: str
    metric: str
    window: str
    output: str
    compute: str | None = None
    dimensions: list[str] = Field(default_factory=list)
    output_config: dict[str, str] = Field(default_factory=dict)


class BIAggregatorModel(BaseDocument):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
        }
    )

    kind: DocumentStandard = Field(default=DocumentStandard.KSDM)
    version: str = Field(default="1.0")
    schedule: str = Field(default="@daily")
    sources: list[dict[str, str]] = Field(default_factory=list)
    aggregations: list[BIAggregation] = Field(default_factory=list)
    targets: list[dict[str, str]] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)


# ============================================================
# BI Aggregation Formats
# ============================================================

class BiAggregationKind(str, Enum):
    XMLA_CUBE = "xmla_cube"
    MDX_QUERY = "mdx_query"
    CWM_WAREHOUSE = "cwm_warehouse"
    MONDRIAN_SCHEMA = "mondrian_schema"


# ============================================================
# XMLA / MDX Models
# ============================================================

class XmlaDiscoverRequest(BaseModel):
    request_type: str = ""
    restrictions: dict[str, str] = Field(default_factory=dict)
    properties: dict[str, str] = Field(default_factory=dict)


class XmlaDiscoverResponse(BaseModel):
    request_type: str = ""
    rows: list[dict[str, str]] = Field(default_factory=list)
    schema_rowset: str | None = None


class MdxAxis(BaseModel):
    axis: str = "ROWS"
    hierarchy: str | None = None
    level: str | None = None


class MdxQuery(BaseModel):
    cube_name: str = ""
    axes: list[MdxAxis] = Field(default_factory=list)
    measures: list[str] = Field(default_factory=list)
    slicer: str | None = None
    query_text: str | None = None


# ============================================================
# CWM (Common Warehouse Model) Schema
# ============================================================

class CwmAttribute(BaseModel):
    name: str = ""
    data_type: str = ""
    nullable: bool = True
    is_key: bool = False


class CwmClass(BaseModel):
    name: str = ""
    package: str | None = None
    attributes: list[CwmAttribute] = Field(default_factory=list)


class CwmAssociation(BaseModel):
    name: str = ""
    source_class: str = ""
    target_class: str = ""
    multiplicity: str | None = None


class CwmSchema(BaseModel):
    name: str | None = None
    package: str | None = None
    classes: list[CwmClass] = Field(default_factory=list)
    associations: list[CwmAssociation] = Field(default_factory=list)


# ============================================================
# Mondrian Schema
# ============================================================

class MondrianMeasure(BaseModel):
    name: str = ""
    column: str = ""
    aggregator_name: str = "sum"
    visible: bool = True


class MondrianLevel(BaseModel):
    name: str = ""
    table: str = ""
    column: str = ""
    name_column: str | None = None
    unique_members: bool = True
    level_type: str = "Regular"


class MondrianDimensionHierarchy(BaseModel):
    has_all: bool = True
    primary_key: str | None = None
    levels: list[MondrianLevel] = Field(default_factory=list)


class MondrianDimension(BaseModel):
    name: str = ""
    type: str = "StandardDimension"
    hierarchy: MondrianDimensionHierarchy | None = None


class MondrianSchema(BaseModel):
    name: str = ""
    table: str | None = None
    dimensions: list[MondrianDimension] = Field(default_factory=list)
    measures: list[MondrianMeasure] = Field(default_factory=list)


# ============================================================
# ML Mining Models
# ============================================================

class MiningModelType(str, Enum):
    NEURAL_NETWORK = "neural_network"
    DECISION_TREE = "decision_tree"
    REGRESSION = "regression"
    CLUSTERING = "clustering"
    ASSOCIATION_RULES = "association_rules"
    SEQUENCE_CLUSTERING = "sequence_clustering"
    TIME_SERIES = "time_series"
    SVM = "svm"
    NAIVE_BAYES = "naive_bayes"
    GAUSSIAN_PROCESS = "gaussian_process"
    ONNX_MODEL = "onnx_model"


class PmmlVersion(str, Enum):
    V4_1 = "4.1"
    V4_2 = "4.2"


class PmmlMiningField(BaseModel):
    name: str = ""
    usage_type: str = "active"
    importance: float | None = None
    missing_value_replacement: Any | None = None


class PmmlMiningSchema(BaseModel):
    fields: list[PmmlMiningField] = Field(default_factory=list)


class PmmlModel(BaseModel):
    model_name: str | None = None
    model_type: MiningModelType = MiningModelType.DECISION_TREE
    function: str = "classification"
    pmml_version: PmmlVersion = PmmlVersion.V4_2
    mining_schema: PmmlMiningSchema | None = None


class OnnxOpsetImport(BaseModel):
    domain: str = ""
    version: int = 0


class OnnxNode(BaseModel):
    op_type: str = ""
    input_names: list[str] = Field(default_factory=list)
    output_names: list[str] = Field(default_factory=list)
    attributes: dict[str, Any] = Field(default_factory=dict)


class OnnxGraph(BaseModel):
    name: str = ""
    nodes: list[OnnxNode] = Field(default_factory=list)
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    initializers: list[dict[str, Any]] = Field(default_factory=list)
    value_info: list[dict[str, Any]] = Field(default_factory=list)


class OnnxModel(BaseModel):
    model_name: str | None = None
    ir_version: int = 0
    producer_name: str = ""
    producer_version: str = ""
    opset_imports: list[OnnxOpsetImport] = Field(default_factory=list)
    graph: OnnxGraph


# ============================================================
# BI Aggregation Document
# ============================================================

class BiAggregationDocument(BIAggregatorModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )
    bi_aggregation_kind: BiAggregationKind = BiAggregationKind.XMLA_CUBE
    xmla_discover_request: XmlaDiscoverRequest = Field(default_factory=XmlaDiscoverRequest)
    xmla_discover_response: XmlaDiscoverResponse = Field(default_factory=XmlaDiscoverResponse)
    mdx_query: MdxQuery | None = None
    cwm_schema: CwmSchema | None = None
    mondrian_schema: MondrianSchema | None = None


# ============================================================
# ML Mining Document
# ============================================================

class MlMiningDocument(BaseDocument):
    model_type: MiningModelType
    model_data: bytes = b""
    pmml_model: PmmlModel | None = None
    onnx_model: OnnxModel | None = None
    mining_results: dict[str, Any] = Field(default_factory=dict)
    features: list[str] = Field(default_factory=list)
    target: str | None = None


# ============================================================
# Metrics Document
# ============================================================

@dataclass
class Metric:
    name: str
    description: str | None = None
    type: MetricType = MetricType.GAUGE
    value: Any = None
    labels: dict[str, str] = Field(default_factory=dict)
    timestamp: datetime | None = None
    buckets: list[float] = Field(default_factory=list)
    bucket_counts: list[int] = Field(default_factory=list)
    sum_obs: float | None = None
    count_obs: int | None = None


class KSDMMetricsDocument(BaseDocument):
    """
    A metrics/analytics document containing aggregated data.
    """
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
        }
    )

    kind: DocumentStandard = Field(default=DocumentStandard.KSDM)
    title: str = ""
    document_id: str = ""
    start_time: datetime | None = Field(default=None)
    end_time: datetime | None = Field(default=None)
    granularity: TimeGranularity | None = Field(default=None)
    dimensions: list[str] = Field(default_factory=list)
    metrics: list[Metric] = Field(default_factory=list)
    data_rows: list[dict[str, Any]] = Field(default_factory=list)
    source_info: dict[str, Any] = Field(default_factory=dict)


# Rebuild model
KSDMDocument.model_rebuild()
KsdDocument.model_rebuild()
KnowledgeGraphDocument.model_rebuild()
BIAggregatorModel.model_rebuild()
BiAggregationDocument.model_rebuild()
MlMiningDocument.model_rebuild()
KSDMMetricsDocument.model_rebuild()
