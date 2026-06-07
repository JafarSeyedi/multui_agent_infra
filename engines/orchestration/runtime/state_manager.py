"""Instance state persistence and recovery helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from threading import Lock
from typing import Any

from engines.storage.event_log.base import LogStorage
from engines.storage.key_value.base import KeyValueStorage
from engines.storage.timeseries.base import TimeSeriesStorage

from ..persistence.runtime_records import (
    STATE_SNAPSHOT_RECORD,
    RuntimeRecordEnvelope,
    deserialize_runtime_record,
    serialize_runtime_record,
    snapshot_payload,
)


@dataclass
class InstanceStateSnapshot:
    """Snapshot of a runtime state entry."""

    instance_id: str
    state: str
    created_at: datetime
    updated_at: datetime
    data: dict[str, Any]


class StateManager:
    """Thread-safe, process-local state store with history for recovery."""

    def __init__(
        self,
        *,
        key_value_storage: KeyValueStorage | None = None,
        time_series_storage: TimeSeriesStorage | None = None,
        log_storage: LogStorage | None = None,
        key_prefix: str = "orchestration:state:",
        measurement: str = "orchestration_runtime_state",
    ) -> None:
        self._states: dict[str, InstanceStateSnapshot] = {}
        self._history: dict[str, list[InstanceStateSnapshot]] = {}
        self._lock = Lock()
        self._key_value_storage = key_value_storage
        self._time_series_storage = time_series_storage
        self._log_storage = log_storage
        self._key_prefix = key_prefix
        self._measurement = measurement

    def get(self, instance_id: str) -> InstanceStateSnapshot | None:
        with self._lock:
            snapshot = self._states.get(instance_id)
            if snapshot is None:
                return None
            return InstanceStateSnapshot(
                instance_id=snapshot.instance_id,
                state=snapshot.state,
                created_at=snapshot.created_at,
                updated_at=snapshot.updated_at,
                data=dict(snapshot.data),
            )

    def set(self, instance_id: str, state: str, *, data: dict[str, Any] | None = None) -> InstanceStateSnapshot:
        now = datetime.utcnow()
        with self._lock:
            existing = self._states.get(instance_id)
            created_at = existing.created_at if existing else now
            snapshot = InstanceStateSnapshot(
                instance_id=instance_id,
                state=state,
                created_at=created_at,
                updated_at=now,
                data=dict(data or {}),
            )
            self._states[instance_id] = snapshot
            self._history.setdefault(instance_id, []).append(snapshot)
            return InstanceStateSnapshot(
                instance_id=snapshot.instance_id,
                state=snapshot.state,
                created_at=snapshot.created_at,
                updated_at=snapshot.updated_at,
                data=dict(snapshot.data),
            )

    async def set_persisted(self, instance_id: str, state: str, *, data: dict[str, Any] | None = None) -> InstanceStateSnapshot:
        snapshot = self.set(instance_id, state, data=data)
        await self.persist_snapshot(snapshot)
        return snapshot

    def delete(self, instance_id: str) -> None:
        with self._lock:
            self._states.pop(instance_id, None)

    def history(self, instance_id: str) -> list[InstanceStateSnapshot]:
        with self._lock:
            return [
                InstanceStateSnapshot(
                    instance_id=item.instance_id,
                    state=item.state,
                    created_at=item.created_at,
                    updated_at=item.updated_at,
                    data=dict(item.data),
                )
                for item in self._history.get(instance_id, [])
            ]

    def clear(self) -> None:
        with self._lock:
            self._states.clear()
            self._history.clear()

    async def persist_snapshot(self, snapshot: InstanceStateSnapshot) -> None:
        """Persist a state snapshot via DSDM serialization and storage adapters."""
        serialized = await serialize_runtime_record(
            STATE_SNAPSHOT_RECORD,
            snapshot_payload(
                snapshot.instance_id,
                snapshot.state,
                snapshot.created_at,
                snapshot.updated_at,
                snapshot.data,
            ),
        )
        if self._key_value_storage is not None:
            await self._key_value_storage.ensure_connected()
            await self._key_value_storage.set(self._snapshot_key(snapshot.instance_id), serialized)

        if self._time_series_storage is not None:
            await self._time_series_storage.ensure_connected()
            await self._time_series_storage.write(
                self._measurement,
                snapshot.updated_at,
                fields={
                    "state": snapshot.state,
                    "payload": serialized,
                    "history_size": len(self._history.get(snapshot.instance_id, [])),
                },
                tags={
                    "instance_id": snapshot.instance_id,
                    "record_type": STATE_SNAPSHOT_RECORD,
                },
            )

        if self._log_storage is not None:
            await self._log_storage.ensure_connected()
            await self._log_storage.log_event(
                "orchestration.state_snapshot",
                {
                    "instance_id": snapshot.instance_id,
                    "state": snapshot.state,
                    "updated_at": snapshot.updated_at.isoformat(),
                    "data": dict(snapshot.data),
                },
            )

    async def load_persisted(self, instance_id: str) -> InstanceStateSnapshot | None:
        """Load persisted snapshot from storage and hydrate the in-memory cache."""
        if self._key_value_storage is None:
            return self.get(instance_id)

        await self._key_value_storage.ensure_connected()
        raw = await self._key_value_storage.get(self._snapshot_key(instance_id))
        if raw is None:
            return self.get(instance_id)

        envelope = deserialize_runtime_record(raw)
        snapshot = self._snapshot_from_envelope(envelope)
        with self._lock:
            self._states[instance_id] = snapshot
            self._history.setdefault(instance_id, []).append(snapshot)
        return self.get(instance_id)

    async def delete_persisted(self, instance_id: str) -> None:
        self.delete(instance_id)
        if self._key_value_storage is not None:
            await self._key_value_storage.ensure_connected()
            await self._key_value_storage.delete(self._snapshot_key(instance_id))

    def _snapshot_key(self, instance_id: str) -> str:
        return f"{self._key_prefix}{instance_id}"

    @staticmethod
    def _snapshot_from_envelope(envelope: RuntimeRecordEnvelope) -> InstanceStateSnapshot:
        payload = envelope.payload
        return InstanceStateSnapshot(
            instance_id=str(payload["instance_id"]),
            state=str(payload["state"]),
            created_at=_parse_datetime(payload.get("created_at")),
            updated_at=_parse_datetime(payload.get("updated_at")),
            data=dict(payload.get("data") or {}),
        )


def _parse_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    return datetime.utcnow()
