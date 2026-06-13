# Expression Evaluators — Rust Migration Report

## Files Analyzed
- `__init__.py` (18 lines) — re-exports
- `evaluator.py` (20 lines) — protocol + context dataclass
- `context_builder.py` (21 lines) — frozen dataclass
- `feel_evaluator.py` (34 lines) — FEEL → Python eval bridge
- `javascript_evaluator.py` (31 lines) — js2py wrapper
- `juel_evaluator.py` (22 lines) — JUEL → Python wrapper
- `python_evaluator.py` (37 lines) — restricted `eval()`

## 1. Pre-refactor Patterns

| Pattern | Files | Details |
|---------|-------|---------|
| `Any` | evaluator.py:11, feel_evaluator.py:15, javascript_evaluator.py:20, juel_evaluator.py:20, python_evaluator.py:33 | Return type of `evaluate()` in all evaluators |
| `dict[str, Any]` | evaluator.py:11 | `EvaluationContext.variables` |
| `isinstance` | None | Not present in these files |
| Global state | None | No mutable globals |
| Mutable defaults | None | No mutable default arguments |

## 2. Migration Notes & Rust Score

| File | Lines | Complexity | Rust Score | Notes |
|------|-------|-----------|------------|-------|
| evaluator.py | 20 | Low | 5/5 | Protocol → Rust trait, trivial |
| context_builder.py | 21 | Low | 5/5 | Frozen struct, `from_mapping` → `FromIterator` |
| feel_evaluator.py | 34 | Medium | 4/5 | String parsing → Rust `eval` equivalent needed; current impl delegates to Python `eval()` |
| javascript_evaluator.py | 31 | Low | 3/5 | Optional `js2py` dependency — Rust would need a JS runtime crate (e.g. `boa_engine`) |
| juel_evaluator.py | 22 | Low | 5/5 | Simple string replacement then delegates to PythonEvaluator |
| python_evaluator.py | 37 | Low | 5/5 | Restricted `eval()` → Rust would need a scripting runtime (e.g. `rhai`) or predefine operand set |

**Overall**: 4.5/5 — strong migration candidate. The `eval()` calls are the only challenge; they'd require `rhai` or `mlua` as an embedded scripting runtime in Rust.

## 3. Ownership Map

```
Evaluator (trait/protocol)
 ├── FEELExpressionEvaluator    — standalone eval implementation
 ├── JuelExpressionEvaluator     — wraps PythonEvaluator
 ├── JavaScriptEvaluator         — wraps js2py
 └── PythonEvaluator             — restricted eval()

EvaluationContext (value object)
ExpressionContext (frozen value object)
EvaluationError (error type)
```

## 4. PyO3 Binding Structure

```rust
// evaluator.rs — trait + context structs
#[pyclass]
struct EvaluationContext { variables: HashMap<String, PyObject> }

#[pyclass]
struct ExpressionContext { data: HashMap<String, PyObject> }

// Each evaluator as a #[pyclass] implementing the trait
// PythonEvaluator.evaluate() → exposed as Python-callable
#[pymethods]
impl PythonEvaluator {
    fn evaluate(&self, expression: &str, context: &EvaluationContext) -> PyResult<PyObject> { ... }
}
```

## 5. Libraries Analysis

| Current Python | Rust Equivalent | Notes |
|---------------|----------------|-------|
| `js2py` (optional) | `boa_engine` | Full JS interpreter crate, adds ~5MB binary |
| `builtins` (Python eval) | `rhai` or `meval` | For restricted expression evaluation |
| `re` (FEEL parser) | `regex` | String parsing for ternary expressions |

## 6. Performance Hot Paths

- `PythonEvaluator.evaluate()` — called for every expression in every engine. Currently uses `eval()` which acquires GIL. Rust with precompiled `rhai` ASTs would be 10-100x faster.
- `FEELExpressionEvaluator.evaluate()` — string splitting + `eval()` per call. String operations are cheap but `eval()` dominates.

## 7. Error Handling

| Python | Rust Strategy |
|--------|---------------|
| `EvaluationError(RuntimeError)` | `thiserror::Error` enum `EvaluationError` |
| Bare `except Exception` wrapping | `Result<T, EvaluationError>` with `map_err` |
| `js2py` import guard (None check) | Cargo feature flag + compile-time check |
