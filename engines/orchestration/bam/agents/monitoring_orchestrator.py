from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

from engines.document.models.bam_models import (
    AgentReport, MonitoringAgentDefinition,
)

from ..collector.metric_collector import MetricCollector


class BaseMonitoringAgent(ABC):
    def __init__(self, agent_id: str, name: str) -> None:
        self.agent_id = agent_id
        self.name = name

    @abstractmethod
    async def execute(self) -> AgentReport:
        ...


class MonitoringOrchestrator:
    def __init__(self, collector: MetricCollector) -> None:
        self._collector = collector
        self._agents: dict[str, BaseMonitoringAgent] = {}
        self._definitions: dict[str, MonitoringAgentDefinition] = {}

    def register(
        self,
        definition: MonitoringAgentDefinition,
        agent: BaseMonitoringAgent,
    ) -> None:
        self._definitions[definition.agent_id] = definition
        self._agents[definition.agent_id] = agent

    def unregister(self, agent_id: str) -> None:
        self._definitions.pop(agent_id, None)
        self._agents.pop(agent_id, None)

    def get(self, agent_id: str) -> BaseMonitoringAgent | None:
        return self._agents.get(agent_id)

    async def run_all(self) -> list[AgentReport]:
        reports: list[AgentReport] = []
        for agent_id, agent in self._agents.items():
            report = await agent.execute()
            reports.append(report)
        return reports

    async def run(self, agent_id: str) -> AgentReport | None:
        agent = self._agents.get(agent_id)
        if agent is None:
            return None
        return await agent.execute()
