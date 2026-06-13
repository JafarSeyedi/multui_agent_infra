import pytest
from engines.orchestration.bam.engine import BamEngine
from engines.orchestration.models.bam_models import MonitoringDashboardDocument, BusinessMetric


@pytest.mark.asyncio
async def test_bam_engine_create():
    engine = BamEngine()
    assert engine is not None


@pytest.mark.asyncio
async def test_bam_engine_lifecycle():
    engine = BamEngine()
    await engine.start()
    assert engine._running is True
    await engine.stop()
    assert engine._running is False


@pytest.mark.asyncio
async def test_bam_engine_deploy():
    engine = BamEngine()
    await engine.start()
    doc = MonitoringDashboardDocument(title="Test", document_id="test-1")
    doc.metrics["m1"] = BusinessMetric(metric_id="m1", name="Test")
    await engine.deploy(doc)
    assert "test-1" in engine._deployments


@pytest.mark.asyncio
async def test_bam_engine_record_metric():
    engine = BamEngine()
    await engine.start()
    await engine.record_metric("m1", 42.5)
    history = await engine.get_metric_history("m1", "1h")
    assert len(history) >= 1
    assert history[-1].value == 42.5
