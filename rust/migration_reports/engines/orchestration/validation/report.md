# Validation Layer — Rust Migration Report

## Files Analyzed
- `__init__.py` (33 lines) — re-exports
- `validator.py` (73 lines) — base class + chain of responsibility
- `bpmn_validator.py` (15 lines) — BPMN validator
- `cmmn_validator.py` (15 lines) — CMMN validator
- `dmn_validator.py` (15 lines) — DMN validator
- `model_visitor.py` (57 lines) — visitor pattern
- `osdm_validator.py` (204 lines) — OSDM validators (BPMN, CMMN, DMN, SM)
- `semantic_validator.py` (23 lines) — cross-domain semantic checks
- `state_machine_validator.py` (15 lines) — SM validator

## 1. Pre-refactor Patterns

| Pattern | Files | Details |
|---------|-------|---------|
| `Any` | validator.py:12,41, bpmn_validator.py:10, etc. | `validate(payload: Any)` on every validator |
| `dict[str, Any]` | semantic_validator.py:21-22 | Payload type in `find_reference_gaps` |
| `isinstance` | bpmn_validator.py:11, cmmn_validator.py:11, dmn_validator.py:11, semantic_validator.py:12, state_machine_validator.py:11, osdm_validator.py:11 | `isinstance(payload, dict)` in all validators |
| Global state | None | No mutable global state |
| Mutable defaults | None | No mutable defaults |

## 2. Migration Notes & Rust Score

| File | Lines | Complexity | Rust Score | Notes |
|------|-------|-----------|------------|-------|
| validator.py | 73 | Low | 5/5 | Chain of Responsibility → trait + `Vec<Box<dyn Validator>>` |
| bpmn_validator.py | 15 | Low | 5/5 | Trivial |
| cmmn_validator.py | 15 | Low | 5/5 | Trivial |
| dmn_validator.py | 15 | Low | 5/5 | Trivial |
| model_visitor.py | 57 | Low | 5/5 | Visitor pattern → trait dispatch with enum |
| osdm_validator.py | 204 | Medium | 5/5 | Pure dict navigation, no eval, no deps |
| semantic_validator.py | 23 | Low | 5/5 | Trivial |
| state_machine_validator.py | 15 | Low | 5/5 | Trivial |

**Overall**: 5/5. This is the cleanest migration candidate. All validators are pure functions over dictionary payloads. No external dependencies, no eval, no async. The visitor dispatch can use an enum instead of `isinstance`.

## 3. Ownership Map

```
ValidatorChain (Vec<Box<dyn Validator>>)
 └── Validator (trait with visit_* methods)
      ├── BPMNValidator
      ├── CMMNValidator
      ├── DMNValidator
      ├── SemanticValidator
      ├── StateMachineValidator
      ├── BpmnOsdmValidator
      ├── CmmnOsdmValidator
      ├── DmnOsdmValidator
      └── StateMachineOsdmValidator

ModelVisitor (trait)
 └── _VISIT_DISPATCH (type → method mapping)

Value types:
ValidationResult, ValidationLevel (enum)
ValidationError, OsdmValidationResult
```

## 4. PyO3 Binding Structure

```rust
#[pyclass]
struct ValidatorChain { validators: Vec<PyObject> }

#[pyclass]
enum ValidationLevel { Info, Warning, Error }

#[pyclass]
struct ValidationResult { level: ValidationLevel, code: String, message: String }

// Each validator as a standalone #[pyclass] or as methods on ValidatorChain
```

## 5. Libraries Analysis

| Current Python | Rust Equivalent | Notes |
|---------------|----------------|-------|
| `abc.ABC` | Native traits | Direct mapping |
| `enum` | Native enums | Direct mapping |
| `dataclass` | `#[derive(Clone)]` structs | Direct mapping |

**Zero external dependencies required.** All logic is pure string/dict manipulation.

## 6. Performance Hot Paths

- None. Each validator does O(1) or O(n) dict lookups. No computation-heavy paths.
- `osdm_validator.py:_validate_sequence_flows` — O(n*m) over flows × activities for ID cross-referencing. Trivially fast in Rust with `HashSet`.

## 7. Error Handling

| Python | Rust Strategy |
|--------|---------------|
| `ValidationResult` (list accumulator) | `Vec<ValidationResult>` via `Result<(), Vec<ValidationError>>` |
| `.add_error()` / `.add_warning()` | Builder pattern on `ValidationResult` |
| `isinstance(payload, dict)` guard | `match payload { Value::Object(_) => ..., _ => Err(...) }` |
