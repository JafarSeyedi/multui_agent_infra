# Runtime Layer — Rust Migration Analysis

## Files Analyzed (22 files)

| # | File | Lines | Role |
|---|------|-------|------|
| 1 | `osdm_serializer.py` | 481 | Serialization/deserialization (BPMN, CMMN, DMN, state machine) |
| 2 | `migration.py` | 345 | Process instance migration, batch operations |
| 3 | `external_task.py` | 297 | External task pattern (Camunda worker) |
| 4 | `error_handler.py` | 247 | Error capture, recovery, cross-layer error events |
| 5 | `incident_manager.py` | 207 | Incident lifecycle, retry, dead letter queue |
| 6 | `listeners.py` | 205 | Task & execution lifecycle listeners (Observer) |
| 7 | `state_manager.py` | 204 | Thread-safe state store + persistence |
| 8 | `circuit_breaker.py` | 174 | Circuit breaker + retry handler |
| 9 | `timer_manager.py` | 174 | Async timer scheduling (OSDM-aligned) |
| 10 | `async_continuation.py` | 155 | Async-before/after job management |
| 11 | `dynamic_injection.py` | 148 | Dynamic step injection |
| 12 | `state_snapshot.py` | 140 | State snapshots + crash recovery |
| 13 | `rate_limiter.py` | 139 | Sliding-window rate limiter |
| 14 | `tenant.py` | 105 | Multi-tenancy, contextvars |
| 15 | `command.py` | 103 | Command pattern (execute/undo) |
| 16 | `circuit_states.py` | 93 | State pattern for circuit breaker |
| 17 | `variable_manager.py` | 94 | Thread-safe variables + persistence |
| 18 | `compensation.py` | 45 | Compensation registration + rollback |
| 19 | `executor.py` | 43 | Sync/async execution wrapper |
| 20 | `resource_manager.py` | 39 | Async semaphore-based resource governance |
| 21 | `__init__.py` | 62 | Public API re-exports |
| 22 | `state_snapshot.py` | — | *(covered above)* |

---

## 1. Pre-Refactor Analysis

### `Any` / `dict[str, Any]` Usage

Every file uses `Any` and `dict[str, Any]` pervasively — this is the single largest migration concern:

| File | `Any` count | `dict[str, Any]` count |
|------|-------------|------------------------|
| `osdm_serializer.py` | ~5 | ~25 |
| `circuit_breaker.py` | ~10 | ~5 |
| `circuit_states.py` | 0 | 0 |
| `command.py` | ~6 | 0 |
| `compensation.py` | ~3 | 0 |
| `dynamic_injection.py` | ~10 | ~8 |
| `error_handler.py` | ~10 | ~10 |
| `executor.py` | ~8 | 0 |
| `external_task.py` | ~6 | ~4 |
| `incident_manager.py` | ~8 | ~4 |
| `listeners.py` | ~6 | ~3 |
| `migration.py` | ~12 | ~6 |
| `state_manager.py` | ~5 | ~3 |
| `state_snapshot.py` | ~10 | ~6 |
| `tenant.py` | ~3 | ~3 |
| `timer_manager.py` | ~4 | 0 |
| `variable_manager.py` | ~8 | ~2 |
| `rate_limiter.py` | ~2 | 0 |
| `resource_manager.py` | 0 | 0 |
| `async_continuation.py` | ~6 | ~3 |
| **Total** | **~120** | **~80** |

**Critical hotspots:**
- `OsdmSerializer` — `RawData` is `dict[str, Any]`, all flow element handlers take/return `dict[str, Any]`
- `dynamic_injection.py` — `InjectionRequest.new_activities: list[dict[str, Any]]`, `engine: Any`
- `error_handler.py` — `CrossLayerErrorEvent.payload: dict[str, Any]`, `event_bus: Any`
- `migration.py` — `ProcessInstanceMigrator._engine: Any`, `BatchOperationManager._engine: Any`, `DynamicInjectionManager._engine: Any`

### `isinstance` Chains

| Location | Pattern |
|----------|---------|
| `osdm_serializer.py:467-480` | `isinstance(element, SequenceFlow)`, `isinstance(element, BoundaryEvent)`, `isinstance(element, SubProcess)` |
| `state_manager.py:200-203` | `isinstance(value, datetime)`, `isinstance(value, str)` |
| `executor.py:29-30` | `asyncio.iscoroutinefunction(func)` |
| `error_handler.py:119-123` | `isinstance(exc, ExecutionError)` |
| `listeners.py:146-161` | Check on `listener.expression`, `listener.script`, `listener.class_name` |
| `runtime_records.py:202-213` | `isinstance(raw, Mapping)`, `isinstance(raw, (bytes, bytearray))` |

**Rust approach:** `isinstance` chains map to `match` + `downcast_ref` on `dyn Any` or enum dispatch.

### Async Patterns

| Pattern | Files |
|---------|-------|
| `async def` method | `circuit_breaker.py`, `command.py`, `dynamic_injection.py`, `executor.py`, `external_task.py`, `listeners.py`, `migration.py`, `state_manager.py`, `timer_manager.py`, `variable_manager.py`, `async_continuation.py` |
| `asyncio.create_task` | `external_task.py:127`, `timer_manager.py:109/141` |
| `asyncio.sleep` | `circuit_breaker.py:116`, `timer_manager.py:99/131`, `external_task.py:132` |
| `asyncio.gather` | `timer_manager.py:174` |
| `asyncio.Semaphore` | `resource_manager.py:22` |
| `@asynccontextmanager` | `resource_manager.py:29` |
| `Awaitable` isinstance check | `executor.py:41` |

**Key insight for Rust:** The async patterns fall into three categories:
1. **Wrappers around sync Python** (executor.py, listeners.py `_invoke_listener`) — keep in Python
2. **Event-loop scheduling** (timer_manager.py, external_task.py) — keep in Python
3. **Simple async methods calling sync code** (most managers) — these can become `async fn` in Rust with `tokio`

### Global State

| Type | File | Detail |
|------|------|--------|
| `ContextVar` (global) | `tenant.py:18` | `_current_tenant: ContextVar[str \| None]` |
| Module-level `Lock` | (none directly) | Instance-level locks in `state_manager.py:48`, `variable_manager.py:22`, `rate_limiter.py:47` |
| `threading.Lock` | `state_manager.py`, `variable_manager.py`, `rate_limiter.py` | Thread-safety for in-memory state |
| In-memory `dict` stores | All manager classes | Every manager maintains an in-memory dict of objects |

---

## 2. Migration Scores (1-5)

| Module | Score | Rationale |
|--------|-------|-----------|
| **Circuit Breaker** (`circuit_breaker.py` + `circuit_states.py`) | **5** | Pure state machine with well-defined transitions. `CircuitBreaker` + `CBState` state pattern maps directly to Rust enum + trait. No external deps. Trivially thread-safe with `Arc<RwLock>`. |
| **Compensation Handler** (`compensation.py`) | **4** | Pure logic — `CompensationManager` is a list of callables with LIFO iteration. Simple `Vec<CompensationStep>` in Rust. Score 4 (not 5) because `Callable` is harder to represent. |
| **OsdmSerializer** (`osdm_serializer.py`) | **4** | Pure data transformation `dict → OSDM objects`. High-value for Rust (JSON parsing via `serde_json`). Vast type hierarchy (176 OSDM model imports) makes this non-trivial — score 4. |
| **Command Pattern** (`command.py`) | **4** | Abstract `Command[T]` with `execute/undo`. Generic + async. Well-defined interface → trait in Rust. |
| **State Snapshot** (`state_snapshot.py`) | **3** | `StateSnapshot` + `CheckpointConfig` data structures are pure (score 5), but SnapshotManager has in-memory list + hashing. Mixed — split into data structs in Rust, management stay in Python. |
| **Rate Limiter** (`rate_limiter.py`) | **3** | Sliding window with `threading.Lock`. Pure algorithm but `time.time()` is platform-specific. Straightforward in Rust with `Instant` + `Mutex<VecDeque>`. |
| **Error Handler** (`error_handler.py`) | **2-3** | `CrossLayerErrorEvent` + OSDM conversion logic is pure (score 4), but `CrossLayerErrorHandler` depends on `event_bus: Any` → Python. Keep error event types in Rust, handler in Python. |
| **External Task** (`external_task.py`) | **2-3** | `ExternalTaskWorker` has `asyncio` polling loop with `Callable` handler — keep in Python. `ExternalTask` data + `ExternalTaskManager` storage could migrate (score 3). |
| **Incident Manager** (`incident_manager.py`) | **2-3** | Pure data structures (`Incident`, `RetryPolicy`) + management. But callbacks for `_retry_callbacks: dict[str, Callable]` tie to Python. Data structs in Rust, manager in Python. |
| **Async Continuation** (`async_continuation.py`) | **2-3** | `AsyncJob` data is pure, but `handler: Callable` is Python callback. Data structs in Rust. |
| **Static/Dynamic Injection** (`dynamic_injection.py`) | **2** | Heavy `engine: Any` dependency. All 3 injection methods call `instance.set_variable()`. Keep in Python. |
| **Migration** (`migration.py`) | **2** | `ProcessInstanceMigrator` + `BatchOperationManager` both depend on `engine: Any`. Heavy Python coupling. |
| **Listeners** (`listeners.py`) | **2** | `_BaseListenerManager` depends on `Callable`, `PythonEvaluator`, `FEELEngine`. Python evaluation logic. |
| **Timer Manager** (`timer_manager.py`) | **1-2** | Pure `asyncio.create_task` scheduling. Keep in Python. `OsDmTimerDefinition` + `TimerHandle` data structs could migrate (score 3). |
| **State Manager** (`state_manager.py`) | **2** | `InstanceStateSnapshot` data is pure, but `StateManager` ties to `KeyValueStorage`, `TimeSeriesStorage`, `LogStorage` — all Python async storage backends. |
| **Variable Manager** (`variable_manager.py`) | **2** | `VariableRepository` dependency keeps this Python-bound. `VariableConflictError` + `VariableManager` in-memory logic is simple. |
| **Executor** (`executor.py`) | **2** | Tiny wrapper around `asyncio.iscoroutinefunction`. Not worth migrating — trivial overhead. |
| **Resource Manager** (`resource_manager.py`) | **1-2** | Thin wrapper around `asyncio.Semaphore`. Keep in Python. |
| **Tenant** (`tenant.py`) | **1** | `ContextVar` + `contextmanager`. Python-specific concurrency mechanism. Keep in Python. |

### Summary

```
Score 5:  circuit_breaker + circuit_states       (pure state machine)
Score 4:  compensation, osdm_serializer, command  (pure logic/data transform)
Score 3:  state_snapshot, rate_limiter            (mixed: pure data + management)
Score 2:  error_handler, external_task, incident, async_continuation, migration, listeners, state_manager, variable_manager, executor, resource_manager
Score 1:  tenant, timer_manager, dynamic_injection
```

---

## 3. Ownership Map: Runtime State → Persistence → Recovery Cycle

```
┌─────────────────────────────────────────────────────────────────┐
│                        RUNTIME STATE                             │
│                                                                   │
│  In-Memory (thread-safe)        Persisted (via storage backends)  │
│  ┌─────────────────────┐        ┌──────────────────────────────┐ │
│  │ StateManager        │───────▶│ KeyValueStorage (snapshots)   │ │
│  │  _states: dict      │        │ TimeSeriesStorage (metrics)   │ │
│  │  _history: dict     │        │ LogStorage (audit events)     │ │
│  │ VariableManager     │───────▶│ VariableRepository             │ │
│  │  _vars: dict        │        │  (DSDM-serialized JSON)       │ │
│  │ StateSnapshotManager│        │                              │ │
│  │  _snapshots: dict   │        │ (no direct persistence)       │ │
│  │ IncidentManager     │        │ (no direct persistence)       │ │
│  │ ExternalTaskManager │        │ (no direct persistence)       │ │
│  │ AsyncContinuation   │        │ (no direct persistence)       │ │
│  │ CircuitBreaker      │        │ (no direct persistence)       │ │
│  └─────────────────────┘        └──────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
                    RECOVERY CYCLE
    ┌─────────────────────────────────────────────┐
    │ 1. Crash/restart detected                    │
    │ 2. StateManager.load_persisted(instance_id)  │
    │    → KeyValueStorage.get(snapshot_key)       │
    │    → deserialize_runtime_record(raw)         │
    │    → hydrate _states dict                    │
    │ 3. VariableManager.restore_persisted()       │
    │    → VariableRepository.get_by_instance()    │
    │ 4. StateSnapshotManager.restore_latest()     │
    │    → return in-memory dict                   │
    │ 5. TimerManager (rebuild from persisted)     │
    │    → reschedule from TimerRecord             │
    └─────────────────────────────────────────────┘
```

**Bottleneck:** Every write goes through DSDM serialization pipeline (`JSONWriter.write` → `bytes` → JSON string). This is the primary persistence bottleneck.

---

## 4. PyO3 Binding Structure

### Recommended Rust Boundary

```
Python (keep)                          Rust (migrate)
─────────────────────────────────────────────────────

TenantManager                          CircuitBreaker
TimerManager                           CircuitBreakerRegistry
ResourceManager                        RetryHandler (sync path)
AsyncContinuationManager               RetryConfig
DynamicInjectionManager                CompensationManager
ExternalTaskWorker (async poll loop)   CompensationStep
Listeners (FEEL engine bridge)         Command<T> trait
IncidentManager                        CommandQueue
StateManager                           StateSnapshot (data struct)
VariableManager                        CheckpointConfig
BatchOperationManager                  OsdmSerializer
ProcessInstanceMigrator                OsdmDeserializer
ErrorResolver (event_bus binding)      SerializationContext
CrossLayerErrorHandler                 SerializationResult
RuntimeExecutor                        ExecutionOutcome
                                       RuntimeTaskError
                                       RateLimiter
                                       RateLimitConfig
                                       ErrorLevel, ErrorSource
                                       ErrorRecord
                                       ErrorRecoveryContext
                                       CrossLayerErrorEvent
                                       Incident, RetryPolicy
                                       ExternalTask (data)
                                       ExternalTaskQuery
                                       TaskListener, ExecutionListener
                                       ListenerInvocation
                                       InjectionRequest
                                       InjectionResult
                                       MigrationPlan
                                       MigrationResult
                                       MigrationMapping
                                       BatchOperation
                                       AsyncJob
```

### Compile-Time State Machines (Rust)

```rust
// circuit_breaker — STATE MACHINE (score 5)
pub enum CircuitState {
    Closed { failure_count: u64 },
    Open { since: Instant },
    HalfOpen { success_count: u64, calls: u64 },
}

impl CircuitState {
    fn can_execute(&self, config: &CircuitBreakerConfig) -> bool { ... }
    fn record_success(self, config: &CircuitBreakerConfig) -> Self { ... }
    fn record_failure(self, config: &CircuitBreakerConfig) -> Self { ... }
}

// compensation — PURE LOGIC (score 4)
pub struct CompensationManager {
    steps: Vec<CompensationStep>,
}

impl CompensationManager {
    pub fn register(&mut self, step: CompensationStep) { ... }
    pub fn rollback(&mut self) -> Vec<String> { ... }
}

// serializer — DATA TRANSFORM (score 4)
pub struct OsdmSerializer;

impl OsdmSerializer {
    pub fn serialize_bpmn(&self, data: RawData) -> Result<BpmnDocument> { ... }
    pub fn deserialize_bpmn(&self, doc: &BpmnDocument) -> Result<RawData> { ... }
}
```

### Keep in Python (I/O boundary):

```python
# TimerManager — asyncio scheduling
# ExternalTaskWorker — polling loop + callback
# CrossLayerErrorHandler — event_bus publish
# DynamicInjectionManager — engine reference
# StateManager — storage backends
```

---

## 5. Libraries Analysis

### External Dependencies (no external libs within runtime layer)

The runtime layer itself imports **zero** external libraries. All dependencies are intra-package:

| Import Source | Files | What's Used |
|--------------|-------|-------------|
| `engines._types` | `listeners.py`, `osdm_serializer.py` | `RawData`, `FeelContext`, `Metadata` (all `dict[str, Any]` aliases) |
| `engines.document.models.osdm_models` | `osdm_serializer.py`, `error_handler.py`, `timer_manager.py` | 176 OSDM model classes |
| `engines.document.models.media_types` | `osdm_serializer.py`, `__init__.py` | `MEDIA_TYPES` registry |
| `engines.document.models.dsdm_models` | `__init__.py` → `runtime_records.py` | `DataDocument`, `DataSchemaReference` |
| `engines.storage.{event_log,key_value,timeseries}.base` | `state_manager.py` | `LogStorage`, `KeyValueStorage`, `TimeSeriesStorage` |
| `..core.instance` | `migration.py`, `incident_manager.py` | `InstanceState` enum |
| `..core._context_protocols` | `circuit_states.py` | `ICircuitBreaker` protocol |
| `..persistence.runtime_records` | `state_manager.py`, `__init__.py` | Serialization/deserialization helpers |
| `..persistence.variable_repository` | `variable_manager.py` | `VariableRepository` |
| `..expression.evaluator` | `listeners.py` | `EvaluationContext` |
| `..expression.python_evaluator` | `listeners.py` | `PythonEvaluator` |
| `..dmn.feel_engine` | `listeners.py` | `FEELEngine` |
| `..utils.time_utils` | `timer_manager.py` | `parse_duration`, `utc_now` |

**Standard library only:** `asyncio`, `threading`, `time`, `datetime`, `dataclasses`, `enum`, `abc`, `json`, `hashlib`, `random`, `contextvars`, `contextlib`, `uuid`, `logging`, `collections.abc`, `typing`.

**No PyPI dependencies** in the runtime layer itself. All external deps are at the `engines.document` layer (which the runtime imports). This means:
- OSDM model types are the only "heavy" import — they carry a large Pydantic model hierarchy
- Storage backends (`KeyValueStorage`, etc.) are protocol/abstract-base classes
- Rust migration of OSDM models is the primary external-dependency concern

---

## 6. Performance Hot Paths

| Hot Path | Location | Throughput | Current Cost | Rust Benefit |
|----------|----------|------------|-------------|--------------|
| **State transitions** | `StateManager.set()` | Thousands/sec per engine | `threading.Lock` + `dict` copy + snapshot creation | `Arc<RwLock<HashMap>>` — zero-copy reads |
| **Circuit breaker checks** | `CircuitBreaker.can_execute()` | Every operation | `_state_obj.can_execute()` → dynamic dispatch | Static dispatch via enum → inlineable |
| **Retry delay calc** | `RetryConfig.get_delay()` | Every retry attempt | Pure float math | Identical perf |
| **Serialization** | `OsdmSerializer._dict_to_process()` | Every API call/response | 176+ model constructors + deep dict walk | `serde_json` → zero-copy deserialization, 10-50x faster |
| **Snapshot write** | `StateManager.persist_snapshot()` | Every state change | DSDM pipeline → JSON string → KV store | `serde_json::to_string` directly |
| **Rate limiter check** | `RateLimiter.check()` | Every external API call | `threading.Lock` + list filter | `Mutex<VecDeque<Instant>>` — identical perf |
| **Timer scheduling** | `TimerManager.schedule()` | Per timer creation | `asyncio.create_task` | Keep in Python (async I/O) |
| **External task fetch** | `ExternalTaskManager.fetch_and_lock()` | Worker polling | Dict iteration + datetime parsing | `HashMap` iteration + `chrono` parsing |
| **Incident query** | `IncidentManager.query_incidents()` | Monitoring/UI | List comprehension filter | `Vec` iteration → similar perf |

**The #1 bottleneck:** `OsdmSerializer` — called on every API request/response cycle. Must build 176 Pydantic model types from `dict[str, Any]`. This is the highest-value Rust migration target.

**The #2 bottleneck:** `StateManager` — `dict` copy on every read/write. `threading.Lock` contention at high concurrency.

---

## 7. Error Handling

### Error Types (exceptions defined in runtime)

```python
RuntimeTaskError(RuntimeError)        # executor.py — task invocation failure
ExecutionError(RuntimeError)          # error_handler.py — engine execution failure
VariableConflictError(ValueError)     # variable_manager.py — variable conflict
```

### Error Levels & Sources

```python
class ErrorLevel(Enum):               # WARNING, ERROR, CRITICAL
class ErrorSource(Enum):              # ORCHESTRATION, BUS, COMMUNICATION, STORAGE, EXTERNAL
class IncidentType(str, Enum):        # 10 incident types (JOB, TASK, CONDITION, TIMER, etc.)
class IncidentState(str, Enum):       # OPEN, RETRYING, RESOLVED, DEAD_LETTER, CANCELLED
```

### Retry Patterns

| Pattern | Location | Mechanism |
|---------|----------|-----------|
| **Exponential backoff** | `RetryHandler` + `RetryConfig` | `get_delay()` with jitter, `asyncio.sleep` / `time.sleep` |
| **Async vs sync retry** | `circuit_breaker.py:91-148` | Dual paths: `execute_with_retry` (async) and `execute_with_retry_sync` (blocking) |
| **Circuit breaker** | `CircuitBreaker` + states | Closed → Open (threshold) → Half-Open (timeout) → Closed/Open |
| **Incident retry** | `IncidentManager.create_incident` | Tracks retry_count, moves to DEAD_LETTER on exhaustion |
| **Job retry** | `AsyncContinuationManager.execute_job` | Decrements `retries`, marks FAILED when exhausted |
| **External task retry** | `ExternalTaskManager.fail` | Decrements `retries`, reverts to PENDING or FAILED |

### Recovery Flow

```
Operation fails
  │
  ▼
RetryHandler.execute_with_retry()    ─── CircuitBreaker checks
  │                                         │
  ├── retry → asyncio.sleep(delay)          ├── CLOSED → allow
  │         (up to max_attempts)            ├── OPEN → reject immediately
  │                                          └── HALF_OPEN → allow (limited)
  └── exhausted ──────────────►
         │
         ▼
  ErrorResolver.handle()
         │
         ├── ExecutionError → ERROR level
         └── Other → CRITICAL level
                │
                ▼
         CrossLayerErrorHandler
         └── _publish_error_event(event_bus)
                │
                ▼
         IncidentManager.create_incident()
         ├── retry_count++
         └── retry_exhausted → move_to_dead_letter()
```

### Rust Error Mapping

```rust
#[derive(Debug, thiserror::Error)]
pub enum RuntimeError {
    #[error("Task execution failed: {0}")]
    TaskError(String),

    #[error("Execution error: {0}")]
    ExecutionError(String),

    #[error("Variable conflict: {0}")]
    VariableConflict(String),

    #[error("Circuit breaker open: {0}")]
    CircuitOpen(String),

    #[error("Compensation failed: {0}")]
    CompensationFailed(String),
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ErrorLevel { Warning, Error, Critical }

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ErrorSource { Orchestration, Bus, Communication, Storage, External }
```

---

## Summary: Migration Priority Order

```
Priority 1 (High value, low coupling):
  CircuitBreaker + CircuitStates   → Rust enum state machine
  RetryConfig + RetryHandler       → Rust struct with methods (sync path)
  CompensationManager              → Rust Vec<CompensationStep>
  Command trait + CommandQueue     → Rust trait + Vec<CommandEntry>
  ExecutionOutcome                 → Rust Result<ExecutionOutcome>

Priority 2 (Medium value, higher coupling):
  OsdmSerializer + OsdmDeserializer → Rust serde_json (biggest perf win)
  StateSnapshot data structures      → Rust structs
  RateLimiter                        → Rust Mutex<VecDeque<Instant>>
  ErrorRecord, CrossLayerErrorEvent  → Rust structs + thiserror

Priority 3 (Low priority — keep in Python):
  TimerManager, ExternalTaskWorker   → Pure async I/O
  StateManager, VariableManager      → Storage backend coupling
  Listeners                          → FEEL/Python evaluation
  Tenant                             → ContextVar (Python-specific)
  DynamicInjection, Migration        → `engine: Any` coupling
```
