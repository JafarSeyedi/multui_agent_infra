import pytest
from engines.orchestration.core.engine import OrchestrationEngine, EngineConfig
from engines.orchestration.bam.engine import BamEngine


@pytest.mark.asyncio
async def test_orchestration_has_bam_flag():
    config = EngineConfig()
    assert hasattr(config, "enable_bam")


@pytest.mark.asyncio
async def test_bam_engine_receives_orchestration_ref():
    config = EngineConfig(enable_bam=True, enable_persistence=False)
    engine = OrchestrationEngine(config)
    await engine.start()
    assert engine._bam_engine is not None
    assert isinstance(engine._bam_engine, BamEngine)
    await engine.stop()


@pytest.mark.asyncio
async def test_bam_engine_starts_and_stops_with_orchestrator():
    config = EngineConfig(enable_bam=True, enable_persistence=False)
    engine = OrchestrationEngine(config)
    await engine.start()
    assert engine._bam_engine._running is True
    await engine.stop()
    assert engine._bam_engine._running is False


@pytest.mark.asyncio
async def test_bam_engine_disabled():
    config = EngineConfig(enable_bam=False, enable_persistence=False)
    engine = OrchestrationEngine(config)
    await engine.start()
    assert engine._bam_engine is None
    await engine.stop()


@pytest.mark.asyncio
async def test_bam_handler_registered():
    config = EngineConfig(enable_bam=True, enable_persistence=False)
    engine = OrchestrationEngine(config)
    assert "bam" in engine.engine_handlers
    assert engine.engine_handlers["bam"] is engine._bam_engine
