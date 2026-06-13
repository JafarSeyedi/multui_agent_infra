# Storage Engine — Rust Migration Analysis

**Source:** `engines/storage/`
**Date:** 2026-06-13
**Scope:** 46 Python files across 9 storage categories + factory + proxy layers

---

## 1. Pre-refactor Analysis

### `Any` usage: 30 occurrences
- `base_storage.py`: 3 (`__aexit__` exc_type, exc, tb)
- `factories.py`: 12 (`**kwargs: Any` on all factory methods, `StorageT = Any`)
- `proxies.py`: 4 (value params, factory_kwargs, `__getattr__`)
- `cache/base.py`: 1 (`value: Any`)
- `cache/backends/memory_adapter.py`: 1 (`value: Any`)
- `cache/backends/redis_adapter.py`: 1 (`value: Any`)
- `key_value/base.py`: 1 (`value: Any`)
- `key_value/backends/memory_adapter.py`: 1 (`value: Any`)
- `key_value/backends/redis_adapter.py`: 1 (`value: Any`)
- `relational/implementors.py`: 2 (`_engine`, `_connection`)
- `timeseries/backends/influx_adapter.py`: 3 (`_client`, `_write_api`, `_query_api`)
- `vector/backends/faiss_adapter.py`: 1 (`self.index`)
- `stream/backends/kafka_adapter.py`: 1 (`_producer`)

### `dict[str, Any]` usage: 74 occurrences
- Heaviest: `vector/backends/*.py` (32), `relational/backends/*.py` (12), `key_value/backends/redis_adapter.py` (3), `graph/backends/neo4j_adapter.py` (5)
- **Critical**: Most abstract method signatures use `dict[str, Any]` — would become `HashMap<String, Value>` or generic `BTreeMap` in Rust

### `isinstance` usage: 15 occurrences
- `redis_adapter.py:131` — `isinstance(value, (dict, list))` for serialization branching
- `redis_stream_adapter.py:137` — `isinstance(value, (dict, list, str, int, float))` for payload normalization
- `chroma_adapter.py:31-37` — `isinstance(v, (bool, int, float, str))` for metadata sanitization
- `qdrant_adapter.py:122-151` — `isinstance(value, (bool, int, float, str, dict))` for filter construction
- `faiss_adapter.py:99` — `isinstance(self.index, faiss.IndexIVFFlat)`
- `pinecone_adapter.py:144` — `isinstance(value, dict)`

### `hasattr` usage: 10 occurrences
- `proxies.py:105,116,121,125` — duck-typing proxy delegation
- `implementors.py:130,139` — row factory detection
- `redis_adapter.py:115`, `redis_stream_adapter.py:115`, `cache/backends/redis_adapter.py:35` — awaitable detection

### ABCs/abstractmethod: 14 ABC classes, 45 abstract methods
| Class | File | Methods |
|-------|------|---------|
| `BaseStorage` | `base_storage.py` | 0 abstract (concrete lifecycle) |
| `StorageFactory` | `factories.py` | `category()`, `_create_default()` |
| `CacheStorage` | `cache/base.py` | `set`, `get`, `delete`, `exists`, `list_keys` |
| `KeyValueStorage` | `key_value/base.py` | `set`, `get`, `delete`, `exists`, `list_keys` |
| `RelationalStorage` | `relational/base.py` | `execute`, `fetch_one`, `fetch_all` |
| `RelationalImplementor` | `relational/implementors.py` | `connect`, `disconnect`, `health`, `execute`, `fetch_one`, `fetch_all` |
| `VectorDBAdapter` | `vector/base.py` | `create_index`, `upsert`, `batch_upsert`, `query`, `delete` |
| `VectorStorage` | `vector/base.py` | `upsert`, `delete`, `query` |
| `StreamStorage` | `stream/base.py` | `publish`, `consume` |
| `ObjectStorage` | `object/base.py` | `put`, `get`, `delete`, `exists`, `generate_url` |
| `GraphStorage` | `graph/base.py` | `add_node`, `add_edge`, `query` |
| `LogStorage` | `event_log/base.py` | `log_agent_execution`, `list_agent_logs`, `get_agent_log`, `log_event`, `list_events`, `get_event` |
| `TimeSeriesStorage` | `timeseries/base.py` | `write`, `query` |
| `SQLStorage` | `relational/base.py` | 0 abstract (concrete aiosqlite) |

---

## 2. Migration Notes (Score 1-5)

| Component | Score | Rationale |
|-----------|-------|-----------|
| **Trait definitions** (all ABCs) | *N/A* | Interface definitions — not migratable alone, define Rust trait targets |
| **InMemoryCacheStorage** | **5** | Pure `dict[str, tuple[Any, float]]` + TTL loop |
| **InMemoryKeyValueStorage** | **5** | Pure `dict[str, Any]` |
| **InMemoryVectorStore** | **4** | numpy cosine similarity — ndarray → `ndarray` crate, numpy → linfa/ndarray |
| **LocalFileAdapter** | **4** | `asyncio.to_thread(pathlib ops)` → `tokio::fs` |
| **NullStorage** | **5** | Trivial no-op |
| **LazyInitStorageProxy** | **3** | Proxy pattern — `Box<dyn>` + `OnceCell` |
| **CachingStorageProxy** | **3** | `OrderedDict` → `LruCache` |
| **SQLStorage** (aiosqlite) | **3** | `aiosqlite` → `sqlx::Sqlite`, but JSON serialization stays |
| **BridgeRelationalStorage + Implementors** | **2** | Bridge pattern — SQLAlchemy async engine dependency |
| **Redis adapters** (cache, kv, stream) | **2** | `redis-py` → `redis-rs`, `ExponentialBackoff` → `backon` |
| **KafkaStreamAdapter** | **1** | `aiokafka` → `rdkafka`, consumer group logic |
| **Postgres/Mysql/SqlServer adapters** | **1** | `sqlalchemy[asyncio]` → `sqlx` |
| **FaissAdapter** | **2** | `faiss` Python lib → `faiss-rs` (thinner binding) |
| **ChromaAdapter** | **1** | `chromadb` Python client — no Rust equivalent, PyO3 bridge |
| **QdrantAdapter** | **2** | `qdrant-client` → qdrant gRPC/REST client in Rust |
| **PineconeAdapter** | **1** | `pinecone` Python SDK → Rust HTTP client |
| **WeaviateAdapter** | **1** | `weaviate-client` Python → Rust HTTP client |
| **Neo4jAdapter** | **2** | `neo4j` Python driver → `neo4rs` |
| **InfluxDBStorageAdapter** | **1** | `influxdb-client` Python → `influxdb2` / `influxdb3` Rust client |
| **S3Adapter** | **2** | `boto3` → `aws-sdk-rust` (S3) |
| **MinioAdapter** | **2** | `minio` Python → `rust-s3` / `aws-sdk-rust` |
| **RSyslogStorage** | **4** | UDP socket send + in-memory dict |
| **SqlLogStorage** | **3** | Delegates to SQLStorage |
| **Factories / Registry** | **3** | `dict[str, type]` → `HashMap<&str, fn() -> Box<dyn Trait>>` |

---

## 3. Ownership Map

```
create_storage()                           # Top-level entry point (factories.py:236)
  └─ _STORAGE_FACTORIES["category"]         # HashMap<&str, StorageFactory> (factories.py:223)
       └─ ConcreteFactory.create(backend)   # 9 factories, each with _registry
            ├─ _registry["category:name"]   # HashMap<String, Type<StorageT>>
            │    └─ Backend class           # Instantiated with **kwargs
            │
            └─ LazyInitStorageProxy        # Optional proxy wrapper (proxies.py:13)
                 └─ CachingStorageProxy     # Optional LRU cache wrapper (proxies.py:59)
                      └─ Backend instance   # Actual storage backend

StorageFactory (ABC)                        # Abstract Factory (factories.py:67)
  Registry pattern: class-level dict holds backend classes
  └─ CacheStorageFactory                    # "cache" → memory, redis
  └─ KeyValueStorageFactory                 # "key_value" → memory, redis
  └─ RelationalStorageFactory               # "relational" → sqlite, postgres, mysql, sql_server
  └─ VectorStorageFactory                   # "vector" → memory, chroma, faiss, qdrant
  └─ ObjectStorageFactory                   # "object" → filesystem, s3 (minio not registered!)
  └─ EventLogStorageFactory                 # "event_log" → sql, rsyslog
  └─ StreamStorageFactory                   # "stream" → memory(redis), kafka
  └─ TimeSeriesStorageFactory               # "timeseries" → influx
  └─ GraphStorageFactory                    # "graph" → neo4j

Proxy chain (factories.py is NOT wrapping in proxies, usage is manual):
  NullStorage                               # Null Object pattern
  LazyInitStorageProxy                      # Deferred creation + connection
  CachingStorageProxy                       # LRU read cache, delegates write-through
```

**NOTABLE:** The `factories.py` does **not** automatically wrap backends in proxies — `_register_builtins()` registers bare classes. Proxies are used manually by callers.

**NOTABLE:** `MinioAdapter` is **not registered** in `_register_builtins()` (factories.py:45-48 only registers `filesystem` and `s3`).

---

## 4. PyO3 Binding Structure

```
                 ┌──────────────────────────────┐
                 │   Rust Trait Definition       │
                 │   pub trait StorageBackend    │
                 │   (connect/disconnect/health)  │
                 └──────────────┬───────────────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                      │
    ┌─────┴──────┐     ┌───────┴───────┐     ┌───────┴───────┐
    │ In-memory  │     │  Rust-native  │     │  PyO3 Bridge  │
    │ (native)   │     │  (sqlx,       │     │  (calls back  │
    │            │     │   redis-rs,   │     │   to Python)  │
    │ Score 4-5  │     │   aws-sdk)    │     │               │
    └────────────┘     │ Score 2-3     │     │  Score 1      │
                       └───────────────┘     └───────────────┘
```

### Layer 1 — Pure Rust (Score 4-5)
- `InMemoryCacheStorage` → `struct InMemoryCache<K, V>` with `HashMap` + TTL
- `InMemoryKeyValueStorage` → `struct InMemoryKv<K, V>` with `HashMap`
- `InMemoryVectorStore` → `struct InMemoryVectorIndex` with `ndarray` cosine similarity
- `LocalFileAdapter` → `struct LocalFileBackend` with `tokio::fs`
- `NullStorage` → `struct NullBackend`
- `RSyslogStorage` → UDP socket in `tokio::net::UdpSocket`

### Layer 2 — Rust-native external (Score 2-3)
- `RedisAdapters` → `redis-rs` async client
- `PostgresStorageAdapter` → `sqlx::PgPool`
- `SQLiteStorageAdapter` → `sqlx::SqlitePool`
- `S3Adapter` → `aws-sdk-s3`
- `MinioAdapter` → `aws-sdk-s3` (S3-compatible)
- Proxy layer → `Box<dyn StorageBackend>`, `OnceCell`, `LruCache`

### Layer 3 — PyO3 bridge (Score 1)
- `ChromaAdapter` → `pyo3` bridge to Python `chromadb`
- `FaissAdapter` → `pyo3` bridge or `faiss-rs` (thin bindings exist)
- `PineconeAdapter` → HTTP client in Rust (gRPC available)
- `WeaviateAdapter` → HTTP/gRPC client in Rust
- `QdrantAdapter` → Qdrant gRPC client in Rust
- `Neo4jAdapter` → `neo4rs` crate
- `InfluxDBStorageAdapter` → `influxdb2` / `influxdb3` crate
- `KafkaStreamAdapter` → `rdkafka` crate

### Trait hierarchy in Rust

```rust
#[async_trait]
pub trait BaseStorage: Send + Sync {
    async fn connect(&mut self) -> Result<()>;
    async fn disconnect(&mut self) -> Result<()>;
    async fn health(&self) -> bool;
    fn is_connected(&self) -> bool;
}

#[async_trait]
pub trait CacheStorage: BaseStorage {
    async fn set(&mut self, key: &str, value: Vec<u8>, ttl: Option<Duration>) -> Result<()>;
    async fn get(&self, key: &str) -> Result<Option<Vec<u8>>>;
    async fn delete(&mut self, key: &str) -> Result<()>;
    async fn exists(&self, key: &str) -> Result<bool>;
    async fn list_keys(&self, prefix: Option<&str>) -> Result<Vec<String>>;
}

// Similar for: KeyValueStorage, RelationalStorage, VectorStorage, ObjectStorage,
// StreamStorage, GraphStorage, TimeSeriesStorage, LogStorage
```

**Key challenge**: `Any` → `Vec<u8>` or generic `<V>` — the Python code freely passes any Python object. Rust requires concrete types or `Box<dyn Any + Send>`.

---

## 5. Libraries Analysis

| Python Library | Rust Equivalent | Status | Notes |
|---|---|---|---|
| `redis` (`redis-py`) | `redis-rs` | ✅ Mature | `redis::AsyncCommands`, `ExponentialBackoff` → `backon` |
| `sqlalchemy[asyncio]` | `sqlx` | ✅ Mature | Connection pool, migration. `diesel` is sync-only |
| `aiosqlite` | `sqlx::Sqlite` | ✅ Mature | `rusqlite` also an option |
| `aiokafka` | `rdkafka` | ✅ Mature | Wraps `librdkafka` C library |
| `faiss` | `faiss-rs` | ⚠️ Beta | Thin unsafe bindings to FAISS C API |
| `chromadb` | — | ❌ None | Requires PyO3 bridge to Python client |
| `qdrant-client` | Qdrant gRPC | ✅ | Official Qdrant gRPC proto + Rust tonic client |
| `pinecone` | HTTP client | ✅ | Pinecone REST/gRPC API |
| `weaviate-client` | HTTP/gRPC client | ✅ | Weaviate v4 API |
| `neo4j` | `neo4rs` | ✅ | Async Bolt protocol driver |
| `motor` (MongoDB) | `mongodb` | ✅ | Official MongoDB Rust driver |
| `minio` | `aws-sdk-s3` / `rust-s3` | ✅ | S3-compatible API |
| `boto3` | `aws-sdk-rust` | ✅ | Official AWS SDK (S3, STS, etc.) |
| `influxdb-client` | `influxdb2` / `influxdb3` | ✅ | Official InfluxDB v2/v3 Rust client |
| `numpy` | `ndarray` | ✅ | Array/tensor ops |
| `numpy` (cosine sim) | `ndarray` + custom | ✅ | Trivial `dot / (norm_a * norm_b)` |
| `json` (stdlib) | `serde_json` | ✅ | Serialization/deserialization |
| `Pathlib` | `std::path` + `tokio::fs` | ✅ | Async file operations |

---

## 6. Performance Hot Paths

### Hot path 1: Cache `get`/`set` (cache/backends/*.py)
- `InMemoryCacheStorage.get` + `_purge_expired()` — O(n) scan on every access
- `CachingStorageProxy.get` — `OrderedDict` move-to-end + backend fallback
- **Rust strategy**: `HashMap` + background TTL sweeper (tokio interval) or `BTreeMap` for ordered expiry

### Hot path 2: Key-value `set`/`get` (key_value/backends/*.py)
- `RedisStorageAdapter.set` — JSON serialization branch (`isinstance(dict, list)`)
- `RedisStorageAdapter.get` — JSON deserialization try/except
- **Rust strategy**: `serde_json::to_vec`/`from_slice`, avoid branching on types

### Hot path 3: Vector similarity search (vector/backends/memory_adapter.py)
- `InMemoryVectorStore.query` — numpy `@` operator (matrix multiply), `np.argsort`
- **Rust strategy**: `ndarray::Array2::dot`, `argsort` via `ndarray-ext` or manual

### Hot path 4: Serialization in stream backends
- `RedisStreamAdapter.publish` — per-field `isinstance` check for JSON serialization
- **Rust strategy**: `serde_json::Value` enum, no isinstance branching

### Hot path 5: `LazyInitStorageProxy.__getattr__` (proxies.py:51)
- Runtime attribute forwarding — eliminated in Rust (compile-time dispatch via traits)

---

## 7. Error Handling

| Python Pattern | Occurrences | Rust Strategy |
|---|---|---|
| `try/except Exception -> return False` | health() methods (10+) | `Result<bool, StorageError>` |
| `try/except ImportError -> raise RuntimeError` | adapater connect() methods | Compile-time cargo deps, no runtime import |
| `assert self.xxx is not None` | postgres/sqlite/neo4j/redis (20+) | `Option<T>` + early return with `?` |
| `raise ValueError("...")` | validation in upsert | `anyhow::bail!` or `Err(StorageError::InvalidInput)` |
| `hasattr(result, "__await__")` | sync/async ping detection | Eliminated — Rust futures are concrete |
| `except Exception: pass` | `RedisStreamAdapter.xgroup_create` | `if let Err(_) = ...` or log + ignore |
| `logger.error("...")` + `raise` | `RedisManager.connect` | `tracing::error!` + `anyhow::Error` |
| Retry: `ExponentialBackoff(base=1, cap=10), retries=3` | Redis managers | `backon::ExponentialBuilder` |
| `RuntimeError("Backend not initialized")` | Proxy pattern | `Option<Box<dyn Backend>>` + compile-time safety |

### Connection lifecycle (common pattern):
```
connect() -> try: init client / pool, catch Exception: log + raise
disconnect() -> if client: close, set None
health() -> try: ping, except: return False
ensure_connected() -> if not connected: connect()
```

### Rust error enum sketch:
```rust
#[derive(thiserror::Error)]
pub enum StorageError {
    #[error("connection failed: {0}")]
    ConnectionFailed(#[source] Box<dyn std::error::Error + Send>),
    #[error("not connected")]
    NotConnected,
    #[error("query failed: {0}")]
    QueryFailed(#[source] Box<dyn std::error::Error + Send>),
    #[error("invalid input: {0}")]
    InvalidInput(String),
    #[error("not found: {0}")]
    NotFound(String),
    #[error("serialization error: {0}")]
    Serialization(#[from] serde_json::Error),
}
```

---

## 8. File Inventory

| Directory | Files | Lines of Code | Category |
|-----------|-------|---------------|----------|
| `cache/` | 4 | 166 | Cache abstraction |
| `key_value/` | 4 | 289 | Key-value store |
| `relational/` | 7 | 511 | SQL databases |
| `vector/` | 9 | 916 | Vector databases |
| `stream/` | 4 | 375 | Event streams |
| `object/` | 5 | 345 | Blob storage |
| `graph/` | 3 | 147 | Graph databases |
| `event_log/` | 4 | 167 | Log persistence |
| `timeseries/` | 3 | 153 | Time-series |
| Root files | 4 | 454 | Base, factories, proxies, `__init__` |
| **Total** | **47** | **~3523** | |

---

## 9. Recommendations

1. **Start with in-memory backends** (score 4-5): `InMemoryCache`, `InMemoryKv`, `InMemoryVector`, `LocalFileAdapter`, `NullStorage`, `RSyslogStorage` — pure data structures, no external deps.

2. **Define Rust traits first**: Mirror the ABC hierarchy exactly. Use `#[async_trait]` from `async-trait` crate.

3. **`Any` elimination strategy**: Replace `dict[str, Any]` with `HashMap<String, serde_json::Value>`. Replace bare `Any` with `Vec<u8>` or generic `<V: Serialize + Deserialize>`.

4. **PyO3 for Chroma/Pinecone**: These have no good Rust equivalent — keep as thin PyO3 bridges calling back to the Python client, or replace with Qdrant/Weaviate.

5. **Factory pattern in Rust**: `HashMap<&'static str, fn(HashMap<String, String>) -> Box<dyn Any>>` with `downcast` per category.

6. **Proxy pattern in Rust**: `LazyInitStorageProxy` → `OnceCell<Box<dyn StorageBackend>>`. `CachingStorageProxy` → `LruCache` crate. `NullStorage` → a unit struct.

7. **Imports to handle**: `MinioAdapter` is defined but **not registered** in factory (should be addressed or deprecated).
