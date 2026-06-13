# Rust Migration Readiness — Cross-Cutting Summary

## Overview

| Metric | Value |
|--------|-------|
| **Total Python files analyzed** | 1,089 |
| **Total lines analyzed** | 161,918 |
| **Overall Rust readiness score** | **2.3 / 5** |
| **Overall migration feasibility** | Partial — high-value core components; most modules stay in Python |

The codebase is 162K lines across 1,089 files in 10 engine packages. While individual sub-modules
(circuit breaker, state machines, data models, FEEL engine) are excellent Rust candidates,
>70 % of the codebase is I/O-bound adapter code, format-specific parsers/writers, or
LLM-driven orchestration — all best kept in Python.

---

## Priority Migration Order

| Module | Score | Key Rust-Migration Blockers | Est. Effort | Phase |
|--------|-------|-----------------------------|-------------|-------|
| orchestration/runtime — circuit_breaker | **5** | None (pure state machine) | Small | 1 |
| orchestration/runtime — compensation | **4** | `Callable` → closure/boxed fn | Small | 1 |
| orchestration/runtime — osdm_serializer | **4** | 176 OSDM model types; `dict[str,Any]` | Large | 1 |
| orchestration/runtime — command | **4** | Generic trait design | Small | 1 |
| document/models — base_types | **4** | Circular imports (merged module) | Medium | 1 |
| document/models — osdm | **4** | Deep inheritance; Union types | Medium | 1 |
| document/models — csdm | **4** | `Any` migration payloads → `serde_json::Value` | Medium | 1 |
| document/models — msdm | **4** | `PropertyValue` untagged enum | Medium | 1 |
| document/models — ssdm, tsdm | **4** | Straightforward struct mapping | Medium | 1 |
| document/models — sub-models (BPMN, CMMN, DMN, SCXML, CEP, Petri) | **4** | Graph structures; deeply nested hierarchy | Medium | 1 |
| orchestration/state_machine | **4** | None (state machines → Rust enums) | Medium | 1 |
| orchestration/dmn (FEEL engine) | **3-4** | `Any` in AST nodes; pure logic | Large | 1 |
| document/chunking | **4** | Small, pure logic, no external deps | Small | 2 |
| orchestration/runtime — rate_limiter | **3** | `threading.Lock` → `Mutex<VecDeque>` | Small | 2 |
| orchestration/runtime — state_snapshot | **3** | In-memory dict management | Small | 2 |
| document/ingestion | **2-3** | Pipeline orchestration | Medium | 3 |
| document/parsers — base | **3** | Abstract parser protocol | Small | 2 |
| document/writers — base | **3** | Abstract writer protocol | Small | 2 |
| orchestration/bpmn | **3** | 131 Anys; execution engine coupling | Large | 3 |
| orchestration/cmmn | **3** | 43 Anys; case management engine | Medium | 3 |
| orchestration/cep | **3** | 122 Anys; complex event engine | Medium | 3 |
| orchestration/validation | **3** | 43 Anys; validation rules | Medium | 3 |
| orchestration/persistence | **2-3** | Storage backend coupling | Medium | 3 |
| orchestration/runtime — error_handler | **2-3** | `event_bus: Any` coupling | Small | 3 |
| orchestration/runtime — external_task | **2-3** | `Callable` callbacks; asyncio polling | Medium | 3 |
| orchestration/runtime — incident | **2-3** | `Callable` callbacks | Medium | 3 |
| orchestration/runtime — async_continuation | **2-3** | `Callable` handlers | Small | 3 |
| agent (core) | **3** | `Any` I/O; Pydantic models | Medium | 3 |
| **orchestration/runtime — migration** | **2** | `engine: Any` coupling | Large | Keep |
| **orchestration/runtime — dynamic_injection** | **2** | `engine: Any` coupling | Medium | Keep |
| **orchestration/runtime — listeners** | **2** | `Callable`, `FEELEngine`, `PythonEvaluator` | Large | Keep |
| **orchestration/runtime — state_manager** | **2** | Async storage backends | Large | Keep |
| **orchestration/runtime — variable_manager** | **2** | `VariableRepository` dependency | Medium | Keep |
| **orchestration/runtime — executor** | **2** | Trivial async wrapper | Small | Keep |
| **orchestration/runtime — timer_manager** | **1-2** | `asyncio.create_task` scheduling | Medium | Keep |
| **orchestration/runtime — resource_manager** | **1-2** | Thin `asyncio.Semaphore` wrapper | Small | Keep |
| **orchestration/runtime — tenant** | **1** | `ContextVar` (Python-specific) | Small | Keep |
| **orchestration/api** | **2** | Web framework coupling (FastAPI) | Large | Keep |
| **orchestration/expression** | **2** | JS/Python evaluator coupling | Small | Keep |
| **orchestration/monitoring** | **2** | Prometheus/OpenTelemetry external deps | Medium | Keep |
| **orchestration/deployment** | **2** | K8s/Docker manifest generation | Small | Keep |
| **orchestration/utils** | **2-3** | Utility functions | Small | Keep |
| **orchestration/forms** | **2** | Form rendering (Python-specific) | Small | Keep |
| **orchestration/multi_agent** | **2-3** | 54 Anys; agent coordination | Medium | Keep |
| **orchestration/core** | **2-3** | 146 Anys; heavy `engine: Any` | Large | Keep |
| **communication** | **2** | I/O-bound bus/transport adapters | Large | Keep |
| **storage** | **1-2** | External service adapter wrappers | Large | Keep |
| **knowledge** | **2** | LLM-driven; heavy external deps | Extra Large | Keep |
| **interaction** | **2-3** | Agent conversation strategies | Medium | Keep |
| **memory** | **2-3** | Abstract base | Small | Keep |
| **tools** | **2** | I/O-heavy adapter wrappers | Medium | Keep |
| **document/parsers (format-specific)** | **2** | Format-specific I/O; heavy deps | Extra Large | Keep |
| **document/writers (format-specific)** | **2** | Format-specific I/O; heavy deps | Extra Large | Keep |
| **document/embedding** | **2** | External embedding service calls | Small | Keep |
| **document/storage** | **2** | Storage adapter wrappers | Small | Keep |
| **document/model_tools** | **3** | Diff engines, converters | Medium | 3 |
| **document/utils** | **3** | Binary codecs, utilities | Small | 2 |

---

## Top Rust Candidates (Score 4-5)

These modules should be migrated first — they are pure logic, well-encapsulated, and yield immediate performance wins:

| Priority | Module | Score | Key Reason |
|----------|--------|-------|------------|
| **1** | orchestration/runtime — circuit_breaker | **5** | Pure state machine with 3 well-defined states; zero external deps; `Arc<RwLock>` thread-safety |
| **2** | orchestration/runtime — compensation | **4** | Pure `Vec<CompensationStep>` with LIFO rollback |
| **3** | orchestration/runtime — command | **4** | Generic `Command<T>` trait with `execute/undo`; async support via `tokio` |
| **4** | orchestration/runtime — osdm_serializer | **4** | Biggest perf win: `serde_json` vs 176 Pydantic constructors; 10-50x faster deserialization |
| **5** | document/models — all sub-models | **4** | ~260 types, ~8,500 lines of pure data definitions; `#[derive(Serialize, Deserialize)]` replaces Pydantic |
| **6** | orchestration/state_machine | **4** | State machines → Rust enums with compile-time transition validation |
| **7** | document/chunking | **4** | 3 files, 147 lines; pure logic, no deps; trivial migration |
| **8** | orchestration/dmn — FEEL engine | **3-4** | 874-line pure expression engine; tokenizer/parser/evaluator maps to `pest` or `nom` |

---

## Must Stay in Python (Score 1-2)

| Module | Reason |
|--------|--------|
| **storage/** | 57 files of adapter wrappers for Redis, Kafka, S3, Minio, Neo4j, InfluxDB, Qdrant, Chroma, Weaviate, Pinecone, FAISS, SQLAlchemy — all calling Python SDKs for external services. No performance gain from Rust, massive porting cost. |
| **communication/** | 60 files of I/O-bound transport/bus adapters (HTTP, gRPC, AMQP, Kafka, MQTT, Redis Pub/Sub). Async event-loop scheduling. Best kept in Python. |
| **knowledge/** | 148 files of LLM-driven RAG (OpenAI, Ollama), ML training (sklearn, torch, numpy), graph algorithms. Python is the natural language for this domain. |
| **orchestration/runtime — tenant** | `ContextVar` is a Python-specific concurrency primitive with no Rust equivalent. |
| **orchestration/runtime — timer_manager** | Pure `asyncio.create_task` scheduling. |
| **orchestration/runtime — resource_manager** | Thin `asyncio.Semaphore` wrapper. |
| **orchestration/runtime — executor** | Tiny `asyncio.iscoroutinefunction` wrapper. |
| **orchestration/runtime — dynamic_injection** | Heavily coupled to `engine: Any`. |
| **orchestration/runtime — migration** | Heavily coupled to `engine: Any` + storage backends. |
| **orchestration/api** | FastAPI route handlers — keep in Python for FastAPI runtime. |
| **document/parsers (format-specific)** | 190 files; each calls Python libraries for PDF, XML, SQL, CQL, Protobuf, MsgPack, bson, etc. Porting all would be >5,000 person-days with zero user-visible difference. |
| **document/writers (format-specific)** | 174 files; same argument as parsers. |
| **interaction/** | Agent conversation strategies that call Python-based agent backends (autogen, native). |
| **tools/** | 19 files of adapter wrappers for HTTP, gRPC, CLI, MCP, SNMP, TCP sockets. |
| **memory/** | 6 files; tiny abstract base, trivial to keep in Python. |

---

## Cross-Cutting Issues

### 1. `Any` / `dict[str, Any]` Usage — 3,086 / 1,479 occurrences

| Module | `Any` | `dict[str, Any]` | % of Total |
|--------|-------|------------------|------------|
| document | 1,402 | 822 | 45 % |
| orchestration | 950 | 404 | 31 % |
| knowledge | 223 | 55 | 7 % |
| communication | 182 | 83 | 6 % |
| storage | 160 | 81 | 5 % |
| agent | 94 | 24 | 3 % |
| tools | 36 | 1 | 1 % |
| interaction | 17 | 0 | <1 % |
| memory | 15 | 5 | <1 % |

**Hotspots:**
- `document/parsers/` — 671 Any, 441 dict[str,Any] (format-agnostic data pipelines)
- `document/writers/` — 547 Any, 286 dict[str,Any]
- `orchestration/bpmn/` — 131 Any, 64 dict[str,Any]
- `orchestration/cep/` — 122 Any, 59 dict[str,Any]
- `orchestration/core/` — 146 Any, 47 dict[str,Any]

**Rust strategy:** Replace `dict[str, Any]` with `HashMap<String, serde_json::Value>` or domain-specific enums.
For the 1,479 dict[str, Any] occurrences, approximately 300 are in high-value migration targets
(OSDM models, runtime); the rest are in code that stays in Python.

### 2. Global State — 175 module-level mutable variables

| Module | Count | Examples |
|--------|-------|----------|
| orchestration | 86 | Registry maps, factory caches, default configs |
| document | 52 | Parser/writer registries, media type maps |
| agent | 13 | Agent registry, skill caches |
| communication | 12 | Bus registries, transport caches |
| storage | 7 | Factory registries |
| knowledge | 2 | Parser/writer maps |
| interaction | 2 | Strategy registry |
| tools | 1 | Tool registry |

**Key finding:** Most global state is *registry* pattern (parser/writer/strategy lookup tables).
These are naturally replaced by Rust's module-level `lazy_static` or `OnceLock<HashMap>`.
Only 1 `ContextVar` usage exists (`orchestration/runtime/tenant.py`).

### 3. Circular Imports — Mostly Resolved

- **6 files** use `TYPE_CHECKING` for forward references
- The only critical circular pair is `document_base.py ↔ generic_models.py` (both import each other)
- **Rust resolution:** Merge into `base_types.rs` — Rust disallows circular modules natively

### 4. `# type: ignore` — 57 occurrences by category

| Category | Count | Example Files |
|----------|-------|---------------|
| `import-untyped` | 19 | `msgpack`, `fitz`, `camelot`, `sklearn`, `pandas`, `rdflib`, `networkx` |
| `import-not-found` | 26 | `aio_pika`, `aiohttp`, `grpc`, `kubernetes`, `js2py`, `pdfplumber`, `cv2`, `PyPDF2` |
| `arg-type` | 3 | `storage/factories.py`, `knowledge/rag/knowledge_rag_engine.py` |
| `attr-defined` | 2 | `protobuf_parser.py`, `protobuf_writer.py` |
| `general` (untyped) | 3 | `interaction/backends/autogen_backend.py`, `storage/stream/backends/kafka_adapter.py` |
| `import-not-found,import-untyped` | 2 | `communication/common/transport/kafka_client.py` |
| `var-annotated` | 1 | `document/parsers/usdm_parsers/pdf/structure_parser.py` |

**Interpretation:** ~80 % of `type: ignore` are for missing/untyped third-party stubs — not code quality issues.
The 3 `arg-type` and 2 `attr-defined` are actual type safety gaps.

### 5. Exception Handling Patterns

**42 custom exception classes** defined across the codebase, following a consistent pattern:

```
DomainError(BaseExceptionClass):
  ├── DocumentError → DocumentParseError, DocumentWriteError, DocumentValidationError
  ├── ExecutionError → BPMNExecutionError, CMMNExecutionError, CEPExecutionError, DMNExecutionError
  ├── RuntimeTaskError, VariableConflictError
  ├── IngestionError
  ├── MCPAdapterError
  ├── FEELError
  └── PDFError → PDFParseError, PDFMetadataError, PDFValidationError
```

**Common patterns:**
- `raise ValueError(...)` — 183 occurrences (most common, used for validation)
- `raise RuntimeError(...)` — 176 occurrences (used for operational failures)
- `except ImportError` — 37 occurrences (optional dependency pattern)
- `except ValueError` — 103 occurrences (validation error catching)

**Rust error strategy:** A unified `thiserror` enum with domain-specific variants,
mapping `ValueError` → `ValidationError`, `RuntimeError` → `InternalError`,
custom exceptions → named enum variants.

---

## Library Replacement Table

| Python Library | Rust Equivalent | Availability | Notes |
|---|---|---|---|
| **pydantic** v2 | `serde` + `serde_json` + `serde_derive` | ✅ Mature | `#[derive(Serialize, Deserialize)]`; field validation via `validator` crate |
| **lxml** | `quick-xml` / `roxmltree` | ✅ Mature | Streaming: `quick-xml`, DOM: `roxmltree` |
| **numpy** | `ndarray` / `nalgebra` | ✅ Mature | Linear algebra via `nalgebra`; tensor via `ndarray` |
| **pandas** | `polars` | ✅ Mature | Rust-native DataFrame; 3-10x faster than pandas |
| **PyYAML / ruamel.yaml** | `serde_yaml` | ✅ Mature | Serde-based YAML serialization |
| **toml** | `toml` / `toml_edit` | ✅ Mature | Serde-based TOML parsers |
| **msgpack** | `rmp-serde` | ✅ Mature | MessagePack via Serde |
| **cbor2** | `ciborium` / `serde_cbor` | ✅ Mature | CBOR via Serde |
| **protobuf** | `prost` | ✅ Mature | Protocol Buffers codegen |
| **pyarrow** | `arrow` / `parquet` | ✅ Mature | Apache Arrow Rust implementation |
| **onnx** / **onnxruntime** | `ort` / `tract` | ✅ Mature | ONNX Runtime Rust binding; tract for inference |
| **orjson** / **json** | `serde_json` | ✅ Mature | 10x faster than Python json; zero-copy deserialization |
| **httpx** / **aiohttp** / **requests** | `reqwest` | ✅ Mature | HTTP client |
| **grpcio** | `tonic` | ✅ Mature | gRPC server/client framework |
| **aiokafka** | `rdkafka` / `kafka` | ✅ Mature | Kafka client (rust-rdkafka bindings) |
| **aio_pika** (RabbitMQ) | `lapin` | ✅ Mature | AMQP client |
| **redis** / **redis-py** | `redis-rs` | ✅ Mature | Redis client |
| **sqlalchemy** | `sqlx` / `diesel` | ✅ Mature | Async SQL toolkit; `sqlx` for compile-time checked queries |
| **motor** (MongoDB) | `mongodb` | ✅ Mature | Official MongoDB Rust driver |
| **elasticsearch** | `elasticsearch-rs` | ✅ Mature | Elasticsearch client |
| **neo4j** | `neo4rs` | ✅ Mature | Bolt protocol driver |
| **cassandra** | `scylla` | ✅ Mature | ScyllaDB/Cassandra driver |
| **minio** / **boto3** (S3) | `aws-sdk-s3` / `rust-s3` | ✅ Mature | AWS SDK for Rust; Minio-compatible |
| **faiss** | `faiss-rs` | ✅ Mature | FAISS bindings; `arrow` or `qdrant` alternatives |
| **qdrant_client** | `qdrant-client` | ✅ Mature | Official Qdrant Rust client |
| **chromadb** | `chromadb` (via REST) | 🔶 Partial | No native Rust client; HTTP API only |
| **weaviate** | `weaviate-rs` | ✅ Mature | Community Weaviate client |
| **pinecone** | `pinecone-rs` | 🔶 Partial | Community client; REST-based |
| **influxdb_client** | `influxdb2` | ✅ Mature | InfluxDB v2 Rust client |
| **rdflib** (RDF) | `rio` / `sophia` | ✅ Mature | RDF parser/serializer; turtle, rdf/xml |
| **networkx** | `petgraph` | ✅ Mature | Graph data structures and algorithms |
| **matplotlib** | `plotters` | ✅ Mature | Charting and visualization |
| **PIL** / **Pillow** | `image` | ✅ Mature | Image loading/manipulation |
| **fitz** / **PyMuPDF** | `lopdf` / `pdf` | ✅ Partial | PDF manipulation; less mature than PyMuPDF |
| **pdfplumber** | `pdf-extract` / `pdf` | 🔶 Partial | PDF text extraction; less mature |
| **reportlab** | `printpdf` | 🔶 Partial | PDF generation; basic features only |
| **jinja2** | `tera` | ✅ Mature | Template engine |
| **joblib** | n/a | ❌ N/A | Only used for model serialization; use `bincode` / `rmp-serde` |
| **sklearn** | `linfa` / `smartcore` | 🔶 Partial | ML algorithms; sklearn coverage is limited |
| **torch** / **pytorch** | `tch-rs` / `candle` | ✅ Mature | PyTorch C++ bindings; `candle` minimal |
| **openai** | `async-openai` | ✅ Mature | OpenAI API client |
| **fastapi** | `axum` / `actix-web` | ✅ Mature | Web framework; Axum for async Rust |
| **kubernetes** | `kube` | ✅ Mature | Kubernetes client |
| **cryptography** | `rustls` / `ring` / `aes-gcm` | ✅ Mature | Crypto primitives |
| **chardet** | `charset` / `chardetng` | ✅ Mature | Character encoding detection |
| **defusedxml** | `quick-xml` (safe mode) | ✅ Mature | XML bomb protection baked in |
| **fontTools** | `ttf-parser` / `fontdb` | ✅ Mature | Font parsing |
| **psutil** | `sysinfo` | ✅ Mature | System information |
| **pyarrow** | `arrow` | ✅ Mature | Apache Arrow columnar format |
| **js2py** | `boa-engine` / `rquickjs` | ✅ Mature | JavaScript engine embedding |
| **autogen** | n/a | ❌ N/A | Multi-agent framework; Python-only |
| **openpyxl** / **python-docx** | `calamine` / `excelize` / `docx-rs` | 🔶 Partial | Office format support is limited in Rust |
| **odapython** | n/a | ❌ N/A | Proprietary CAD library; no Rust equivalent |

---

## Recommended PyO3 Architecture

A single Rust workspace (`engines/`) with crates that mirror the Python module hierarchy
where migration is justified:

```
engines/                          # Root Cargo workspace
├── Cargo.toml                    # Workspace members
│
├── _types/                       # Shared type definitions
│   ├── Cargo.toml
│   └── src/lib.rs                # RawData, Metadata, VariableValue, DmnValue, FeelContext
│                                 # All typed as enums or HashMap<String, serde_json::Value>
│
├── document/                     # Data models (the ~260 types)
│   ├── Cargo.toml
│   ├── src/
│   │   ├── lib.rs                # Re-exports
│   │   ├── base_types.rs         # BaseElement, BaseDocument, FormalExpression
│   │   ├── osdm.rs               # OSDM top-level document (orchestration definition)
│   │   ├── csdm.rs               # CSDM (CAD/Spatial) models + migration framework
│   │   ├── msdm.rs               # MSDM (Schema) models
│   │   ├── ssdm.rs               # SSDM (Service) models
│   │   ├── tsdm.rs               # TSDM (Tools) models
│   │   └── sub_models/
│   │       ├── bpmn.rs
│   │       ├── cmmn.rs
│   │       ├── dmn.rs
│   │       ├── scxml.rs
│   │       ├── cep.rs
│   │       └── petri.rs
│   └── tests/
│
├── orchestration/                # Runtime core
│   ├── Cargo.toml
│   └── src/
│       ├── lib.rs
│       ├── circuit_breaker.rs    # State machine (priority 1)
│       ├── compensation.rs       # Rollback manager (priority 1)
│       ├── command.rs            # Command trait + queue (priority 1)
│       ├── serializer.rs         # OsdmSerializer (priority 1 — largest perf win)
│       ├── state_machine.rs      # Generic state machine engine
│       ├── feel.rs               # FEEL expression engine (tokenizer, parser, evaluator)
│       ├── rate_limiter.rs       # Sliding window rate limiter
│       └── error.rs             # Unified error types
│
├── communication/                # Cross-cutting types only
│   ├── Cargo.toml
│   └── src/
│       ├── lib.rs
│       ├── circuit_breaker.rs    # (shared: the same state machine used across layers)
│       ├── serialization.rs      # Serialization traits (reused by PyO3 bridge)
│       └── types.rs
│
├── storage/                      # Trait definitions only
│   ├── Cargo.toml
│   └── src/
│       ├── lib.rs
│       ├── traits.rs             # KeyValueStorage, VectorStorage, etc. traits
│       └── memory_backends.rs    # In-memory HashMap/Vec implementations for testing
│
└── knowledge/                    # Algorithmic kernels only
    ├── Cargo.toml
    └── src/
        ├── lib.rs
        ├── graph/               # Graph algorithms (shortest path, subgraph, traversal)
        ├── scoring/             # ML scoring helpers
        └── chunking.rs          # Text chunking (reimplements document/chunking)
```

### PyO3 Binding Strategy

Use `pyo3` to expose Rust data structures as Python classes **only where Python code must consume them**:

```rust
// Example: document model exposed to Python for backward compat
#[pyclass]
#[derive(Serialize, Deserialize)]
pub struct BpmnDocument {
    #[pyo3(get, set)]
    pub id: String,
    #[pyo3(get, set)]
    pub name: Option<String>,
    #[pyo3(get, set)]
    pub processes: Vec<Process>,
}
```

For performance-critical paths, pass serialized JSON bytes across the boundary
and deserialize in Rust — avoids per-field PyO3 overhead:

```rust
// Fast path: JSON bytes in, JSON bytes out
#[pyfunction]
fn deserialize_bpmn(json_bytes: &[u8]) -> PyResult<Vec<u8>> {
    let doc: BpmnDocument = serde_json::from_slice(json_bytes)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
    // ... transform ...
    serde_json::to_vec(&result)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))
}
```

---

## Error Handling Strategy

### Single Rust Error Type Hierarchy

```rust
// Unified error type covering ALL migrated modules
#[derive(Debug, thiserror::Error)]
pub enum EngineError {
    // ── Validation Layer ──
    #[error("Validation error: {0}")]
    Validation(String),                        // replaces ValueError, DocumentValidationError

    // ── Domain-Specific ──
    #[error("Parse error: {0}")]
    Parse(String),                             // replaces DocumentParseError, PDFParseError, XmlParseError

    #[error("Write error: {0}")]
    Write(String),                             // replaces DocumentWriteError

    #[error("Execution error: {0}")]
    Execution(String),                         // replaces ExecutionError, RuntimeTaskError

    #[error("FEEL evaluation error: {0}")]
    FeelEvaluation(String),                    // replaces FEELError

    #[error("State machine error: {0}")]
    StateMachine(String),                      // replaces StateMachineError

    #[error("Circuit breaker open: {0}")]
    CircuitOpen(String),                       // replaces RuntimeError with circuit-open message

    #[error("Compensation failed: {0}")]
    Compensation(String),                      // replaces RuntimeError in rollback

    #[error("Variable conflict: {0}")]
    VariableConflict(String),                  // replaces VariableConflictError

    // ── I/O Layer ──
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),               // replaces OSError, FileNotFoundError

    #[error("Serialization error: {0}")]
    Serialization(#[from] serde_json::Error),  // replaces json.JSONDecodeError

    // ── External Service Layer ──
    #[error("Storage error: {0}")]
    Storage(String),                           // replaces RepositoryError

    #[error("External service error: {0}")]
    External(String),                          // replaces MCPAdapterError

    // ── Internal ──
    #[error("Internal error: {0}")]
    Internal(String),                          // replaces RuntimeError (catch-all)
}

// Severity levels mirroring Python's ErrorLevel enum
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ErrorSeverity {
    Warning,
    Error,
    Critical,
}

// Error source mirroring Python's ErrorSource enum
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ErrorSource {
    Orchestration,
    Bus,
    Communication,
    Storage,
    External,
    Serialization,
    Validation,
}
```

### Mapping from Python Exception Patterns

| Python Pattern | Rust Pattern |
|----------------|--------------|
| `raise ValueError(msg)` | `Err(EngineError::Validation(msg))` |
| `raise RuntimeError(msg)` | `Err(EngineError::Internal(msg))` |
| `raise DocumentParseError(msg)` | `Err(EngineError::Parse(msg))` |
| `raise FEELError(msg)` | `Err(EngineError::FeelEvaluation(msg))` |
| `try: ... except ValueError: ...` | `match result { Err(EngineError::Validation(_)) => ... }` |
| `try: ... except ImportError: ...` | `#[cfg(feature = "...")]` or `cfg!()` |
| `raise from e` (chain) | `#[error("...")]` with `#[source]` |

---

## Total Migration Effort Estimate

### Per-Module Estimates

| Module / Component | Files | Lines | Person-Days | Phase |
|--------------------|-------|-------|-------------|-------|
| **document/models** | 27 | 8,500 | ~16 | 1 |
| — base_types.rs | 2 | 330 | 1 | 1 |
| — osdm.rs | 1 | 1,766 | 3 | 1 |
| — csdm.rs | 3 | 1,616 | 2 | 1 |
| — msdm.rs | 1 | 1,342 | 2 | 1 |
| — ssdm.rs + tsdm.rs | 2 | 2,100 | 2 | 1 |
| — sub-models (6 mods) | 6 | ~1,800 | 3 | 1 |
| — tests | — | — | 3 | 1 |
| **orchestration/runtime — high value** | 7 | ~800 | ~8 | 1 |
| — circuit_breaker | 2 | 267 | 1.5 | 1 |
| — compensation | 1 | 45 | 0.5 | 1 |
| — command | 1 | 103 | 1 | 1 |
| — osdm_serializer | 1 | 481 | 3 | 1 |
| — rate_limiter | 1 | 139 | 1 | 1 |
| — state_snapshot | 1 | 140 | 1 | 1 |
| **orchestration/state_machine** | 10 | 1,239 | 3 | 1 |
| **orchestration/dmn — FEEL engine** | 1 | 874 | 5 | 1 |
| **document/chunking** | 3 | 147 | 1 | 2 |
| **orchestration/runtime — mixed** | 8 | 2,000 | ~12 | 3 |
| **document/ingestion** | 10 | 884 | 3 | 3 |
| **agent (core models + registry)** | 5 | 500 | 2 | 3 |
| **orchestration/bpmn** | 21 | 5,553 | 10 | 3 |
| **orchestration/cmmn** | 9 | 1,878 | 4 | 3 |
| **orchestration/cep** | 7 | 1,056 | 3 | 3 |
| **orchestration/validation** | 8 | 425 | 2 | 3 |
| **document/model_tools** | 4 | 155 | 1 | 3 |
| **document/utils** | 6 | 155 | 1 | 2 |
| **PyO3 bindings + integration** | — | — | 10 | All |
| **Testing + validation** | — | — | 15 | All |

### Overall Estimate

| Metric | Value |
|--------|-------|
| **Phase 1 (score 4-5, high value)** | ~90 files, ~12,000 lines → **~30 person-days** |
| **Phase 2 (score 3-4, medium value)** | ~25 files, ~2,000 lines → **~8 person-days** |
| **Phase 3 (score 2-3, lower value)** | ~70 files, ~12,000 lines → **~35 person-days** |
| **Kept in Python (score 1-2)** | ~900 files, ~136,000 lines → **0 person-days (stay)** |
| **PyO3 bindings + integration** | — → **~10 person-days** |
| **Testing across all phases** | — → **~15 person-days** |
| **Total** | **1,089 files, 161,918 lines** | **~98 person-days** |

### Risk Factors

1. **Serde untagged enum complexity**: Python's `str | int | float | bool | None | list | dict` union
   types (common in MSDM models, FEEL engine) require careful `#[serde(untagged)]` ordering.
   Incorrect ordering causes silent deserialization failures.

2. **PyO3 performance cliff**: Per-field `#[pyo3(get, set)]` is ~10x slower than passing
   serialized bytes. The JSON-bytes boundary pattern must be used for hot paths
   (serializer, circuit breaker checks).

3. **`asyncio` ↔ `tokio` bridging**: Async Python code calling Rust sync code via
   `loop.run_in_executor()` adds ~100μs overhead per call. Batch operations
   (serialize/deserialize) amortize this; per-call operations (circuit breaker checks) do not.

4. **FEEL engine parity risk**: The 874-line FEEL engine has ~80 built-in functions,
   temporal arithmetic, quantified expressions. Achieving full DMN 1.3 compliance
   in Rust requires a complete reimplementation (~5 person-days minimum).

5. **Circular dependency between `document_base.py` and `generic_models.py`**:
   Must be merged into one Rust module (all 6 files that depend on these must be updated).

6. **176 OSDM model types as single-file monolith**: `osdm_models.py` (1,766 lines)
   is the largest single file. Need to split into ~6 Rust modules.

7. **Storéd Python SDKs have no Rust equivalent**: `odapython` (CAD bridge),
   `autogen` (multi-agent framework), `arabic_reshaper` / `bidi` (text layout).
   These components must remain in Python permanently.

8. **`anyhow` vs `thiserror`**: Use `thiserror` for library crate error types
   (engine errors). Use `anyhow` only in binary/test crates.

---

*Generated from analysis of 1,089 Python files, 161,918 lines, using 2 existing
reports (`document/models`, `orchestration/runtime`) and direct source analysis
of the remaining 8 engine packages.*
