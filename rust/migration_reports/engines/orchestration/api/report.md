# REST API Layer — Rust Migration Report

## Files Analyzed
- `__init__.py` (17 lines) — re-exports
- `admin_api.py` (124 lines) — cleanup, replay, migration, restart, batch ops
- `deployment_api.py` (90 lines) — deploy, list, get definitions
- `engine_api.py` (89 lines) — start/stop/pause/resume, health
- `instance_api.py` (170 lines) — instance query, variables, tokens, history, modify, incidents
- `process_api.py` (119 lines) — start, terminate, suspend, resume, signal, message
- `task_api.py` (70 lines) — list tasks, claim, complete, variables

## 1. Pre-refactor Patterns

| Pattern | Files | Details |
|---------|-------|---------|
| `Any` | admin_api.py:7, deployment_api.py:7, instance_api.py:8, process_api.py:11, task_api.py:7 | Widespread — `FeelContext`, `Metadata` type aliases |
| `dict[str, Any]` | admin_api.py:75, deployment_api.py:28,45,57,69, instance_api.py:58,106, process_api.py:26,45,87, task_api.py:58,65 | Parameters and return types |
| `isinstance` | instance_api.py:44,84 | `hasattr` checks, state value access |
| Global state | engine_api.py:17, instance_api.py:14, process_api.py:17 | Module-level `logger` |
| Mutable defaults | None | No mutable default arguments |

## 2. Migration Notes & Rust Score

| File | Lines | Complexity | Rust Score | Notes |
|------|-------|-----------|------------|-------|
| admin_api.py | 124 | Medium | 3/5 | Heavy coupling to engine internals (`engine.instances`, `engine.batch_manager`, `engine.snapshot_manager`, etc.). Dynamic imports (`__import__`). |
| deployment_api.py | 90 | Low | 4/5 | Filter loops, dict construction. Clean. |
| engine_api.py | 89 | Low | 4/5 | `hasattr` checks, health aggregation. |
| instance_api.py | 170 | Medium | 3/5 | Tight coupling to engine + managers. `try/except: return []` patterns. |
| process_api.py | 119 | Medium | 3/5 | Dynamic import (`__import__("engines.orchestration.core.instance")`), `getattr` for optional managers. |
| task_api.py | 70 | Low | 4/5 | Stub-heavy. Many methods return `True` without real impl. |

**Overall**: 3.5/5. The APIs are thin facades over engine internals. Migration difficulty depends on how the core engine is migrated — the APIs would naturally follow. The `__import__` and `hasattr` patterns indicate fragile late-binding that Rust's type system would eliminate.

## 3. Ownership Map

```
AdminAPI      (admin + recovery + batch)
DeploymentAPI (deploy + list + definitions)
EngineAPI     (lifecycle + health)
InstanceAPI   (query + modify + incidents + external tasks + forms)
ProcessAPI    (start + signal + message + terminate/suspend/resume)
TaskAPI       (user tasks + claim/complete)

All APIs own a reference to OrchestrationEngine
```

## 4. PyO3 Binding Structure

```rust
#[pyclass]
struct AdminAPI { engine: Py<OrchestrationEngine> }

#[pyclass]
struct DeploymentAPI { engine: Py<OrchestrationEngine> }

#[pyclass]
struct EngineAPI { engine: Py<OrchestrationEngine> }

#[pyclass]
struct InstanceAPI { engine: Py<OrchestrationEngine> }

#[pyclass]
struct ProcessAPI { engine: Py<OrchestrationEngine> }

#[pyclass]
struct TaskAPI { engine: Py<OrchestrationEngine> }
```

## 5. Libraries Analysis

| Current Python | Rust Equivalent | Notes |
|---------------|----------------|-------|
| `logging` | `log` | Module loggers |
| `datetime` | `chrono` | Timestamps |
| `uuid` | `uuid` crate | Instance IDs |
| `engines.orchestration.core.*` | PyO3 FFI or Rust-native | Heavy coupling to internal modules |

## 6. Performance Hot Paths

- `InstanceAPI.query_instances()` — O(n) scan over engine.instances dict. With many instances, needs indexing.
- `AdminAPI.get_batch_operations()` — O(n) list comprehension with slice.
- `DeploymentAPI.get_definitions()` — O(n) filter loop.
- `TaskAPI.list_user_tasks()` — O(n) scan with state checks.

## 7. Error Handling

| Python | Rust Strategy |
|--------|---------------|
| `try/except: return False/[]` | `Result<T, ApiError>` |
| `hasattr` guards | Option types + compile-time checks |
| `getattr(engine, "signal_manager", None)` | Optional fields in engine struct |
| `__import__` dynamic imports | Direct use of InstanceState enum |
| `{"success": False, "error": ...}` | `Result<Success, ApiError>` response types |
