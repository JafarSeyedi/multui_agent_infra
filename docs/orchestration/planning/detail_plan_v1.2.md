# Detail Plan v1.2 — Post-Compliance Analysis

## Current State
- **BPMN 2.0 Compliance**: ~88%
- **OSDM Class Coverage**: ~85.4% (211/247 classes used)
- **CMMN Coverage**: ~80%
- **DMN Coverage**: ~85%
- **State Machine Coverage**: ~80%
- **CEP Coverage**: ~75%
- **Estimated Overall**: ~84%

## Goals
1. Reach **95%+ BPMN 2.0 compliance**
2. Reach **90%+ OSDM class coverage** (222+ classes)
3. Implement all **critical and high-priority** gaps from compliance analysis
4. Maintain layer separation (Orch/Comm/Bus/Doc/Storage/ML/UI)

---

## Phase A: BPMN Critical Gaps (Est: 36h)

### A1 — Parallel End Event Aggregation (4h)
- **File**: `bpmn/process_executor.py`
- **Task**: Modify `_check_sub_process_completion()` to track ALL end events, not just one
- **Status**: ✅ Already implemented in this session
- **Spec Reference**: §11.3, A.1

### A2 — Parallel Event-Based Gateway (4h)
- **File**: `bpmn/gateway_handler.py`
- **Task**: Add `parallel` variant where ALL outgoing branch events must occur, then join
- **Changes**:
  - Add `token_split_parallel_event_based()` method
  - Track event occurrence per branch
  - Join tokens after ALL events received
- **Spec Reference**: §10.5, A.3

### A3 — Timer Duration Scheduling (4h)
- **File**: `runtime/timer_manager.py`, `core/scheduler.py`
- **Task**: Connect `TimerEventDefinition.time_duration` to actual job scheduling
- **Changes**:
  - Calculate deadline from `time_duration` using `DueTimeDuration` OSDM class
  - Create scheduler job when timer event is reached during execution
  - Fire timer event when deadline is reached
- **Spec Reference**: §9.2.2

### A4 — OSDM Unused Classes Import (8h)

#### A4.1 — DueTimeDuration (1h)
- **File**: `runtime/timer_manager.py`
- **Task**: Import `DueTimeDuration` from OSDM, use in timer deadline calculation

#### A4.2 — DataStore (1h)
- **File**: `bpmn/data_object_handler.py`
- **Task**: Import `DataStore` from OSDM, add data store lifecycle handling

#### A4.3 — Property (1h)
- **File**: `runtime/variable_manager.py` or `bpmn/data_object_handler.py`
- **Task**: Import `Property` from OSDM, use for process properties

#### A4.4 — Global Task Subtypes (1h)
- **File**: `bpmn/global_task_handler.py`
- **Task**: Import `GlobalUserTask`, `GlobalScriptTask`, `GlobalManualTask`, `GlobalBusinessRuleTask`, dispatch type-specific behavior

#### A4.5 — ImplicitThrowEvent (1h)
- **File**: `bpmn/event_handler.py`
- **Task**: Import `ImplicitThrowEvent`, add handling (e.g., end of non-interrupting event sub-process)

#### A4.6 — InputOutputBinding (1h)
- **File**: `bpmn/data_object_handler.py`
- **Task**: Import `InputOutputBinding` from OSDM

#### A4.7 — Assignment (1h)
- **File**: `bpmn/data_object_handler.py`
- **Task**: Import `Assignment` from OSDM for data association expressions

#### A4.8 — CorrelationPropertyRetrievalExpression (1h)
- **File**: `core/correlation.py`
- **Task**: Import `CorrelationPropertyRetrievalExpression` from OSDM

### A5 — Choreography Executor (20h)

#### A5.1 — Cross-Instance Coordination (6h)
- **File**: `bpmn/choreography_executor.py`
- **Task**: Implement `ChoreographyExecutor.coordinate_participants()` method
- **Changes**:
  - Use `Participant` refs from `ChoreographyTask` to identify target instances
  - Route messages via `MessageFlow` between participants
  - Track initiating vs. receiving participant activation

#### A5.2 — Sub-Choreography Expansion (4h)
- **File**: `bpmn/choreography_executor.py`
- **Task**: Implement recursive expansion of `SubChoreography` flow elements
- **Changes**:
  - Map nested `flow_elements` into parent execution context
  - Handle participant inheritance from parent choreography

#### A5.3 — Call Choreography Resolution (4h)
- **File**: `bpmn/choreography_executor.py`
- **Task**: Implement `CallChoreography` → `Choreography` reference resolution

#### A5.4 — Global Choreography Task (4h)
- **File**: `bpmn/choreography_executor.py`
- **Task**: Execute `GlobalChoreographyTask` references across deployments

#### A5.5 — Participant Message Coordination (2h)
- **File**: `bpmn/choreography_executor.py`
- **Task**: Complete message routing between initiating/receiving participants

### A6 — Conversation Cross-Participant Routing (6h)
- **File**: `bpmn/conversation_executor.py`
- **Changes**:
  - Implement conversation-to-conversation message routing
  - Complete `ConversationLink` traversal during execution
  - Add participant set lifecycle management (add/remove participants at runtime)

---

## Phase B: CMMN & State Machine Gaps (Est: 16h)

### B1 — CMMN Sentry Enhancements (4h)
- **File**: `cmmn/sentry_evaluator.py`
- **Task**: Add `OnPart`, `IfPart`, `ExternalOnPart`, `TimerOnPart` support
- **Changes**: Ensure all `Sentry` types from OSDM are evaluated

### B2 — CMMN Plan Fragment Enhancements (4h)
- **File**: `cmmn/case_executor.py`
- **Task**: Complete plan fragment lifecycle (show/hide/discretionary)

### B3 — State Machine Pseudo-State Handling (4h)
- **File**: `state_machine/state_executor.py`
- **Task**: Add deep history resolution, junction/choice dynamic routing
- **OSDM Classes**: Ensure `PseudoStateKind` variants all handled

### B4 — State Machine Internal Transitions (2h)
- **File**: `state_machine/transition_handler.py`
- **Task**: Add internal transition handling (state-preserving transitions)

### B5 — State Machine Deferrable Events (2h)
- **File**: `state_machine/state_executor.py`
- **Task**: Add deferrable event queue for deferred trigger events

---

## Phase C: DMN Gaps (Est: 8h)

### C1 — FEEL Engine Enhancement (4h)
- **File**: `dmn/feel_engine.py`
- **Task**: Add missing FEEL functions (list, context, temporal, range)
- **Scope**: Basic FEEL exists; full DMN spec coverage requires extensive parser

### C2 — Decision Requirements Graph Execution (4h)
- **File**: `dmn/decision_requirements_graph.py`
- **Task**: Add topological execution order for chained decisions
- **Changes**:
  - Build dependency graph from `Decision.required_decisions`
  - Topological sort for execution order
  - Pass output variables between chained decisions

---

## Phase D: Error Handling Across Layers (Est: 8h)

### D1 — Bus Error → OSDM Error Events (3h)
- **File**: `runtime/error_handler.py`
- **Task**: Catch errors from `engines/buses` and generate OSDM `ErrorEvent`
- **Changes**:
  - Import `ErrorEventDefinition` from OSDM
  - Map bus error codes to `ErrorEventDefinition.error_ref`
  - Publish error event on event bus

### D2 — Communication Error → OSDM Error Events (3h)
- **File**: `runtime/error_handler.py`
- **Task**: Catch errors from `engines/communication` and generate OSDM `ErrorEvent`
- **Changes**:
  - Map communication timeouts/failures to error events
  - Import `Error` from OSDM for error code definitions

### D3 — Storage Error → OSDM Error Events (2h)
- **File**: `runtime/error_handler.py`
- **Task**: Catch errors from `engines/storage` and generate OSDM `ErrorEvent`
- **Changes**:
  - Map storage failures to error events
  - Ensure storage layer errors propagate to OSDM layer

---

## Phase E: OSDM Class Coverage Expansion (Est: 12h)

### E1 — Pool/Lane Execution Scoping (4h)
- **File**: `bpmn/pool_lane_executor.py`
- **Task**: Add pool-scoped variable access, lane-based task assignment
- **OSDM Classes**: `ParticipantMultiplicity`, `Lane`, `LaneSet`

### E2 — Resource Parameter Binding (2h)
- **File**: `bpmn/activity_handler.py`
- **Task**: Import `ResourceParameterBinding`, use for resource parameter mapping

### E3 — Participant Association (2h)
- **File**: `bpmn/collaboration_handler.py`
- **Task**: Import `ParticipantAssociation`, use for inner/outer participant mapping

### E4 — Participant Multiplicity (2h)
- **File**: `bpmn/collaboration_handler.py`
- **Task**: Import `ParticipantMultiplicity`, validate multi-instance participants

### E5 — Partner Entity / Partner Role (2h)
- **File**: `bpmn/collaboration_handler.py`
- **Task**: Import `PartnerEntity` / `PartnerRole` for BPMN collaboration extensions

---

## Phase F: Documentation & Final Reports (Est: 6h)

### F1 — Update OPEN_ISSUES_FINAL.md (2h)
- Mark completed issues
- Re-estimate remaining hours
- Add new issues found during compliance analysis

### F2 — Update Compliance Reports (2h)
- Regenerate `COMPLIANCE_FINAL_V4.md` with post-fix scores
- Update `COMPLIANCE_ENGINE_FEATURES_V3.md`
- Update `COMPLIANCE_BPMN20_SECTION_V2.md`

### F3 — Generate Final Comparison Table (2h)
- Create `COMPLIANCE_COMPETITOR_FINAL.md` with updated scores
- Include layer annotations for features implemented outside orchestration

---

## Phase G: Features Implemented in Other Layers (No Orch Code Changes)

These features are important for the competitor comparison table but are correctly implemented in other layers. No orchestration changes needed — document only:

| Feature | Layer | Status | Comparison Note |
|---|---|---|---|
| Kafka Connector | `[Bus]` + `[Comm]` | Interface defined | Needs external dep (`aiokafka`) |
| AMQP/RabbitMQ | `[Bus]` + `[Comm]` | Interface defined | Needs external dep |
| gRPC Communication | `[Comm]` | `engines/communication` | Out of scope for orch |
| WebSocket Push | `[Bus]` | Interface defined, needs async framework | — |
| GraphQL Subscriptions | `[Bus]` | Interface defined, needs async framework | — |
| Form Rendering | `[UI]` | `forms/form_engine.py` exists | Rendering in UI layer |
| AI/ML Integration | `[ML]+[Orch]` | `integration/llm_connector.py` exists | — |
| Rate Limiting | `[Comm]+[Orch]` | `runtime/rate_limiter.py` exists | — |
| Circuit Breaker | `[Comm]+[Orch]` | `runtime/circuit_breaker.py` exists | — |
| State Snapshots | `[Orch]+[Storage]` | `runtime/state_snapshot.py` exists | — |
| Multi-tenancy | `[Orch]+[Storage]` | `runtime/tenant.py` exists | — |
| XSD Validation | `[Doc]` | Out of scope — needs XSD parser | — |
| DI Rendering | `[Doc]` | Out of scope — presentation layer | — |

---

## Total Estimated Effort

| Phase | Hours | Priority |
|---|---|---|
| A — BPMN Critical Gaps | 36 | 🔴 Critical |
| B — CMMN & State Machine | 16 | 🟡 High |
| C — DMN Gaps | 8 | 🟡 High |
| D — Error Handling Cross-Layer | 8 | 🟡 High |
| E — OSDM Class Coverage | 12 | 🟢 Medium |
| F — Documentation & Reports | 6 | 🟢 Medium |
| G — Other Layers (doc only) | 0 | — |
| **Total** | **~86h** | — |

## Expected Post-Completion Scores

| Metric | Current | Target |
|---|---|---|
| BPMN 2.0 Overall | ~88% | ~95% |
| OSDM Class Coverage | 85.4% | ~92% |
| CMMN Coverage | ~80% | ~90% |
| DMN Coverage | ~85% | ~92% |
| State Machine Coverage | ~80% | ~90% |
| Overall Engine | ~84% | ~92% |

## Execution Order

1. **Phase A first** — All BPMN critical gaps and choreography (longest pole)
2. **Phase D parallel** — Cross-layer error handling (can be done independently)
3. **Phase B + C** — CMMN, State Machine, DMN gaps (after A unblocks)
4. **Phase E** — OSDM class coverage expansion
5. **Phase F** — Documentation regeneration
6. **Phase G** — No code changes, update comparison tables only
