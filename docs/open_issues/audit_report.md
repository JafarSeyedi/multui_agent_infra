# Code Audit Report

**Generated:** 2026-06-12
**Project:** multi-agent-infra (BPMS Platform)
**Scope:** engines/ (8 packages), 42+ files audited

---

## Executive Summary

**Overall Compliance: ~35%** against coding principles (`coding_concepts.md`) and software patterns (`software_patterns.md`).

| Severity | Count | Key Issues |
|----------|-------|-----------|
| **HIGH** | 6 | God classes, missing mandatory patterns (State, Command, Strategy, Visitor), lazy hidden imports |
| **MEDIUM** | 13 | Error swallowing, deep inheritance, DI gaps, missing cross-cutting patterns, type hint abuse |
| **LOW** | 4 | Dead code, mutation side effects, unbounded caches, hardcoded defaults |

---

## HIGH Severity Issues

### H1 — OrchestrationEngine God Class (DI + SOC Violation)
- **File:** `engines/orchestration/core/engine.py` (644 lines)
- **Issue:** 25+ dependencies hard-instantiated in `__init__` with no injection path. Class has 7+ distinct responsibilities (lifecycle, deployment, definition, instance, recovery, executors, persistence).
- **Principles violated:** DI (rule 9), SoC (rule 3), ISP (rule 8), God Class anti-pattern

### H2 — Missing State Pattern for Process/Task Lifecycle
- **File:** `engines/orchestration/core/instance.py`, `core/token.py`
- **Issue:** `InstanceState` / `TokenState` are flat enums with `if state != X: raise` conditional guards. No polymorphic state objects.
- **Pattern violated:** State pattern (mandatory per rule 1)

### H3 — Missing Strategy Pattern for Gateway Routing
- **File:** `engines/orchestration/bpmn/gateway_handler.py`
- **Issue:** `choose()` and `choose_osdm()` use `if gateway_type == EXCLUSIVE/INCLUSIVE/PARALLEL/...` chains. Adding a new gateway type requires modifying the chain.
- **Pattern violated:** Strategy pattern (mandatory per rule 4)

### H4 — Missing Command Pattern for Operations
- **File:** entire codebase
- **Issue:** No `Command` ABC, no `execute()`/`undo()`, no operation queue. All operations are direct method calls.
- **Pattern violated:** Command pattern (mandatory per rule 3)

### H5 — Missing Visitor Pattern for Validation/Export
- **File:** `engines/orchestration/validation/*.py`
- **Issue:** No `Visitor` interface, no `accept(visitor)` on models. Validators are standalone unrelated classes.
- **Pattern violated:** Visitor pattern (mandatory per rule 5)

### H6 — Lazy Hidden Imports in All 8 Bus Implementations
- **File:** `engines/communication/buses/*.py` (8 files)
- **Issue:** `_get_agent_message()` with `global` cache and method-level import. Hides dependency graph, breaks test isolation.
- **Principles violated:** Explicit over Implicit (rule 5), hidden dependencies anti-pattern

---

## MEDIUM Severity Issues

| ID | Issue | File(s) | Principle |
|----|-------|---------|-----------|
| M1 | Error swallowing: `except Exception: return False` in guard/condition evaluators | `state_machine/guard_evaluator.py`, `transition_handler.py`, `state_executor.py`, `bpmn/process_executor.py` | Fail Fast (rule 6) |
| M2 | `AgentRegistry.register()` silently mutates agent instances by setting `vector_db`/`storage` | `agent/agent_registry.py:21-23` | Explicit over Implicit (rule 5) |
| M3 | `ProcessInstance` knows about DSDM serialization (domain model mixing infra concern) | `core/instance.py:485-510` | SoC (rule 3) |
| M4 | Lazy evaluator imports inside methods (4 files, 6 locations) | `bpmn/process_executor.py`, `state_machine/*.py` | Explicit over Implicit (rule 5) |
| M5 | Excessive `Any` type usage in public APIs | `core/engine.py`, `state_machine/*.py` | Explicit Typing (rule 12) |
| M6 | `BPMNProcessExecutor` God Class (881 lines) | `bpmn/process_executor.py` | SoC (rule 3) |
| M7 | Missing Decorator pattern for cross-cutting concerns | `runtime/` | Decorator pattern |
| M8 | Missing Builder pattern for complex models | `core/engine.py` (EngineConfig: 29 fields) | Builder pattern |
| M9 | Missing Chain of Responsibility for validation pipeline | `validation/*.py` | Chain of Responsibility |
| M10 | `CoordinationHandler` is all stubs returning dummy data (83 lines) | `multi_agent/coordination_handler.py` | Mediator pattern |
| M11 | Missing Abstract Factory for storage backends | `storage/*/backends/` | Abstract Factory |
| M12 | Hardcoded `db_path = "database.db"` default | `storage/relational/base.py:16` | DI (rule 9) |
| M13 | DI gaps: ContextManager, PythonEvaluator, handlers created inline | `bpmn/engine.py`, `state_machine/engine.py`, `bpmn/process_executor.py` | DI (rule 9) |

---

## LOW Severity Issues

| ID | Issue | File(s) |
|----|-------|---------|
| L1 | 100+ lines of commented-out dead code | `document/ingestion/ingestion_service.py` |
| L2 | Unbounded BPMN document cache (`_parsed_documents`) | `bpmn/engine.py:59` |
| L3 | Unknown guard ID returns `False` instead of raising error | `state_machine/guard_evaluator.py:43-47` |
| L4 | StateMachineHistory all in-memory, lost on restart | `state_machine/history_manager.py` |

---

## Well-Implemented Patterns (Good)

| Pattern | Evidence |
|---------|----------|
| ✅ **Adapter** | All storage backends (vector, relational, object, KV, cache, message transports) implement proper interfaces |
| ✅ **Repository** | EventRepository, InstanceRepository, TokenRepository, VariableRepository, MetricRepository, AlertRepository |
| ✅ **Memento** | StateSnapshotManager, Token.create_snapshot(), StateManager.history() |
| ✅ **Template Method** | BaseAgent.run() skeleton, Validator.validate(), BaseStorage.connect/disconnect |
| ✅ **Facade** | OrchestrationEngine provides simplified public API |
| ✅ **Strategy (interaction)** | InteractionStrategy base with concrete backends (debate, group-chat, ensemble, self-refine, broadcast, round-robin) |
| ✅ **Pydantic v2** | Correct use of model_fields, @field_validator, ConfigDict |
| ✅ **Async/await** | Consistent async patterns for I/O-bound operations |
| ✅ **Dataclasses** | Used consistently for data containers |
| ✅ **Type hints (partial)** | Most public methods have type hints (excessive `Any` is the remaining issue) |

---

## Fix Status

| Phase | Items | Status |
|-------|-------|--------|
| Phase 1 — Mandatory Patterns | H2 (State), H3 (Strategy), H4 (Command), H5 (Visitor), H6 (Bus imports) | **Not started** |
| Phase 2 — God Classes + DI | H1 (OrchestrationEngine), M6 (BPMNProcessExecutor), M13 (DI gaps) | **Not started** |
| Phase 3 — Cross-cutting | M1 (error swallowing), M7 (Decorator), M8 (Builder), M9 (CoR), M10 (Mediator), M11 (Factory) | **Not started** |
| Phase 4 — Cleanup | M2 (mutation), M3 (DSDM in domain), M4 (lazy imports), M5 (Any types), M12 (db_path), L1-L4 | **Not started** |
