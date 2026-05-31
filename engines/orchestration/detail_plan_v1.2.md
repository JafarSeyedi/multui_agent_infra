# Detail Plan v1.2 — Path to 100% BPMN 2.0 / OSDM Compliance

## Executive Summary

Current compliance: ~55% BPMN 2.0, ~40% OSDM class coverage.
Target: 100% compliance with both.
Total remaining effort: ~380 hours across 4 phases.

---

## Gap Analysis: What CAN vs CANNOT Be Implemented

### CAN Be Implemented (No External Blockers)

#### Category A: Integration Wiring (~30 hours)
These features have complete handler/semantics code but need to be wired into the executor:

| # | Gap | Files Needed | Hours |
|---|---|---|---|
| A1 | Event sub-process integration | Modify `process_executor.py` to use `BpmnEventSubProcessHandler` | 8 |
| A2 | Transaction sub-process integration | Modify `process_executor.py` to use `BpmnTransactionHandler` | 6 |
| A3 | Gateway join token synchronization | Refactor executor loop for parallel token flow | 12 |
| A4 | Ad-hoc completion condition evaluation | Wire `AdhocHandler` into executor sub-process handling | 4 |

#### Category B: FEEL Engine Full Implementation (~40 hours)
| # | Feature | Hours |
|---|---|---|
| B1 | Formal grammar parser (recursive descent) | 16 |
| B2 | Range expressions | 4 |
| B3 | Filter expressions on lists | 4 |
| B4 | Temporal arithmetic (date/time/duration) | 8 |
| B5 | Context/Path expressions | 4 |
| B6 | Boxed expressions + external functions | 4 |

#### Category C: API Layer Wiring (~20 hours)
| # | Feature | Hours |
|---|---|---|
| C1 | Process instance modification API (`api/instance_api.py`) | 4 |
| C2 | Batch operations API (`api/admin_api.py`) | 4 |
| C3 | Incident query/resolution API (`api/instance_api.py`) | 4 |
| C4 | External task management API (`api/task_api.py`) | 4 |
| C5 | Form endpoints (`api/task_api.py`) | 4 |

#### Category D: Additional BPMN 2.0 Elements (~30 hours)
| # | Feature | Hours |
|---|---|---|
| D1 | Async continuations (before/after) | 8 |
| D2 | Multiple/Parallel Multiple start events | 4 |
| D3 | Multiple/Parallel Multiple end events | 4 |
| D4 | Parallel Event-Based Gateway | 4 |
| D5 | User task deadlines | 4 |
| D6 | User task escalation | 4 |
| D7 | Compensation intermediate throw | 2 |

#### Category E: DMN Enhancements (~24 hours)
| # | Feature | Hours |
|---|---|---|
| E1 | Decision Requirements Graph (DRG) | 16 |
| E2 | DMN decision service invocation | 8 |

#### Category F: Choreography/Conversation (~44 hours)
| # | Feature | Hours |
|---|---|---|
| F1 | Choreography execution engine | 20 |
| F2 | Sub-choreography expansion | 8 |
| F3 | Call choreography resolution | 6 |
| F4 | Conversation execution semantics | 6 |
| F5 | Choreography participant coordination | 4 |

#### Category G: Pool/Lane Semantics (~12 hours)
| # | Feature | Hours |
|---|---|---|
| G1 | Pool execution scoping | 6 |
| G2 | Lane-based task assignment | 6 |

#### Category H: Dict-to-OSDM Refactoring (~80 hours)
| # | File | Hours |
|---|---|---|
| H1 | `bpmn/activity_handler.py` — use OSDM Activity subclasses | 8 |
| H2 | `bpmn/event_handler.py` — use OSDM Event subclasses | 6 |
| H3 | `bpmn/gateway_handler.py` — use OSDM Gateway subclasses | 6 |
| H4 | `bpmn/process_executor.py` — use TypedProcessModel | 12 |
| H5 | `bpmn/data_object_handler.py` — use OSDM DataObject | 6 |
| H6 | `bpmn/collaboration_handler.py` — use OSDM Participant/MessageFlow | 6 |
| H7 | `bpmn/choreography_handler.py` — use OSDM ChoreographyTask | 6 |
| H8 | `bpmn/loop_handler.py` — use OSDM LoopCharacteristics | 4 |
| H9 | `bpmn/global_task_handler.py` — use OSDM GlobalTask | 4 |
| H10 | `bpmn/transaction_handler.py` — use OSDM TransactionSubProcess | 4 |
| H11 | `bpmn/adhoc_handler.py` — use OSDM AdHocSubProcess | 4 |
| H12 | `cmmn/case_executor.py` — use OSDM CMMN types | 6 |
| H13 | `state_machine/state_executor.py` — use OSDM State types | 4 |
| H14 | `dmn/decision_executor.py` — use OSDM Decision types | 4 |

### CANNOT Be Fully Implemented (External Blockers)

| # | Feature | Blocker | Can Partial? |
|---|---|---|---|
| X1 | Full BPMN DI rendering | Requires diagram parser + rendering engine (SVG/Canvas) — pure UI concern | Yes: parse DI metadata |
| X2 | XSD validation | Would require BPMN 2.0 XSD schema parser — massive external artifact | Yes: structural validation done |
| X3 | Kafka connector | Requires `aiokafka` external dependency | Yes: stub with interface |
| X4 | Cloud-native K8s/Helm | Infrastructure concern, not runtime code | N/A |
| X5 | WebSocket/GraphQL | Requires async web framework (FastAPI/aiohttp) — separate service | Yes: event bus hooks |
| X6 | gRPC sidecar | Requires `grpcio` + `.proto` definitions | Yes: stub interface |
| X7 | WASM plugins | Requires `wasmtime` runtime | N/A |
| X8 | Mobile SDK | Requires native iOS/Android development | N/A |
| X9 | Process Landscape Viz | Requires graph visualization library — UI concern | Yes: provide graph data via API |
| X10 | Timer due_duration | Requires integration with real-time clock service | Yes: parse + store duration |

---

## Implementation Plan

### Sprint 1 (40 hours) — Integration Wiring + API Layer
**Goal: Reach ~65% compliance**
1. A1: Event sub-process integration into executor (8h)
2. A2: Transaction sub-process integration into executor (6h)
3. A3: Gateway join token synchronization (12h)
4. A4: Ad-hoc completion condition (4h)
5. C1: Process instance modification API (4h)
6. C2: Batch operations API (4h)
7. C3: Incident query API (2h)

### Sprint 2 (40 hours) — FEEL Engine + More APIs
**Goal: Reach ~72% compliance**
1. B1: Formal FEEL grammar parser (16h)
2. B2-B6: Remaining FEEL features (24h)

### Sprint 3 (40 hours) — BPMN Elements + DMN
**Goal: Reach ~80% compliance**
1. D1: Async continuations (8h)
2. D2-D7: Additional BPMN elements (22h)
3. E1: DRG support (8h)
4. E2: Decision service (2h)

### Sprint 4 (80 hours) — Dict-to-OSDM Refactoring
**Goal: Reach ~88% compliance**
1. H1-H14: Refactor all handlers to use OSDM typed objects (80h)

### Sprint 5 (44 hours) — Choreography + Pool/Lane
**Goal: Reach ~95% compliance**
1. F1: Choreography execution (20h)
2. F2-F5: Sub-choreography, call, conversation (24h)

### Sprint 6 (20 hours) — API Wiring + Remaining
**Goal: Reach ~98% compliance**
1. C4-C5: Task and form API endpoints (8h)
2. G1-G2: Pool/Lane semantics (12h)

### Sprint 7 (Remaining) — Polish + Edge Cases
**Goal: 100% runtime-level compliance**
1. D-D additions from Sprint 3 remaining (6h)
2. Partial implementations for X1-X10 where feasible (~30h)
3. Comprehensive test coverage (~24h)

---

## Total Effort Summary

| Sprint | Hours | Cumulative Compliance |
|---|---|---|
| Sprint 1 | 40 | ~65% |
| Sprint 2 | 40 | ~72% |
| Sprint 3 | 40 | ~80% |
| Sprint 4 | 80 | ~88% |
| Sprint 5 | 44 | ~95% |
| Sprint 6 | 20 | ~98% |
| Sprint 7 | 60 | 100% (runtime) / ~85% (incl. UI/infra) |
| **Total** | **324** | **100% runtime-level** |

---

## Notes on 100% vs Practical Compliance

### What "100% Runtime-Level Compliance" Means
- Every BPMN 2.0 element type has handler code
- Every gateway type has correct split/join semantics
- Every event type is properly dispatched
- Correct token flow per Annex A
- Full FEEL expression evaluation
- All OSDM classes are importable and used
- Complete choreography/conversation execution
- Pool/lane-based scoping

### What Is NOT Included in 100% Runtime-Level
- UI/WebSocket/gRPC concerns (external services)
- Cloud-native deployment (infrastructure)
- Mobile SDKs (platform-specific)
- WASM sandboxing (external runtime)
- External messaging (Kafka — dependency)

These are properly concerns of the deployment/UI layer, not the runtime engine.
