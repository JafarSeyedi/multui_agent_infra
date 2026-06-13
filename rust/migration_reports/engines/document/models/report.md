# Models Analysis Report for Rust Migration

## Overview

Analyzed 27 Python files containing data model definitions for OSDM, CSDM, MSDM, SSDM, TSDM, BPMN, CMMN, DMN, SCXML/State Machines, CEP, Petri nets, and Multi-Agent interaction models. Total: **~8,500 lines** across all files.

## Architecture Summary

### Model Hierarchy

```
BaseDocument (Pydantic BaseModel, dict-based)
├── BaseCSDMDocument (CSDM models)
├── BaseMSDMDocument (MSDM models)
├── BaseSSDMDocument (SSDM models)
├── BaseTSDMDocument (TSDM models)
└── BaseOSDMDocument
    ├── BPMNDocument
    ├── CMMNDocument
    ├── StateMachineDocument
    ├── DMNDocument
    ├── CEPDocument
    └── MultiAgentInteractionDocument
```

### Top-level orchestration

```
OSDMModel ─► processes / collaborations / choreographies / cmmn / state_machines / dmn / cep / interaction_models
```

## Key Findings

### 1. Two Serialization Paradigms

| Mechanism | Files | Strategy |
|-----------|-------|----------|
| **Pydantic v2** (`BaseModel`) | `generic_models.py`, `document_base.py`, `msdm_models.py`, `ssdm_models.py`, `tsdm_models.py`, `csdm_base.py`, `csdm_models.py`, `csdm_migration.py` | `model_dump()` / `model_validate()` |
| **Dataclass + manual to_dict/to_json** | `osdm_models.py`, all BPMN/CMMN/DMN/SCXML/CEP models | Recursive `to_dict()`, `to_json()`, `from_dict()` classmethods |

**Impact on Rust migration**: The dataclass-based models require implementing a custom serialization layer. Pydantic models could leverage Serde-like derive macros.

### 2. Cross-File Dependencies

```
osdm_models.py ─► document_base.py (BaseDocument, BaseElement)
                ─► csdm_base.py (CSDMBaseElement)
                ─► generic_models.py (FormalExpression, etc.)

csdm_models.py ─► csdm_base.py (CSDMBase)
csdm_migration.py ─► csdm_models.py

msdm_models.py ─► base_models.py (Parameter, PropertyValue)
ssdm_models.py ─► base_models.py
tsdm_models.py ─► base_models.py
```

### 3. Circular Dependency Risk

`document_base.py` imports from `generic_models.py`. `generic_models.py` imports from `document_base.py`. This is managed in Python via forward references. Rust's module system and lack of circular imports means **these must be merged or restructured**.

### 4. Inheritance Patterns

| Pattern | Frequency | Examples |
|---------|-----------|----------|
| Pydantic model inheritance | 6 files | `BaseDocument` → `BaseCSDMDocument`, `BaseMSDMDocument`, etc. |
| Dataclass inheritance | 2 files | `FlowElement` → `FlowNode` → `Activity`, `State` → `Place` |
| Enum inheritance | 2 files | `PseudoStateKind`, `CEPOperator`, etc. |
| Mixin-style (multiple base) | Rare | Some SCXML nodes extend from multiple base types |

### 5. Type Complexity

| Complexity | Count | Examples |
|------------|-------|----------|
| `str` fields | ~150 | Names, IDs, descriptions |
| `Optional[str]` | ~60 | Optional refs, descriptions |
| `list[...]` | ~80 | Child element collections |
| `dict[str, ...]` | ~20 | Extensions, attributes |
| `Any` | ~10 | Generic parameter values, loose dicts |
| `int`, `float`, `bool` | ~50 | Counters, flags, durations |
| **Union types** | ~5 | `str | Script`, `str | ServiceOperation` |

### 6. Element Counts by File

| File | Classes/Dataclasses | Enums | Lines |
|------|-------------------|-------|-------|
| osdm_models.py | 40 | 8 | 1766 |
| document_base.py | 4 | 0 | 60 |
| generic_models.py | 15 | 4 | 270 |
| csdm_base.py | 6 | 0 | 89 |
| csdm_models.py | 18 | 10 | 1270 |
| csdm_migration.py | 9 | 0 | 257 |
| base_models.py | 8 | 1 | 189 |
| msdm_models.py | 30 | 6 | 1342 |
| ssdm_models.py | 25 | 5 | 1120 |
| tsdm_models.py | 20 | 4 | 980 |
| bpmn_models.py | 22 | 3 | ~450 |
| scxml_models.py | 15 | 2 | ~300 |
| cmmn_models.py | 18 | 3 | ~350 |
| dmn_models.py | 14 | 2 | ~280 |

## Recommendations per Domain

### OSDM Layer (`osdm_models.py`)

**Strategy**: Replace `@dataclass` with Rust `struct` + Serde. Remove manual `to_dict`/`to_json` in favor of `#[derive(Serialize, Deserialize)]`.

**Challenges**:
- Deep inheritance chains (`BaseElement` → `FlowElement` → `FlowNode` → `Activity`)
- `field(default_factory=list)` → `Vec<T>` with `#[serde(default)]`
- `field(default_factory=dict)` → `HashMap<String, V>` with `#[serde(default)]`
- `str | None` → `Option<String>`
- `Script | str` union → Enum-based dispatch or `serde_untagged`
- `CloudResourceBinding` has `dict[str, Any]` → `HashMap<String, serde_json::Value>`

**Circular import resolution**: Merge `document_base.py` and `generic_models.py` into a single `base_types.rs` module, since they have bidirectional dependencies.

### CSDM Layer (`csdm_models.py`, `csdm_base.py`, `csdm_migration.py`)

**Strategy**: Pydantic migration state tracking → Rust enum with version mapping.

**Challenges**:
- `StateEntry` pattern (from_state → to_state + migrate function) → trait `MigrationStep<S, T>`
- `OriginalProcess` and `OriginalDataFlow` Pydantic models → serde-based structs
- `Any` types for generic migration payloads → `serde_json::Value`

**Recommendation**: The migration framework maps cleanly to a trait-based approach in Rust.

### MSDM Layer (`msdm_models.py`)

**Strategy**: Mostly straightforward `BaseModel` → Rust struct mapping.

**Challenges**:
- `PropertyValue` = `str | int | float | bool | None | list | dict` → `#[serde(untagged)]` enum
- `Parameter` with `property_value: PropertyValue` → recursive serde enum
- Complex nested structure definitions (data flows, boundaries, dependencies)

**Recommendation**: Most types are naturally `struct` + `Option<T>` with `#[serde(default)]`. The `PropertyValue` enum needs careful serde untagged handling.

### SSDM Layer (`ssdm_models.py`)

**Strategy**: Similar to MSDM.

**Specifics**:
- Service, Endpoint, Interface models → straightforward struct mapping
- Security and SLA fields → Option-wrapped inner structs
- `Parameter` reuse from `base_models.py`

### TSDM Layer (`tsdm_models.py`)

**Strategy**: Direct mapping.

**Specifics**:
- Task, Workflow, Step, Condition models
- `document_links: list[DocumentLink]` → `Vec<DocumentLink>`
- State machine model references → String IDs resolved in OSDM layer

### BPMN / CMMN / DMN / SCXML / CEP / Petri Net sub-models

**Strategy**: Each sub-domain maps to a Rust module.

**Challenges**:
- Graph structures with edges/nodes → `Vec<State>`, `Vec<Transition>` adjacency
- BPMN: deeply nested element hierarchy (FlowElement → FlowNode → Gateway/Activity/Event)
- Petri nets: Places, Transitions, Arcs with inhibitor/reset semantics
- CEP: pattern matching rules with string expressions
- `FormalExpression` used as a generic across ALL domains → needs to be a shared base type

## Code Statistics

### Total unique types: ~260
### Total enums: ~48
### Total fields: ~1,200+
### Union types (sum types needed): ~8

## Recommended Module Layout for Rust

```
document/
├── base_types.rs          # BaseElement, BaseDocument, FormalExpression (merged from document_base.py + generic_models.py)
├── osdm.rs                # OSDM top-level document types
├── csdm.rs                # CSDM models + migration framework
├── msdm.rs                # MSDM models
├── ssdm.rs                # SSDM models
├── tsdm.rs                # TSDM models
├── sub_models/
│   ├── bpmn.rs
│   ├── cmmn.rs
│   ├── dmn.rs
│   ├── scxml.rs
│   ├── cep.rs
│   └── petri.rs
└── mod.rs                 # Re-exports
```

## First Migration Target

**`document_base.py` + `generic_models.py`** → `base_types.rs`

These are the foundation with zero file-specific dependencies. Once these compile, everything else can build on top.

### Estimated Effort

| Phase | Files | Est. Person-Days | Dependencies |
|-------|-------|------------------|--------------|
| base_types.rs | 2 | 1 | Serde + serde_json |
| osdm.rs | 1 | 3 | base_types |
| csdm.rs | 3 | 2 | base_types |
| msdm.rs | 1 | 2 | base_types |
| ssdm.rs + tsdm.rs | 2 | 2 | base_types |
| sub-models (6 modules) | 6 | 3 | osdm |
| Tests | All | 3 | All |
| **Total** | **27** | **~16** | |

## Key Rust Crates Needed

- `serde` + `serde_json` + `serde_derive` — core serialization
- `serde_yaml` — optional YAML support
- `thiserror` — error types for parsing/validation
- `strum` + `strum_macros` — enum string conversions (replacing Python `str(Enum)`)
- `chrono` — date/time types (used in BPMN, DMN models)
