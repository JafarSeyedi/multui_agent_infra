"""Primary orchestration API facade around core engine control.

Exposes engine lifecycle, health, and registry operations.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ..core.engine import OrchestrationEngine, EngineState
from ..core.instance import InstanceState


logger = logging.getLogger(__name__)


@dataclass
class HealthStatus:
    status: str = "healthy"
    engine_state: str = "running"
    active_instances: int = 0
    suspended_instances: int = 0
    deployments: int = 0
    uptime_seconds: float = 0.0
    checks: dict[str, bool] = field(default_factory=dict)


@dataclass(frozen=True)
class EngineAPI:
    engine: OrchestrationEngine

    async def start(self) -> None:
        await self.engine.start()

    async def stop(self) -> None:
        await self.engine.stop()

    async def pause(self) -> None:
        await self.engine.pause()

    async def resume(self) -> None:
        await self.engine.resume()

    def is_running(self) -> bool:
        return self.engine.state == "running"

    def get_state(self) -> str:
        return self.engine.state

    def get_health(self) -> HealthStatus:
        active = len(self.engine.active_instances) if hasattr(self.engine, "active_instances") else 0
        suspended = len(self.engine.suspended_instances) if hasattr(self.engine, "suspended_instances") else 0
        deployments = len(self.engine.deployments) if hasattr(self.engine, "deployments") else 0

        checks: dict[str, bool] = {
            "engine_running": self.is_running(),
            "scheduler_ok": self.engine.scheduler is not None,
            "state_manager_ok": self.engine.state_manager is not None,
            "token_manager_ok": self.engine.token_manager is not None,
            "variable_manager_ok": self.engine.variable_manager is not None,
            "correlation_ok": self.engine.correlation_engine is not None,
        }

        status = "healthy" if all(checks.values()) else "degraded"

        return HealthStatus(
            status=status,
            engine_state=self.engine.state,
            active_instances=active,
            suspended_instances=suspended,
            deployments=deployments,
            checks=checks,
        )

    def get_statistics(self) -> dict[str, Any]:
        return {
            "engine_state": self.engine.state,
            "active_instances": len(self.engine.active_instances) if hasattr(self.engine, "active_instances") else 0,
            "suspended_instances": len(self.engine.suspended_instances) if hasattr(self.engine, "suspended_instances") else 0,
            "deployments": len(self.engine.deployments) if hasattr(self.engine, "deployments") else 0,
            "definitions": len(self.engine.definitions) if hasattr(self.engine, "definitions") else 0,
            "registered_handlers": (
                list(self.engine.engine_handlers.keys())
                if hasattr(self.engine, "engine_handlers") else []
            ),
        }
