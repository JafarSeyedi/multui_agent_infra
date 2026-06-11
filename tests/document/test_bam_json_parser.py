import json
import pytest
from engines.document.models.bam_models import (
    MonitoringDashboardDocument, BusinessMetric, KPI,
)
from engines.document.parsers.bam_parsers.bam_json_parser import BamJsonParser


@pytest.fixture
def valid_bam_json():
    return json.dumps({
        "title": "Test Dashboard",
        "document_id": "test-1",
        "metrics": {
            "m1": {
                "metric_id": "m1",
                "name": "Process Cycle Time",
                "category": "process",
                "aggregation": "avg",
                "unit": "ms"
            }
        },
        "kpis": {
            "k1": {
                "kpi_id": "k1",
                "name": "SLA Compliance",
                "metric_ref": "m1",
                "target_value": 95.0,
                "threshold_warning": 90.0,
                "threshold_critical": 80.0
            }
        }
    })


@pytest.mark.asyncio
async def test_parse_bam_json(valid_bam_json):
    parser = BamJsonParser()
    doc = await parser.parse_bytes(valid_bam_json.encode("utf-8"), "test-1", "test.bam.json")
    assert isinstance(doc, MonitoringDashboardDocument)
    assert doc.title == "Test Dashboard"
    assert doc.document_id == "test-1"
    assert "m1" in doc.metrics
    assert doc.metrics["m1"].name == "Process Cycle Time"
    assert "k1" in doc.kpis
    assert doc.kpis["k1"].name == "SLA Compliance"


@pytest.mark.asyncio
async def test_parse_bam_json_empty():
    parser = BamJsonParser()
    doc = await parser.parse_bytes(b"{}", "empty", "empty.bam.json")
    assert isinstance(doc, MonitoringDashboardDocument)


@pytest.mark.asyncio
async def test_parse_bam_json_invalid():
    parser = BamJsonParser()
    with pytest.raises(Exception):
        await parser.parse_bytes(b"not json", "bad", "bad.bam.json")


def test_json_parser_supported_extensions():
    parser = BamJsonParser()
    exts = list(parser.iter_supported_extensions())
    assert ".bam.json" in exts
