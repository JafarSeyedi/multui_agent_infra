from __future__ import annotations

from datetime import datetime
from typing import Any

from ..models.bam_models import AgentReport

from .monitoring_orchestrator import BaseMonitoringAgent


class AdvisoryAgent(BaseMonitoringAgent):
    def __init__(
        self,
        agent_id: str,
        name: str,
    ) -> None:
        super().__init__(agent_id, name)
        self._context: dict[str, Any] = {}

    def set_context(self, context: dict[str, Any]) -> None:
        self._context = context

    async def execute(self) -> AgentReport:
        findings: list[str] = []
        recommendations: list[str] = []

        for key, value in self._context.items():
            findings.append(f"{key}: {value}")

        if self._context.get("load_avg", 0) > 80:
            recommendations.append("Consider scaling up resources")
        if self._context.get("error_rate", 0) > 5:
            recommendations.append("Investigate error sources")

        return AgentReport(
            agent_id=self.agent_id,
            name=self.name,
            executed_at=datetime.utcnow(),
            status="success",
            findings=findings,
            recommendations=recommendations,
            metrics={"context_keys": len(self._context)},
        )
