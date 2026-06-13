# BPMN Execution Engine — Rust Migration Analysis

**Source:** `engines/orchestration/bpmn/` (22 files, ~5300 lines)  
**Analysis date:** 2026-06-13  
**Scope:** Read-only analysis for Rust migration planning

---

## 1. Pre-refactor Analysis

### `Any` usage — 126 occurrences
Ubiquitous. Every file imports `Any`. Root cause: dual dict/OSDM-typed API pattern and weak parametricity in collections.

| File | `Any` count | Notes |
|------|-------------|-------|
| `process_executor.py` | ~12 | `activities: list[Any]`, `engine: Any`, `ref: Any` |
| `conversation_executor.py` | ~12 | `orchestration_engine: Any \| None` pattern |
| `loop_handler.py` | ~10 | `element: Any`, `collection_data: list[Any]` |
| `model_normalizer.py` | ~6 | `activity: Any` dispatched by isinstance |
| `event_handler.py` | ~5 | `payload: dict[str, Any]` |
| `sub_process_manager.py` | ~7 | `model: Any`, `orchestration_engine: Any` |
| `process_model.py` | ~4 | `_raw_node_index: dict[str, dict[str, Any]]` |
| Others | scattered | dataclass payload/correlation fields |

### `dict[str, Any]` — 64 occurrences
Heaviest in conversation/choreography executors (message flows, payloads). The `FeelContext`, `RawData`, `MessagePayload`, `Metadata` type aliases in `_types.py` are all `dict[str, Any]` renames.

### `isinstance` chains — 130 occurrences
The biggest migration tax. Two critical chains:

- **`classify_node()`** in `process_model.py:226-278`: 23 `isinstance` checks covering every BPMN node type. Called on every node traversal.
- **`_resolve_activity_type()`** in `process_executor.py:351-370`: 6+ `isinstance` on Activity/Task/Event/Gateway.
- **`_resolve_osdm_event_type()`** in `event_handler.py:161-174`: 6 `isinstance` for event subclasses.
- **`_osdm_to_handler_event()`** in `event_handler.py:110-159`: 8 `isinstance` for event definition types.
- **`_handle_loop_osdm()`** in `activity_handler.py:408-439`: isinstance for MultiInstance vs StandardLoopCharacteristics.
- **`can_converge()`** in `bpmn_execution_semantics.py:212-229`: isinstance on ParallelGateway/InclusiveGateway.
- **Dict-vs-OSDM dispatch**: `isinstance(activity, dict)` / `isinstance(flow, HandlerSequenceFlow)` patterns throughout.

**Strategy maps** mitigate some isinstance chains:
- `_ACTIVITY_DISPATCH: dict[type, tuple[str, str]]` (activity_handler.py:139)
- `_GATEWAY_TYPE_MAP: dict[type, GatewayType]` (gateway_handler.py:41)
- `_GATEWAY_CLASSIFIER_MAP: dict[type, str]` (gateway_classifier.py:17)
- `_GATEWAY_SPLIT_HANDLERS: dict[type, Callable]` (bpmn_execution_semantics.py:232)
- `_GLOBAL_TASK_TYPE_MAP: dict[type, str]` (global_task_handler.py:44)

### `cast()` — 12 occurrences
Concentrated in `process_executor.py` (5 uses) and `sequence_flow.py` (2 uses). Signals where the type system can't express the dual dict/OSDM protocol.

### `# type: ignore` — 0 occurrences
Clean. No type-ignore comments anywhere in the BPMN module.

### Global / Module-Level State
| Location | State | Risk |
|----------|-------|------|
| `sequence_flow.py:210-211` | Module-level `_backbone = SequenceFlowEngine()`, aliased `compute_next_nodes` | Modestly shared — reentrant by design (no instance state) |
| `bpmn_execution_semantics.py:232` | `_GATEWAY_SPLIT_HANDLERS` dict | Immutable, safe |
| `gateway_classifier.py:17` | `_GATEWAY_CLASSIFIER_MAP` dict | Immutable, safe |
| `gateway_handler.py:41` | `_GATEWAY_TYPE_MAP` dict | Immutable, safe |
| `global_task_handler.py:44` | `_GLOBAL_TASK_TYPE_MAP` dict | Immutable, safe |

### Mutable Default Arguments — 0 issues
All mutable defaults use `field(default_factory=...)` correctly in dataclasses. No mutable default arguments in function signatures.

---

## 2. Migration Notes (Function Complexity Scores: 1–5)

| Function | Score | Rationale |
|----------|-------|-----------|
| `classify_node()` (process_model.py:226) | **2** | 23 isinstance checks — tedious but mechanical. Map pattern. |
| `_resolve_activity_type()` (process_executor.py:351) | **2** | isinstance dispatch + ActivityType enum check |
| `BPMNProcessExecutor.execute()` (process_executor.py:93) | **5** | Main execution loop: token management, gateway dispatch, convergence detection, sub-process stack, async persistence, guard limit |
| `ActivityHandler._ACTIVITY_DISPATCH` pattern + `execute_osdm()` | **3** | Strategy map plus handler methods — each handler is simple, but many (14 types) |
| `BpmnGatewaySemantics._split_*()` family | **2** | Pure logic: condition evaluation, target selection |
| `GatewayHandler.choose_osdm()` + strategy classes | **3** | Strategy pattern is Rust-idiomatic via trait objects or enum dispatch |
| `EventHandler.handle_*()` (6 handlers) | **2** | Switch on EventDefinitionType, return outcome. Mechanical. |
| `BpmnTokenEngine` operations | **2** | CRUD on token placements — straightforward mapping |
| `SequenceFlowEngine.compute_next_nodes()` | **3** | Overloaded + condition evaluation via PythonEvaluator |
| `LoopHandler.execute()` | **3** | Condition evaluation, sequential/parallel branching |
| `TransactionHandler.{begin,commit,rollback,cancel}` | **2** | State machine + compensation stack |
| `ChoreographyExecutor` / `ConversationExecutor` | **4** | I/O bound (async message routing, event bus publish, engine lookups) |
| `Engine.execute_instance()` | **4** | Orchestrates parsing, normalization, executor call, state persistence |
| `BpmnModelNormalizer.normalize()` + `normalize_osdm()` | **3** | Dual path (dict vs OSDM), definition XML → TypedProcessModel |

**Key insight:** Gateway handlers, token semantics, and process execution are pure computational logic — ideal for Rust. Activity/event handlers interact with `OrchestrationEngine` and event bus — more I/O bound, best behind async traits.

---

## 3. Ownership Map

### Core Data Structures

```
ProcessModel (frozen dataclass)                    — process_executor.py:52
├── definition_id: str
├── start_node: str | None
├── activities: list[Any]                          ← Any leakage
└── flows: list[HandlerSequenceFlow]

TypedProcessModel (dataclass)                      — process_model.py:81
├── definition_id: str
├── start_node_id: str | None
├── process: Process | None
├── _node_index: dict[str, FlowNode]               ← primary typed index
├── _raw_node_index: dict[str, dict[str, Any]]     ← fallback for dict-mode
├── _flow_index: dict[str, list[SequenceFlow]]     ← source_id → flows
└── _boundary_events: dict[str, list[BoundaryEvent]]

ProcessInstance (from ..core.instance)              — external dependency
└── variables, activity state, token state

Token (from ..core.token)                          — external dependency
├── token_id, current_element_id, state
└── snapshot, parent_token_id
```

### Token Flow Diagram (conceptual)

```
StartEvent → Activity/Event/Gateway → SequenceFlow → next Node
    ↑                                                     |
    |                                                     v
    +--------------- converge? ──── ParallelGateway ──────+
                                    InclusiveGateway
                                    ExclusiveGateway
                                    EventBasedGateway
                                    ComplexGateway
```

### Instance State Ownership

```
BPMNEngine (engine.py)
├── BPMNProcessExecutor (process_executor.py)
│   ├── ActivityHandler (activity_handler.py)
│   ├── BpmnSubProcessManager (sub_process_manager.py)
│   │   ├── BpmnEventSubProcessHandler (bpmn_execution_semantics.py)
│   │   └── BpmnTransactionHandler (bpmn_execution_semantics.py)
│   ├── BpmnModelNormalizer (model_normalizer.py)
│   ├── BpmnGatewayClassifier (gateway_classifier.py)
│   └── state: dict[instance_id, ProcessExecutionOutcome]
├── ChoreographyExecutor (choreography_executor.py)
├── ConversationExecutor (conversation_executor.py)
└── PoolLaneExecutor (pool_lane_executor.py)
```

---

## 4. PyO3 Binding Structure

### Proposed Rust Module Hierarchy

```rust
bpmn/
├── mod.rs                          // Public API, re-exports
├── engine.rs                       // BPMNEngine — top-level orchestrator
│   └── pub async fn execute_instance(instance, definition) -> Result<ProcessExecutionOutcome>
├── process_executor.rs             // BPMNProcessExecutor — main execution loop
│   ├── pub async fn execute(model, instance) -> Result<ProcessExecutionOutcome>
│   └── fn compute_next(...), fn resolve_activity_type(...)
├── model.rs                        // ProcessModel + TypedProcessModel
│   ├── pub struct ProcessModel { definition_id, start_node, activities, flows }
│   └── pub struct TypedProcessModel { node_index, flow_index, boundary_index }
├── token.rs                        // Token placement, active token management
│   └── pub struct BpmnTokenEngine { placements: HashMap<String, TokenPlacement> }
├── gateway.rs                      // GatewayHandler + all Strategy impls
│   ├── pub trait GatewayStrategy { fn choose(...) -> GatewayDecision }
│   └── pub enum GatewayKind { Exclusive, Inclusive, Parallel, EventBased, Complex }
├── activity.rs                     // ActivityHandler — dispatch to 14+ types
│   └── pub enum ActivityKind { ServiceTask, UserTask, ScriptTask, ... }
├── event.rs                        // EventHandler — start/end/intermediate/boundary
│   └── pub enum EventDef { Message, Timer, Signal, Error, Escalation, ... }
├── sequence_flow.rs                // SequenceFlowEngine + flow traversal
├── loop_handler.rs                 // LoopHandler — standard + multi-instance
├── transaction.rs                  // TransactionHandler — compensation + state machine
├── sub_process.rs                  // BpmnSubProcessManager — event/adhoc sub-processes
├── choreography.rs                 // ChoreographyExecutor — mostly I/O
├── conversation.rs                 // ConversationExecutor — mostly I/O
├── collaboration.rs                // CollaborationHandler — message routing
├── data_object.rs                  // DataObjectHandler — registry
├── pool_lane.rs                    // PoolLaneExecutor — scoping
├── model_normalizer.rs             // BpmnModelNormalizer — payload → model
├── gateway_classifier.rs           // BpmnGatewayClassifier — type detection
└── semantics.rs                    // BpmnExecutionSemantics — rules from BPMN 2.0 Annex A
```

### Key Trait Definitions for PyO3

```rust
// GatewayHandler strategies — natural `enum` dispatch, no trait object needed
#[pyclass]
enum GatewayKind { Exclusive, Inclusive, Parallel, EventBased, Complex }

#[pymethods]
impl GatewayHandler {
    fn choose_osdm(&self, gateway: &Gateway, flows: &[SequenceFlow], ctx: FeelContext) -> GatewayDecision;
}

// Activity dispatch — enum + associated data
#[pyclass]
enum ActivityKind {
    ServiceTask { implementation: String },
    UserTask { assignee: Option<String>, candidate_groups: Vec<String>, ... },
    ScriptTask { script: String, script_format: String },
    // ... 11 more variants
}

// Event dispatch
#[pyclass]
enum EventDefKind {
    None, Message, Timer, Signal, Error, Escalation, Conditional,
    Compensation, Link, Cancel, Terminate,
}
```

---

## 5. Libraries Analysis

### External Python (stdlib only)
| Module | Used In | Notes |
|--------|---------|-------|
| `dataclasses` | All files | Dataclasses are trivial in Rust (struct + derive) |
| `enum` | `transaction_handler.py`, `bpmn_execution_semantics.py` | Rust `enum` is superior |
| `collections.abc` | `adhoc_handler.py`, `global_task_handler.py`, `loop_handler.py` | Iterator/ Callable patterns |
| `datetime` | `event_handler.py` | `chrono` in Rust |
| `asyncio` | `choreography_executor.py`, `choreography_handler.py`, `engine.py` | `tokio` / `async-std` |
| `logging` | Most files | `log` / `tracing` in Rust |
| `abc` | `gateway_handler.py` | Trait objects in Rust |
| `typing` (overload) | `sequence_flow.py` | Not needed in Rust |

### Internal `engines.*` Dependencies
| Import | Strength | Notes |
|--------|----------|-------|
| `engines.document.models.osdm_models` | **Heavy** | Entire BPMN OSDM type hierarchy — the biggest dependency. Must define Rust equivalents. |
| `engines.document.models.dsdm_models` | Light | `DataDocument`, `SchemaBinding` — only in `data_object_handler.py` |
| `engines.document.models.msdm_models` | Light | `Entity`, `Attribute` — only in `data_object_handler.py` |
| `engines.core.engine` | Medium | `OrchestrationEngine`, `ProcessDefinition` |
| `engines.core.instance` | Medium | `ProcessInstance`, `InstanceState` |
| `engines.core.token` | Medium | `Token`, `TokenStateEnum` |
| `engines.core.context` | Light | `ExecutionContext`, `ContextManager`, `ContextScope` |
| `engines.core.event_bus` | Light | `Event`, `EventType` — async publish |
| `engines.core.correlation` | Light | `CorrelationKeySet` |
| `engines.expression.evaluator` | Medium | `EvaluationContext` — needed everywhere conditions are evaluated |
| `engines.expression.python_evaluator` | **Critical** | `PythonEvaluator` — the heaviest Python-specific dependency. Gate conditions, loop conditions, completion conditions all use it. |
| `engines.dmn.feel_engine` | Light | `EvaluationContext` import only |
| `engines.runtime.state_manager` | Light | `StateManager.set_persisted()` |
| `engines.runtime.compensation` | Light | `CompensationManager` — only in `transaction_handler.py` |
| `engines._types` | Light | Type aliases: `FeelContext`, `RawData`, `Metadata`, `MessagePayload` — all `dict[str, Any]` |

### PythonEvaluator — Migration Risk
`PythonEvaluator` is called in 6 files for condition evaluation:
- `gateway_handler.py` (exclusive, inclusive, complex strategies)
- `gateway_classifier.py`
- `bpmn_execution_semantics.py`
- `loop_handler.py`
- `sequence_flow.py`
- `sub_process_manager.py`

**Strategy**: Define a `ConditionEvaluator` trait in Rust. During PyO3 interop, the default implementation calls back into Python via PyO3 for evaluating Python expressions. A pure-Rust evaluator (simple boolean expressions + variable lookup) can be phased in.

---

## 6. Performance Hot Paths

### Hot Path 1: Token Traversal Loop
**File:** `process_executor.py:117-288`  
**Cost:** Up to 200 iterations, each with:
- `classify_node()` — 23 isinstance checks
- Gateway convergence detection
- Token snapshot + persist (async)
- Variable diff persistence
- Event bus publish (async)

**Rust advantage:** Static dispatch via enum, no isinstance overhead. Guard loop is cache-friendly.

### Hot Path 2: Gateway Condition Evaluation
**Files:** `gateway_handler.py`, `bpmn_execution_semantics.py`, `sequence_flow.py`  
**Cost:** `PythonEvaluator.evaluate()` call per condition. Python string parsing + eval.

**Rust advantage:** Native boolean expression evaluation. `#![no_std]` possible for pure conditions.

### Hot Path 3: Activity Dispatch
**File:** `activity_handler.py:139-153`  
**Cost:** Loop over `_ACTIVITY_DISPATCH` dict with isinstance check per entry until match.

**Rust advantage:** `match` on enum variant — O(1), monomorphized.

### Hot Path 4: `classify_node()` 
**File:** `process_model.py:226-278`  
**Cost:** 23 isinstance checks per call. Called for every node traversal.

**Rust advantage:** `enum NodeKind` with a single discriminant check.

### Hot Path 5: Sequence Flow Collection
**File:** `sequence_flow.py:186-196`, `process_model.py:147-155`  
**Cost:** Linear scan of `_flow_index` values on each call.

**Rust advantage:** `HashMap<&str, Vec<&SequenceFlow>>` — same approach but faster.

### Hot Path 6: Token Persistence
**File:** `process_executor.py:511-513`  
**Cost:** Iterates all tokens and calls async `persist_token()` per token. Can batch.

---

## 7. Error Handling

### Error Types

| Type | File | Kind |
|------|------|------|
| `BPMNExecutionError(RuntimeError)` | `engine.py:31` | Frozen dataclass — raised for document/process resolution failures |
| `BpmnExecutionError(RuntimeError)` | `bpmn_execution_semantics.py:49` | Separate class for semantics-level errors (same name, different module) |

### Error Handling Patterns

1. **Activity failure wrapper** (`activity_handler.py:136-137`):
   ```python
   except Exception as exc:
       return ActivityExecutionResult(success=False, error=exc)
   ```
   Wraps any exception into a result object. Never raises.

2. **Process-level catch** (`engine.py:217-224`):
   ```python
   except Exception as exc:
       await update_instance_state(FAILED)
       await state_manager.set_persisted("failed")
       raise
   ```
   Catches, logs to state, re-raises.

3. **Activity failure propagation** (`process_executor.py:158-164`):
   ```python
   if not execution_result.success:
       instance.fail_activity(...)
       await sub_process_manager.handle_activity_failure(...)
       raise RuntimeError(...)
   ```
   Delegates to `BpmnSubProcessManager.handle_activity_failure()` for transaction compensation.

4. **Condition evaluation errors** — swallowed everywhere:
   ```python
   except Exception:
       return False  # or continue
   ```
   Occurs in 6+ locations. Conditions that fail to evaluate are treated as `false`.

5. **Parse errors** (`engine.py:126-129`):
   ```python
   if not isinstance(bpmn_document, BPMNDocument):
       raise BPMNExecutionError(...)
   ```

6. **Execution guard** (`process_executor.py:286-287`):
   ```python
   if current and guard_steps >= 200:
       raise RuntimeError("BPMN process execution exceeded step limit")
   ```

7. **Sub-process completion checks** (`sub_process_manager.py:84-154`):
   Returns `bool`. Completion condition evaluation errors logged at DEBUG, return `false`.

### Retry Logic
No explicit retry logic exists in the BPMN engine. Failures are:
- Reported via `ActivityExecutionResult(success=False, error=exc)`
- Propagated to `RuntimeError` in the main execution loop
- Handled via compensation for transactions

### Rust Error Model Recommendation
```rust
#[derive(Debug, thiserror::Error)]
pub enum BpmnError {
    #[error("Activity failed: {0}")]
    ActivityFailed(String),
    #[error("Gateway condition evaluation error: {0}")]
    ConditionError(String),
    #[error("Step limit exceeded ({0})")]
    StepLimitExceeded(u32),
    #[error("Process definition error: {0}")]
    DefinitionError(String),
    #[error("Transaction error: {0}")]
    TransactionError(String),
    #[error("Token error: {0}")]
    TokenError(String),
}
```

Compensation should use Rust's `Drop` or explicit rollback structs rather than a `list[str]` stack.

---

## 8. Summary of Migration Complexity

| Category | Assessment |
|----------|------------|
| **Lines of Python** | ~5300 across 22 files |
| **Pure computation (easy)** | Gateway handlers, token engine, sequence flow, loop handler, transaction handler, event handler dispatch |
| **I/O bound (requires async traits)** | Activity execution (event bus), choreography routing, conversation routing, state persistence |
| **Python-specific dependency** | `PythonEvaluator` — requires callbacks or reimplementation |
| **OSDM model dependency** | ~200 BPMN types from `osdm_models` — must define Rust equivalents or use PyO3 bindings |
| **PyO3 interop surface** | ~15 public classes + ~30 handler methods |
| **Async runtime mismatch** | Python `asyncio` → Rust `tokio`. PyO3 `pyo3-asyncio` for bridging. |
| **Risk: isinstance chains** | 130 occurrences — fully eliminable via Rust enums. Biggest upside. |
| **Risk: `Any` / `dict[str, Any]`** | 126 + 64 occurrences — represents 30-40% of migration effort to type-erase. |
| **Risk: PythonEvaluator** | Gate to Rust FFI or reimplement expression evaluation. Condition logic is simple (string compares + variable lookup). |

### Recommended Phasing

1. **Phase 1 — Core semantics**: `BpmnTokenEngine`, `ProcessModel`/`TypedProcessModel`, `SequenceFlowEngine`, `GatewayHandler` (pure logic, no I/O, low `Any` exposure)
2. **Phase 2 — Activity dispatch**: `ActivityHandler` enum dispatch, `LoopHandler`, `ExecutionContext` (still pure, mechanical translation)
3. **Phase 3 — Event handling**: `EventHandler`, `BpmnBoundaryEventHandler`, `BpmnEventSubProcessHandler` (condition evaluation still needs Python bridge)
4. **Phase 4 — I/O handlers**: `ChoreographyExecutor`, `ConversationExecutor`, `CollaborationHandler` (async, event bus integration)
5. **Phase 5 — Orchestrator**: `BPMNEngine`, `BPMNProcessExecutor` main loop (assembles all pieces, async state persistence)
6. **Phase 6 — PyO3 bindings**: `#[pyclass]` wrappers, PythonEvaluator FFI bridge, `pyo3-asyncio` integration
