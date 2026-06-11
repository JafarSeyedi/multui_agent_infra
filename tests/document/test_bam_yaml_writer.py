import pytest
from engines.document.models.bam_models import (
    BusinessMetric, KPI, MonitoringDashboardDocument,
)
from engines.document.writers.bam_writers.bam_yaml_writer import BamYamlWriter


@pytest.mark.asyncio
async def test_write_bam_yaml():
    doc = MonitoringDashboardDocument(title="Test", document_id="test-1")
    doc.metrics["m1"] = BusinessMetric(metric_id="m1", name="CPU Usage", unit="%")
    doc.kpis["k1"] = KPI(kpi_id="k1", name="SLA", metric_ref="m1",
                           target_value=95.0, threshold_warning=90.0, threshold_critical=80.0)

    writer = BamYamlWriter()
    data = await writer.write(doc)
    text = data.decode("utf-8")
    assert "title: Test" in text
    assert "metric_id: m1" in text
    assert "kpi_id: k1" in text


@pytest.mark.asyncio
async def test_yaml_writer_roundtrip():
    from engines.document.parsers.bam_parsers.bam_yaml_parser import BamYamlParser

    doc = MonitoringDashboardDocument(title="RT", document_id="rt-1")
    doc.metrics["m1"] = BusinessMetric(metric_id="m1", name="Test")

    writer = BamYamlWriter()
    data = await writer.write(doc)

    parser = BamYamlParser()
    parsed = await parser.parse_bytes(data, "rt-1", "rt.bam.yaml")
    assert parsed.title == "RT"
    assert "m1" in parsed.metrics
