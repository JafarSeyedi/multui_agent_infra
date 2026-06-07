# tests/document/test_isdm_models.py
"""
Tests for ISDM models: ISDMDocument, BIAggregatorModel, Metric, enums.
"""
from datetime import datetime

from engines.document.models.isdm_models import (
    BIAggregatorModel,
    BIAggregation,
    ISDMDocument,
    Metric,
    MetricType,
    TimeGranularity,
    Aggregation,
)
from engines.document.models.standard import DocumentStandard


def test_isdm_document_creation():
    doc = ISDMDocument(
        title="Test Insights",
        document_id="isdm-001",
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
            )
        ],
        data_rows=[{"region": "EMEA", "product": "A", "revenue": 75000}],
        source_info={"database": "analytics"},
    )
    assert doc.kind == DocumentStandard.ISDM
    assert doc.document_id == "isdm-001"
    assert len(doc.metrics) == 1
    assert doc.metrics[0].name == "revenue"
    assert doc.metrics[0].type == MetricType.GAUGE
    assert doc.metrics[0].labels == {"region": "EMEA"}
    assert doc.granularity == TimeGranularity.DAY
    assert doc.dimensions == ["region", "product"]


def test_metric_histogram():
    metric = Metric(
        name="latency",
        type=MetricType.HISTOGRAM,
        buckets=[0.1, 0.5, 1.0, 5.0],
        bucket_counts=[100, 250, 80, 20],
        sum_obs=125.5,
        count_obs=450,
    )
    assert metric.buckets == [0.1, 0.5, 1.0, 5.0]
    assert metric.bucket_counts == [100, 250, 80, 20]
    assert metric.sum_obs == 125.5
    assert metric.count_obs == 450


def test_bi_aggregator_model():
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
    )
    assert model.version == "2.0"
    assert model.schedule == "@daily"
    assert len(model.aggregations) == 1
    agg = model.aggregations[0]
    assert agg.name == "daily_sales"
    assert agg.metric == "sum_sales"
    assert agg.dimensions == ["region"]
    assert agg.output_config == {"format": "table", "sort_by": "date"}


def test_bi_aggregation_output_config_fix():
    agg = BIAggregation(
        name="test",
        metric="count",
        window="1h",
        output="table",
        output_config={},
    )
    assert isinstance(agg.output_config, dict)
    assert agg.output_config == {}


def test_metric_type_enum():
    assert MetricType.GAUGE == "gauge"
    assert MetricType.COUNTER == "counter"
    assert MetricType.HISTOGRAM == "histogram"
    assert MetricType.SUMMARY == "summary"


def test_time_granularity_enum():
    assert TimeGranularity.SECOND == "second"
    assert TimeGranularity.DAY == "day"
    assert TimeGranularity.MONTH == "month"
    assert TimeGranularity.YEAR == "year"


def test_aggregation_enum():
    assert Aggregation.SUM == "sum"
    assert Aggregation.AVG == "average"
    assert Aggregation.STDDEV == "stddev"
