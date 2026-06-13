from __future__ import annotations

import logging
from abc import ABC
from abc import abstractmethod
from typing import Any

from engines.storage.base_storage import BaseStorage

logger = logging.getLogger(__name__)

StorageT = Any


def _register_builtins() -> None:
    """Seed the registry with known built-in backends."""
    from engines.storage.cache.backends.memory_adapter import InMemoryCacheStorage
    from engines.storage.cache.backends.redis_adapter import RedisCacheStorage
    CacheStorageFactory.register("memory", InMemoryCacheStorage)  # type: ignore[arg-type]
    CacheStorageFactory.register("redis", RedisCacheStorage)  # type: ignore[arg-type]

    from engines.storage.key_value.backends.memory_adapter import InMemoryKeyValueStorage
    from engines.storage.key_value.backends.redis_adapter import RedisStorageAdapter
    KeyValueStorageFactory.register("memory", InMemoryKeyValueStorage)
    KeyValueStorageFactory.register("redis", RedisStorageAdapter)

    from engines.storage.relational.backends.sqlite_adapter import SQLiteStorageAdapter
    from engines.storage.relational.backends.postgres_adapter import PostgresStorageAdapter
    from engines.storage.relational.backends.mysql_adapter import MySQLStorageAdapter
    from engines.storage.relational.backends.sql_server_adapter import SQLServerStorageAdapter
    RelationalStorageFactory.register("sqlite", SQLiteStorageAdapter)
    RelationalStorageFactory.register("postgres", PostgresStorageAdapter)
    RelationalStorageFactory.register("mysql", MySQLStorageAdapter)
    RelationalStorageFactory.register("sql_server", SQLServerStorageAdapter)

    from engines.storage.vector.backends.memory_adapter import InMemoryVectorStore
    from engines.storage.vector.backends.chroma_adapter import ChromaAdapter
    from engines.storage.vector.backends.faiss_adapter import FaissAdapter
    from engines.storage.vector.backends.qdrant_adapter import QdrantAdapter
    VectorStorageFactory.register("memory", InMemoryVectorStore)
    VectorStorageFactory.register("chroma", ChromaAdapter)
    VectorStorageFactory.register("faiss", FaissAdapter)
    VectorStorageFactory.register("qdrant", QdrantAdapter)

    from engines.storage.object.backends.filesystem_adapter import LocalFileAdapter
    from engines.storage.object.backends.s3_adapter import S3Adapter
    ObjectStorageFactory.register("filesystem", LocalFileAdapter)
    ObjectStorageFactory.register("s3", S3Adapter)

    from engines.storage.event_log.backends.sql_event_log import SqlLogStorage
    from engines.storage.event_log.backends.rsyslog import RSyslogStorage
    EventLogStorageFactory.register("sql", SqlLogStorage)
    EventLogStorageFactory.register("rsyslog", RSyslogStorage)

    from engines.storage.stream.backends.redis_stream_adapter import RedisManagerStream, RedisStreamAdapter
    from engines.storage.stream.backends.kafka_adapter import KafkaStreamAdapter
    StreamStorageFactory.register("memory", RedisStreamAdapter)
    StreamStorageFactory.register("kafka", KafkaStreamAdapter)

    from engines.storage.timeseries.backends.influx_adapter import InfluxDBStorageAdapter
    TimeSeriesStorageFactory.register("influx", InfluxDBStorageAdapter)

    from engines.storage.graph.backends.neo4j_adapter import Neo4jAdapter
    GraphStorageFactory.register("neo4j", Neo4jAdapter)


class StorageFactory(ABC):
    """Abstract Factory — creates storage backends by category + name."""

    _registry: dict[str, type[StorageT]] = {}

    @classmethod
    def register(cls, name: str, backend_cls: type[StorageT]) -> None:
        cls._registry[f"{cls.category()}:{name}"] = backend_cls

    @classmethod
    @abstractmethod
    def category(cls) -> str:
        ...

    @classmethod
    def create(cls, backend: str = "memory", **kwargs: Any) -> StorageT:
        key = f"{cls.category()}:{backend}"
        if key in cls._registry:
            return cls._registry[key](**kwargs)
        if backend == "memory":
            return cls._create_default(**kwargs)
        logger.warning("Unknown backend '%s' for %s, using default", backend, cls.category())
        return cls._create_default(**kwargs)

    @classmethod
    @abstractmethod
    def _create_default(cls, **kwargs: Any) -> StorageT:
        ...

    @classmethod
    def known_backends(cls) -> list[str]:
        prefix = f"{cls.category()}:"
        return sorted(k[len(prefix):] for k in cls._registry if k.startswith(prefix))


class CacheStorageFactory(StorageFactory):
    category_name = "cache"

    @classmethod
    def category(cls) -> str:
        return cls.category_name

    @classmethod
    def _create_default(cls, **kwargs: Any) -> StorageT:
        from engines.storage.cache.backends.memory_adapter import InMemoryCacheStorage
        return InMemoryCacheStorage(**kwargs)


class EventLogStorageFactory(StorageFactory):
    category_name = "event_log"

    @classmethod
    def category(cls) -> str:
        return cls.category_name

    @classmethod
    def _create_default(cls, **kwargs: Any) -> StorageT:
        from engines.storage.event_log.backends.sql_event_log import SqlLogStorage
        return SqlLogStorage(**kwargs)


class GraphStorageFactory(StorageFactory):
    category_name = "graph"

    @classmethod
    def category(cls) -> str:
        return cls.category_name

    @classmethod
    def _create_default(cls, **kwargs: Any) -> StorageT:
        from engines.storage.graph.backends.neo4j_adapter import Neo4jAdapter
        return Neo4jAdapter(**kwargs)


class KeyValueStorageFactory(StorageFactory):
    category_name = "key_value"

    @classmethod
    def category(cls) -> str:
        return cls.category_name

    @classmethod
    def _create_default(cls, **kwargs: Any) -> StorageT:
        from engines.storage.key_value.backends.memory_adapter import InMemoryKeyValueStorage
        return InMemoryKeyValueStorage(**kwargs)


class ObjectStorageFactory(StorageFactory):
    category_name = "object"

    @classmethod
    def category(cls) -> str:
        return cls.category_name

    @classmethod
    def _create_default(cls, **kwargs: Any) -> StorageT:
        from engines.storage.object.backends.filesystem_adapter import LocalFileAdapter
        return LocalFileAdapter(**kwargs)


class RelationalStorageFactory(StorageFactory):
    category_name = "relational"

    @classmethod
    def category(cls) -> str:
        return cls.category_name

    @classmethod
    def _create_default(cls, **kwargs: Any) -> StorageT:
        from engines.storage.relational.backends.sqlite_adapter import SQLiteStorageAdapter
        return SQLiteStorageAdapter(**kwargs)


class StreamStorageFactory(StorageFactory):
    category_name = "stream"

    @classmethod
    def category(cls) -> str:
        return cls.category_name

    @classmethod
    def _create_default(cls, **kwargs: Any) -> StorageT:
        from engines.storage.stream.backends.redis_stream_adapter import RedisStreamAdapter
        return RedisStreamAdapter(**kwargs)


class TimeSeriesStorageFactory(StorageFactory):
    category_name = "timeseries"

    @classmethod
    def category(cls) -> str:
        return cls.category_name

    @classmethod
    def _create_default(cls, **kwargs: Any) -> StorageT:
        from engines.storage.timeseries.backends.influx_adapter import InfluxDBStorageAdapter
        return InfluxDBStorageAdapter(**kwargs)


class VectorStorageFactory(StorageFactory):
    category_name = "vector"

    @classmethod
    def category(cls) -> str:
        return cls.category_name

    @classmethod
    def _create_default(cls, **kwargs: Any) -> StorageT:
        from engines.storage.vector.backends.memory_adapter import InMemoryVectorStore
        return InMemoryVectorStore(**kwargs)


# Seed registry with built-in backends
_register_builtins()

# Registry — map category to factory
_STORAGE_FACTORIES: dict[str, type[StorageFactory]] = {
    "cache": CacheStorageFactory,
    "event_log": EventLogStorageFactory,
    "graph": GraphStorageFactory,
    "key_value": KeyValueStorageFactory,
    "object": ObjectStorageFactory,
    "relational": RelationalStorageFactory,
    "stream": StreamStorageFactory,
    "timeseries": TimeSeriesStorageFactory,
    "vector": VectorStorageFactory,
}


def create_storage(category: str, backend: str = "memory", **kwargs: Any) -> StorageT:
    """Convenience entry point — picks the right factory by category."""
    factory_cls = _STORAGE_FACTORIES.get(category)
    if factory_cls is None:
        raise ValueError(
            f"Unknown storage category '{category}'. "
            f"Available: {list(_STORAGE_FACTORIES.keys())}"
        )
    return factory_cls.create(backend=backend, **kwargs)


def register_backend(category: str, name: str, backend_cls: type[StorageT]) -> None:
    """Register a custom backend for a given category."""
    factory_cls = _STORAGE_FACTORIES.get(category)
    if factory_cls is None:
        raise ValueError(f"Unknown storage category '{category}'")
    factory_cls.register(name, backend_cls)
