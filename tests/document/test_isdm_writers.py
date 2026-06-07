# tests/document/test_isdm_writers.py
"""
Tests for ISDM writers.
"""
import json

import pytest
import yaml
from datetime import datetime

from engines.document.parsers.isdm_parsers import (
    ISDMJSONParser,
)
from engines.document.writers.isdm_writers import (
    BIAggregatorJSONWriter,
    BIAggregatorYAMLWriter,
    ISDMJSONWriter,
    ISDMYAMLWriter,
    MetricsCSVWriter,
)
from engines.document.models.isdm_models import (
    BIAggregation,
    BIAggregatorModel,
    ISDMDocument,
    Metric,
    MetricType,
    TimeGranularity,
)
from engines.document.models.media_types import MEDIA_TYPES


@pytest.fixture
def sample_isdm_doc():
    return ISDMDocument(
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
                buckets=[0, 100, 500],
                bucket_counts=[10, 25, 15],
                sum_obs=125.5,
                count_obs=50,
            )
        ],
        data_rows=[{"region": "EMEA", "product": "A", "revenue": 75000}],
        source_info={"database": "analytics"},
        metadata={"author": "bi-team"},
        media_type=MEDIA_TYPES.get("json", MEDIA_TYPES["bi_model_json"]),
    )


@pytest.fixture
def sample_bi_model():
    return BIAggregatorModel(
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


@pytest.mark.asyncio
async def test_isdm_json_writer(sample_isdm_doc):
    writer = ISDMJSONWriter()
    data = await writer.write(sample_isdm_doc)
    parsed = json.loads(data.decode("utf-8"))
    assert parsed["version"] == "1.0"
    assert parsed["granularity"] == "day"
    assert parsed["dimensions"] == ["region", "product"]
    assert len(parsed["metrics"]) == 1
    assert parsed["metrics"][0]["name"] == "revenue"
    assert parsed["metrics"][0]["buckets"] == [0, 100, 500]


@pytest.mark.asyncio
async def test_isdm_yaml_writer(sample_isdm_doc):
    writer = ISDMYAMLWriter()
    data = await writer.write(sample_isdm_doc)
    parsed = yaml.safe_load(data.decode("utf-8"))
    assert parsed["granularity"] == "day"
    assert len(parsed["metrics"]) == 1


@pytest.mark.asyncio
async def test_metrics_csv_writer(sample_isdm_doc):
    writer = MetricsCSVWriter()
    data = await writer.write(sample_isdm_doc)
    text = data.decode("utf-8")
    assert "metric_name" in text
    assert "revenue" in text
    assert "gauge" in text


@pytest.mark.asyncio
async def test_bi_aggregator_json_writer(sample_bi_model):
    writer = BIAggregatorJSONWriter()
    data = await writer.write(sample_bi_model)
    parsed = json.loads(data.decode("utf-8"))
    assert parsed["version"] == "2.0"
    assert parsed["schedule"] == "@daily"
    assert len(parsed["aggregations"]) == 1
    assert parsed["aggregations"][0]["output_config"] == {"format": "table", "sort_by": "date"}


@pytest.mark.asyncio
async def test_bi_aggregator_yaml_writer(sample_bi_model):
    writer = BIAggregatorYAMLWriter()
    data = await writer.write(sample_bi_model)
    parsed = yaml.safe_load(data.decode("utf-8"))
    assert parsed["version"] == "2.0"
    assert len(parsed["aggregations"]) == 1


@pytest.mark.asyncio
async def test_isdm_roundtrip(sample_isdm_doc):
    json_writer = ISDMJSONWriter()
    json_parser = ISDMJSONParser()

    data = await json_writer.write(sample_isdm_doc)
    doc2 = await json_parser.parse_bytes(data, "roundtrip", "roundtrip.isfm.json")

    assert doc2.document_id == "roundtrip"
    assert doc2.granularity == TimeGranularity.DAY
    assert doc2.dimensions == ["region", "product"]
    assert len(doc2.metrics) == 1
    assert doc2.metrics[0].name == "revenue"
