from __future__ import annotations

import pytest

from engines.storage.factories import CacheStorageFactory
from engines.storage.factories import EventLogStorageFactory
from engines.storage.factories import GraphStorageFactory
from engines.storage.factories import KeyValueStorageFactory
from engines.storage.factories import ObjectStorageFactory
from engines.storage.factories import RelationalStorageFactory
from engines.storage.factories import StreamStorageFactory
from engines.storage.factories import TimeSeriesStorageFactory
from engines.storage.factories import VectorStorageFactory
from engines.storage.factories import create_storage
from engines.storage.factories import register_backend


class TestStorageFactories:
    def test_cache_factory_create_returns_backend(self) -> None:
        backend = CacheStorageFactory.create("memory")
        assert backend is not None

    def test_key_value_factory(self) -> None:
        backend = KeyValueStorageFactory.create("memory")
        assert backend is not None

    def test_vector_factory(self) -> None:
        backend = VectorStorageFactory.create("memory")
        assert backend is not None

    def test_relational_factory_sqlite(self) -> None:
        backend = RelationalStorageFactory.create("sqlite")
        assert backend is not None

    def test_object_factory_filesystem(self) -> None:
        backend = ObjectStorageFactory.create("filesystem")
        assert backend is not None

    def test_event_log_factory_sql(self) -> None:
        backend = EventLogStorageFactory.create("rsyslog")
        assert backend is not None

    def test_graph_factory_neo4j(self) -> None:
        from unittest.mock import MagicMock
        backend = GraphStorageFactory.create("neo4j", uri="bolt://localhost", username="test", password="test")
        assert backend is not None

    def test_stream_factory_memory(self) -> None:
        backend = StreamStorageFactory.create("kafka", bootstrap_servers="localhost:9092")
        assert backend is not None

    def test_timeseries_factory_influx(self) -> None:
        from unittest.mock import MagicMock
        backend = TimeSeriesStorageFactory.create("influx", url="http://localhost", token="t", org="o", bucket="b")
        assert backend is not None

    def test_unknown_backend_fallsback(self) -> None:
        backend = CacheStorageFactory.create("nonexistent")
        assert backend is not None

    def test_create_storage_convenience(self) -> None:
        backend = create_storage("cache", "memory")
        assert backend is not None

    def test_create_storage_unknown_category(self) -> None:
        with pytest.raises(ValueError, match="Unknown storage category"):
            create_storage("nonexistent", "memory")

    def test_known_backends(self) -> None:
        known = CacheStorageFactory.known_backends()
        assert "memory" in known

    def test_register_custom_backend(self) -> None:
        from engines.storage.cache.backends.memory_adapter import InMemoryCacheStorage
        register_backend("cache", "custom_test", InMemoryCacheStorage)
        backend = CacheStorageFactory.create("custom_test")
        assert backend is not None

    def test_register_on_unknown_category(self) -> None:
        with pytest.raises(ValueError, match="Unknown storage category"):
            register_backend("nonexistent", "test", type("Fake", (), {}))

    def test_register_then_create(self) -> None:
        from engines.storage.cache.backends.memory_adapter import InMemoryCacheStorage
        CacheStorageFactory.register("my_custom_cache", InMemoryCacheStorage)
        backend = CacheStorageFactory.create("my_custom_cache")
        assert isinstance(backend, InMemoryCacheStorage)
