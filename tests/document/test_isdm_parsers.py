# tests/document/test_isdm_parsers.py
"""
Tests for ISDM parsers.
"""
import json

import pytest
import yaml

from engines.document.parsers.isdm_parsers import (
    BIAggregatorJSONParser,
    BIAggregatorYAMLParser,
    ISDMJSONParser,
    ISDMYAMLParser,
)
from engines.document.models.standard import DocumentStandard


@pytest.fixture
def sample_isdm_json():
    return {
        "version": "2.0",
        "start_time": "2024-01-01T00:00:00Z",
        "end_time": "2024-01-02T00:00:00Z",
        "granularity": "day",
        "dimensions": ["region", "product"],
        "metrics": [
            {
                "name": "revenue",
                "type": "gauge",
                "value": 150000.0,
                "labels": {"region": "EMEA"},
                "timestamp": "2024-01-01T12:00:00Z",
                "buckets": [0, 100, 500],
                "bucket_counts": [10, 25, 15],
            }
        ],
        "data_rows": [{"region": "EMEA", "product": "A", "revenue": 75000}],
        "source_info": {"database": "analytics"},
    }


@pytest.fixture
def sample_bi_json():
    return {
        "version": "1.0",
        "schedule": "@hourly",
        "sources": [{"type": "db", "name": "mydb"}],
        "aggregations": [
            {
                "name": "hourly_count",
                "metric": "count_events",
                "window": "last_hour",
                "output": "summary_table",
                "dimensions": ["event_type"],
                "output_config": {"format": "table"},
            }
        ],
        "targets": [{"type": "db", "table": "bi_hourly"}],
    }


@pytest.fixture
def sample_metrics_csv():
    return "metric_name,type,value,timestamp,labels,buckets,bucket_counts\nrevenue,gauge,150000.0,2024-01-01T12:00:00Z,region=EMEA,0,100,500,10,25,15"


@pytest.mark.asyncio
async def test_isdm_json_parser(sample_isdm_json):
    parser = ISDMJSONParser()
    data = json.dumps(sample_isdm_json).encode("utf-8")
    doc = await parser.parse_bytes(data, "test-isdm", "test.isfm.json")
    assert doc.document_id == "test-isdm"
    assert doc.kind == DocumentStandard.ISDM
    assert doc.granularity.value == "day"
    assert doc.dimensions == ["region", "product"]
    assert len(doc.metrics) == 1
    assert doc.metrics[0].name == "revenue"
    assert doc.metrics[0].type.value == "gauge"
    assert doc.metrics[0].value == 150000.0
    assert doc.metrics[0].labels == {"region": "EMEA"}
    assert doc.metrics[0].buckets == [0, 100, 500]
    assert doc.data_rows == [{"region": "EMEA", "product": "A", "revenue": 75000}]


@pytest.mark.asyncio
async def test_isdm_yaml_parser(sample_isdm_json):
    parser = ISDMYAMLParser()
    data = yaml.dump(sample_isdm_json).encode("utf-8")
    doc = await parser.parse_bytes(data, "test-isdm-yaml", "test.isfm.yaml")
    assert doc.kind == DocumentStandard.ISDM
    assert doc.granularity.value == "day"
    assert len(doc.metrics) == 1


@pytest.mark.asyncio
async def test_bi_aggregator_json_parser(sample_bi_json):
    parser = BIAggregatorJSONParser()
    data = json.dumps(sample_bi_json).encode("utf-8")
    doc = await parser.parse_bytes(data, "test-bi", "test.bi.json")
    assert doc.version == "1.0"
    assert doc.schedule == "@hourly"
    assert len(doc.aggregations) == 1
    agg = doc.aggregations[0]
    assert agg.name == "hourly_count"
    assert agg.dimensions == ["event_type"]
    assert agg.output_config == {"format": "table"}


@pytest.mark.asyncio
async def test_bi_aggregator_yaml_parser(sample_bi_json):
    parser = BIAggregatorYAMLParser()
    data = yaml.dump(sample_bi_json).encode("utf-8")
    doc = await parser.parse_bytes(data, "test-bi-yaml", "test.bi.yaml")
    assert doc.version == "1.0"
    assert len(doc.aggregations) == 1


def test_parser_extensions():
    assert ".isdm.json" in ISDMJSONParser().supported_extensions
    assert ".bi.json" in BIAggregatorJSONParser().supported_extensions
    assert ".bi.yaml" in BIAggregatorYAMLParser().supported_extensions
