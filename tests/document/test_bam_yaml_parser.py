import pytest
from engines.orchestration.models.bam_models import MonitoringDashboardDocument
from engines.orchestration.models.parsers.bam.bam_yaml_parser import BamYamlParser


YAML_CONTENT = """
title: Test Dashboard
document_id: test-1
metrics:
  m1:
    metric_id: m1
    name: Process Cycle Time
    category: process
    aggregation: avg
    unit: ms
kpis:
  k1:
    kpi_id: k1
    name: SLA Compliance
    metric_ref: m1
    target_value: 95.0
    threshold_warning: 90.0
    threshold_critical: 80.0
"""


@pytest.mark.asyncio
async def test_parse_bam_yaml():
    parser = BamYamlParser()
    doc = await parser.parse_bytes(YAML_CONTENT.encode("utf-8"), "test-1", "test.bam.yaml")
    assert isinstance(doc, MonitoringDashboardDocument)
    assert doc.title == "Test Dashboard"
    assert "m1" in doc.metrics
    assert "k1" in doc.kpis


def test_yaml_parser_supported_extensions():
    parser = BamYamlParser()
    exts = list(parser.iter_supported_extensions())
    assert ".bam.yaml" in exts or ".bam.yml" in exts
