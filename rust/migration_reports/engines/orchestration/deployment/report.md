# Deployment & Versioning — Rust Migration Report

## Files Analyzed
- `__init__.py` (17 lines) — re-exports
- `deployer.py` (56 lines) — `Deployer`
- `migration_handler.py` (39 lines) — `MigrationHandler`
- `tenant_manager.py` (36 lines) — `TenantManager`
- `version_manager.py` (48 lines) — `VersionManager`

## 1. Pre-refactor Patterns

| Pattern | Files | Details |
|---------|-------|---------|
| `Any` | deployer.py:7, version_manager.py:6 | Return types / dict values |
| `dict[str, Any]` | deployer.py:44, version_manager.py:47 | `metadata()`, `snapshot()` |
| `isinstance` | None | Not present |
| Global state | None | No mutable module-level state |
| Mutable defaults | None | No mutable defaults |

## 2. Migration Notes & Rust Score

| File | Lines | Complexity | Rust Score | Notes |
|------|-------|-----------|------------|-------|
| deployer.py | 56 | Low | 5/5 | Simple checksum generation, metadata |
| migration_handler.py | 39 | Low | 5/5 | State check + ID reassign |
| tenant_manager.py | 36 | Low | 5/5 | HashMap with immutable values |
| version_manager.py | 48 | Low | 5/5 | Version counter, key-indexed |

**Overall**: 5/5. Simplest sub-module in the orchestration engine. Pure data management with no I/O, no eval, no complex dependencies.

## 3. Ownership Map

```
Deployer
 ├── VersionManager
 └── methods: deploy, apply, metadata

VersionManager
 └── index: HashMap<(Option<String>, String), Vec<ProcessDefinition>>
      └── methods: versions, assign_version, get_latest, snapshot

TenantManager
 └── tenants: HashMap<String, TenantInfo>
      └── methods: register, disable, is_enabled, get

MigrationHandler
 └── instance_manager: Option<InstanceManager>
      └── methods: migrate

Value types:
DeploymentArtifact, DeploymentError
MigrationPlan, MigrationResult
TenantInfo
VersionConflict
```

## 4. PyO3 Binding Structure

```rust
#[pyclass]
struct Deployer { version_manager: VersionManager }

#[pyclass]
struct VersionManager {
    index: HashMap<(Option<String>, String), Vec<PyObject>>,
}

#[pyclass]
struct TenantManager {
    tenants: HashMap<String, TenantInfo>,
}

#[pyclass]
struct MigrationHandler {
    instance_manager: Option<PyObject>,
}
```

## 5. Libraries Analysis

| Current Python | Rust Equivalent | Notes |
|---------------|----------------|-------|
| `uuid.uuid4()` | `uuid` crate | Checksum generation |
| `datetime` | `chrono` | Deployment timestamps |

**Zero external dependencies required** beyond `uuid` and `chrono` (both trivial).

## 6. Performance Hot Paths

- None. All operations are O(1) or O(n) over tiny collections.
- `VersionManager.assign_version()` — O(1) lookup + append.
- `Deployer.deploy()` — O(1) checksum generation.

## 7. Error Handling

| Python | Rust Strategy |
|--------|---------------|
| `DeploymentError(RuntimeError)` | `thiserror` enum |
| `VersionConflict(RuntimeError)` | Error variant in `VersionError` |
| `RuntimeError("Cannot migrate inactive")` | `MigrationError::InactiveInstance` |
