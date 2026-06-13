from __future__ import annotations

from datetime import datetime
from typing import Any

from engines.orchestration.models.bam_models import AgentReport

from .monitoring_orchestrator import BaseMonitoringAgent


class AnomalyAgent(BaseMonitoringAgent):
    def __init__(
        self,
        agent_id: str,
        name: str,
        stddev_multiplier: float = 2.0,
    ) -> None:
        super().__init__(agent_id, name)
        self._stddev_mult = stddev_multiplier
        self._values: list[float] = []

    def set_values(self, values: list[float]) -> None:
        self._values = values

    async def execute(self) -> AgentReport:
        findings: list[str] = []
        recommendations: list[str] = []
        status = "success"

        if len(self._values) >= 3:
            import statistics
            try:
                mean = statistics.mean(self._values)
                stdev = statistics.stdev(self._values) if len(self._values) >= 2 else 0
                threshold = stdev * self._stddev_mult
                anomalies = [v for v in self._values if abs(v - mean) > threshold]
                if anomalies:
                    findings.append(f"Detected {len(anomalies)} anomalous values (>{self._stddev_mult}σ)")
                    recommendations.append("Review anomaly detection parameters")
                    status = "warning"
            except statistics.StatisticsError:
                pass

        return AgentReport(
            agent_id=self.agent_id,
            name=self.name,
            executed_at=datetime.utcnow(),
            status=status,
            findings=findings,
            recommendations=recommendations,
            metrics={"stddev_multiplier": self._stddev_mult},
        )
