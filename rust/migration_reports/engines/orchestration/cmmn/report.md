# CMMN Engine — Rust Migration Analysis

**Source:** `multi_agent_infra/engines/orchestration/cmmn/`
**Files:** 10 Python files (612+ lines total)

---

## 1. Pre-refactor Analysis

### `Any` / `dict[str, Any]` Usage (High)

| Location | Usage | Count |
|----------|-------|-------|
| `case_executor.py` | `definition: Any` (line 320), `payload: Any` (line 463), `RawData` throughout | ~40+ sites |
| `sentry_evaluator.py` | `instance_or_context: Any` (line 141), `criterion: Any` (line 235) | ~15 sites |
| `milestone_handler.py` | `entry_criteria: list[dict[str, Any]]` (line 28) | ~10 sites |
| `stage_handler.py` | `entry_criteria: list[dict[str, Any]]` (line 50) | ~8 sites |
| `discretionary_handler.py` | `criteria: list[dict[str, Any]]` (line 110) | ~10 sites |
| `planning_table_handler.py` | `rules: list[dict[str, Any]]` (line 75) | ~10 sites |

All case file data, task payloads, sentry criteria, and event data flow through `dict[str, Any]` or `RawData` (aliased to `Any`).

### `isinstance` Chains (Medium)

- `case_executor.py:_execute_osdm_task` (lines 332–353): 3-way `isinstance` dispatch (`HumanTask` / `ProcessTask` / `CaseTask`) with fallback `else`.
- `case_executor.py:_collect_plan_items` (lines 371–391): nested `isinstance` against `Milestone` / `Stage`.
- `sentry_evaluator.py:register` (lines 72–113): 2-way `isinstance(sentry, dict)` vs `isinstance(sentry, Sentry)` — union type handling.
- `sentry_evaluator.py:evaluate_entry_criteria` (lines 141–155): `isinstance(criterion, EntryCriterion)` / `isinstance(criterion, ExitCriterion)`.
- `task_handler.py:execute` (lines 93–116): string-equality dispatch on `task_type` (not isinstance, but equivalent pattern).

### Dynamic Dispatch (High)

- **String-keyed handler maps**: `_AGGREGATION_HANDLERS` pattern is absent in CMMN, but the equivalent is the `if/elif` chain in `case_executor.py:_execute_task` (lines 472–513) dispatching on `CMMNTaskType` enum values as strings.
- **RawData dict access**: Sentry evaluation and task execution access nested dicts via `.get()` chains with no static shape guarantee.
- **`_normalize_definition`** (case_executor.py:581–608): normalizes multiple key aliases (`stages`/`fragments`, `tasks`/`elements`) — schema inference from runtime data.

### Global / Mutable State (High)

| Component | State | Scope |
|-----------|-------|-------|
| `SentryEvaluator` | `_rules: dict[str, SentryRule]`, `_fired_events: dict[str, set[str]]` | Instance-level mutable |
| `CaseExecutor` | `_stages`, `_milestones`, `_planning_items` | Dicts mutated during `execute()` |
| `StageHandler` | `_stages: dict[str, Stage]` | Instance-level mutable |
| `MilestoneHandler` | `_milestones`, `_audit_log` | Append-only list + mutable dict |
| `DiscretionaryTaskHandler` | `_items`, `_planning_tables` | Instance-level mutable |
| `CMMNTaskHandler` | `_tasks`, `_human_tasks`, etc. | 5 separate mutable dicts |

No immutability guarantees — all contexts mutated in-place via direct field assignment or dict updates.

### Sentry `_fired_events` as Dynamic State Machine

The `SentryEvaluator` at `sentry_evaluator.py:70` maintains `_fired_events: dict[str, set[str]]` tracking which plan items have emitted which events. This is an implicit state tracking mechanism — the sentry satisfaction model (AND semantics over OnParts) tracks external event firings without an explicit state machine.

---

## 2. Migration Notes

**Score: 5/5** — Excellent Rust fit.

### State Machine Mapping

The CMMN lifecycle is a textbook state machine:

```
Draft → Active → Completed → Closed
         ↓   ↑       ↓
      Suspended → → → → 
         ↓
      Terminated → Closed
         ↓
      Failed → Closed/Active (reactivate)
```

Already encoded as `CMMNCaseState` enum (engine.py:25–33) with `CMMN_VALID_TRANSITIONS` dict (lines 37–45). This maps directly to a Rust `enum` with `Transition` trait:

```rust
enum CMMNCaseState { Draft, Active, Completed, Terminated, Suspended, Closed, Failed }

impl CMMNCaseState {
    fn valid_transitions(&self) -> &[CMMNCaseState] { ... }
    fn transition(self, to: CMMNCaseState) -> Result<Self, CMMNError> { ... }
}
```

### Plan Item Lifecycle

`CMMNTaskState` (task_handler.py:15–22), `StageState` (stage_handler.py:30–37), `MilestoneState` (milestone_handler.py:15–19) are all string enums that become Rust enums trivially.

### Sentry Evaluation

`SentryEvaluator` is a pure function with external event tracking — ideal for Rust. The OnPart AND semantics (sentry_evaluator.py:207–221) and IfPart condition evaluation (lines 223–227) are deterministic logic with no side effects beyond the `_fired_events` tracking.

### Repetition & Reentry

Stage reentry (stage_handler.py:98–109), task repetition rules, and discretionary planning all involve state transitions that Rust's type system can enforce at compile time.

---

## 3. Ownership Map

```
CMMNEngine
 ├── CaseExecutor
 │    ├── SentryEvaluator
 │    │    ├── _rules: dict<string, SentryRule>
 │    │    │    ├── on_parts (OnPart list)
 │    │    │    ├── if_part (optional condition)
 │    │    │    └── triggered_on_parts (tracking set)
 │    │    └── _fired_events: dict<string, set<string>>
 │    ├── _stages: dict<string, StageContext>
 │    ├── _milestones: dict<string, MilestoneContext>
 │    └── _planning_items: dict<string, PlanningItemContext>
 ├── StageHandler
 │    └── _stages: dict<string, Stage>
 ├── MilestoneHandler
 │    ├── _milestones: dict<string, Milestone>
 │    └── _audit_log: list<MilestoneAuditEntry>
 ├── DiscretionaryTaskHandler
 │    ├── _items: dict<string, DiscretionaryItem>
 │    └── _planning_tables: dict<string, PlanningTableTable>
 └── CMMNTaskHandler
      ├── _tasks: dict<string, CMMNTask>
      ├── _human_tasks: dict<string, HumanTaskConfig>
      ├── _process_tasks: dict<string, ProcessTaskConfig>
      ├── _case_tasks: dict<string, CaseTaskConfig>
      └── _decision_tasks: dict<string, DecisionTaskConfig>
```

**Rust ownership pattern:** `CaseExecutor` owns all child handlers. Each handler owns its state dicts. Rust's `HashMap<String, T>` replaces `dict[str, T]`. The `SentryRule.triggered_on_parts` uses a `HashSet<String>`.

**Key ownership challenge:** The `SentryEvaluator._fired_events` is mutated by `record_event()` and read by `check_sentry_satisfied()` / `_check_on_parts_and()`. These are called in sequence during `execute()`, so borrow-checker-safe with `&mut self`.

---

## 4. PyO3 Binding Structure

### Recommended Architecture

```
┌─────────────────────────────────────────────────┐
│                   Python                         │
│  CMMNEngine.execute(instance, definition)        │
│  CaseExecutor.execute_osdm(document, instance)   │
│  SentryEvaluator.evaluate_entry_criteria(...)    │
│                                                   │
│  ┌───────────────────────────────────────────┐   │
│  │            PyO3 Bridge                     │   │
│  │  PyClass CMMNEngine → Rust CMMNEngine      │   │
│  │  PyClass CaseExecutor → Rust CaseExecutor  │   │
│  │  PyClass SentryEvaluator → ...              │   │
│  └───────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────┐
│                   Rust                           │
│  CMMNEngine::execute_instance()                  │
│  CaseExecutor::execute()                         │
│  SentryEvaluator::evaluate()                     │
│                                                   │
│  State machine: CMMNCaseState enum                │
│  Transition validation at compile time            │
│  Sentry evaluation: pure fn on EventSet           │
│  No Python GIL needed during evaluation           │
└─────────────────────────────────────────────────┘
```

**Layer breakdown:**
1. **Rust core** (no GIL): State machine transitions, sentry evaluation, plan item lifecycle, milestone tracking
2. **PyO3 bindings**: Thin wrappers exposing `#[pyclass]` + `#[pymethods]` for each handler
3. **Python API**: Unchanged public interface — Python callers see same API

### Thread Safety

Each `CMMNEngine` is tied to one instance. The engine is not `Send`-safe currently because `SentryEvaluator._fired_events` is mutated from `execute()`. In Rust, `&mut self` ensures single-threaded access. If concurrent instances are needed, each gets its own `CMMNEngine` — no shared state between instances.

---

## 5. Libraries Analysis

### External (stdlib only)

| Import | Files |
|--------|-------|
| `logging` | `engine.py`, `sentry_evaluator.py` |
| `dataclasses` | All files (data carriers) |
| `enum` | `engine.py`, `milestone_handler.py`, `stage_handler.py`, `task_handler.py` |
| `typing` / `collections.abc` | All files |
| `asyncio` | `stage_handler.py:76`, case_executor uses async/await everywhere |

### Internal Dependencies

| Import Path | Used By |
|-------------|---------|
| `..._types` (`Metadata`, `RawData`, `FeelContext`) | `case_executor.py`, `sentry_evaluator.py`, `task_handler.py` |
| `..core.instance` (`ProcessInstance`) | All files |
| `..core.engine` (`OrchestrationEngine`) | `engine.py`, `case_executor.py`, `discretionary_handler.py`, etc. |
| `..core.event_bus` (`Event`, `EventType`) | `engine.py`, `case_executor.py`, `stage_handler.py` |
| `..core.context` (`ContextManager`, `ContextScope`) | `engine.py` |
| `..runtime.state_manager` (`StateManager`) | `engine.py` |
| `..expression.evaluator` (`EvaluationContext`) | `sentry_evaluator.py`, `discretionary_handler.py`, `planning_table_handler.py` |
| `..expression.python_evaluator` (`PythonEvaluator`) | `sentry_evaluator.py`, `discretionary_handler.py`, `planning_table_handler.py` |
| `...document.models.osdm_models` (OSDM types) | `case_executor.py`, `sentry_evaluator.py`, `stage_handler.py` |

**No third-party PyPI dependencies.** This simplifies Rust migration — no CPython extension interop concerns beyond PyO3.

### Key Dependency: `PythonEvaluator`

Used for dynamic expression evaluation (sentry IfPart conditions, applicability rules). This is a runtime expression evaluator that interprets Python expressions against instance variables. **Migration strategy:** Replace with a Rust expression evaluator (or embed a scripting language) for the Rust core, or pass expressions back to Python via PyO3 callback.

---

## 6. Performance Hot Paths

### Hot Path 1: Sentry Evaluation (N criteria per transition)

**Location:** `sentry_evaluator.py:_check_on_parts_and()` (lines 207–221) + `_evaluate_if_part()` (lines 223–227)

**Triggered:** On every `record_event()` call — iterates all `_rules` and for each rule iterates all `on_parts`.

**Current complexity:** O(R × P) where R = registered sentries, P = on-parts per sentry.

**Rust optimization:** Convert to indexed lookup using `HashMap<source_ref, Vec<sentry_id>>` for O(1) rule lookup by event source. `_check_on_parts_and` becomes iterative over pre-filtered rules.

### Hot Path 2: Task Dispatch / isinstance Chain

**Location:** `case_executor.py:_execute_osdm_task()` (lines 316–359)

**Triggered:** Per task in execution.

**Current cost:** 3 isinstance checks + attribute access per task. Python overhead dominates.

**Rust optimization:** Enum dispatch via `match` — compiler-optimized jump table.

### Hot Path 3: Event Publishing

**Location:** `case_executor.py:execute()` (lines 178–204) — two `event_bus.publish()` calls per task.

**Cost:** Async overhead. Await on every task start/completion.

**Rust optimization:** Tokio broadcast channel or mpsc sender. Zero-cost async with work-stealing scheduler.

### Hot Path 4: PythonEvaluator per Sentry

**Location:** `sentry_evaluator.py:_evaluate_if_part()` (line 227)

**Cost:** Expression parsing + execution per sentry evaluation. This is the biggest bottleneck — every sentry transition triggers Python expression evaluation.

---

## 7. Error Handling

### Current Python Pattern

| Error Type | Location | Mechanism |
|------------|----------|-----------|
| `CaseExecutionError` | `case_executor.py:71` | `@dataclass(frozen=True)` inheriting `RuntimeError` |
| `CMMNExecutionError` | `engine.py:49` | `@dataclass(frozen=True)` inheriting `RuntimeError` |
| Invalid state transition | `engine.py:71–78` | Raises `CMMNExecutionError` with message |
| Execution failure | `engine.py:150–160` | `try/except Exception` → sets FAILED state, re-raises |
| Sentinel errors | `discretionary_handler.py:125` | `try/except Exception` → returns `False` |
| Planning table errors | `planning_table_handler.py:90` | `try/except Exception` → returns `False` |

### Rust Mapping

| Python | Rust |
|--------|------|
| `CaseExecutionError(RuntimeError)` | `enum CaseExecutionError { ... }` implementing `std::error::Error` |
| `CMMNExecutionError(RuntimeError)` | `enum CMMNExecutionError { ... }` implementing `std::error::Error` |
| `try/except Exception` → `False` | `Result<T, E>` — `Err` propagates, no implicit swallowing |
| State transition errors | Compile-time via `enum CMMNCaseState` + `transition()` returning `Result` |
| `PythonEvaluator` errors | `Err` variant in expression evaluator `Result<bool, EvalError>` |

**Improvement opportunity:** Python silently returns `False` on evaluation errors (discretionary_handler.py:125, planning_table_handler.py:90). Rust should propagate errors and let callers decide on fallback behavior.

---

## Summary

| Dimension | Score | Notes |
|-----------|-------|-------|
| State machine fit | 5/5 | Enums + transition validation map directly |
| Type safety gain | High | Eliminates all `dict[str, Any]` with typed structs |
| Performance gain | High | Sentry evaluation O(R×P) → O(1) indexed |
| Migration complexity | Medium | PythonEvaluator dependency needs bridging |
| Thread safety gain | High | `&mut self` guarantees no shared mutation |
