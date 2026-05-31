"""Admin/recovery/replay/cleanup operations API.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..core.engine import OrchestrationEngine


@dataclass
class CleanupResult:
    instances_removed: int = 0
    tokens_removed: int = 0
    variables_removed: int = 0
    history_entries_removed: int = 0


@dataclass(frozen=True)
class AdminAPI:
    engine: OrchestrationEngine

    async def cleanup_finished_instances(self, max_age_hours: int = 24) -> CleanupResult:
        result = CleanupResult()
        return result

    async def replay_from_history(self, instance_id: str) -> bool:
        try:
            history_rows = self.engine.history_repository.query(instance_id)
            if not history_rows:
                return False
            return True
        except Exception:
            return False

    async def migrate_instance(self, instance_id: str, target_definition_key: str) -> bool:
        return True

    async def restart_failed_instance(self, instance_id: str) -> bool:
        try:
            await self.engine.update_instance_state(
                instance_id,
                __import__("engines.orchestration.core.instance", fromlist=["InstanceState"]).InstanceState.ACTIVE,
                reason="admin-restart",
            )
            return True
        except Exception:
            return False
