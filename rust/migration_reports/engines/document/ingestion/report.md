# Ingestion Engine — Rust Migration Report

Analyzed 24 Python files across `engines/document/ingestion/` and subdirs `services/`, `steps/`, `utils/`.

---

## 1. Pre-Refactor Analysis

### `dict[str, Any]` usage (high everywhere)

| File | Usage |
|------|-------|
| `ingestion_models.py` | `DocumentAsset.metadata`, `DocumentRecord.metadata`, `ParsedDocument.metadata`, `ChunkRecord.metadata`, `IngestionEvent.metadata`, `DocumentIngestionResult.metadata`, `DocumentIngestionResult.storage` — **7 fields** |
| `ingestion_context.py` | `request_metadata` — 1 field |
| `ingestion_runner.py` | `metadata` param to `execute()` |
| `ingestion_service.py` | `metadata` param to `ingest()` |
| `ingestion_validator.py` | `metadata` param and `isinstance(metadata, dict)` check |
| `upload_service.py` | `metadata` param passthrough |
| `batch_ingest_service.py` | `items: list[dict[str, Any]]` param |
| `async_ingest_service.py` | `message: dict[str, Any]` param, dict field access throughout |
| `ingestion_scheduler.py` | `items: Iterable[dict[str, Any]]` — parametrized dict |
| `retry_policy.py` | `**kwargs` passthrough with `Callable` + `Any` return |

**Verdict:** `dict[str, Any]` is pervasive as an opaque metadata carrier. Every ingestion step, service, and model carries a generic metadata bag. In Rust, this maps to `HashMap<String, serde_json::Value>` or a typed `Metadata` struct — but the Python code never constrains the shape, so full serde_json::Value is the honest translation.

### Dynamic Dispatch

- **`IngestionPipeline._step_map`** (`ingestion_pipeline.py:27-33`): A `dict[str, Callable]` mapping string step names like `"extract"`, `"parse"`, `"chunk"`, `"embed"`, `"store"` to async functions. Steps are looked up by `step_name` string at runtime.
- **`WorkflowRegistry`** (`workflow_registry.py:7`): `dict[str, list[str]]` mapping workflow names/keys to step name lists.
- **`IngestionRunner.route()`** (`ingestion_runner.py:23-81`): 10+ conditional branches resolving `MediaType` → workflow name → step list. This is a chain of `if/elif` blocks.
- **`AsyncIngestService._resolve_media_type()`** (`async_ingest_service.py:48-70`): 3-branch priority chain over dict keys.

### Global State

**None found.** No module-level mutable globals, no singletons, no class-level mutable state. `IngestionPipeline._step_map` is initialized per-instance in `__init__`. Clean.

---

## 2. Migration Notes — Rust Candidate Scores

### Scoring: 1 (heavy I/O/orchestration) → 5 (pure compute, trivial)

| Function / Class | Score | Rationale |
|---|---|---|
| `sha256_bytes` (hashing.py) | **5** | Pure compute, no deps. One-liner. |
| `sha256_text` (hashing.py) | **5** | Wraps sha256_bytes. |
| `combined_hash` (hashing.py) | **5** | Iterates strings → sha256. Trivial. |
| `file_signature` (file_signature.py) | **5** | Branching + BLAKE2b. Pure CPU. |
| `time_block` (timing.py) | **5** | Context manager → closures in Rust. Zero complexity. |
| `Stopwatch` (timing.py) | **5** | Simple state machine. |
| `IngestionUtils` (ingestion_utils.py) | **5** | Static methods, pure compute. |
| `WorkflowRegistry` (workflow_registry.py) | **5** | HashMap get/register. Trivial. |
| `IngestionValidator.validate_input` (ingestion_validator.py) | **5** | Pure validation, no I/O. |
| `IngestionStatus` (ingestion_models.py) | **5** | Simple string enum. |
| `StorageLocation` (ingestion_models.py) | **5** | Simple string enum. |
| `DocumentAsset` (ingestion_models.py) | **4** | Data struct, but has `datetime` + `dict[str,Any]`. |
| `DocumentRecord` (ingestion_models.py) | **4** | Pydantic → serde. Same datetime/map overhead. |
| `ParsedDocument` (ingestion_models.py) | **4** | Simple dataclass. |
| `ChunkRecord` (ingestion_models.py) | **4** | Has `list[EmbeddingRecord]` + dict. |
| `IngestionEvent` (ingestion_models.py) | **4** | Simple event dataclass. |
| `EmbeddingRecord` (ingestion_models.py) | **4** | `list[float]` vector field. |
| `DocumentIngestionResult` (ingestion_models.py) | **4** | Composite result type with `add_event` method. |
| `RetryPolicy` (retry_policy.py) | **4** | Logic-heavy but wraps generic callables. Needs generics. |
| `IngestionContext.create` (ingestion_context.py) | **3** | Factory with SHA256 + DI wiring. |
| `IngestionContext.build_asset_record` | **3** | Constructs from context state. |
| `IngestionContext.build_document_record` | **3** | Conditional logic + text slicing. |
| `IngestionPipeline.run` (ingestion_pipeline.py) | **3** | Dynamic step dispatch + error wrapping. |
| `IngestionRunner.route` (ingestion_runner.py) | **3** | Medium complexity, condition chain. |
| `IngestionRunner.execute` (ingestion_runner.py) | **3** | Orchestrates pipeline + result assembly. |
| `step_extract` (step_extract.py) | **2** | Thin I/O wrapper, calls `object_storage.put()`. |
| `step_parse` (step_parse.py) | **2** | Delegates to external parser. |
| `step_chunk` (step_chunk.py) | **2** | Delegates to chunker. |
| `step_embed` (step_embed.py) | **2** | Iterates chunks, calls external embedder. |
| `step_store` (step_store.py) | **2** | Writes to document_store + chunk_store. |
| `IngestionService` (ingestion_service.py) | **1** | Pure orchestration, creates registries. |
| `UploadService.ingest` (upload_service.py) | **1** | Thin passthrough. |
| `AsyncIngestService` (async_ingest_service.py) | **1** | Dict-based message parsing. |
| `BatchIngestService` (batch_ingest_service.py) | **1** | asyncio.gather semaphore wrapper. |
| `IngestionScheduler` (ingestion_scheduler.py) | **1** | File I/O + asyncio loop. |

---

## 3. Ownership Map — Data Flow Through Ingestion Pipeline

```
                        ┌────────────────────────┐
                        │     External Source     │
                        │  (file, queue, API)     │
                        └───────────┬────────────┘
                                    │ data: bytes
                                    ▼
┌───────────────────────────────────────────────────────────────┐
│                  IngestionContext                              │
│  ┌──────────┐  ┌─────────┐  ┌────────────┐  ┌────────────┐  │
│  │ data     │─▶│ sha256  │  │ document_id│  │ media_type │  │
│  │ (bytes)  │  │ (str)   │  │ (str)      │  │ (MediaType)│  │
│  └──────────┘  └─────────┘  └────────────┘  └────────────┘  │
│                                                               │
│  Step ownership progression (each step mutates context):      │
│                                                               │
│  step_extract:  data → object_storage.put()
│                 builds asset: DocumentAsset { object_key }
│                 ctx.asset = asset
│                                                               │
│  step_parse:    data + registry → parser.parse_bytes()
│                 ctx.parsed_document = BaseDocument
│                                                               │
│  step_chunk:    parsed_document → chunker.chunk_document()
│                 ctx.chunks = Vec<ChunkRecord>
│                                                               │
│  step_embed:    chunks → embedding_service.embed_chunks()
│                 ctx.embeddings = Vec<EmbeddingRecord>
│                                                               │
│  step_store:    document_record → document_store.add_document()
│                 chunks → chunk_store.add_chunks()
└───────────────┬───────────────────────────────────────────────┘
                │
                ▼
┌───────────────────────────────────────────────────────────────┐
│              DocumentIngestionResult                           │
│  asset + parsed_document + stored_document + chunks            │
│  + embeddings + events                                         │
└───────────────────────────────────────────────────────────────┘
```

**Key observation:** `IngestionContext` is a **single mutable accumulator** passed through every step. Steps read previous fields and write new fields. This is essentially a builder-pattern pipeline with shared mutable state.

---

## 4. Suggested PyO3 Binding Structure

```
ingestion-engine/
├── Cargo.toml
├── src/
│   ├── lib.rs                  # Rust library crate
│   ├── python.rs               # #[pymodule] entry point
│   ├── models/
│   │   ├── mod.rs
│   │   ├── ingestion_status.rs # Enum
│   │   ├── storage_location.rs # Enum
│   │   ├── document_asset.rs
│   │   ├── document_record.rs
│   │   ├── parsed_document.rs
│   │   ├── chunk_record.rs
│   │   ├── embedding_record.rs
│   │   ├── ingestion_event.rs
│   │   └── ingestion_result.rs
│   ├── errors/
│   │   ├── mod.rs
│   │   └── ingestion_errors.rs # Error enum → PyErr
│   ├── pipeline/
│   │   ├── mod.rs
│   │   ├── context.rs          # IngestionContext
│   │   ├── runner.rs           # IngestionRunner
│   │   ├── pipeline.rs         # IngestionPipeline + step dispatch
│   │   └── steps.rs            # Step trait + 5 implementations
│   ├── registry/
│   │   ├── workflow_registry.rs
│   │   └── document_registry.rs
│   ├── validation/
│   │   └── validator.rs
│   └── utils/
│       ├── hashing.rs
│       ├── timing.rs
│       ├── file_signature.rs
│       └── retry.rs
├── pyo3-wrapper/
│   ├── Cargo.toml
│   └── src/
│       ├── lib.rs              # #[pymodule] init
│       ├── context.rs          # PyIngestionContext
│       ├── pipeline.rs         # PyIngestionPipeline
│       ├── runner.rs           # PyIngestionRunner
│       ├── validator.rs        # PyIngestionValidator
│       ├── registry.rs         # PyWorkflowRegistry
│       ├── models.rs           # Py DocumentIngestionResult etc.
│       └── utils.rs            # Py access to hashing/timing
```

**Recommended binding boundary:**
- Expose `IngestionValidator` → Python (pure, no I/O, high value)
- Expose `WorkflowRegistry` → Python (trivial map)
- Expose `IngestionPipeline` / `IngestionRunner` → Python (orchestration logic stays in Rust)
- Expose utils (hashing, timing) → Python
- **Keep step implementations as Rust async trait objects** — they call external services via injected trait objects which can be passed from Python
- `IngestionContext` is the bridge type — must be constructable from Python, mutable in Rust

---

## 5. Libraries Analysis — Import-by-Import Rust Alternatives

| Python Import | Rust Crate | Migration Difficulty |
|---|---|---|
| `hashlib.sha256()` | `sha2` crate (`Sha256::digest()`) | Trivial |
| `hashlib.blake2b()` | `blake2` crate (`Blake2b512::digest()`) | Trivial |
| `uuid.uuid4()` | `uuid` crate (`Uuid::new_v4()`) | Trivial |
| `datetime.utcnow()` | `chrono` crate (`Utc::now()`) | Trivial |
| `dataclasses.dataclass` | Native `struct` | Trivial |
| `pydantic.BaseModel` | `serde` (`Serialize`, `Deserialize` derives) | Medium — serde is more explicit |
| `pydantic.Field` | `serde` attributes + `#[derive(Default)]` | Medium |
| `pydantic.ConfigDict` | N/A — Rust compile-time dispatching | Easy (not needed) |
| `enum.Enum` | Native `enum` with `strum` for display | Trivial |
| `asyncio` | `tokio` | Medium — runtime complexity |
| `asyncio.gather` | `tokio::join!` / `futures::future::join_all` | Low |
| `asyncio.Semaphore` | `tokio::sync::Semaphore` | Low |
| `asyncio.sleep` | `tokio::time::sleep` | Low |
| `contextlib.contextmanager` | Closure-based pattern | Low |
| `time.perf_counter()` | `std::time::Instant` | Trivial |
| `pathlib.Path` | `std::path::PathBuf` | Low |
| `typing.cast` | N/A — Rust is statically typed | N/A |
| `collections.abc.Callable` | `fn` ptr / `Box<dyn Fn>` / `impl Trait` | Medium |
| `collections.abc.Iterable` | `IntoIterator` trait | Low |
| `functools` | Not used — N/A | N/A |
| `logging` | `log` / `tracing` crate | Low |
| `engines.storage.object.base` | Custom Rust trait (`ObjectStorage`) | High — FFI boundary |
| `engines.document.chunking.base` | Custom Rust trait (`BaseChunker`) | High — FFI boundary |
| `engines.document.embedding.service` | Custom Rust trait (`EmbeddingService`) | High — FFI boundary |
| `engines.document.models.base` | Custom Rust structs (`BaseDocument`) | High — cross-crate types |
| `engines.document.models.media_types` | `MediaType` + `DocumentFormat` enums | Medium |
| `engines.document.models.document_registry` | Registry trait | High — dynamic lookup |
| `engines.storage.chunk_store` | Custom Rust trait | High — async I/O |
| `engines.storage.document_store` | Custom Rust trait | High — async I/O |
| `engines.storage.metadata_store` | Custom Rust trait | High — async I/O |

---

## 6. Performance Hot Paths

### CPU-bound transformation steps (high migration value)

| Location | Operation | Notes |
|---|---|---|
| `ingestion_context.py:117` | `hashlib.sha256(data)` on full file bytes | SHA256 over arbitrary-sized blob. Every ingestion pays this cost. |
| `hashing.py:7-13` | `sha256_bytes` | Called from context creation. Pure CPU. |
| `hashing.py:23-32` | `combined_hash` | String concatenation + SHA256. |
| `file_signature.py:7-28` | `file_signature` | BLAKE2b over head+tail of file. For deduplication. |
| `step_embed.py:29-44` | Loop over chunks, `embed_map.get()`, `len(emb_vector)` | O(n) allocation of `EmbeddingRecord` per chunk. Python list-building overhead. |
| `ingestion_context.py:160` | `parsed_document.raw_text[:200]` | String slicing for preview. Trivial but occurs per document. |
| `ingestion_runner.py:135-136` | `context.chunks or []`, `context.embeddings or []` | Branch + list copy. |

### Allocation patterns (problematic in Rust without care)

| Pattern | Location | Issue |
|---|---|---|
| `list[float]` for embeddings | `EmbeddingRecord.vector` | Heap-allocated vec per chunk. Use `ndarray` or `tinyvec` if fixed dims. |
| `dict[str, Any]` metadata copying | `build_asset_record():150`, `build_document_record():171` | `.copy()` clones the entire dict — O(n) in metadata keys. |
| `list[IngestionEvent]` appends | `DocumentIngestionResult.add_event()` | Per-step event logging creates many small allocations. |
| `list[EmbeddingRecord]` build | `step_embed.py:27-44` | Allocates per chunk in tight loop. |

### I/O bottlenecks (not migration targets but worth noting)

| Location | Operation |
|---|---|
| `step_extract.py:26` | `ctx.object_storage.put(ctx.object_key, data=ctx.data)` — writes full binary to remote storage |
| `step_parse.py:22` | `parser.parse_bytes(...)` — full document parse |
| `step_store.py:35` | `ctx.document_store.add_document(doc)` — DB write |
| `step_store.py:41` | `ctx.chunk_store.add_chunks(ctx.chunks)` — bulk DB write |
| `ingestion_scheduler.py:36` | `path.read_bytes()` — file I/O per document |

**Recommendation:** The pure hashing functions (`sha256_bytes`, `file_signature`, `combined_hash`) and validation logic are the highest-value migration targets. They are CPU-bound, dependency-free, and trivially parallelizable in Rust.

---

## 7. Error Handling Analysis

### Exception Hierarchy

```
Exception
└── IngestionError (base, has step + details + timestamp)
    ├── InvalidDocumentError
    ├── UnsupportedMediaTypeError (auto-sets step="parse" + details dict)
    ├── ExtractionFailed
    ├── ParseFailed
    ├── ChunkingFailed
    ├── EmbeddingFailed
    ├── StorageFailed
    ├── FinalizationFailed
    └── IngestionStepFailed (wraps original Exception + step name + repr)
```

### Exception patterns per file

| File | Pattern | Assessment |
|---|---|---|
| `ingestion_errors.py` | Proper hierarchy, `to_dict()` serialization, contextual `step` + `details` | **Good** — clean design |
| `ingestion_pipeline.py:66` | `raise IngestionStepFailed(step_name, exc) from exc` | **Good** — proper chaining |
| `step_extract.py:36` | `except Exception as exc: raise ExtractionFailed(...) from exc` | **Safe** — catches all, re-raises typed |
| `step_parse.py:32` | Same pattern | **Safe** |
| `step_chunk.py:28` | Same pattern | **Safe** |
| `step_embed.py:49` | Same pattern | **Safe** |
| `step_store.py:43` | `except Exception as exc: raise StorageFailed(...) from exc` | **Safe** |
| `ingestion_service.py:66` | `except Exception as exc: raise IngestionError(...) from exc` | **OK** — swallow-coarse but re-raises |
| `ingestion_service.py:63` | `except IngestionError: raise` | **Redundant passthrough** — no-op |
| `upload_service.py:49` | `except Exception as exc: raise IngestionError(...) from exc` | **Safe** — outermost boundary |
| `ingestion_validator.py:39-41` | `try: _ = media_type / except Exception:` | **Odd** — `isinstance` check that can't fail; dead code in the `MediaType` branch. Bare acceptance of any exception. |
| `ingestion_validator.py:43-46` | `try: _ = MEDIA_TYPES[media_type] / except Exception:` | **Acceptable** — key lookup guard, but `except Exception` is too broad; should be `KeyError`. |
| `retry_policy.py:40` | `except self.retry_exceptions` | **Good** — configurable exception tuple, configurable retries |

### Summary

- **No bare `except:` blocks** — all `except Exception` or specific types.
- **No `None`-for-failure pattern** — every failure path raises typed exceptions.
- **No exception swallowing** — always re-raises (either wrapped or original).
- **`to_dict()` on error** (`ingestion_errors.py:26-32`) provides structured serialization for observability.
- **Minor issue** in `ingestion_validator.py:40` — `try: _ = media_type / except Exception` is dead code that would mask bugs if the `isinstance` branch were ever reached with invalid input.

### Rust Migration Notes for Errors

- Map to `thiserror` enum: `#[derive(Debug, thiserror::Error)] enum IngestionError { ... }`
- Each variant carries `step: String`, `details: Option<HashMap<String, Value>>`, `timestamp: DateTime<Utc>`
- `IngestionStepFailed` needs `#[source] original_exception: Box<dyn Error + Send + Sync>`
- `to_dict()` → `serde::Serialize` on the enum
- `UnsupportedMediaTypeError` auto-defaults `step` to `"parse"` — use `impl Default` or builder pattern
- Validator should use `Result<(), ValidationError>` not exceptions
