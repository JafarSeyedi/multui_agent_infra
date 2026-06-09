from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, ConfigDict

from .base import BaseDocument
from .lsdm_models import EventLogDocument
from .osdm_models import CatchEvent, FlowElement, Process
from .standard import DocumentStandard

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
# TODO unification of the semantic graph models
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

class SemanticGraphDocument(BaseDocument):
    rdf_graphs: list[RdfGraph] = Field(default_factory=list)
    rml_mappings: list[RmlMapping] = Field(default_factory=list)
    gql_schemas: list[GqlSchema] = Field(default_factory=list)
    knowledge_graph: KnowledgeGraph | None = None

    model_config = ConfigDict(
        populate_by_name=True,
    )

# ============================================================
# BI Aggregation Models
# ============================================================

class BiAggregationKind(str, Enum):
    XMLA_CUBE = "xmla_cube"
    MONDRIAN_SCHEMA = "mondrian_schema"
    CWM_WAREHOUSE = "cwm_warehouse"


class BiAggregationDocument(BaseDocument):
    bi_aggregation_kind: BiAggregationKind = BiAggregationKind.XMLA_CUBE
    xmla_discover_request: XmlaDiscoverRequest | None = None
    xmla_discover_response: XmlaDiscoverResponse | None = None
    mondrian_schema: MondrianSchema | None = None
    cwm_schema: CwmSchema | None = None


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
# BI Aggregation Document
# ============================================================
# TODO: Unification of BI Aggregation documents
class XMLADocument(BaseDocument):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )
    xmla_discover_request: XmlaDiscoverRequest = Field(default_factory=XmlaDiscoverRequest)
    xmla_discover_response: XmlaDiscoverResponse = Field(default_factory=XmlaDiscoverResponse)

class MDXQueryDocument(BaseDocument):
    mdx_query: MdxQuery | None = None

class CWMDocument(BaseDocument):
    cwm_schema: CwmSchema | None = None

class MondrianDocument(BaseDocument):
    mondrian_schema: MondrianSchema | None = None

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
# ML Mining Document
# ============================================================
# TODO: unification of ML-Mining models
class MlMiningDocument(BaseDocument):
    model_type: MiningModelType
    model_data: bytes = b""
    pmml_model: PmmlModel | None = None
    onnx_model: OnnxModel | None = None
    mining_results: dict[str, Any] = Field(default_factory=dict)
    features: list[str] = Field(default_factory=list)
    target: str | None = None


# ============================================================
# Process Mining Definition — JPRM / YPRM Model
# ============================================================
# TODO using ML-Mining models in Process Mining
class ClusteringAlgorithm(str, Enum):
    KMEANS = "kmeans"
    DBSCAN = "dbscan"
    HIERARCHICAL = "hierarchical"
    GMM = "gaussian_mixture"
    AGGLOMERATIVE = "agglomerative"
    SPECTRAL = "spectral"
    BIRCH = "birch"
    OPTICS = "optics"


class MiningAlgorithm(str, Enum):
    DECISION_TREE_INDUCTION = "decision_tree_induction"
    RULE_EXTRACTION = "rule_extraction"
    FREQUENT_PATTERN_MINING = "frequent_pattern_mining"
    SEQUENCE_PATTERN_MINING = "sequence_pattern_mining"
    ASSOCIATION_RULE = "association_rule"
    CLUSTERING_BASED = "clustering_based"
    DECISION_POINT_ANALYSIS = "decision_point_analysis"
    FREQUENT_FLOW = "frequent_flow"


@dataclass
class ClusteringConfig:
    algorithm: ClusteringAlgorithm = ClusteringAlgorithm.KMEANS
    n_clusters: int | None = None
    eps: float | None = None
    dbscan_min_samples: int | None = None
    linkage: str | None = None
    affinity: str | None = None
    max_iter: int | None = None
    random_state: int | None = None
    distance_threshold: float | None = None


@dataclass
class DecisionPointDefinition:
    id: str
    description: str | None = None
    flow_element: FlowElement | None = None
    mining_algorithm: MiningAlgorithm = MiningAlgorithm.DECISION_TREE_INDUCTION
    clustering_config: ClusteringConfig | None = None
    min_support: float | None = None
    min_confidence: float | None = None
    max_rules: int | None = None


@dataclass
class CatchEventMiningDefinition:
    id: str
    description: str | None = None
    catch_event: CatchEvent | None = None
    clustering_config: ClusteringConfig | None = None
    min_events_per_cluster: int | None = None
    output_pmml_model: bool = True


@dataclass
class MiningProcessDefinition:
    id: str
    description: str | None = None
    process: Process | None = None
    event_source: EventLogDocument | None = None
    decision_points: dict[str, DecisionPointDefinition] = field(default_factory=dict)
    catch_event_definitions: dict[str, CatchEventMiningDefinition] = field(default_factory=dict)
    mining_name: str | None = None


class ProcessMiningDefinitionDocument(BaseDocument):
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
    processes: dict[str, MiningProcessDefinition] = Field(default_factory=dict)
    default_clustering_config: ClusteringConfig | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)



