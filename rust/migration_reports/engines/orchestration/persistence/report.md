# Persistence Layer — Rust Migration Report

## Files Analyzed
- `__init__.py` (31 lines) — re-exports
- `repository.py` (171 lines) — `RepositoryProtocol`, `InMemoryRepository`, `PersistentRuntimeRepository`
- `runtime_records.py` (280 lines) — MSDM schema definitions, serialization
- `audit_log.py` (147 lines) — `AuditEntry`, `AuditLog`
- `definition_repository.py` (18 lines) — `DefinitionRepository`
- `event_repository.py` (84 lines) — `EventRepository`
- `history_repository.py` (230 lines) — `HistoryRepository`
- `instance_repository.py` (24 lines) — `InstanceRepository`
- `token_repository.py` (21 lines) — `TokenRepository`
- `variable_repository.py` (124 lines) — `VariableRepository`

## 1. Pre-refactor Patterns

| Pattern | Files | Details |
|---------|-------|---------|
| `Any` | repository.py:10, audit_log.py:12, runtime_records.py:8, etc. | Widespread — `**kwargs`, payload values |
| `dict[str, Any]` | repository.py:52-78, runtime_records.py:192-263, audit_log.py:57, etc. | Core data type (`RawData`, `Metadata`) |
| `isinstance` | runtime_records.py:202,207,208, history_repository.py:103-125, variable_repository.py:36,98-102 | Type dispatch in deserialization, aggregation |
| Global state | runtime_records.py:176-186 | Module-level `RUNTIME_SCHEMA`, entity registry |
| Mutable defaults | None | `field(default_factory=...)` in dataclasses |

## 2. Migration Notes & Rust Score

| File | Lines | Complexity | Rust Score | Notes |
|------|-------|-----------|------------|-------|
| repository.py | 171 | Medium | 4/5 | Abstract interfaces + async storage backends. Thread-safety with `Lock` → `Mutex` or `RwLock`. |
| runtime_records.py | 280 | Medium | 3/5 | Heavy DSDM/MSDM model coupling. Schema generation, entity building, JSON serialization. Tight coupling to document engine types. |
| audit_log.py | 147 | Low | 5/5 | Pure in-memory list with filter/sort. Trivial. |
| definition_repository.py | 18 | Low | 5/5 | Thin wrapper. |
| event_repository.py | 84 | Low | 4/5 | Correlator logic, temporal queries. |
| history_repository.py | 230 | Medium | 4/5 | Time-series bucketing, audit reconstruction. |
| instance_repository.py | 24 | Low | 5/5 | Trivial. |
| token_repository.py | 21 | Low | 5/5 | Trivial. |
| variable_repository.py | 124 | Low | 4/5 | MSDM schema binding, validation. Schema binding reconstruction is fragile. |

**Overall**: 4.3/5. Most repositories are thin wrappers. `runtime_records.py` is the risk — it's tightly coupled to the document engine's DSDM/MSDM model types.

## 3. Ownership Map

```
RepositoryProtocol (trait)
 └── InMemoryRepository (thread-safe dict store)
      └── PersistentRuntimeRepository (adds storage backends)
           ├── EventRepository
           ├── HistoryRepository
           ├── InstanceRepository
           ├── TokenRepository
           ├── VariableRepository
           └── DefinitionRepository (extends InMemoryRepository, not Persistent)

AuditLog (standalone)
 └── Vec<AuditEntry>, AuditQuery

Runtime Records:
RuntimeRecordEnvelope
RuntimeSchema / RuntimeEntityByRecordType
serialize_runtime_record / deserialize_runtime_record
normalize_runtime_payload
```

## 4. PyO3 Binding Structure

```rust
#[pyclass]
struct InMemoryRepository { data: RwLock<HashMap<String, RawData>> }

#[pyclass]
struct PersistentRuntimeRepository {
    inner: InMemoryRepository,
    key_value: Option<PyObject>,  // Python-storage bridge
    time_series: Option<PyObject>,
    log_storage: Option<PyObject>,
}

// Each repository subclass as #[pyclass] with inheritance via composition
```

## 5. Libraries Analysis

| Current Python | Rust Equivalent | Notes |
|---------------|----------------|-------|
| `threading.Lock` | `std::sync::{Mutex, RwLock}` | Thread safety |
| `json` | `serde_json` | Serialization |
| `datetime` | `chrono` | Timestamps |
| `uuid` | `uuid` crate | ID generation |
| Storage backends (kv/ts/log) | PyO3 bridge or Rust-native impl | `engines.storage.*` is Python — needs FFI or Rust rewrite |

## 6. Performance Hot Paths

- `AuditLog.query()` — O(n) list filter per query. With growing audit logs, this is unsustainable. Rust could use indexes or `rayon` for parallel filter.
- `HistoryRepository.query_time_series_aggregation()` — O(n) scan + datetime parsing + grouping. Rayon-friendly.
- `HistoryRepository.reconstruct_audit_trail()` — O(n) sequential reconstruction of sorted items.
- `PersistentRuntimeRepository._write_storage()` — 3 sequential async writes (kv + ts + log). Could be `tokio::join!` in Rust.

## 7. Error Handling

| Python | Rust Strategy |
|--------|---------------|
| `RepositoryError(RuntimeError)` | `thiserror` enum |
| `raise ValueError(...)` in variable_repo | `Result<(), ValidationError>` |
| `try/except ValueError` in time series | `filter_map` to skip bad records |
| `except Exception: return False` (admin_api) | Proper `Result<bool, RepoError>` |
