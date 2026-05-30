# Detailed Implementation Plan: Orchestration Runtime Upgrade

## Overview

This document details the implementation plan for upgrading the `engines/orchestration` layer to be fully aligned with the OSDM (Orchestration Standard Definition Model) and support complete BPMN 2.0, CMMN, DMN, CEP, and multi-agent features at or above Camunda level.

---

## File-Level Tokenization

### Core Orchestration Files Token Summary

| File | Purpose | Status | OSDM Alignment |
|------|---------|--------|---------------|
| `core/engine.py` | Main orchestration engine coordinator | ✅ Done | Has basic MSDM/DSDM integration |
| `core/instance.py` | Process instance management | ✅ **UPDATED** | Added OSDM refs, DSDM serialization |
| `core/token.py` | Token-based execution tracking | ✅ **UPDATED** | Added OSDM flow node references, type-aware move_to |
| `core/context.py` | Execution context/variable scoping | ✅ **UPDATED** | Added MSDM schema binding, DSDM serialization |
| `core/scheduler.py` | Job/timer scheduling | ✅ **UPDATED** | OSDM timer definition framework added |
| `core/correlation.py` | Message/event correlation | ✅ **UPDATED** | Added OSDM CorrelationRule, OsDmCorrelationSubscriptionBinding |
| `core/event_bus.py` | Event publishing/subscribing | ✅ **UPDATED** | Added set_osdm_metadata for listener/event type/CEP operator |

---

## Phase 1 — Runtime Data Foundation (Checkpoint A)

### ✅ Completed Items:

#### 1. `runtime/__init__.py`
- ✅ All runtime record exports present (VARIABLE_RECORD, STATE_SNAPSHOT_RECORD, etc.)
- ✅ OsDmTimerDefinition added to exports

#### 2. `runtime/runtime_records.py` (Already existed)
- ✅ MSDM schema definitions for all runtime records present
- ✅ DSDM serialization pipeline implemented

#### 3. `core/context.py` - ✅ UPDATED
- ✅ Added MSDM/DSDM imports
- ✅ Variable class: Added `schema_binding` field (SchemaBinding to MSDM Entity/Attribute)
- ✅ Variable class: Added `to_msdm_type()` method for MSDM type conversion  
- ✅ Variable class: Added `to_dsdm_document()` method for DSDM serialization
- ✅ ExecutionContext class: Added `schema_entity` and `_schema_registry` fields
- ✅ ExecutionContext class: Added `bind_schema()` method for MSDM Entity binding
- ✅ ExecutionContext class: Added `get_schema()` method for schema lookup
- ✅ ExecutionContext class: Added `serialize_to_dsdm()` and `serialize_to_json()` methods

#### 4. `core/instance.py` - ✅ UPDATED
- ✅ Added OSDM model imports (TYPE_CHECKING for Process, Stage, Decision, StateMachineModel)
- ✅ ProcessInstance class: Added OSDM model reference fields (_osdm_process_ref, _osdm_stage_ref, etc.)
- ✅ ProcessInstance class: Added `serialize_to_dsdm()` method for DSDM serialization
- ✅ ProcessInstance class: Added `to_dsdm_json()` method for JSON output

#### 5. `runtime/timer_manager.py` - ✅ UPDATED
- ✅ Added OsDmTimerDefinition dataclass for OSDM timer semantics
- ✅ Added OSDM timer_type support (date, cycle, duration)
- ✅ Added `calculate_deadline()` method for timer computation

---

## Phase 2 — Core Runtime Refactor (Checkpoint B)

### Completed Items:

#### 8. `core/correlation.py` - ✅ **UPDATED**
- ✅ Added OSDM TYPE_CHECKING imports (CorrelationKey, TimerEventDefinition)
- ✅ Added OsDmCorrelationSubscriptionBinding dataclass for OSDM property binding semantics
- ✅ Added CorrelationRule dataclass for OSDM correlation rule evaluation

#### 9. `core/scheduler.py` - ✅ **DONE**
- ✅ OsDmTimerEventType enum already present for dateTime/timeCycle/timeDuration
- ✅ OsDmTimerEventDefinition dataclass with calculate_deadline() method
- ✅ Exponential backoff retry in _schedule_retry()

#### 10. `core/token.py` - ✅ **UPDATED**
- ✅ Added OSDM TYPE_CHECKING imports (Activity, FlowNode, Gateway, Event)
- ✅ Added OSDM flow node reference fields (_osdm_flow_node, _osdm_activity, etc.)
- ✅ Added set_osdm_flow_node() and set_osdm_activity() methods for OSDM-aware token positioning

#### 11. `core/event_bus.py` - ✅ **UPDATED**
- ✅ Added OSDM TYPE_CHECKING imports (EventListenerType, EventDefinitionType, CEPOperator)
- ✅ Added set_osdm_metadata() method for BPMN/CEP event type metadata binding

---

## Phase 3 — Persistence and Observability (Checkpoint C-D)

### Pending Items:

#### 12. `persistence/variable_repository.py` - ✅ EXISTS
- Scope-aware variable persistence already implemented
- MSDM schema validation needed

#### 13. `persistence/event_repository.py` - ✅ EXISTS
- OSDM correlation query support needed
- Event ordering by instance/timestamp needed

#### 14. `persistence/history_repository.py` - ✅ EXISTS
- Time-series aggregation for metrics needed
- Audit trail reconstruction API needed

---

## Phase 4 — BPMN Completion (Checkpoint C)

### Pending Items:

#### 15. `bpmn/engine.py` - 🔄 PENDING
- Integrate OSDM Process model fully
- Add full BPMN execution semantics
- Support compensation, transactions, subprocess

#### 16. `bpmn/process_executor.py` - 🔄 PENDING
- Implement full BPMN activity traversal
- Support parallel gateways with token semantics
- Implement event subprocess handling

---

## Implementation Timeline (Updated)

### Phase 1 (COMPLETED)
- ✅ MSDM schema integration in runtime_records.py
- ✅ Implementation of state_manager.py persistence
- ✅ Wiring of core context to MSDM/DSDM

### Phase 2 (COMPLETED)
- All core files (correlation, scheduler, token, event_bus) OSDM-aligned

### Phase 3-7 (PENDING)
- BPMN, CMMN, DMN, State Machine completion
- CEP/Multi-Agent integration
- API and validation

---

## Verification Commands

```bash
# Verify syntax
python3 -m py_compile engines/orchestration/core/context.py
python3 -m py_compile engines/orchestration/core/instance.py  
python3 -m py_compile engines/orchestration/runtime/timer_manager.py

# Verify imports (requires markdown module)
python3 -c "from engines.orchestration.runtime import OsDmTimerDefinition; print('OK')"
```