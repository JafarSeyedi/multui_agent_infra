# tests/knowledge/test_writers.py
"""
Tests for knowledge writers.
"""
import io
import pytest
import xml.etree.ElementTree as ET
from datetime import datetime

from engines.document.models.media_types import MEDIA_TYPES
from engines.document.models.ksdm_models import (
    KSDMMetricsDocument,
    Metric,
    MetricType,
    TimeGranularity,
    BiAggregationDocument,
    BiAggregationKind,
    CwmSchema,
    CwmClass,
    CwmAttribute,
    CwmAssociation,
    MondrianSchema,
    MondrianDimension,
    MondrianDimensionHierarchy,
    MondrianLevel,
    MondrianMeasure,
    MiningModelType,
    PmmlVersion,
    PmmlMiningSchema,
    PmmlMiningField,
    PmmlModel,
    MlMiningDocument,
)
from engines.document.models.ksdm_models import (
    KSDMDocument,
)


@pytest.fixture
def sample_metrics_doc():
    return KSDMMetricsDocument(
        title="Test Insights",
        document_id="kmd-001",
        start_time=datetime(2024, 1, 1),
        end_time=datetime(2024, 1, 2),
        granularity=TimeGranularity.DAY,
        dimensions=["region", "product"],
        metrics=[
            Metric(
                name="revenue",
                type=MetricType.GAUGE,
                value=150000.0,
                labels={"region": "EMEA"},
                timestamp=datetime(2024, 1, 1, 12, 0, 0),
                buckets=[0, 100, 500],
                bucket_counts=[10, 25, 15],
            )
        ],
        data_rows=[{"region": "EMEA", "product": "A", "revenue": 75000}],
        source_info={"database": "analytics"},
        media_type=MEDIA_TYPES.get("json"),
    )


@pytest.fixture
def sample_bi_doc():
    return BiAggregationDocument(
        title="BI Test",
        document_id="bi-001",
        version="2.0",
        schedule="@daily",
        sources=[{"type": "db", "name": "mydb"}],
        aggregations=[],
        targets=[],
        metadata={},
        bi_aggregation_kind=BiAggregationKind.MONDRIAN_SCHEMA,
        mondrian_schema=MondrianSchema(
            name="FoodMart",
            dimensions=[
                MondrianDimension(
                    name="Time",
                    type="StandardDimension",
                    hierarchy=MondrianDimensionHierarchy(
                        has_all=True,
                        levels=[
                            MondrianLevel(name="Years", table="time", column="year", unique_members=True)
                        ],
                    ),
                )
            ],
            measures=[MondrianMeasure(name="Unit Sales", column="unit_sales", aggregator_name="sum")],
        ),
        media_type=MEDIA_TYPES.get("xml"),
    )


@pytest.fixture
def sample_pmml_doc():
    return MlMiningDocument(
        title="PMML Test",
        document_id="pmml-001",
        model_type=MiningModelType.DECISION_TREE,
        model_data=b"<PMML></PMML>",
        pmml_model=PmmlModel(
            model_name="DecisionTree",
            model_type=MiningModelType.DECISION_TREE,
            function="classification",
            pmml_version=PmmlVersion.V4_2,
            mining_schema=PmmlMiningSchema(fields=[
                PmmlMiningField(name="age", usage_type="active", importance=0.8),
                PmmlMiningField(name="class", usage_type="target"),
            ]),
        ),
        features=["age", "income"],
        target="class",
        media_type=MEDIA_TYPES.get("xml"),
    )


def test_xmla_writer_can_write(sample_bi_doc):
    from engines.document.writers.ksdm_writers.bi.xmla_writer import XmlaDiscoverWriter
    writer = XmlaDiscoverWriter()
    assert writer.can_write(sample_bi_doc) is False


def test_mondrian_writer_can_write(sample_bi_doc):
    from engines.document.writers.ksdm_writers.bi.mondrian_writer import MondrianSchemaWriter
    writer = MondrianSchemaWriter()
    assert writer.can_write(sample_bi_doc)


def test_pmml_writer_can_write(sample_pmml_doc):
    from engines.document.writers.ksdm_writers.ml_mining.pmml_writer import PmmlWriter
    writer = PmmlWriter()
    assert writer.can_write(sample_pmml_doc)


def test_rml_writer_can_write():
    from engines.document.writers.ksdm_writers.semantic_graph.rml_writer import RmlWriter
    writer = RmlWriter()
    doc = KSDMDocument(
        title="RML Test",
        document_id="rml-001",
        media_type=MEDIA_TYPES.get("json"),
    )
    assert writer.can_write(doc) is False


def test_mondrian_writer_output():
    from engines.document.writers.ksdm_writers.bi.mondrian_writer import MondrianSchemaWriter
    writer = MondrianSchemaWriter()

    direct_doc = BiAggregationDocument(
        title="Mondrian Write Test",
        document_id="write-test",
        bi_aggregation_kind=BiAggregationKind.MONDRIAN_SCHEMA,
        mondrian_schema=MondrianSchema(
            name="TestMart",
            dimensions=[
                MondrianDimension(
                    name="Products",
                    type="StandardDimension",
                    hierarchy=MondrianDimensionHierarchy(
                        has_all=True,
                        levels=[MondrianLevel(name="Category", table="prod", column="category")]
                    ),
                )
            ],
            measures=[MondrianMeasure(name="Sales", column="sales", aggregator_name="sum")],
        ),
        media_type=MEDIA_TYPES.get("xml"),
    )

    buf = io.BytesIO()
    writer.write(direct_doc, buf)
    xml_bytes = buf.getvalue()
    assert b"Schema" in xml_bytes
    assert b"TestMart" in xml_bytes
    root = ET.fromstring(xml_bytes)
    assert root.get("name") == "TestMart"


def test_pmml_writer_output():
    from engines.document.writers.ksdm_writers.ml_mining.pmml_writer import PmmlWriter
    writer = PmmlWriter()

    direct_doc = MlMiningDocument(
        title="PMML Write Test",
        document_id="write-test",
        model_type=MiningModelType.DECISION_TREE,
        model_data=b"<PMML></PMML>",
        pmml_model=PmmlModel(
            model_name="DirectModel",
            model_type=MiningModelType.DECISION_TREE,
            mining_schema=PmmlMiningSchema(fields=[
                PmmlMiningField(name="age", usage_type="active"),
                PmmlMiningField(name="class", usage_type="target"),
            ]),
        ),
        features=["age"],
        target="class",
        media_type=MEDIA_TYPES.get("xml"),
    )

    buf = io.BytesIO()
    writer.write(direct_doc, buf)
    xml_bytes = buf.getvalue()
    assert b"<PMML" in xml_bytes or b"PMML" in xml_bytes
    assert b"directmodel" in xml_bytes.lower() or b"DirectModel" in xml_bytes or b"MiningModel" in xml_bytes


def test_cwm_writer_output():
    from engines.document.writers.ksdm_writers.bi.cwm_writer import CwmWriter
    writer = CwmWriter()
    doc = BiAggregationDocument(
        title="CWM",
        document_id="cwm-001",
        bi_aggregation_kind=BiAggregationKind.CWM_WAREHOUSE,
        cwm_schema=CwmSchema(
            name="Warehouse",
            classes=[CwmClass(name="Customer", attributes=[CwmAttribute(name="id", data_type="INTEGER", is_key=True)])],
            associations=[CwmAssociation(name="Places", source_class="Customer", target_class="Order")],
        ),
        media_type=MEDIA_TYPES.get("xml"),
    )
    assert writer.can_write(doc)
    buf = io.BytesIO()
    writer.write(doc, buf)
    xml_bytes = buf.getvalue()
    root = ET.fromstring(xml_bytes)
    assert root.get("name") == "Warehouse"
    cls = root.findall(".//Class")
    assert len(cls) == 1
