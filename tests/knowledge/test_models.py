# tests/knowledge/test_models.py
"""
Tests for knowledge models (ISDM + KSDM).
"""
from datetime import datetime

from engines.document.models.isdm_models import (
    ISDMDocument,
    Metric,
    MetricType,
    TimeGranularity,
    BIAggregatorModel,
    BIAggregation,
    BiAggregationDocument,
    BiAggregationKind,
    XmlaDiscoverRequest,
    XmlaDiscoverResponse,
    MiningModelType,
    PmmlMiningField,
    PmmlMiningSchema,
    PmmlModel,
    MlMiningDocument,
    XesExtension,
    XesClassifier,
    XesAttribute,
    XesEvent,
    XesTrace,
    XesEventLog,
    DmnDecisionTable,
    DdDecisionPoint,
    ProcessMiningDocument,
)
from engines.document.models.ksdm_models import (
    KSDMDocument,
    Entity,
    EntityType,
    Relation,
    RelationType,
    RdfTriple,
    RmlLogicalSource,
    RmlSubjectMap,
    RmlPredicateObjectMap,
    RmlMapping,
    GraphNode,
    GraphEdge,
    KnowledgeGraph,
    KnowledgeGraphDocument,
    Domain,
)
from engines.document.models.media_types import (
    KnowledgeMediaType,
    KNOWLEDGE_MEDIA_TYPES,
)
from engines.document.models.media_types import MEDIA_TYPES


def test_isdm_document_creation():
    doc = ISDMDocument(
        title="Test Insights",
        document_id="isdm-001",
        start_time=datetime(2024, 1, 1),
        end_time=datetime(2024, 1, 2),
        granularity=TimeGranularity.DAY,
        dimensions=["region", "product"],
        metrics=[Metric(name="revenue", type=MetricType.GAUGE, value=150000.0, labels={"region": "EMEA"})],
        data_rows=[{"region": "EMEA", "product": "A", "revenue": 75000}],
        source_info={"database": "analytics"},
        media_type=MEDIA_TYPES.get("json"),
    )
    assert doc.document_id == "isdm-001"
    assert len(doc.metrics) == 1


def test_bi_aggregation_document():
    doc = BiAggregationDocument(
        title="BI Test",
        document_id="bi-001",
        bi_aggregation_kind=BiAggregationKind.XMLA_CUBE,
        xmla_discover_request=XmlaDiscoverRequest(request_type="DISCOVER_DATASOURCES"),
        xmla_discover_response=XmlaDiscoverResponse(request_type="DISCOVER_DATASOURCES", rows=[{"DataSourceName": "test"}]),
        media_type=MEDIA_TYPES.get("json"),
    )
    assert doc.bi_aggregation_kind == BiAggregationKind.XMLA_CUBE
    assert doc.xmla_discover_request.request_type == "DISCOVER_DATASOURCES"


def test_ml_mining_document():
    doc = MlMiningDocument(
        title="ML Test",
        document_id="ml-001",
        model_type=MiningModelType.DECISION_TREE,
        model_data=b"<PMML></PMML>",
        pmml_model=PmmlModel(
            model_name="test_model",
            model_type=MiningModelType.DECISION_TREE,
            mining_schema=PmmlMiningSchema(fields=[PmmlMiningField(name="age")]),
        ),
        features=["age", "income"],
        target="class",
        media_type=MEDIA_TYPES.get("json"),
    )
    assert doc.model_type == MiningModelType.DECISION_TREE
    assert doc.features == ["age", "income"]
    assert doc.pmml_model is not None


def test_process_mining_document():
    doc = ProcessMiningDocument(
        title="Process Test",
        document_id="pm-001",
        xes_log=XesEventLog(
            log_id="log-1",
            extensions=[XesExtension(name="Concept", prefix="concept", uri="http://www.xes-standard.org/concept.xesext")],
            classifiers=[XesClassifier(name="Activity", keys=["concept:name"])],
            traces=[XesTrace(
                id="trace-1",
                events=[XesEvent(id="ev-1", attributes=[XesAttribute(key="concept:name", value="start")])]
            )],
        ),
        dmn_decision_table=DmnDecisionTable(id="dt-1", name="Loan Approval", hit_policy="UNIQUE"),
        media_type=MEDIA_TYPES.get("json"),
    )
    assert doc.xes_log is not None
    assert doc.xes_log.traces[0].events[0].attributes[0].value == "start"
    assert doc.dmn_decision_table.name == "Loan Approval"


def test_process_mining_model_classes():
    e1 = XesExtension(name="Concept", prefix="concept", uri="http://example.org")
    assert e1.name == "Concept"
    dp = DdDecisionPoint(id="dp-1", name="Test", confidence=0.9, support=100)
    assert dp.name == "Test"


def test_ksdm_document():
    doc = KSDMDocument(
        title="KG Test",
        document_id="kg-001",
        entities=[Entity(id="e1", type=EntityType.PERSON, label="Alice", properties={"age": 30})],
        relations=[Relation(id="r1", source_id="e1", target_id="e2", type=RelationType.WORKS_FOR, weight=0.9)],
        media_type=MEDIA_TYPES.get("json"),
    )
    assert len(doc.entities) == 1
    assert len(doc.relations) == 1


def test_knowledge_graph_document():
    doc = KnowledgeGraphDocument(
        title="KG Doc",
        document_id="kgd-001",
        knowledge_graph=KnowledgeGraph(
            nodes=[GraphNode(id="n1", label="Node 1", type="Person")],
            edges=[GraphEdge(source="n1", target="n2", relation="KNOWS")],
        ),
        media_type=MEDIA_TYPES.get("json"),
    )
    assert len(doc.knowledge_graph.nodes) == 1
    assert len(doc.knowledge_graph.edges) == 1


def test_media_types_registry():
    assert "xmla_discover_xml" in KNOWLEDGE_MEDIA_TYPES
    assert "pmml_xml" in KNOWLEDGE_MEDIA_TYPES
    assert "xes_xml" in KNOWLEDGE_MEDIA_TYPES
    assert "rdf_turtle" in KNOWLEDGE_MEDIA_TYPES
    assert isinstance(KNOWLEDGE_MEDIA_TYPES["pmml_xml"], KnowledgeMediaType)
    assert ".pmml" in KNOWLEDGE_MEDIA_TYPES["pmml_xml"].extensions


def test_domain_enum():
    assert Domain.KNOWLEDGE == "knowledge"
    assert Domain.HEALTHCARE == "healthcare"
    assert Domain.FINANCE == "finance"


def test_bi_aggregation_kind_enum():
    assert BiAggregationKind.XMLA_CUBE == "xmla_cube"
    assert BiAggregationKind.MONDRIAN_SCHEMA == "mondrian_schema"


def test_bi_aggregator_model_schedule():
    model = BIAggregatorModel(
        title="Daily Sales",
        document_id="bi-001",
        version="2.0",
        schedule="@daily",
        sources=[{"type": "database", "name": "sales_db"}],
        aggregations=[
            BIAggregation(
                name="daily_sales",
                metric="sum_sales",
                window="last_24h",
                output="summary_table",
                compute="sum(amount)",
                dimensions=["region"],
                output_config={"format": "table", "sort_by": "date"},
            )
        ],
        targets=[{"type": "database", "table": "bi_daily_sales"}],
        metadata={"owner": "bi-team"},
        media_type=MEDIA_TYPES.get("json"),
    )
    assert model.schedule == "@daily"
    assert len(model.aggregations) == 1


def test_entity_embedding():
    entity = Entity(id="e1", type=EntityType.PERSON, embedding=[0.1, 0.2])
    assert entity.embedding == [0.1, 0.2]


def test_rdf_triple_creation():
    triple = RdfTriple(subject="ex:Alice", predicate="rdf:type", object_="ex:Person")
    assert triple.subject == "ex:Alice"
    assert triple.predicate == "rdf:type"


def test_rml_mapping():
    mapping = RmlMapping(
        base_iri="http://example.org/",
        prefixes={"ex": "http://example.org/"},
        logical_sources=[RmlLogicalSource(reference_formulation="csv", table_name="people.csv")],
        subject_maps=[RmlSubjectMap(uri_template="ex:{name}")],
        predicate_object_maps=[RmlPredicateObjectMap(predicate="ex:name")],
    )
    assert mapping.base_iri == "http://example.org/"
