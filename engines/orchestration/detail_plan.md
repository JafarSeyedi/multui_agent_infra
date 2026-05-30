# Detailed Implementation Plan: Orchestration Runtime Upgrade

## Overview

This document details the implementation plan for upgrading the `engines/orchestration` layer to be fully aligned with the OSDM (Orchestration Standard Definition Model) and support complete BPMN 2.0, CMMN, DMN, CEP, and multi-agent features at or above Camunda level.

---

## File-Level Tokenization

### Core Orchestration Files Token Summary

| File | Purpose | Current Status | OSDM Alignment Gap |
|------|---------|---------------|-------------------|
| `core/engine.py` | Main orchestration engine coordinator | Has basic engine lifecycle, deployment, instance management | Needs OSDM model integration, MSDM/DSDM serialization alignment |
| `core/instance.py` | Process instance management | Has InstanceState, ProcessInstance, InstanceManager | Needs OSDM instance types, state machine integration |
| `core/token.py` | Token-based execution tracking | Has Token, TokenState, TokenManager | Missing OSDM BPMN token semantics alignment |
| `core/context.py` | Execution context/variable scoping | Has ExecutionContext, ContextManager | Needs MSDM schema binding for variables |
| `core/scheduler.py` | Job/timer scheduling | Has ScheduledTask, Scheduler | Missing OSDM timer definition alignment |
| `core/correlation.py` | Message/event correlation | Has CorrelationKey, MessageSubscription | OSDM correlation model coverage incomplete |
| `core/event_bus.py` | Event publishing/subscribing | Has Event, EventBus, Subscription | Good foundation, needs replay enhancement |

### OSDM Models Token Summary

| Model File | Key Entities | Orchestration Relevance |
|------------|-------------|----------------------|
| `osdm_models.py` | BPMN: Process, Activity, Gateway, Event; CMMN: PlanItem, Stage, Milestone, Sentry; DMN: Decision, InputData, DecisionTable; State: State, Transition, StateMachineModel; CEP: EventStream, CEPRule; Multi-Agent: InteractionProtocol, InteractionModel | Complete metamodel for all orchestration standards |
| `msdm_models.py` | Entity, Attribute, DataType, Constraint, Annotation, Index | Structure metadata for runtime records serialization |
| `dsdm_models.py` | DataNode, DataDocument, SchemaBinding, DataValue | Data instance format for runtime state persistence |
| `ssdm_models.py` | ServiceOperation, Interface, Binding | Service integration for external task execution |

---

## Phase 1 — Runtime Data Foundation (Checkpoint A)

### Files to Create/Modify

#### 1. `runtime/__init__.py`
**Purpose:** Export stable runtime record schemas and managers.
**Changes:**
- Export `RuntimeRecordEnvelope`, `serialize_runtime_record`, `deserialize_runtime_record`
- Export `StateManager`, `VariableManager`, `TimerManager`, `ResourceManager`
- Remove any incomplete exports

#### 2. `runtime/runtime_records.py` (Already exists - verify completeness)
**Purpose:** Define MSDM-backed runtime record schemas.
**Changes:**
- Add missing record types: `JOB_RECORD`, `AUDIT_RECORD`, `TIMER_RECORD` already present
- Add OSDM field alignment for all runtime records
- Ensure all records use MSDM Entity definitions for schema validation

#### 3. `core/context.py`
**Purpose:** Replace loose variable storage with MSDM/DSDM-backed scoped execution state.
**Detailed Changes:**
```
- Variable class:
  * Add schema_binding field (SchemaBinding to MSDM Entity/Attribute)
  * Add MSDM-aware type coercion in _infer_type()
  * Add to_dsdm() method for DSDM serialization
  
- ExecutionContext class:
  * Add bind_schema() method to link context to MSDM Entity
  * Add persist_variables() method using DSDM serialization
  * Add restore_variables() method from DSDM DataDocument
  
- ContextManager class:
  * Integrate with MSDMEntityRegistry for schema lookups
  * Add schema-aware context creation
  * Add variable conflict/version control
```

#### 4. `core/instance.py`
**Purpose:** Replace ad hoc instance/activity state with OSDM-aware runtime records.
**Detailed Changes:**
```
- ProcessInstance class:
  * Add osdm_process_ref field (Process reference from OSDM)
  * Add osdm_state semantics (map to OSDM InstanceState)
  * Add serialize_to_dsdm() / deserialize_from_dsdm() methods
  
- InstanceManager class:
  * Use MSDM schema for instance serialization
  * Add OSDM-compatible to_dict() format
  * Add MSDM-aware loading with schema validation
```

#### 5. `persistence/repository.py`
**Purpose:** Add DSDM/MSDM-aware codec helpers and storage-backed repository abstractions.
**Detailed Changes:**
```
- RepositoryProtocol:
  * Add async methods: save_persisted(), get_persisted(), append_persisted()
  * Add MSDM schema binding support
  
- PersistentRuntimeRepository:
  * Implement full DSDM serialization pipeline
  * Add time-series writeback for audit/history records
  * Add event-log integration for traceability
```

#### 6. `persistence/instance_repository.py`
**Purpose:** Persist instance records with MSDM/DSDM serialization.
**Detailed Changes:**
- Already extends `PersistentRuntimeRepository` - verify integration
- Add OSDM instance type support (process/case/state/decision instances)

#### 7. `runtime/state_manager.py` (Already exists - enhance)
**Purpose:** Persist state snapshots through storage adapters with MSDM/DSDM.
**Detailed Changes:**
- Verify storage adapter integration completeness
- Add OSDM state semantics (state machine states)
- Add replay support from time-series storage

---

## Phase 2 — Core Runtime Refactor (Checkpoint B)

### 8. `core/correlation.py`
**Purpose:** Align correlation with OSDM event/message definitions.
**Detailed Changes:**
```
- CorrelationSubscription:
  * Add osdm_correlation_key_ref field
  * Add subscription scope (process/case/dmn)
  
- CorrelationEngine:
  * Add OSDM CorrelationKey model support
  * Add persistent subscription lifecycle
  * Add correlation rule evaluation against OSDM semantics
```

### 9. `core/scheduler.py`
**Purpose:** Persist jobs/timers with OSDM timer definition alignment.
**Detailed Changes:**
```
- ScheduledTask:
  * Add osdm_timer_event_def field (TimerEventDefinition)
  * Add job_executor context (process activity reference)
  
- Scheduler:
  * Implement full OSDM timer semantics (date/cycle/duration)
  * Add recovery/retry with exponential backoff from OSDM
  * Add calendar timer support
```

### 10. `core/token.py`
**Purpose:** Align token semantics with BPMN/petri-like execution models.
**Detailed Changes:**
```
- Token:
  * Add osdm_scope_ref (Activity flow scope)
  * Add osdm_activity_ref (Activity reference)
  * Add petri net transition semantics
  
- TokenManager:
  * Add OSDM flow element type awareness
  * Add token history persistence
  * Add compensation/subprocess token scopes
```

### 11. `core/event_bus.py`
**Purpose:** Persist domain events with OSDM semantics.
**Detailed Changes:**
```
- Event:
  * Add osdm_event_def reference
  * Add osdm_activity_instance_ref
  
- EventBus:
  * Add OSDM event type enumeration
  * Add replay from persistent storage
  * Add ordering guarantees per OSDM requirements
```

---

## Phase 3 — Persistence and Observability (Checkpoint C-D)

### 12. `persistence/variable_repository.py`
**Purpose:** Persist scoped variable revisions with MSDM schema binding.
**Detailed Changes:**
- Implement full scope-aware variable persistence
- Add MSDM schema validation on write
- Add time-based history queries

### 13. `persistence/event_repository.py`
**Purpose:** Persist runtime/event-bus/domain events.
**Detailed Changes:**
- Add OSDM correlation query support
- Add event ordering by instance/timestamp
- Add replay filtering capabilities

### 14. `persistence/history_repository.py`
**Purpose:** Store audit/history in time-series/event-log format.
**Detailed Changes:**
- Add time-series aggregation for metrics
- Add audit trail reconstruction API
- Add migration support hooks

---

## Phase 4 — BPMN Completion

### 15. `bpmn/engine.py`
**Changes:**
- Integrate OSDM Process model
- Add full BPMN execution semantics
- Support compensation, transactions, subprocess

### 16. `bpmn/process_executor.py`
**Changes:**
- Implement full BPMN activity traversal
- Support parallel gateways with token semantics
- Implement event subprocess handling

### 17. `bpmn/activity_handler.py`
**Purpose:** Support all task/activity kinds.
**Changes:**
- ServiceTask handler with SSDM integration
- UserTask handler with work assignment
- ScriptTask with safe execution
- BusinessRuleTask with DMN integration

### 18. `bpmn/gateway_handler.py`
**Purpose:** Support all gateway types.
**Changes:**
- ExclusiveGateway with condition evaluation
- ParallelGateway with token splitting/merging
- InclusiveGateway with token accumulation
- EventBasedGateway with event correlation

### 19. `bpmn/event_handler.py`
**Purpose:** Implement all event types.
**Changes:**
- Start/End events
- Intermediate catch/throw events
- Boundary events with interruption
- Timer/signal/message/error escalation

---

## Phase 5 — CMMN / State Machine / DMN (Checkpoint D)

### 20. `cmmn/engine.py`
**Purpose:** Case lifecycle with OSDM alignment.
**Changes:**
- Integrate OSDM CMMN models (Stage, PlanItem, Milestone)
- Add sentry evaluation engine
- Support case file item management

### 21. `cmmn/case_executor.py`
**Purpose:** CMMN execution.
**Changes:**
- Discretionary item activation
- Planning table behavior
- Stage lifecycle management

### 22. `state_machine/engine.py`
**Purpose:** State machine lifecycle.
**Changes:**
- Support hierarchical states (nested regions)
- Add history (shallow/deep) semantics
- Implement pseudostate handling

### 23. `dmn/engine.py`
**Purpose:** Decision execution.
**Changes:**
- FEEL expression evaluation
- Decision table hit policies
- Decision service invocation

---

## Phase 6 — CEP / Multi-Agent / Integration (Checkpoint E)

### 24. `cep/engine.py`
**Changes:**
- Windowing with RecoveryState
- Pattern matching operators
- Event stream processing

### 25. `multi_agent/engine.py`
**Changes:**
- Protocol-aware interaction
- Coordination state management
- Negotiation timeout handling

### 26. `integration/service_invoker.py`
**Changes:**
- SSDM service operation binding
- Async invocation support
- Retry/policy propagation

---

## Phase 7 — API / Deployment / Validation / Tests (Checkpoint F)

### 27. `api/__init__.py`
**Changes:**
- Export stable API surface
- Remove internal/test endpoints

### 28. `validation/validator.py`
**Changes:**
- OSDM structural validation
- Cross-model semantic validation
- Instance migration validation

---

## Implementation Timeline

### Week 1: Phase 1 Foundation
- Complete MSDM schema integration in runtime_records.py
- Implement state_manager.py persistence
- Wire core context to MSDM/DSDM

### Week 2: Phase 2 Core Refactor
- Complete correlation engine OSDM alignment
- Enhance scheduler with OSDM timer semantics
- Upgrade token manager with BPMN semantics

### Week 3-4: Phase 4 BPMN Completion
- Implement missing BPMN element handlers
- Add gateway and event handlers
- Complete process executor

### Week 5: Phase 5 CMMN/DMN/State Machine
- CMMN case execution
- DMN decision tables and FEEL
- State machine hierarchy

### Week 6: Phase 6 CEP/Multi-Agent
- CEP pattern matching
- Multi-agent protocol handling
- Integration layer completion

### Week 7: Phase 7 Final Integration
- API layer upgrade
- Validation and testing
- Documentation and examples

---

## OSDM Model Alignment Checklist

### BPMN Elements (from osdm_models.py)
- [ ] Process - DONE (schema defined, execution needed)
- [ ] Activity (Task, SubProcess, CallActivity) - PARTIAL
- [ ] Gateway (Exclusive, Parallel, Inclusive, EventBased, Complex) - MISSING
- [ ] Event (Start, End, Intermediate, Boundary) - PARTIAL
- [ ] SequenceFlow with conditions - MISSING
- [ ] ItemDefinition for data - MISSING
- [ ] ResourceRole - MISSING
- [ ] CorrelationSubscription - PARTIAL

### CMMN Elements (from osdm_models.py)
- [ ] CasePlanModel (Stage) - MISSING
- [ ] PlanItem - MISSING
- [ ] Sentry - MISSING
- [ ] CaseFileItem - MISSING
- [ ] Milestone - MISSING

### DMN Elements (from osdm_models.py)
- [ ] Decision - MISSING
- [ ] DecisionTable - MISSING
- [ ] InputData - MISSING
- [ ] InformationRequirement - MISSING
- [ ] HitPolicy - MISSING
- [ ] FEEL expressions - PARTIAL

### State Machine Elements (from osdm_models.py)
- [ ] State and Transition - MISSING
- [ ] PseudoState (initial, history, fork, join) - MISSING
- [ ] StateMachineRegion - MISSING

### CEP Elements (from osdm_models.py)
- [ ] EventStream - MISSING
- [ ] CEPRule - MISSING
- [ ] Window operators - MISSING

### Multi-Agent (from osdm_models.py)
- [ ] InteractionProtocol - MISSING
- [ ] InteractionStrategy enum - MISSING

---

## Verification Strategy

1. **Schema Validation:** All runtime records must validate against MSDM schemas
2. **Persistence Tests:** Verify key-value, time-series, and event-log writes
3. **BPMN Conformance:** Execute BPMN 2.0 spec examples and verify behavior
4. **CMMN Conformance:** Execute CMMN spec examples
5. **DMN Conformance:** Execute DMN spec decision table scenarios
6. **Replay Testing:** Kill/restart engine and verify state recovery
7. **Migration Testing:** Deploy new versions and migrate live instances

---

## Risk Mitigation

1. **Breaking Changes:** Maintain backward compatibility with existing ProcessInstance format
2. **Performance:** Cache MSDM schemas, lazy-load DSDM documents
3. **Storage Integration:** Graceful degradation when storage unavailable
4. **Expression Evaluation:** Sandboxed FEEL/Python/JS evaluators