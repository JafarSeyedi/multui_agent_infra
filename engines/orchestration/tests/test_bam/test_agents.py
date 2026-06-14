import pytest
from datetime import datetime
from typing import Any

from engines.orchestration.bam.agents.threshold_agent import ThresholdAgent
from engines.orchestration.bam.agents.monitoring_orchestrator import (
    MonitoringOrchestrator,
)
from engines.orchestration.bam.models.bam_models import (
    MonitoringAgentDefinition, MonitoringAgentType,
    AgentReport, MetricValue,
)


@pytest.mark.asyncio
async def test_threshold_agent_below_threshold():
    agent = ThresholdAgent("t1", "CPU Agent", threshold=90.0)
    agent.set_value(50.0)
    report = await agent.execute()
    assert report.status == "success"
    assert len(report.findings) == 0


@pytest.mark.asyncio
async def test_threshold_agent_above_threshold():
    agent = ThresholdAgent("t1", "CPU Agent", threshold=90.0)
    agent.set_value(95.0)
    report = await agent.execute()
    assert report.status == "warning"
    assert len(report.findings) > 0
    assert "95.0" in report.findings[0]


@pytest.mark.asyncio
async def test_orchestrator_run_agents():
    class MockCollector:
        def average(self, metric_id: str) -> float | None:
            return 85.0

    t_agent = ThresholdAgent("t1", "Test Agent", threshold=80.0)
    t_agent.set_value(85.0)
    t_agent_def = MonitoringAgentDefinition(
        agent_id="t1", name="Test Agent",
        input_metrics=["cpu"],
    )
    orchestrator = MonitoringOrchestrator(MockCollector())  # type: ignore
    orchestrator.register(t_agent_def, t_agent)
    reports = await orchestrator.run_all()
    assert len(reports) == 1
    assert reports[0].agent_id == "t1"


def test_orchestrator_register_and_unregister():
    class MockCollector:
        def average(self, metric_id: str) -> float | None:
            return 50.0

    agent_def = MonitoringAgentDefinition(
        agent_id="a1", name="Agent 1",
        input_metrics=["cpu"],
    )
    t_agent = ThresholdAgent("a1", "Agent 1", threshold=90.0)
    orchestrator = MonitoringOrchestrator(MockCollector())  # type: ignore
    orchestrator.register(agent_def, t_agent)
    assert orchestrator.get("a1") is not None
    orchestrator.unregister("a1")
    assert orchestrator.get("a1") is None
