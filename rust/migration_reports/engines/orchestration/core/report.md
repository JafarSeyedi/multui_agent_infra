# Migration Report: `engines/orchestration/core/`

**21 Python files analyzed** — 0 modified. Report generated for Rust migration preparation.

---

## 1. Pre-Refactor Analysis

### `Any` usage — pervasive across codebase

Every file imports `Any` from `typing`. The shared `engines/_types.py` defines `VariableValue: TypeAlias = Any`, `Metadata: TypeAlias = dict[str, Any]`, `RawData: TypeAlias = dict[str, Any]`, `FeelContext: TypeAlias = dict[str, Any]` — these type aliases are used ubiquitously across all 21 files. This is the single largest obstacle to Rust migration.

**Count by file:**
| File | Notable `Any`/`dict[str,Any]` usage |
|------|--------------------------------------|
| `engine.py` | `self.engine_handlers: dict[str, Any]`, `self._bam_engine: Any`, all `_definition_to_dict`/`_definition_from_dict` return/signatures |
| `engine_services.py` | All Protocol signatures return `Any`, `config: Any = None`, `_BamEngine`, `_StateManager`, `_VariableManager` protocols |
| `instance.py` | `get_metadata(..., default: Any) -> Any`, `from_record_payload` uses `cast(dict[str, Any], ...)` |
| `token.py` | `repository: Any | None`, `get_metadata(..., default: Any) -> Any` |
| `transaction.py` | `participants: dict[str, Any]`, `metadata: dict[str, Any]`, `log: list[dict[str, Any]]` |
| `context.py` | `SchemaBinding`, `_schema_registry: dict[str, Entity]`, `get_metadata(..., default: Any) -> Any` |
| `event_bus.py` | `data: dict[str, Any]`, `Event.to_dict/from_record_payload` return dict[str,Any] |
| `correlation.py` | `payload: dict[str, Any]`, all `to_dict` returns `dict[str, Any]` |
| `scheduler.py` | `schedule_data: dict[str, Any]`, `metadata: dict[str, Any]` |
| `engine_bridge.py` | `raw_engine: Any`, `_GenericImplementor` |
| `proxies.py` | All storage backend duck-typed as `Any` |
| `factories.py` | `StorageBackendFactory` uses `Any` for config |
| `decorators.py` | `execute(context: Metadata) -> Any` — `Metadata` is `dict[str, Any]` |
| `builders.py` | `extra: dict[str, Any]`, `**kwargs: Any` |

### `isinstance` chains

- **`_parse_datetime(value: Any) -> datetime`** — identical pattern in 6 files (`engine.py`, `engine_services.py`, `instance.py`, `token.py`, `context.py`, `event_bus.py`, `correlation.py`):
  ```python
  if isinstance(value, datetime): return value
  if isinstance(value, str): return datetime.fromisoformat(value)
  return datetime.utcnow()
  ```
- **`_optional_str(value: Any) -> str | None`** — identical in 3 files (`instance.py`, `token.py`, `event_bus.py`):
  ```python
  return None if value is None else str(value)
  ```
- **`from_record_payload` methods** — isinstance checks for nested payload dicts throughout `instance.py`, `token.py`, `event_bus.py`, `context.py`
- **`asyncio.iscoroutinefunction`** — in `transaction.py` `_do_prepare`, `_do_commit`, `_do_rollback` methods
- **`isinstance(self._inner, ExecutionDecorator)`** — in `decorators.py` for decorator chaining

### Global state (mutable module-level)

- **`instance_states.py:262`** — `_STATE_MAP: dict[str, ProcessState] = {}` — lazy-populated global registry
- **`token_states.py:160`** — `_STATE_MAP: dict[str, TokenState] = {}` — lazy-populated global registry

These are lazy-init caches mapping enum values → singleton state objects. Prime candidates for Rust `match` or `HashMap<StateEnum, State>`.

### Mutable default arguments

No mutable default arguments found. All dataclasses use `field(default_factory=...)` correctly. Methods use `Optional` type hints with `None` defaults.

### `# type: ignore`

- **`factories.py:109`** — `from engines.storage.sql_storage import SQLStorage  # type: ignore[import-not-found]`
- **`factories.py:120`** — `from engines.storage.file_storage import FileStorage  # type: ignore[import-not-found]`

Both are inside `try/except ImportError` blocks for optional/fallback storage backends.

### State Pattern Analysis — Prime Rust Enum Candidates

Four independent state machine implementations, each following the same architecture:
ABC base → concrete state classes → Protocol for context → global registry map

#### 1. `engine_states.py` (140 lines)
- Abstract: `EngineState(ABC)` — `start()`, `stop()`, `pause()`, `resume()`, `name`
- Concrete: `StoppedState`, `StartingState`, `RunningState`, `PausedState`, `StoppingState`, `ErrorState` (6 states)
- Protocol: `IEngine` (from `_context_protocols.py`) — `_lifecycle_state: EngineState`
- Transitions: state → engine._lifecycle_state = NextState()

#### 2. `instance_states.py` (280 lines)
- Abstract: `ProcessState(ABC)` — `suspend()`, `resume()`, `complete()`, `terminate()`, `fail()`
- Concrete: `_ActiveState`, `_SuspendedState`, `_CompletedState`, `_FailedState`, `_TerminatedState`, `_DraftState`, `_ClosedState`, `_CompensatingState`, `_MigratingState` (9 states)
- Protocol: `IProcessInstance` — `set_state(state, state_obj)`, `_calculate_duration()`
- Global: `_STATE_MAP` + `state_for(enum_value)` function

#### 3. `token_states.py` (174 lines)
- Abstract: `TokenState(ABC)` — `wait()`, `resume()`, `complete()`, `terminate()`, `merge()`
- Concrete: `_ActiveTokenState`, `_WaitingTokenState`, `_CompletedTokenState`, `_TerminatedTokenState`, `_MergedTokenState` (5 states)
- Protocol: `IToken` — `set_state(state, state_obj)`
- Global: `_STATE_MAP` + `token_state_for(enum_value)` function

#### 4. `transaction_states.py` (167 lines)
- Abstract: `TransactionState(ABC)` — `prepare()`, `commit()`, `rollback()`, `name`
- Concrete: `ActiveState`, `PreparingState`, `PreparedState`, `CommittingState`, `CommittedState`, `RollingBackState`, `RolledBackState`, `FailedState` (8 states)
- Protocol: `ITransactionScope` — `_do_prepare()`, `_do_commit()`, `_do_rollback()`

---

## 2. Migration Notes — Function Scoring

| Score | Category | Files | Rationale |
|-------|----------|-------|-----------|
| **5/5** | State Machines | `engine_states.py`, `instance_states.py`, `token_states.py`, `transaction_states.py` | Direct 1:1 mapping to Rust enums with `match`. No Python-isms. Clear state-to-state transitions. Protocols break circular imports — Rust's module system eliminates this need entirely. The `_STATE_MAP` globals become dead code. |
| **4/5** | Data Models + Managers | `token.py`, `instance.py`, `transaction.py`, `correlation.py`, `event_bus.py` | Rich behavior, multiple indexes, CRUD operations. Requires `HashMap`-based managers. Token splitting/merging is non-trivial. EventBus async queue maps to `tokio::mpsc`. Correlation messages need careful lifetime design. DSDM/OSDM imports add dependency complexity. |
| **3/5** | Engine Facade + Services | `engine.py`, `engine_services.py` | `OrchestrationEngine.__init__` is massive (creates 25+ sub-components). PyO3 will need careful ownership planning. Services use Protocol-based duck typing → trait objects in Rust. Recovery/definition services are straightforward. |
| **2/5** | Pattern Implementations | `decorators.py`, `engine_bridge.py`, `proxies.py`, `builders.py` | Python-specific patterns (decorators wrapping callables, duck-typed auto-detection of engine types) need rethinking for Rust. Bridge pattern adapts well. Proxy pattern needs trait objects. Builder pattern is clean. |
| **1/5** | Infrastructure | `factories.py` | Dynamic `try/except ImportError` won't work in Rust. Conditional compilation (`cfg(feature = "sql")`) is the Rust equivalent. `# type: ignore` indicates optional dependency — use feature flags. |

---

## 3. Ownership Map

```
OrchestrationEngine (root owner)
├── self.instances: HashMap<String, ProcessInstance>        ← lifecycle managed by engine
├── self.deployments: HashMap<String, Deployment>           ← deploy/delete_deployment
├── self.definitions: HashMap<String, ProcessDefinition>    ← loaded from DefinitionService
├── self.definition_versions: HashMap<String, Vec<ProcessDefinition>>
├── self.active_instances: HashSet<String>                   ← ID set (temporary)
├── self.suspended_instances: HashSet<String>
├── self.engine_handlers: HashMap<String, Box<dyn EngineHandler>>
└── self._bam_engine: Option<BamEngine>

  ├──► InstanceManager
  │     ├── instances: HashMap<String, ProcessInstance>     ← SHARED REF with engine.instances? Or owned?
  │     ├── business_key_index: HashMap<String, HashSet<String>>
  │     └── definition_index: HashMap<String, HashSet<String>>
  │
  ├──► TokenManager
  │     ├── tokens: HashMap<String, Token>
  │     ├── instance_tokens: HashMap<String, HashSet<String>>
  │     └── element_tokens: HashMap<String, HashSet<String>>
  │
  ├──► TransactionManager
  │     ├── transactions: HashMap<String, TransactionScope>
  │     └── active_transactions: HashSet<String>
  │
  ├──► ContextManager
  │     ├── contexts: HashMap<String, ExecutionContext>
  │     └── root_contexts: HashSet<String>
  │
  ├──► CorrelationEngine
  │     ├── message_subscriptions: HashMap<String, MessageSubscription>
  │     ├── message_name_index: HashMap<String, HashSet<String>>
  │     ├── event_subscriptions: HashMap<String, EventSubscription>
  │     └── buffered_messages: Vec<Message>
  │
  ├──► EventBus
  │     ├── subscriptions: HashMap<String, Subscription>
  │     ├── type_subscriptions: BTreeMap<EventType, HashSet<String>>
  │     ├── event_queue: tokio::mpsc::Sender<Event>
  │     └── event_history: VecDeque<Event>
  │
  └──► Scheduler
        ├── tasks: HashMap<String, ScheduledTask>
        └── task_heap: BinaryHeap<ScheduledTask>

Services (owned by Engine, operate on refs):
  ├── DefinitionService      (&definitions, &definition_versions, &definition_repository)
  ├── InstanceService        (&instance_manager, &token_manager, &variable_manager, &event_bus, ...)
  ├── RecoveryService        (&instance_manager, &token_manager, &state_manager, &definitions, ...)
  └── EngineLifecycleService  (&event_bus, &scheduler, &recovery_service, &bam_engine)

Storage (repository traits):
  ├── EventRepository
  ├── InstanceRepository
  ├── TokenRepository
  ├── DefinitionRepository
  ├── VariableRepository
  └── HistoryRepository
```

**Key design decision**: In Python, the Engine creates manager objects and passes their refs to services. In Rust, the Engine should own all managers directly, and services should take `&mut Manager` references. Alternatively, use `Arc<RwLock<Manager>>` for shared mutable access.

---

## 4. PyO3 Binding Structure

```
pyo3_orchestration/
├── Cargo.toml
└── src/
    ├── lib.rs                          ← PyO3 init, module registration
    ├── engine/
    │   ├── mod.rs                      ← PyOrchestrationEngine (main PyO3 class)
    │   ├── config.rs                   ← EngineConfig
    │   └── deployment.rs               ← Deployment, deployment types
    ├── services/
    │   ├── mod.rs
    │   ├── lifecycle.rs                ← EngineLifecycleService
    │   ├── instance_service.rs         ← InstanceService
    │   ├── recovery.rs                 ← RecoveryService
    │   └── definition.rs               ← DefinitionService
    ├── state_machine/
    │   ├── mod.rs
    │   ├── engine_states.rs            ← EngineState enum + match transitions
    │   ├── instance_states.rs          ← ProcessState enum + match transitions
    │   ├── token_states.rs             ← TokenState enum + match transitions
    │   └── transaction_states.rs       ← TransactionState enum + match transitions
    ├── models/
    │   ├── mod.rs
    │   ├── process_definition.rs       ← ProcessDefinition (derive PyO3)
    │   ├── process_instance.rs         ← ProcessInstance, InstanceState, InstanceType
    │   ├── token.rs                    ← Token, TokenStateEnum, TokenType, TokenSnapshot
    │   ├── transaction.rs              ← TransactionScope, TransactionParticipant, CompensationAction
    │   ├── activity.rs                 ← ActivityInstance, IncidentInfo
    │   └── variable.rs                 ← Variable, VariableScope
    ├── event_bus/
    │   ├── mod.rs
    │   ├── event.rs                    ← Event, EventType, EventPriority
    │   ├── bus.rs                      ← EventBus
    │   └── subscription.rs             ← Subscription
    ├── correlation/
    │   ├── mod.rs
    │   ├── engine.rs                   ← CorrelationEngine
    │   ├── message.rs                  ← Message, MessageSubscription
    │   └── key.rs                      ← CorrelationKey, CorrelationKeySet
    ├── scheduler/
    │   ├── mod.rs
    │   ├── scheduler.rs                ← Scheduler
    │   └── task.rs                     ← ScheduledTask, TaskState, ScheduleType
    ├── context/
    │   ├── mod.rs
    │   ├── execution_context.rs        ← ExecutionContext
    │   └── manager.rs                  ← ContextManager
    ├── managers/
    │   ├── mod.rs
    │   ├── instance_manager.rs         ← InstanceManager
    │   ├── token_manager.rs            ← TokenManager
    │   └── transaction_manager.rs      ← TransactionManager
    ├── patterns/
    │   ├── mod.rs
    │   ├── decorator.rs                ← ExecutionDecorator trait + impls
    │   ├── bridge.rs                   ← EngineBridge, EngineImplementor, ProcessEngine
    │   ├── proxy.rs                    ← LazyInitProxy, CachingProxy, EngineProtectionProxy
    │   ├── builder.rs                  ← EngineConfigBuilder
    │   └── factory.rs                  ← StorageBackendFactory
    └── storage/
        ├── mod.rs
        ├── backend.rs                  ← StorageBackend trait
        ├── memory.rs                   ← InMemoryBackend
        └── sql_adapter.rs              ← SQL backend adapter (feature-gated)
```

**PyO3 exposure strategy:**
- `OrchestrationEngine` → `#[pyclass]` with `#[pymethods]` for `start()`, `stop()`, `pause()`, `resume()`, `deploy()`, `start_process_instance()`, etc.
- State enums → `#[pyclass]` with `#[derive(Clone, PartialEq)]`
- Managers → not exposed to Python directly; accessed through engine methods
- Repository traits → `#[pyclass]` trait implementations in Python adapter layer

---

## 5. Libraries Analysis

### External/Internal Imports (blockers for isolated Rust migration)

| Import Source | Used By | Notes |
|---------------|---------|-------|
| `engines.document.models.osdm_models` | `instance.py`, `token.py`, `correlation.py`, `event_bus.py` | Process, Stage, Decision, FlowNode types — dependency on document engine |
| `engines.document.models.dsdm_models` | `instance.py`, `context.py` | DataDocument, SchemaBinding — serialization layer |
| `engines.document.models.msdm_models` | `context.py` | Entity, Attribute, DataType — schema binding |
| `engines.document.models.media_types` | `instance.py`, `context.py` | MEDIA_TYPES registry |
| `engines.document.parsers.dsdm_parsers.dsdm_utils` | `instance.py`, `context.py` | `build_node_from_python` — DSDM serialization |
| `engines.document.writers.dsdm_writers.json_writer` | `instance.py`, `context.py` | `JSONWriter` — DSDM serialization |
| `engines.orchestration.persistence.*` | `engine.py`, `event_bus.py`, `correlation.py`, `scheduler.py` | Repository classes for persistence |
| `engines.orchestration.runtime.*` | `engine.py` | StateManager, VariableManager, IncidentManager, etc. |
| `engines.orchestration.validation.osdm_validator` | `engine.py` | BPMN/CMMN/DMN validators |
| `engines.orchestration.monitoring.*` | `engine.py` | MetricsCollector, ProcessHeatmap, etc. |
| `engines.orchestration.forms.form_engine` | `engine.py` | FormEngine |
| `engines.orchestration.utils.time_utils` | `token.py`, `scheduler.py` | `parse_duration` — utility function |
| `engines.orchestration.core._context_protocols` | `engine_states.py`, `instance_states.py`, `token_states.py`, `transaction_states.py` | Circular import breakers |
| `engines.orchestration.core._definition_models` | `engine.py`, `engine_services.py` | Shared definition models |

### Python Standard Library Only (in this directory)

`abc`, `asyncio`, `dataclasses`, `datetime`, `enum`, `functools`, `heapq`, `logging`, `re` (inline imports), `time`, `typing`, `collections.abc`, `contextlib`, `copy`, `uuid`, `collections`

**Rust equivalents:**
- `asyncio` → `tokio`
- `dataclasses` → `#[derive(Clone)]` + `impl` constructors
- `datetime` → `chrono`
- `enum` → Rust native `enum`
- `functools.wraps` → not needed (Rust doesn't have decorators)
- `heapq` → `std::collections::BinaryHeap`
- `logging` → `log` + `env_logger`
- `re` → `regex`
- `time` → `std::time::Instant`
- `typing.Protocol` → Rust traits
- `copy.deepcopy` → `Clone` trait
- `uuid4` → `uuid` crate
- `defaultdict` → `Entry::or_default()` pattern
- `OrderedDict` → `indexmap` crate
- `asynccontextmanager` → RAII pattern

---

## 6. Performance Hot Paths

### Critical (per-activity-execution)

1. **TokenManager operations** (`token.py`):
   - `create_token` — called for every execution step/activity
   - `split_token` / `merge_tokens` — parallel gateway execution
   - `get_instance_tokens` / `get_active_tokens` — frequent query pattern
   - `persist_token` / `load_instance_tokens` — recovery path
   - Outcome: TokenManager is the hottest object. The index structures (3 HashMaps with HashSet values) should be optimized with small-map optimizations. Consider `dashmap` for concurrent access.

2. **State transitions** (`transaction.py`):
   - `_do_prepare`, `_do_commit`, `_do_rollback` — each calls handlers per participant
   - `asyncio.iscoroutinefunction` check on every handler call — eliminable in Rust

3. **Event publishing** (`event_bus.py`):
   - `EventBus.publish` → queue → `_handle_event` → handler dispatch per subscription
   - `_append_history` (list append + O(1) pop) — fine
   - `_persist_event` (async repository write) — potential bottleneck

### Warm (per-second or per-transaction)

4. **Scheduler loop** (`scheduler.py`):
   - `_scheduler_loop` sleeps 1s, checks heap, processes due jobs
   - `process_due_jobs` — `heapq.heappop` per due task
   - `_execute_task` — handler invocation, persistence, rescheduling

5. **Correlation matching** (`correlation.py`):
   - `_find_message_matches` — O(n) scan over subscriptions per message
   - `_check_buffered_messages` — O(n) scan over buffer per new subscription
   - `reload_from_history` — full scan of history, O(h) reconstruction

6. **Context variable lookup** (`context.py`):
   - `get_variable(name, search_parent=True)` — O(depth) parent traversal
   - `get_all_variables` — O(n * depth) worst case

7. **Persistence** (across all files):
   - `persist_instance`, `persist_token`, `persist_context_variables`
   - `load_instance`, `load_instance_tokens`, `load_context_variables`
   - All check `hasattr(repository, "save_persisted")` — runtime attribute sniffing

---

## 7. Error Handling

### Custom Exceptions

**None defined in this directory.** All error handling uses standard Python exceptions:

| Exception | Used In | Context |
|-----------|---------|---------|
| `ValueError` | `engine.py:356`, `engine_services.py:456`, `token.py:445`, `context.py:490` | Not found errors, invalid arguments |
| `RuntimeError` | `engine_states.py`, `instance_states.py`, `token_states.py`, `transaction_states.py` (all states) | Invalid state transitions |
| `PermissionError` | `proxies.py:160` | Engine protection proxy access denied |
| `TypeError` | `engine_bridge.py:331` | Engine missing `execute_instance` method |

### Bare `except` Pattern

All files use `except Exception:` (never bare `except:`). The predominant pattern is:

```python
except Exception:
    logger.exception("...")  # or
    logger.error("...", exc_info=True)
```

This appears in all executor loops (`_job_executor_loop`, `_async_executor_loop`, `_monitoring_loop`, `_scheduler_loop`, `_process_events`) and in `transaction._do_prepare/_do_commit/_do_rollback`.

### `None`-for-Failure Pattern

Consistent across all managers — methods return `None` or empty collections rather than raising:

- `InstanceManager.get_instance(id) -> ProcessInstance | None`
- `TokenManager.get_token(id) -> Token | None`
- `TransactionManager.get_transaction(id) -> TransactionScope | None`
- `ContextManager.get_context(id) -> ExecutionContext | None`
- `CorrelationEngine.cleanup_instance_subscriptions(id) -> int` (returns count)
- `Scheduler.cancel_task(id) -> bool`
- `InstanceManager.find_by_business_key(key) -> list[ProcessInstance]` (empty on miss)

### Rust Error Handling Strategy

- State transition errors → `Result<(), StateTransitionError>`, match the enum variant
- Not-found errors → `Option<T>` (mirrors existing Python pattern)
- Persistence errors → `Result<T, PersistenceError>` — wrap repository failures
- No need for `anyhow`-style dynamic errors — each error domain has a fixed set of variants
- The `try/except Exception` with `logger.exception` pattern → `Result::unwrap_or_else(|e| { error!("..."); })` in executor loops

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| Python files | 21 |
| Total lines | ~6,200 |
| State machine files | 4 (`engine_states`, `instance_states`, `token_states`, `transaction_states`) |
| State classes | 28 total (6 + 9 + 5 + 8) |
| State Protocol files | 1 (`_context_protocols.py` — 5 protocols) |
| Manager classes | 6 (`InstanceManager`, `TokenManager`, `TransactionManager`, `ContextManager`, `EventBus`, `Scheduler`) |
| Custom exceptions | 0 |
| `# type: ignore` | 2 (both in `factories.py`, optional dependencies) |
| Global mutable state | 2 (`_STATE_MAP` in `instance_states.py`, `token_states.py`) |
| `isinstance` chains | ~7 files share `_parse_datetime`, plus deserialization checks |
| External module deps | ~12 document/persistence/runtime modules |
| PyO3 modules recommended | ~15 Rust modules |
