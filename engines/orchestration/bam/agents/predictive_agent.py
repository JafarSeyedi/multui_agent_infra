from __future__ import annotations

from datetime import datetime
from typing import Any

from engines.document.models.bam_models import AgentReport

from .monitoring_orchestrator import BaseMonitoringAgent


class PredictiveAgent(BaseMonitoringAgent):
    def __init__(
        self,
        agent_id: str,
        name: str,
    ) -> None:
        super().__init__(agent_id, name)
        self._values: list[float] = []

    def set_values(self, values: list[float]) -> None:
        self._values = values

    async def execute(self) -> AgentReport:
        findings: list[str] = []
        recommendations: list[str] = []
        status = "success"

        if len(self._values) >= 2:
            trend = self._values[-1] - self._values[0]
            if trend > 0:
                findings.append(f"Upward trend detected: +{trend:.1f} over {len(self._values)} samples")
                recommendations.append("Investigate cause of increasing metric")
                status = "warning"
            elif trend < 0:
                findings.append(f"Downward trend: {trend:.1f} over {len(self._values)} samples")

        return AgentReport(
            agent_id=self.agent_id,
            name=self.name,
            executed_at=datetime.utcnow(),
            status=status,
            findings=findings,
            recommendations=recommendations,
            metrics={"sample_count": len(self._values)},
        )
