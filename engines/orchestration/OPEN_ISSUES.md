# Open Issues Report

## Features Not Implemented — Reasons and Recommendations

This document catalogs all features identified in the compliance analysis
that have NOT been implemented, along with the specific reason for each
omission and recommendations for future implementation.

---

## 1. Critical Priority — Not Implemented

### 1.1 Process Instance Modification API Endpoints
- **Status**: Core logic exists in `runtime/migration.py` but API endpoints not wired
- **Reason**: The `ProcessInstanceMigrator` and `BatchOperationManager` classes are implemented and integrated into the engine constructor. However, the `api/instance_api.py` and `api/admin_api.py` files have not been updated to expose these capabilities through the API layer.
- **Recommendation**: Add `modify_instance()`, `suspend_instances()`, `resume_instances()`, `delete_instances()` methods to `InstanceAPI` and `AdminAPI`.
- **Effort**: ~4 hours

### 1.2 Async Continuations (Before/After)
- **Status**: Not implemented
- **Reason**: Async continuations require deep integration with the transaction manager and token lifecycle. The token system supports `TokenState.WAITING` but the async continuation pattern (where an activity can be marked "async before" to create a job, execute the activity, then "async after" to continue) requires:
  - Job creation on activity start
  - Token suspension while job executes
  - Token resumption on job completion
  - Transaction boundary management across the async boundary
- **Recommendation**: Extend `core/token.py` with async continuation markers and integrate with `core/scheduler.py` for job-based execution.
- **Effort**: ~8 hours

### 1.3 Kafka Connector
- **Status**: Not implemented
- **Reason**: The HTTP connector is implemented. A Kafka connector requires an external dependency (`aiokafka` or `confluent-kafka`) which may not be available in all deployment environments. The connector interface is designed to be pluggable.
- **Recommendation**: Create `integration/connectors/kafka_connector.py` with the same interface as `HttpConnector`. Make the Kafka dependency optional.
- **Effort**: ~4 hours

---

## 2. High Priority — Not Implemented

### 2.1 Full FEEL Expression Engine
- **Status**: Basic FEEL exists in `dmn/feel_engine.py` (~150 lines) but does not cover the full DMN 1.3 FEEL specification
- **Reason**: Full FEEL coverage requires:
  - Context/Path expressions
  - Range expressions
  - Filter expressions on lists
  - Temporal arithmetic (date/time/duration operations)
  - External function definitions
  - Boxed expressions (tables, lists, contexts)
  - Formal grammar parser (current implementation uses string matching)
- **Recommendation**: Integrate a full FEEL parser (e.g., `feel-parser` from Camunda) or implement a recursive descent parser for the complete FEEL grammar.
- **Effort**: ~40 hours

### 2.2 Decision Requirements Graph (DRG)
- **Status**: Not implemented
- **Reason**: The DMN engine supports individual decision tables but does not implement the Decision Requirements Graph (DRG) which chains multiple decisions together. This requires:
  - Parsing DRD from DMN XML
  - Building a dependency graph of decisions
  - Topological execution of decisions
  - Input/output mapping between decisions
- **Recommendation**: Extend `dmn/decision_executor.py` with DRG support.
- **Effort**: ~16 hours

### 2.3 Event Sub-Process Full Integration
- **Status**: Handler exists in `bpmn/bpmn_execution_semantics.py` but not integrated into `BPMNProcessExecutor`
- **Reason**: The `BpmnEventSubProcessHandler` class is implemented with registration, triggering, and interruption logic. However, the `BPMNProcessExecutor.execute()` method does not yet:
  - Register event sub-processes during process traversal
  - Check for triggered sub-processes at each step
  - Handle interrupting sub-process token termination
- **Recommendation**: Integrate `BpmnEventSubProcessHandler` into `BPMNProcessExecutor.execute()`.
- **Effort**: ~8 hours

### 2.4 Transaction Sub-Process Full Integration
- **Status**: Handler exists in `bpmn/bpmn_execution_semantics.py` but not integrated into `BPMNProcessExecutor`
- **Reason**: Same as event sub-process — the handler class exists but the executor does not use it during sub-process traversal.
- **Recommendation**: Integrate `BpmnTransactionHandler` into `BPMNProcessExecutor.execute()`.
- **Effort**: ~6 hours

### 2.5 Gateway Join Token Synchronization
- **Status**: Partial — `BpmnGatewaySemantics.can_converge()` exists but not used in executor
- **Reason**: The `BPMNProcessExecutor` currently takes only the first next node (`next_nodes[0]`) instead of properly synchronizing tokens at converging gateways.
- **Recommendation**: Refactor the executor loop to handle parallel token flow and gateway convergence.
- **Effort**: ~12 hours

---

## 3. Medium Priority — Not Implemented

### 3.1 BPMN Diagram Interchange (DI)
- **Status**: Not implemented
- **Reason**: BPMN DI is a presentation-layer concern (diagram layout, coordinates, colors). The runtime engine focuses on execution semantics. DI support would require:
  - Parsing BPMN DI XML elements
  - Storing diagram metadata
  - Providing diagram data for rendering
- **Recommendation**: Create a separate `diagram/` module for DI parsing and storage.
- **Effort**: ~20 hours

### 3.2 Cloud-Native Deployment (Kubernetes/Helm)
- **Status**: Not implemented
- **Reason**: Infrastructure concern, not runtime code. Kubernetes deployment requires:
  - Docker image configuration
  - Helm charts
  - Health check endpoints
  - Graceful shutdown handling
  - Cluster discovery configuration
- **Recommendation**: Create a separate `deployment/` directory with K8s manifests and Helm charts.
- **Effort**: ~16 hours

### 3.3 Process Landscape Visualization
- **Status**: Not implemented
- **Reason**: UI concern. Requires:
  - Process relationship graph
  - Visual rendering (SVG/Canvas)
  - Interactive navigation
- **Recommendation**: Implement as a separate web application consuming the engine's REST API.
- **Effort**: ~40 hours

### 3.4 WebSocket/GraphQL Notifications
- **Status**: Not implemented
- **Reason**: Transport layer concern. The engine's event bus publishes events but does not provide real-time push notifications.
- **Recommendation**: Add WebSocket and GraphQL subscription endpoints to the API layer.
- **Effort**: ~12 hours

### 3.5 gRPC Sidecar Plugins
- **Status**: Not implemented
- **Reason**: Infrastructure concern. Requires gRPC protocol definitions and server implementation.
- **Recommendation**: Define `.proto` files and generate Python stubs.
- **Effort**: ~16 hours

### 3.6 WASM Plugin Support
- **Status**: Not implemented
- **Reason**: Sandboxing concern. Requires WASM runtime integration (e.g., `wasmtime`).
- **Recommendation**: Create a WASM plugin loader using `wasmtime` Python bindings.
- **Effort**: ~20 hours

### 3.7 Mobile SDK (iOS/Android)
- **Status**: Not implemented
- **Reason**: Platform-specific concern. Requires native mobile development.
- **Recommendation**: Implement as separate mobile SDKs consuming the engine's REST API.
- **Effort**: ~80 hours

---

## 4. Low Priority — Not Implemented

### 4.1 Multiple/Parallel Multiple Events
- **Status**: Not implemented
- **Reason**: These are specialized event types that aggregate multiple event triggers. The basic event types are implemented.
- **Effort**: ~8 hours

### 4.2 Escalation Start/End Events
- **Status**: Not implemented
- **Reason**: Escalation events are primarily used in event sub-processes. The escalation throw/catch is handled.
- **Effort**: ~4 hours

### 4.3 Parallel Event-Based Gateway
- **Status**: Not implemented
- **Reason**: Variant of event-based gateway where ALL events must occur (not just the first).
- **Effort**: ~4 hours

### 4.4 Data Store (Persistent Storage)
- **Status**: Not implemented
- **Reason**: Data stores require persistent storage integration beyond the scope of the runtime engine.
- **Effort**: ~8 hours

### 4.5 Error Handling Escalation Chains
- **Status**: Not implemented
- **Reason**: Requires error code matching and escalation propagation across process boundaries.
- **Effort**: ~8 hours

### 4.6 Compensation Intermediate Throw Event
- **Status**: Not implemented
- **Reason**: Compensation throw events are used to trigger compensation from outside the compensation handler scope.
- **Effort**: ~4 hours

### 4.7 Conversation Execution Semantics
- **Status**: Not implemented
- **Reason**: Conversation execution requires participant coordination across process boundaries.
- **Effort**: ~12 hours

### 4.8 Sub-Choreography Expansion
- **Status**: Not implemented
- **Reason**: Sub-choreography requires expanding nested choreography definitions.
- **Effort**: ~8 hours

### 4.9 Call Choreography Resolution
- **Status**: Not implemented
- **Reason**: Call choreography requires resolving global choreography references.
- **Effort**: ~6 hours

### 4.10 Choreography Task Participant Coordination
- **Status**: Not implemented
- **Reason**: Requires message exchange coordination between participants.
- **Effort**: ~12 hours

---

## 5. Summary

| Priority | Not Implemented | Total Effort |
|---|---|---|
| Critical | 3 | ~16 hours |
| High | 5 | ~82 hours |
| Medium | 7 | ~136 hours |
| Low | 10 | ~64 hours |
| **Total** | **25** | **~298 hours** |

### Key Architectural Gaps Remaining
1. **Dict-based processing** — Handlers still work with `dict[str, Any]` instead of OSDM-typed objects. Full refactoring would require ~80 hours.
2. **Gateway token synchronization** — Parallel gateway join semantics not implemented in executor.
3. **Event/Transaction sub-process integration** — Handlers exist but not wired into executor.
4. **Full FEEL engine** — Requires complete parser implementation.
5. **API layer wiring** — New services not exposed through REST API.

### Recommended Next Steps
1. Wire event sub-process and transaction handlers into executor (14 hours)
2. Implement gateway join token synchronization (12 hours)
3. Add API endpoints for new services (8 hours)
4. Implement Kafka connector (4 hours)
5. Begin FEEL engine full implementation (40 hours)
