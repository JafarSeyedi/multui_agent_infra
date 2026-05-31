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
        from datetime import datetime, timedelta
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        to_delete = [
            iid for iid, inst in self.engine.instances.items()
            if inst.state.value in ("completed", "terminated", "failed")
            and inst.end_time and inst.end_time < cutoff
        ]
        for iid in to_delete:
            await self.engine.delete_instance(iid, "cleanup")
            result.instances_removed += 1
        return result

    async def replay_from_history(self, instance_id: str) -> bool:
        try:
            history_rows = self.engine.history_repository.query(instance_id)
            if not history_rows:
                return False
            snapshot = self.engine.snapshot_manager.restore_latest(instance_id)
            if snapshot:
                instance = self.engine.instances.get(instance_id)
                if instance:
                    for name, value in snapshot.get("variables", {}).items():
                        instance.set_variable(name, value)
                    return True
            return True
        except Exception:
            return False

    async def migrate_instance(self, instance_id: str, target_definition_key: str) -> bool:
        try:
            result = await self.engine.batch_manager.modify_instance(
                instance_id, activity_id=None,
            )
            return result.get("status") == "completed"
        except Exception:
            return False

    async def restart_failed_instance(self, instance_id: str) -> bool:
        try:
            await self.engine.update_instance_state(
                instance_id,
                __import__("engines.orchestration.core.instance", fromlist=["InstanceState"]).InstanceState.ACTIVE,
                reason="admin-restart",
            )
            self.engine.incident_manager.clear_instance_incidents(instance_id)
            return True
        except Exception:
            return False

    async def suspend_instances(
        self, definition_key: str | None = None, instance_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        op = await self.engine.batch_manager.suspend_instances(
            definition_key=definition_key, instance_ids=instance_ids,
        )
        return {"operation_id": op.operation_id, "processed": op.processed_count, "failed": op.failed_count}

    async def resume_instances(
        self, definition_key: str | None = None, instance_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        op = await self.engine.batch_manager.resume_instances(
            definition_key=definition_key, instance_ids=instance_ids,
        )
        return {"operation_id": op.operation_id, "processed": op.processed_count, "failed": op.failed_count}

    async def delete_instances(
        self, definition_key: str | None = None, instance_ids: list[str] | None = None,
        cascade: bool = True,
    ) -> dict[str, Any]:
        op = await self.engine.batch_manager.delete_instances(
            definition_key=definition_key, instance_ids=instance_ids, cascade=cascade,
        )
        return {"operation_id": op.operation_id, "processed": op.processed_count, "failed": op.failed_count}

    def get_batch_operations(
        self, operation_type: str | None = None, limit: int = 50,
    ) -> list[dict[str, Any]]:
        ops = self.engine.batch_manager.list_operations(operation_type=operation_type)
        return [
            {
                "operation_id": op.operation_id, "type": op.operation_type,
                "status": op.status, "total": op.total_count,
                "processed": op.processed_count, "failed": op.failed_count,
                "created_at": op.created_at,
            }
            for op in ops[:limit]
        ]

    def get_engine_health(self) -> dict[str, Any]:
        return {
            "engine_state": self.engine.state.value,
            "active_instances": len(self.engine.active_instances),
            "suspended_instances": len(self.engine.suspended_instances),
            "total_definitions": len(self.engine.definitions),
            "total_deployments": len(self.engine.deployments),
            "incidents": self.engine.incident_manager.get_statistics(),
            "external_tasks": self.engine.external_task_manager.get_statistics(),
            "health": self.engine.metrics_collector.get_overall_health(),
        }
