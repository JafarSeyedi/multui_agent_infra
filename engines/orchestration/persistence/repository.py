"""Generic persistence interfaces used by runtime and engines."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from threading import Lock
from typing import Any

from engines.storage.event_log.base import LogStorage
from engines.storage.key_value.base import KeyValueStorage
from engines.storage.timeseries.base import TimeSeriesStorage

from ..runtime.runtime_records import deserialize_runtime_record, normalize_runtime_payload, serialize_runtime_record

PredicateFn = Callable[[dict[str, Any]], bool]
FilterFn = PredicateFn


@dataclass(frozen=True)
class RepositoryError(RuntimeError):
    """Repository-specific error."""


class RepositoryProtocol:
    """Small, explicit interface for document/instance stores."""

    def save(self, key: str, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def get(self, key: str) -> dict[str, Any] | None:
        raise NotImplementedError

    def delete(self, key: str) -> bool:
        raise NotImplementedError

    def list(self, *, predicate: FilterFn | None = None) -> list[dict[str, Any]]:
        raise NotImplementedError


class InMemoryRepository(RepositoryProtocol):
    """Thread-safe dictionary-backed repository useful for tests and single-process deploys."""

    def __init__(self) -> None:
        self._data: dict[str, dict[str, Any]] = {}
        self._lock = Lock()

    def save(self, key: str, payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            self._data[key] = dict(payload)
            return dict(payload)

    def get(self, key: str) -> dict[str, Any] | None:
        with self._lock:
            value = self._data.get(key)
            return dict(value) if value is not None else None

    def delete(self, key: str) -> bool:
        with self._lock:
            return self._data.pop(key, None) is not None

    def list(self, *, predicate: FilterFn | None = None) -> list[dict[str, Any]]:
        with self._lock:
            items = [dict(v) for v in self._data.values()]
        if predicate is None:
            return items
        return [item for item in items if predicate(item)]

    def clear(self) -> None:
        with self._lock:
            self._data.clear()


class PersistentRuntimeRepository(InMemoryRepository):
    """Repository with optional storage-backed persistence using runtime record serialization."""

    def __init__(
        self,
        *,
        record_type: str,
        key_value_storage: KeyValueStorage | None = None,
        time_series_storage: TimeSeriesStorage | None = None,
        log_storage: LogStorage | None = None,
        key_prefix: str = "orchestration:records:",
        measurement: str = "orchestration_runtime_records",
    ) -> None:
        super().__init__()
        self.record_type = record_type
        self.key_value_storage = key_value_storage
        self.time_series_storage = time_series_storage
        self.log_storage = log_storage
        self.key_prefix = key_prefix
        self.measurement = measurement

    async def save_persisted(self, key: str, payload: dict[str, Any]) -> dict[str, Any]:
        normalized = normalize_runtime_payload(self.record_type, payload)
        saved = self.save(key, normalized)
        serialized = await serialize_runtime_record(self.record_type, normalized)
        await self._write_storage(key, saved, serialized)
        return saved

    async def get_persisted(self, key: str) -> dict[str, Any] | None:
        cached = self.get(key)
        if cached is not None:
            return cached
        if self.key_value_storage is None:
            return None

        await self.key_value_storage.ensure_connected()
        raw = await self.key_value_storage.get(self._storage_key(key))
        if raw is None:
            return None
        payload = deserialize_runtime_record(raw).payload
        return self.save(key, payload)

    async def delete_persisted(self, key: str) -> bool:
        deleted = self.delete(key)
        if self.key_value_storage is not None:
            await self.key_value_storage.ensure_connected()
            await self.key_value_storage.delete(self._storage_key(key))
        return deleted

    async def _write_storage(self, key: str, payload: dict[str, Any], serialized: str) -> None:
        if self.key_value_storage is not None:
            await self.key_value_storage.ensure_connected()
            await self.key_value_storage.set(self._storage_key(key), serialized)

        if self.time_series_storage is not None:
            await self.time_series_storage.ensure_connected()
            timestamp = _parse_timestamp(payload)
            await self.time_series_storage.write(
                self.measurement,
                timestamp,
                fields={
                    "payload": serialized,
                    "record_type": self.record_type,
                    "state": str(payload.get("state", "")),
                },
                tags={
                    "key": key,
                    "record_type": self.record_type,
                    "instance_id": str(payload.get("instance_id", "")),
                },
            )

        if self.log_storage is not None:
            await self.log_storage.ensure_connected()
            await self.log_storage.log_event(f"orchestration.repository.{self.record_type}", dict(payload))

    def _storage_key(self, key: str) -> str:
        return f"{self.key_prefix}{key}"


def _parse_timestamp(payload: dict[str, Any]) -> datetime:
    for candidate in ("updated_at", "created_at", "recorded_at"):
        value = payload.get(candidate)
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                continue
    return datetime.utcnow()
