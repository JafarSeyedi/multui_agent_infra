# State Machine Engine — Rust Migration Report

## Files Analyzed
- `__init__.py` (43 lines) — re-exports
- `action_executor.py` (98 lines) — entry/exit/do/transition actions
- `engine.py` (85 lines) — top-level adapter
- `guard_evaluator.py` (58 lines) — guard condition evaluation
- `hierarchical_handler.py` (96 lines) — parent/child state tree
- `history_manager.py` (92 lines) — shallow/deep history
- `parallel_state_handler.py` (69 lines) — orthogonal regions
- `state_execution.py` (1 line) — re-export
- `state_executor.py` (545 lines) — **core execution loop** (legacy + OSDM)
- `transition_handler.py` (152 lines) — trigger match, guard, priority

## 1. Pre-refactor Patterns

| Pattern | Files | Details |
|---------|-------|---------|
| `Any` | state_executor.py:15, engine.py:11, guard_evaluator.py:10, etc. | Widespread — transition/action payloads, guard results |
| `dict[str, Any]` | engine.py:43, state_executor.py:83-91, transition_handler.py:45-46, etc. | Definition payloads, context, results |
| `isinstance` | state_executor.py:153,172,206,503 | `isinstance(state_obj, State/PseudoState)` — type dispatch |
| Global state | logger throughout | Module-level `logger = logging.getLogger(__name__)` in 6 files |
| Mutable defaults | None | `field(default_factory=...)` only |

## 2. Migration Notes & Rust Score

| File | Lines | Complexity | Rust Score | Notes |
|------|-------|-----------|------------|-------|
| action_executor.py | 98 | Medium | 4/5 | Expression eval dependency, but clear async pattern |
| engine.py | 85 | Low | 4/5 | Thin orchestrator, async/await |
| guard_evaluator.py | 58 | Low | 4/5 | Expression eval dependency |
| hierarchical_handler.py | 96 | Low | 5/5 | Pure tree operations, no eval |
| history_manager.py | 92 | Low | 5/5 | List/dict operations, simple |
| parallel_state_handler.py | 69 | Low | 5/5 | Simple state tracking |
| state_executor.py | 545 | High | 3/5 | **Largest file**. Dual execution paths (legacy dict + OSDM typed). Complex control flow with `isinstance` dispatch. Async calls. |
| transition_handler.py | 152 | Medium | 4/5 | Guard eval, trigger matching, priority sorting |

**Overall**: 4.3/5. State machine logic is well-defined. `state_executor.py` is the risk due to dual execution paths.

## 3. Ownership Map

```
StateMachineEngine (adapter)
 └── StateMachineExecutor (core loop)
      ├── StateMachineModel_Legacy (dict-based)
      ├── StateMachineModel (OSDM typed)
      ├── TransitionHandler
      │    ├── match triggers
      │    ├── evaluate guards
      │    └── priority sort
      ├── StateMachineHistory
      │    ├── shallow/deep history
      │    └── push/query/clear
      ├── ActionExecutor
      │    ├── entry/exit/do/transition actions
      │    └── expression evaluation
      ├── GuardEvaluator
      │    └── expression → bool
      ├── HierarchicalHandler
      │    ├── parent/child tree
      │    └── LCA, ancestor checks
      └── ParallelStateHandler
           ├── orthogonal regions
           └── join detection

Data types:
StateContext, RegionContext, StateNode, GuardCondition
Transition, TriggerMatch, HistoryEntry, HistoryKind
RegionState, StateKind, PseudoStateKind
```

## 4. PyO3 Binding Structure

```rust
#[pyclass]
struct StateMachineEngine { ... }

#[pyclass]
struct StateMachineExecutor { ... }

#[pyclass]
struct TransitionHandler { ... }

#[pyclass]
struct StateMachineHistory { ... }

// OSDM model types would need PyO3 wrappers or be exposed as dicts
```

## 5. Libraries Analysis

| Current Python | Rust Equivalent | Notes |
|---------------|----------------|-------|
| `asyncio` | `tokio` | Required for `async fn execute()` |
| `logging` | `log` / `tracing` | Module-level loggers |
| `datetime.utcnow()` | `chrono::Utc::now()` | Timestamp generation |
| `Core` engine deps | PyO3 FFI or Rust native | `OrchestrationEngine`, `ProcessInstance` |
| `PythonEvaluator` | `rhai` | Expression eval |

## 6. Performance Hot Paths

- `StateMachineExecutor._execute_legacy()` — main loop with max_steps=200. Each iteration does dict lookups, guard eval (Python `eval()`), action execution.
- `StateMachineExecutor.execute_osdm()` — same loop but with typed OSDM objects. `isinstance` dispatch per iteration.
- `TransitionHandler.resolve()` — O(n) over transitions per state, with guard/trigger eval per transition.
- `HierarchicalHandler.get_common_ancestor()` — O(h) tree traversal (h = hierarchy depth).
- `StateMachineHistory.push()` — list append, called on each transition.

## 7. Error Handling

| Python | Rust Strategy |
|--------|---------------|
| `StateMachineError(RuntimeError)` | `thiserror` enum |
| `ActionExecutionError(RuntimeError)` | Separate error variant |
| `raise` in executor | `Result<(), SmError>` |
| `try/except` guard eval → returns `False` | `match` + default false |
| `RuntimeError("exceeded step limit")` | `SmError::StepLimitExceeded` |
