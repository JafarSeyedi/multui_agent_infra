"""State snapshot and crash recovery for orchestration runtime.

Supports state snapshot creation/restore per Kestra/Orch8/Stormchaser patterns.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


logger = logging.getLogger(__name__)


@dataclass
class StateSnapshot:
    snapshot_id: str
    instance_id: str
    engine_id: str
    state_hash: str = ""
    process_state: dict[str, Any] = field(default_factory=dict)
    variables: dict[str, Any] = field(default_factory=dict)
    tokens: list[dict[str, Any]] = field(default_factory=list)
    current_activity_id: str | None = None
    created_at: str = ""
    version: int = 1
    checkpoint_type: str = "auto"

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()

    def compute_hash(self) -> str:
        import hashlib, json
        data = json.dumps({"vars": self.variables, "tokens": self.tokens, "activity": self.current_activity_id}, sort_keys=True)
        self.state_hash = hashlib.sha256(data.encode()).hexdigest()
        return self.state_hash


@dataclass
class CheckpointConfig:
    enabled: bool = True
    auto_checkpoint_interval_seconds: int = 30
    checkpoint_on_activity_start: bool = True
    checkpoint_on_activity_complete: bool = True
    checkpoint_on_variable_change: bool = False
    checkpoint_on_error: bool = True
    max_snapshots_per_instance: int = 100
    persist_to_storage: bool = True


class StateSnapshotManager:
    def __init__(self, config: CheckpointConfig | None = None) -> None:
        self._config = config or CheckpointConfig()
        self._snapshots: dict[str, list[StateSnapshot]] = {}
        self._latest: dict[str, StateSnapshot] = {}

    def create_snapshot(
        self,
        instance_id: str,
        process_state: dict[str, Any],
        variables: dict[str, Any],
        tokens: list[dict[str, Any]],
        current_activity_id: str | None = None,
        engine_id: str = "",
        checkpoint_type: str = "auto",
    ) -> StateSnapshot:
        from uuid import uuid4
        snapshot = StateSnapshot(
            snapshot_id=str(uuid4()),
            instance_id=instance_id,
            engine_id=engine_id,
            process_state=process_state,
            variables=dict(variables),
            tokens=list(tokens),
            current_activity_id=current_activity_id,
            checkpoint_type=checkpoint_type,
        )
        snapshot.compute_hash()

        if instance_id not in self._snapshots:
            self._snapshots[instance_id] = []
        self._snapshots[instance_id].append(snapshot)
        self._latest[instance_id] = snapshot

        max_count = self._config.max_snapshots_per_instance
        if len(self._snapshots[instance_id]) > max_count:
            self._snapshots[instance_id] = self._snapshots[instance_id][-max_count:]

        logger.debug("Snapshot created: %s for instance %s (type=%s)",
                      snapshot.snapshot_id[:8], instance_id, checkpoint_type)
        return snapshot

    def get_latest_snapshot(self, instance_id: str) -> StateSnapshot | None:
        return self._latest.get(instance_id)

    def get_snapshots(self, instance_id: str) -> list[StateSnapshot]:
        return list(self._snapshots.get(instance_id, []))

    def restore_from_snapshot(self, snapshot: StateSnapshot) -> dict[str, Any]:
        logger.info("Restoring instance %s from snapshot %s",
                     snapshot.instance_id, snapshot.snapshot_id[:8])
        return {
            "instance_id": snapshot.instance_id,
            "process_state": dict(snapshot.process_state),
            "variables": dict(snapshot.variables),
            "tokens": list(snapshot.tokens),
            "current_activity_id": snapshot.current_activity_id,
            "version": snapshot.version,
        }

    def restore_latest(self, instance_id: str) -> dict[str, Any] | None:
        snapshot = self._latest.get(instance_id)
        if snapshot is None:
            return None
        return self.restore_from_snapshot(snapshot)

    def clear_instance_snapshots(self, instance_id: str) -> int:
        snapshots = self._snapshots.pop(instance_id, [])
        self._latest.pop(instance_id, None)
        return len(snapshots)

    def compare_snapshots(self, snapshot_a: StateSnapshot, snapshot_b: StateSnapshot) -> dict[str, bool]:
        return {
            "same_variables": snapshot_a.variables == snapshot_b.variables,
            "same_tokens": snapshot_a.tokens == snapshot_b.tokens,
            "same_activity": snapshot_a.current_activity_id == snapshot_b.current_activity_id,
            "same_hash": snapshot_a.state_hash == snapshot_b.state_hash,
        }

    def get_statistics(self) -> dict[str, Any]:
        total = sum(len(s) for s in self._snapshots.values())
        return {
            "total_snapshots": total,
            "instances_with_snapshots": len(self._snapshots),
            "latest_snapshots": len(self._latest),
        }
