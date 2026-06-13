# Form Engine — Rust Migration Report

## Files Analyzed
- `__init__.py` (21 lines) — re-exports
- `form_engine.py` (263 lines) — FormDefinition, FormField, FormEngine

## 1. Pre-refactor Patterns

| Pattern | Files | Details |
|---------|-------|---------|
| `Any` | form_engine.py:14,59,68,80,132 | `default_value`, `value` in validation, `Metadata` type alias |
| `dict[str, Any]` | form_engine.py:131,155,222,228,247 | Method return types, `Metadata` = `dict[str, Any]` |
| `isinstance` | form_engine.py:85-111 | `isinstance(value, str)`, `isinstance(value, (int, float))` in field validation |
| Global state | form_engine.py:18 | Module-level `logger` |
| Mutable defaults | form_engine.py:74-78 | `field(default_factory=list/dict)` in dataclasses (safe, dataclass pattern) |

## 2. Migration Notes & Rust Score

| File | Lines | Complexity | Rust Score | Notes |
|------|-------|-----------|------------|-------|
| form_engine.py | 263 | Medium | 4/5 | Enums, validation logic, regex — all straightforward. `None` optional fields need `Option`. Python `eval` in `_evaluate_condition` is a complication. |

**Overall**: 4/5. The form engine is mostly data-oriented with enum fields and validation. The expression evaluation dependency is the main migration challenge. `to_dict()` / `from_dict()` serialization maps cleanly to `serde`.

## 3. Ownership Map

```
FormEngine (registry + operations)
 ├── Dict<String, FormDefinition> — registered forms
 └── operations: register, get, submit, render, remove

FormDefinition
 ├── Vec<FormField>
 ├── get_field(), validate(), apply_defaults(), to_dict(), from_dict()
 └── _evaluate_condition() → depends on PythonEvaluator

FormField
 ├── FormFieldValidationRule -> Vec
 ├── FormFieldOption -> Vec
 └── validate(value) -> Vec<String>

FormFieldType (enum), FormFieldValidation (enum)
FormFieldOption, FormFieldValidationRule (dataclasses)
```

## 4. PyO3 Binding Structure

```rust
// FormFieldType, FormFieldValidation as simple enums
#[pyclass]
enum FormFieldType { ... }

#[pyclass]
struct FormField { ... }  // with getters/setters

#[pyclass]
struct FormDefinition { ... }

#[pyclass]
struct FormEngine {
    forms: HashMap<String, FormDefinition>,
}
```

## 5. Libraries Analysis

| Current Python | Rust Equivalent | Notes |
|---------------|----------------|-------|
| `re` (regex) | `regex` crate | Pattern matching for field validation |
| `logging` | `log` + `env_logger` | Structured logging |
| `enum` (stdlib) | Native Rust enums | Direct translation |

## 6. Performance Hot Paths

- `FormField.validate()` — called per field per form submission. O(n) string operations + regex.
- `FormDefinition._evaluate_condition()` — calls `PythonEvaluator.evaluate()` which uses `eval()`. Would need `rhai` or to precompute conditions.
- `FormEngine.submit_form()` — iterates all fields and validates. Trivially parallelizable in Rust.
- `FormEngine.render_form()` — deep clone of form definition + defaults. Clone is cheap in Rust with `#[derive(Clone)]`.

## 7. Error Handling

| Python | Rust Strategy |
|--------|---------------|
| `list[str]` error accumulation | `Vec<String>` returned from validate |
| `dict[str, list[str]]` errors | `HashMap<String, Vec<String>>` |
| `{"success": False, "errors": ...}` pattern | Proper `Result<T, FormError>` enum |
| `except Exception` in condition eval | `Result<bool, EvalError>` |
