# engines/document/models/isdm_models.py
"""
ISDM – Insights Standard Definition Model
==========================================
Format-independent representation of insights / aggregated analytics data.
Supports metrics, time series, OLAP cubes, etc.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, ConfigDict

from .base import BaseDocument, BinaryPayload
from .media_types import MediaType
from .standard import DocumentStandard


# ============================================================
# Enums
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
    metric: str  # e.g., "count_entities_by_type", "sum_sales", "avg_temperature"
    window: str  # e.g., "last_7_days", "last_hour", "year_to_date"
    output: str  # e.g., "summary_table", "metrics_series"
    compute: str | None = None  # Optional computation expression/filter
    # Optional: specific dimensions to group by for this aggregation
    dimensions: list[str] = Field(default_factory=list)
    output_config: dict[str, str] = Field(default_factory=dict)


class BIAggregatorModel(BaseDocument):
    """
    A BI aggregator model definition that specifies how to aggregate data.
    """
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
        }
    )
    
    kind: DocumentStandard = Field(default=DocumentStandard.ISDM)
    # Version of the BI aggregator model schema
    version: str = Field(default="1.0")
    # Schedule for execution (e.g., "@daily", "@hourly", cron expression)
    schedule: str = Field(default="@daily")
    # Data sources to aggregate from
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
    title: str = ""
    document_id: str = ""
    media_type: MediaType | None = None
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
    title: str = ""
    document_id: str = ""
    media_type: MediaType | None = None
    model_type: MiningModelType
    model_data: bytes = b""
    pmml_model: PmmlModel | None = None
    onnx_model: OnnxModel | None = None
    mining_results: dict[str, Any] = Field(default_factory=dict)
    features: list[str] = Field(default_factory=list)
    target: str | None = None


# ============================================================
# Process Mining Models
# ============================================================

class XesExtension(BaseModel):
    name: str
    prefix: str = ""
    uri: str = ""


class XesClassifier(BaseModel):
    name: str
    keys: list[str] = Field(default_factory=list)


class XesAttribute(BaseModel):
    key: str
    value: str = ""
    typ: str | None = None


class XesEvent(BaseModel):
    id: str | None = None
    timestamp: datetime | None = None
    attributes: list[XesAttribute] = Field(default_factory=list)
    resources: list[str] = Field(default_factory=list)


class XesTrace(BaseModel):
    id: str | None = None
    attributes: list[XesAttribute] = Field(default_factory=list)
    events: list[XesEvent] = Field(default_factory=list)


class XesLogBody(BaseModel):
    extensions: list[XesExtension] = Field(default_factory=list)
    classifiers: list[XesClassifier] = Field(default_factory=list)
    attributes: list[XesAttribute] = Field(default_factory=list)


class XesEventLog(BaseModel):
    log_id: str | None = None
    extensions: list[XesExtension] = Field(default_factory=list)
    classifiers: list[XesClassifier] = Field(default_factory=list)
    attributes: list[XesAttribute] = Field(default_factory=list)
    traces: list[XesTrace] = Field(default_factory=list)


class DmnDecisionRule(BaseModel):
    id: str = ""
    description: str = ""
    label: str | None = None
    condition: str = ""
    input_entries: list[dict[str, Any]] = Field(default_factory=list)
    output_entries: list[dict[str, Any]] = Field(default_factory=list)


class DmnDecisionAction(BaseModel):
    id: str = ""
    description: str = ""
    label: str | None = None
    decision: str = ""
    parameters: list[dict[str, Any]] = Field(default_factory=list)


class DmnDecisionTable(BaseModel):
    id: str = ""
    name: str = ""
    decision_rules: list[DmnDecisionRule] = Field(default_factory=list)
    decision_actions: list[DmnDecisionAction] = Field(default_factory=list)
    hit_policy: str = "UNIQUE"
    aggregation: str = ""


class DdDecisionPoint(BaseModel):
    id: str = ""
    name: str = ""
    context: str = ""
    discovered_rules: list[dict[str, Any]] = Field(default_factory=list)
    confidence: float = 0.0
    support: int = 0


class DdDecisionDiscoveryFramework(BaseModel):
    framework_id: str = ""
    algorithm: str = ""
    source_log: str = ""
    decision_points: list[DdDecisionPoint] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProcessMiningDocument(BaseDocument):
    title: str = ""
    document_id: str = ""
    media_type: MediaType | None = None
    xes_log: XesEventLog | None = None
    dmn_decision_table: DmnDecisionTable | None = None
    ddf_framework: DdDecisionDiscoveryFramework | None = None
    discovered_process_model: dict[str, Any] = Field(default_factory=dict)


# ============================================================
# ISDM Document
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


class ISDMDocument(BaseDocument):
    """
    An insights document containing aggregated data.
    """
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
        }
    )

    kind: DocumentStandard = Field(default=DocumentStandard.ISDM)
    title: str = ""
    document_id: str = ""
    # Time range of the data
    start_time: datetime | None = Field(default=None)
    end_time: datetime | None = Field(default=None)
    granularity: TimeGranularity | None = Field(default=None)
    dimensions: list[str] = Field(default_factory=list)
    metrics: list[Metric] = Field(default_factory=list)
    data_rows: list[dict[str, Any]] = Field(default_factory=list)
    source_info: dict[str, Any] = Field(default_factory=dict)


# Rebuild model
ISDMDocument.model_rebuild()
BIAggregatorModel.model_rebuild()
BiAggregationDocument.model_rebuild()
MlMiningDocument.model_rebuild()
ProcessMiningDocument.model_rebuild()
