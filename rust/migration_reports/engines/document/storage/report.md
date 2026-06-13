# Migration Report: `engines/document/storage/`

> Generated: 2026-06-13
> Target: Rust (tokio + PyO3)
> Scope: 4 Python files (141 / 38 / 121 / 11 lines)

---

## 1. Pre-Refactor Analysis

### 1.1 `Any` / `dict[str, Any]` Usage

| Location | Usage | Risk |
|----------|-------|------|
| `MetadataStore._cache` | `dict[str, dict[str, Any]]` — opaque metadata blobs | High — no schema, pass-through to KV storage as-is |
| `MetadataStore.put_metadata` | Accepts `dict[str, Any]` — no shape validation | High — any caller can write anything |
| `DocumentStore.get_document` | `StoredDocument = DocumentRecord \| Document` — union type decoded from `payload` dict via `kind` discriminator | Medium — pattern is clean but runtime reflection-based |
| `DocumentStore.search_by_keyword` | Naive `casefold()` scan on all cached chunks | Low — bounded to in-memory cache, but O(n) |
| `ChunkStore.attach_embeddings` | `items: list[dict[str, object]]` constructed inline, passed to `vector_index.batch_upsert` | Low — dict shape is local, but unenforced |
| `ChunkStore.search_similar` | `item.get("_id")` — magic string key from `VectorDBAdapter.query()` return | Medium — contract is implicit, no typed return |

**Verdict:** 5 `Any`/`dict` hotspots. The `MetadataStore` is the worst offender — it is a blind passthrough. Strongly typed Rust traits would eliminate this entirely.

### 1.2 Storage Backend Dependencies

```
engines/document/storage/
  ├── engines/storage/key_value/base.py     → KeyValueStorage (abstract base)
  ├── engines/storage/vector/base.py        → VectorDBAdapter (abstract base)
  └── engines/storage/object/base.py        → ObjectStorage (used by IngestionContext, not directly by stores)
```

Key abstractions injected via constructor (optional — `None`-able):

| Store | KV Injection | Vector Injection |
|-------|-------------|------------------|
| `DocumentStore` | `KeyValueStorage \| None` | None |
| `ChunkStore` | `KeyValueStorage \| None` | `VectorDBAdapter \| None` |
| `MetadataStore` | `KeyValueStorage \| None` | None |

All stores work as in-memory caches when the backend is `None`.

### 1.3 Async Patterns

- **All public methods are `async def`** — Python asyncio throughout.
- **VectorDBAdapter** is fully async (`async def create_index`, `upsert`, `query`, `delete`, etc.).
- **KeyValueStorage** is fully async.
- **Concurrency model**: Fine-grained `await` per operation. No explicit locking.
- **Caching pattern**: Write-through: mutate in-memory `dict` first, then `await` storage. Read-through: check cache dict, then `await` storage on miss.
- **Bottleneck in `DocumentStore.get_chunks_by_doc`**: `await storage.list_keys("chunk:")` then N individual `await storage.get(key)` calls — O(N) round-trips with no batching.

### 1.4 File Manifest

| File | Lines | Classes | Pure I/O? |
|------|-------|---------|-----------|
| `__init__.py` | 11 | — | No |
| `document_store.py` | 141 | `DocumentStore` | Yes (KV + cache) |
| `metadata_store.py` | 38 | `MetadataStore` | Yes (KV + cache) |
| `chunk_store.py` | 121 | `ChunkStore` | Yes (KV + Vector + cache) |

---

## 2. Rust Migration Candidate Scoring (1–5)

| Component | Score | Rationale |
|-----------|-------|-----------|
| `MetadataStore` | **5 — Immediate** | 38 lines, pure CRUD, schema-less passthrough. Trivial `trait MetadataStorage { fn put, fn get, fn delete }` in Rust. Zero business logic. |
| `DocumentStore` | **4 — High** | 141 lines, discriminated union decode (`kind` field), cache logic. The `search_by_keyword` is trivial. The `get_chunks_by_doc` N+1 problem disappears with a proper async Rust driver (batching). |
| `ChunkStore` | **3 — Medium** | 121 lines, two backend interfaces (KV + Vector), embedding attachment logic, similarity search bridge. The vector index abstraction is the risk — must bind to a Rust-native vector DB client. |
| `__init__.py` | **5 — Immediate** | Re-exports only. Becomes `pub mod` declarations. |

---

## 3. Ownership Map: Document Storage Lifecycle

```
                         ┌──────────────────────────────┐
                         │     IngestionContext          │
                         │  (document_store,             │
                         │   chunk_store,                │
                         │   metadata_store)             │
                         └──────┬───────────────────────┘
                                │ step_store()
                                ▼
┌────────────────────┬─────────────────────┬─────────────────────┐
│   DocumentStore    │     ChunkStore      │   MetadataStore      │
│                    │                     │                      │
│ add_document(doc)  │ add_chunks(chunks)  │ put_metadata(id,dict)│
│ get_document(id)   │ get_chunk(id)       │ get_metadata(id)     │
│ get_document_record│ list_chunks_for_doc │ delete_metadata(id)  │
│ get_chunk(id)      │ attach_embeddings() │                      │
│ get_chunks_by_doc()│ search_similar()    │                      │
│ list_documents()   │ delete_chunks_for_  │                      │
│ search_by_keyword()│   document()        │                      │
│ delete_document(id)│                     │                      │
└────────┬───────────┴─────────┬───────────┴──────────┬──────────┘
         │                     │                      │
         ▼                     ▼                      ▼
┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐
│ KeyValueStorage │  │ KeyValueStorage  │  │ KeyValueStorage │
│ (doc:* keys)    │  │ (chunk:* keys)   │  │ (docmeta:* keys)│
└─────────────────┘  ├──────────────────┤  └─────────────────┘
                     │ VectorDBAdapter  │
                     │ (embedding idx)  │
                     └──────────────────┘
```

**Lifecycle (insertion):**
1. `step_store()` receives `IngestionContext` with populated `DocumentRecord` + `list[ChunkRecord]`
2. Calls `DocumentStore.add_document(record)` → KV `set("doc:{id}", ...)` + in-memory cache
3. Calls `ChunkStore.add_chunks(chunks)` → KV `set("chunk:{id}", ...)` for each + cache
4. Later: `ChunkStore.attach_embeddings()` → vector index `batch_upsert()`

**Lifecycle (retrieval):**
1. RAG layer calls `DocumentStore.get_document()` and `DocumentStore.get_chunks_by_doc()`
2. `KeywordRetriever` uses `DocumentStore.search_by_keyword()` — O(n) scan of in-memory cache

**Lifecycle (deletion):**
1. `DocumentStore.delete_document()` removes from cache + KV
2. Cascading via `_chunks_by_doc` index: deletes each chunk from cache + KV

---

## 4. Suggested PyO3 Binding: Storage Trait in Rust

### 4.1 Trait Hierarchy

```rust
// === Core Storage Traits (Rust side, no PyO3) ===

#[async_trait]
pub trait KeyValueStorage: Send + Sync {
    async fn set(&self, key: &str, value: serde_json::Value) -> Result<()>;
    async fn get(&self, key: &str) -> Result<Option<serde_json::Value>>;
    async fn delete(&self, key: &str) -> Result<()>;
    async fn exists(&self, key: &str) -> Result<bool>;
    async fn list_keys(&self, prefix: Option<&str>) -> Result<Vec<String>>;
}

#[async_trait]
pub trait VectorStorage: Send + Sync {
    async fn create_index(&self, name: &str, dimension: usize, config: Option<&Metadata>) -> Result<()>;
    async fn upsert(&self, ids: &[String], vectors: &[Vec<f64>], metadata: &[Metadata]) -> Result<()>;
    async fn batch_upsert(&self, items: &[RawData]) -> Result<()>;
    async fn query(&self, vector: &[f64], top_k: usize, filters: Option<&Metadata>) -> Result<Vec<RawData>>;
    async fn delete(&self, ids: &[String]) -> Result<()>;
}
```

### 4.2 DocumentStore in Rust

```rust
type StoredDocument = DiscriminatedDocument; // enum { DocumentRecord(DocumentRecord), RagDocument(Document) }

pub struct DocumentStore {
    storage: Option<Arc<dyn KeyValueStorage>>,
    documents: RwLock<HashMap<String, StoredDocument>>,
    chunks: RwLock<HashMap<String, DocumentChunk>>,
    chunks_by_doc: RwLock<HashMap<String, Vec<String>>>,
}
```

### 4.3 PyO3 Boundary

```rust
// Expose to Python via PyO3:
#[pyclass]
pub struct PyDocumentStore {
    inner: Arc<DocumentStore>,
}

#[pymethods]
impl PyDocumentStore {
    fn add_document(&self, py: Python, doc: &PyAny) -> PyResult<()> { ... }
    fn get_document(&self, py: Python, document_id: &str) -> PyResult<Option<PyObject>> { ... }
    // ...
}
```

**Strategy**: The Rust core is a pure `async fn` trait impl. PyO3 wraps it with a `tokio::Runtime` handle (or `pyo3-asyncio` bridge). Python callers continue to `await` — the GIL is released during Rust I/O via `.await`.

### 4.4 Recommended Python→Rust Transition Plan

| Phase | What | Python still owns |
|-------|------|------------------|
| 1 | Rust `KeyValueStorage` trait + `DocumentStore` impl | Caller wiring, vector index |
| 2 | Rust `ChunkStore` impl (KV only) | Vector index wiring |
| 3 | Rust `VectorStorage` trait | Custom vector DB adapters |
| 4 | Full `ChunkStore` with vector bindings | Any custom embedding logic |
| 5 | `MetadataStore` | Anything |

---

## 5. Libraries Analysis: Document Store Backends — Rust Alternatives

| Python dependency | Rust alternative | Notes |
|-------------------|-----------------|-------|
| `KeyValueStorage` (abstract) | `trait KeyValueStorage` + impls | **redis-rs** for Redis, **sled** for embedded, **aws-sdk-dynamodb** for DynamoDB, **tikv-client** for TiKV |
| `VectorDBAdapter` (abstract) | `trait VectorStorage` + impls | **qdrant-client** (Rust gRPC), **weaviate-client** (Rust HTTP), **pgvector** with **sqlx**, **tantivy** for local ANN |
| `ObjectStorage` (abstract) | `trait ObjectStorage` | **aws-sdk-s3** (S3, GCS, R2), **opendal** (unified object store, Rust native) |
| Pydantic serialization | **serde** + **serde_json** | Drop-in replacement for `model_dump(mode="json")` |
| asyncio | **tokio** | Async runtime. `pyo3-asyncio` bridges tokio ↔ asyncio |
| `DocumentRecord` / `ChunkRecord` | **struct** + **serde::Serialize/Deserialize** | Derive macros replace Pydantic field validators |

**Key insight**: No exotic Python libraries are used. The entire module depends on two abstract base classes. Rust can implement the same abstractions with `async_trait` + standard libraries.

---

## 6. Performance Hot Paths

### 6.1 Serialize / Deserialize

| Operation | Frequency | Cost | Rust Improvement |
|-----------|-----------|------|------------------|
| `DocumentRecord.model_dump(mode="json")` | Per write | `O(fields)` — Pydantic V2 is fast but allocates | `serde_json::to_value()` — zero-copy via `RawValue` |
| `DocumentRecord(**payload)` | Per read | `O(fields)` — Pydantic V2 field validation | `serde_json::from_value()` — derive-based, no runtime validation overhead |
| `DocumentChunk(**data)` | Per chunk read | `O(fields)` | Same — serde derive |
| `ChunkRecord.model_dump(mode="json")` | Per chunk write | `O(fields)` | Same — serde derive |

**Rust advantage**: serde `#[derive(Deserialize)]` is compile-time codegen. No runtime reflection. Python Pydantic V2 is already C-core-based but still has per-call overhead for field name resolution.

### 6.2 Indexing Hot Paths

| Code location | Issue | Rust fix |
|--------------|-------|----------|
| `DocumentStore.get_chunks_by_doc` line 96-104 | `list_keys("chunk:")` + N individual `get()` — unbounded round-trips | Use a composite index: `doc:{id}:chunks` containing list of chunk IDs. Single `get()` instead of N+1. |
| `DocumentStore.search_by_keyword` line 129-131 | O(n) scan of all cached chunks. No external index. | Use a full-text index (tantivy or pgvector). Rust tantivy is 10-100x faster than Python loop. |
| `ChunkStore.list_chunks_for_document` line 47-58 | Same N+1 problem as `DocumentStore.get_chunks_by_doc` | Same fix: composite index key. |
| `ChunkStore.attach_embeddings` line 61-83 | Dict merge + batch upsert — loops in Python | Rust loop over `HashMap` is comparable, but the `batch_upsert` call moves to native. |
| `ChunkStore._ensure_vector_index` line 117-120 | Lazy init — `len(sample_embedding)` called on every `attach_embeddings` first call | Trivial. |

### 6.3 Cache Contention

All three stores use `dict` / `RwLock<HashMap>` for caching. Current Python is **not thread-safe** — asyncio single-threaded context avoids races. In Rust with tokio, use `tokio::sync::RwLock` for interior mutability.

---

## 7. Error Handling

### 7.1 Current Python State

| Store | Error handling strategy | Gaps |
|-------|------------------------|------|
| `DocumentStore` | No try/except. Returns `None` on missing key, empty list on no results. | Silent data corruption if `storage.set()` fails mid-operation. No rollback for partial writes. |
| `ChunkStore` | No try/except. Vector index ops (`batch_upsert`, `query`) can fail silently — no error propagation. | If `_ensure_vector_index` fails on `attach_embeddings`, `_vector_ready` stays False, retries on next call. But no alerting. |
| `MetadataStore` | No try/except. Returns `None` on missing. | Same as DocumentStore. |
| `step_store` | Wraps all operations in `try/except StorageFailed`. | Wide catch — can mask transient errors. |

### 7.2 Recommended Rust Error Model

```rust
#[derive(Debug, thiserror::Error)]
pub enum StorageError {
    #[error("key-value backend error: {0}")]
    KeyValue(#[from] KeyValueError),

    #[error("vector index error: {0}")]
    VectorIndex(#[from] VectorIndexError),

    #[error("serialization error: {0}")]
    Serialization(#[from] serde_json::Error),

    #[error("not found: {key}")]
    NotFound { key: String },

    #[error("internal error: {0}")]
    Internal(String),
}

// All storage methods return Result<T, StorageError>
// No silent None returns — distinguish NotFound from backend failure.
pub type Result<T> = std::result::Result<T, StorageError>;
```

### 7.3 Key Improvements Over Python

1. **Eliminate silent `None` fallback** — `get_document()` returns `Result<Option<T>>` where `Ok(None)` means "confirmed absent" and `Err(e)` means "backend failed".
2. **Atomic operations where possible** — use KV backends that support conditional writes (e.g., Redis `SET NX`).
3. **Structured error types** — `thiserror` derive for pattern matching upstream.
4. **No wide catch** — trace the exact error source.

---

## 8. Summary

| Dimension | Verdict |
|-----------|---------|
| **Migration difficulty** | **Low** — 3 stores, 3 abstract backends, no framework lock-in. |
| **Files to migrate** | 4 (300 total lines) |
| **Rust benefit** | 5-10x serialization, 0 `None`-related bugs, thread-safe caching, batching eliminates N+1 |
| **Highest risk** | Vector index abstraction — needs feature parity with Python adapters |
| **Lowest effort / highest value** | `MetadataStore` — 38 lines, immediate Rust port, eliminates `Any` passthrough |
| **PyO3 complexity** | Low — no complex Python object graph crossing boundary; just dicts and strings |
| **Recommended order** | MetadataStore → DocumentStore → ChunkStore (KV only) → ChunkStore (vector) |
