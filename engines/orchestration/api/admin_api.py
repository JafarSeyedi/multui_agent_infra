"""Administrative helper endpoints for maintenance operations."""

from __future__ import annotations

from dataclasses import dataclass

from ..core.engine import OrchestrationEngine


@dataclass(frozen=True)
class AdminAPI:
    engine: OrchestrationEngine

    def cleanup(self) -> None:
        self.engine.cleanup_inactive_instances()

    def stats(self) -> dict[str, object]:
        return {
            "instances": len(self.engine.instances),
            "active_instances": len(self.engine.active_instances),
            "suspended_instances": len(self.engine.suspended_instances),
            "deployments": len(self.engine.deployments),
            "definitions": len(self.engine.definitions),
        }
