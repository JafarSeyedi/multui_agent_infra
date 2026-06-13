from __future__ import annotations

from datetime import datetime
from typing import Any

from engines.orchestration.models.bam_models import AgentReport

from .monitoring_orchestrator import BaseMonitoringAgent


class ThresholdAgent(BaseMonitoringAgent):
    def __init__(
        self,
        agent_id: str,
        name: str,
        threshold: float = 90.0,
    ) -> None:
        super().__init__(agent_id, name)
        self._threshold = threshold
        self._value: float | None = None

    def set_value(self, value: float) -> None:
        self._value = value

    async def execute(self) -> AgentReport:
        findings: list[str] = []
        recommendations: list[str] = []
        status = "success"

        if self._value is not None and self._value > self._threshold:
            findings.append(
                f"Value {self._value} exceeds threshold {self._threshold}"
            )
            recommendations.append(f"Consider investigating metric above {self._threshold}")
            status = "warning"

        return AgentReport(
            agent_id=self.agent_id,
            name=self.name,
            executed_at=datetime.utcnow(),
            status=status,
            findings=findings,
            recommendations=recommendations,
            metrics={"threshold": self._threshold} if self._value is not None else {},
        )
