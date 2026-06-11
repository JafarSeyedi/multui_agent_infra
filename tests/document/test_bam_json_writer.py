import json
import pytest
from engines.document.models.bam_models import (
    BusinessMetric, KPI, MonitoringDashboardDocument,
)
from engines.document.writers.bam_writers.bam_json_writer import BamJsonWriter


@pytest.mark.asyncio
async def test_write_bam_json():
    doc = MonitoringDashboardDocument(title="Test", document_id="test-1")
    doc.metrics["m1"] = BusinessMetric(metric_id="m1", name="CPU Usage", unit="%")
    doc.kpis["k1"] = KPI(kpi_id="k1", name="SLA", metric_ref="m1",
                           target_value=95.0, threshold_warning=90.0, threshold_critical=80.0)

    writer = BamJsonWriter()
    data = await writer.write(doc)
    parsed = json.loads(data.decode("utf-8"))
    assert parsed["title"] == "Test"
    assert "m1" in parsed["metrics"]
    assert parsed["metrics"]["m1"]["name"] == "CPU Usage"
    assert "k1" in parsed["kpis"]


@pytest.mark.asyncio
async def test_write_bam_json_empty():
    doc = MonitoringDashboardDocument(title="Empty", document_id="empty")
    writer = BamJsonWriter()
    data = await writer.write(doc)
    parsed = json.loads(data.decode("utf-8"))
    assert parsed["title"] == "Empty"


@pytest.mark.asyncio
async def test_json_writer_roundtrip():
    from engines.document.parsers.bam_parsers.bam_json_parser import BamJsonParser

    doc = MonitoringDashboardDocument(title="RT", document_id="rt-1")
    doc.metrics["m1"] = BusinessMetric(metric_id="m1", name="Test", unit="ms")

    writer = BamJsonWriter()
    data = await writer.write(doc)

    parser = BamJsonParser()
    parsed = await parser.parse_bytes(data, "rt-1", "rt.bam.json")
    assert parsed.title == "RT"
    assert "m1" in parsed.metrics
    assert parsed.metrics["m1"].name == "Test"
