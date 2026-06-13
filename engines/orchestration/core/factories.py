"""Abstract Factory for storage backends.

Allows the orchestration engine to be configured with different
storage backends (memory, SQL, file, etc.) without coupling
to concrete implementations.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from ..._types import Metadata, RawData

logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    """Abstract storage backend interface."""

    @abstractmethod
    async def save(self, collection: str, key: str, value: RawData) -> None:
        ...

    @abstractmethod
    async def load(self, collection: str, key: str) -> RawData | None:
        ...

    @abstractmethod
    async def delete(self, collection: str, key: str) -> None:
        ...

    @abstractmethod
    async def list(self, collection: str) -> list[RawData]:
        ...

    @abstractmethod
    async def clear(self, collection: str) -> None:
        ...


class InMemoryBackend(StorageBackend):
    """In-memory dict-based storage backend."""

    def __init__(self) -> None:
        self._stores: dict[str, dict[str, RawData]] = {}

    async def save(self, collection: str, key: str, value: RawData) -> None:
        if collection not in self._stores:
            self._stores[collection] = {}
        self._stores[collection][key] = value

    async def load(self, collection: str, key: str) -> RawData | None:
        return self._stores.get(collection, {}).get(key)

    async def delete(self, collection: str, key: str) -> None:
        self._stores.get(collection, {}).pop(key, None)

    async def list(self, collection: str) -> list[RawData]:
        return list(self._stores.get(collection, {}).values())

    async def clear(self, collection: str) -> None:
        self._stores.pop(collection, None)


class StorageBackendFactory(ABC):
    """Abstract factory for creating storage backends."""

    @abstractmethod
    def create_backend(self, config: Metadata | None = None) -> StorageBackend:
        ...

    @classmethod
    def for_type(cls, backend_type: str) -> StorageBackend:
        registry: dict[str, type[StorageBackendFactory]] = {
            "memory": MemoryBackendFactory,
            "sql": SQLBackendFactory,
            "file": FileBackendFactory,
        }
        factory_cls = registry.get(backend_type)
        if not factory_cls:
            logger.warning("Unknown storage backend '%s', falling back to memory", backend_type)
            factory_cls = MemoryBackendFactory
        return factory_cls().create_backend()

    @classmethod
    def register(cls, backend_type: str, factory: type[StorageBackendFactory]) -> None:
        registry = cls._get_registry()
        registry[backend_type] = factory

    @staticmethod
    def _get_registry() -> dict[str, type]:
        return {"memory": MemoryBackendFactory}

    @classmethod
    def all_types(cls) -> list[str]:
        return list(cls._get_registry().keys())


class MemoryBackendFactory(StorageBackendFactory):
    def create_backend(self, config: Metadata | None = None) -> StorageBackend:
        return InMemoryBackend()


class SQLBackendFactory(StorageBackendFactory):
    def create_backend(self, config: Metadata | None = None) -> StorageBackend:
        try:
            from engines.storage.sql_storage import SQLStorage  # type: ignore[import-not-found]
            instance = SQLStorage(str(config.get("db_path", "engine.db")) if config else "engine.db")
            return _SQLBackendAdapter(instance)
        except ImportError:
            logger.error("SQL storage is not available, falling back to in-memory")
            return InMemoryBackend()


class FileBackendFactory(StorageBackendFactory):
    def create_backend(self, config: Metadata | None = None) -> StorageBackend:
        try:
            from engines.storage.file_storage import FileStorage  # type: ignore[import-not-found]
            instance = FileStorage(str(config.get("base_path", "./data")) if config else "./data")
            return _FileBackendAdapter(instance)
        except ImportError:
            logger.error("File storage is not available, falling back to in-memory")
            return InMemoryBackend()


class _SQLBackendAdapter(StorageBackend):
    def __init__(self, wrapped: Any) -> None:  # duck-typed
        self._wrapped = wrapped

    async def save(self, collection: str, key: str, value: RawData) -> None:
        self._wrapped.save(collection + "_" + key, value)

    async def load(self, collection: str, key: str) -> RawData | None:
        result = self._wrapped.get(collection + "_" + key)
        return result if result else None

    async def delete(self, collection: str, key: str) -> None:
        self._wrapped.delete(collection + "_" + key)

    async def list(self, collection: str) -> list[RawData]:
        return list(self._wrapped.list(collection))

    async def clear(self, collection: str) -> None:
        for key in list(self._wrapped.list(collection)):
            self._wrapped.delete(key)


class _FileBackendAdapter(StorageBackend):
    def __init__(self, wrapped: Any) -> None:  # duck-typed
        self._wrapped = wrapped

    async def save(self, collection: str, key: str, value: RawData) -> None:
        self._wrapped.save(collection, key, value)

    async def load(self, collection: str, key: str) -> RawData | None:
        return self._wrapped.load(collection, key)

    async def delete(self, collection: str, key: str) -> None:
        self._wrapped.delete(collection, key)

    async def list(self, collection: str) -> list[RawData]:
        return self._wrapped.list(collection)

    async def clear(self, collection: str) -> None:
        self._wrapped.clear(collection)
