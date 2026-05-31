# Final Open Issues Report

## Features Not Fully Implemented — Detailed Analysis

---

## 1. CHoreography Execution Engine (20 hours)

### What's Missing
- `ChoreographyTask` execution with participant coordination
- Message exchange between initiating and receiving participants
- `SubChoreography` expansion (recursive nesting)
- `CallChoreography` resolution (global choreography references)
- `GlobalChoreographyTask` execution

### Why Not Implemented
The OSDM model classes (`ChoreographyTask`, `SubChoreography`, `CallChoreography`, `Choreography`) are defined and imported. The `ChoreographyHandler` exists but only handles step tracking via `ChoreographyStep` and `ChoreographyState`. The actual execution engine that:
1. Manages message exchanges between participants
2. Coordinates choreography task activation across process instances
3. Expands sub-choreographies recursively
4. Resolves global choreography references

...is not yet built. This requires a separate execution layer that coordinates across multiple process instances.

### Recommendation
Create `bpmn/choreography_executor.py` with:
- `ChoreographyExecutor` class that manages cross-instance coordination
- Message routing between participants via `MessageFlow`
- Sub-choreography expansion logic
- Integration with `ChoreographyHandler`

---

## 2. Conversation Execution Semantics (16 hours)

### What's Missing
- `Conversation` execution with participant set management
- `SubConversation` expansion
- `CallConversation` resolution
- `ConversationLink` traversal

### Why Not Implemented
The OSDM model classes exist (`Conversation`, `SubConversation`, `CallConversation`, `ConversationLink`). The `ConversationLink` is imported in `collaboration_handler.py`. However, no execution engine exists for:
1. Managing conversation participant sets
2. Expanding sub-conversations
3. Resolving call conversations
4. Traversing conversation links during execution

### Recommendation
Create `bpmn/conversation_executor.py` with conversation lifecycle management.

---

## 3. Pool/Lane Execution Semantics (12 hours)

### What's Missing
- Pool-based execution scoping
- Lane-based task assignment and filtering
- Hierarchical lane nesting

### Why Not Implemented
The OSDM model classes (`Pool`, `Lane`, `LaneSet`, `Participant`) are defined. The `collaboration_handler.py` manages participants and message flows. However:
1. The executor doesn't scope variable access by pool/lane
2. Task assignment doesn't consider lane membership
3. Lane hierarchy is not traversed during execution

### Recommendation
Extend `BPMNProcessExecutor` with pool/lane scoping and integrate with `HumanPerformer`/`PotentialOwner` assignment.

---

## 4. Decision Requirements Graph (16 hours)

### What's Missing
- DRG (Decision Requirements Diagram) parsing and execution
- Dependency graph between decisions
- Topological execution order
- Input/output mapping between chained decisions

### Why Not Implemented
The `Decision` OSDM class exists with `required_decisions` field. The `DecisionExecutor` evaluates individual decisions. However:
1. No DRG parser exists
2. No dependency graph builder
3. No topological sorter for execution order
4. No inter-decision variable mapping

### Recommendation
Extend `dmn/decision_executor.py` with DRG support.

---

## 5. Parallel Event-Based Gateway (4 hours)

### What's Missing
- Variant where ALL events on outgoing branches must occur (not just the first)

### Why Not Implemented
The standard `EventBasedGateway` is implemented with "first event wins" semantics. The parallel variant requires:
1. Token splitting across all outgoing branches
2. Waiting for ALL events to occur
3. Token joining after all events received

### Recommendation
Extend `BpmnGatewaySemantics._split_event_based()` with parallel variant support.

---

## 6. Dict-to-OSDM Refactoring (80 hours)

### What's Missing
All 14 handler files work with `dict[str, Any]` instead of typed OSDM objects.

### Why Not Implemented
This is a large-scale architectural refactoring that would touch every handler:
- `bpmn/activity_handler.py` — Should use `Activity` subclasses
- `bpmn/event_handler.py` — Should use `Event` subclasses
- `bpmn/gateway_handler.py` — Should use `Gateway` subclasses
- `bpmn/process_executor.py` — Uses `ProcessModel(dict)` instead of `TypedProcessModel`
- `bpmn/data_object_handler.py` — Should use `DataObject`/`DataAssociation`
- `bpmn/collaboration_handler.py` — Should use `Participant`/`MessageFlow`
- `bpmn/choreography_handler.py` — Should use `ChoreographyTask`
- `bpmn/transaction_handler.py` — Should use `TransactionSubProcess`
- `bpmn/adhoc_handler.py` — Should use `AdHocSubProcess`
- `bpmn/loop_handler.py` — Should use `LoopCharacteristics` subclasses
- `bpmn/global_task_handler.py` — Should use `GlobalTask`
- `cmmn/case_executor.py` — Should use `Stage`/`Milestone`/`CaseFileItem`
- `state_machine/state_executor.py` — Should use `State`/`Transition`
- `dmn/decision_executor.py` — Should use `Decision`/`BusinessKnowledgeModel`

The `TypedProcessModel` class was created to support this but the refactoring was not completed due to scope.

### Recommendation
This should be done as a dedicated sprint. Each handler needs to:
1. Accept OSDM-typed objects as input
2. Use typed field access instead of dict keys
3. Return OSDM-typed results

---

## 7. Sub-Choreography Expansion (8 hours)

### What's Missing
Recursive expansion of nested choreography definitions during execution.

### Why Not Implemented
The `SubChoreography` OSDM class exists with `flow_elements`. The expansion logic (recursively expanding nested choreography content into the parent execution context) is not implemented.

### Recommendation
Create `bpmn/choreography_executor.py` with expansion logic.

---

## 8. Call Choreography Resolution (6 hours)

### What's Missing
Resolving global choreography references at runtime.

### Why Not Implemented
The `CallChoreography` OSDM class exists with `called_choreography_ref`. The resolution logic (looking up the global choreography definition and expanding it) is not implemented.

### Recommendation
Add reference resolution to choreography executor.

---

## 9. Choreography Participant Coordination (4 hours)

### What's Missing
Message exchange coordination between choreography participants during execution.

### Why Not Implemented
The `ChoreographyTask` has `participant_refs` and `message_flows`. The coordination logic (activating the receiving participant when the initiating participant completes) is not implemented.

### Recommendation
Integrate with collaboration handler's message routing.

---

## 10. Kafka Connector (4 hours)

### What's Missing
Kafka-based connector for event-driven integrations.

### Why Not Implemented
Requires external dependency (`aiokafka` or `confluent-kafka`). The connector interface is designed to be pluggable.

### Recommendation
Create `integration/connectors/kafka_connector.py` with optional dependency.

---

## 11. WebSocket/GraphQL Hooks (12 hours)

### What's Missing
Real-time push notifications for process events.

### Why Not Implemented
The event bus publishes events but doesn't provide WebSocket or GraphQL subscription endpoints. This requires an async web framework (FastAPI/aiohttp) which is a separate service.

### Recommendation
Add WebSocket/GraphQL hooks to the event bus. Create subscription management.

---

## 12. XSD Structural Validation (20 hours)

### What's Missing
Full BPMN 2.0 XSD schema validation.

### Why Not Implemented
Would require BPMN 2.0 XSD schema file parsing. The current `osdm_validator.py` provides structural validation but not XSD-level validation (namespace, schema types, etc.).

### Recommendation
Use `xmlschema` Python library for XSD validation, or validate against OSDM model constraints.

---

## 13. DI Metadata Parsing (16 hours)

### What's Missing
BPMN Diagram Interchange (DI) metadata parsing for diagram layout.

### Why Not Implemented
DI parsing is a presentation-layer concern. The runtime engine focuses on execution semantics. DI metadata (coordinates, colors, labels, edge waypoints) would require:
1. Parsing BPMN DI XML elements
2. Storing diagram metadata
3. Providing diagram data for rendering

### Recommendation
Create `diagram/di_parser.py` for DI metadata extraction and storage.

---

## 14. Parallel End Event Aggregation (Missing)

### What's Missing
Aggregation of multiple end events in a single process instance.

### Why Not Implemented
The end events are handled individually. The aggregation logic (waiting for all end events to complete before considering the process complete) is not implemented.

### Recommendation
Track end event completion and only complete the instance when all paths have reached an end event.

---

## 15. Timer Due Duration (Missing)

### What's Missing
Integration with real-time clock service for timer due duration evaluation.

### Why Not Implemented
Timer durations are parsed and stored. The actual scheduling of timer jobs (evaluating `due_duration` against the current time) requires integration with the scheduler and a real-time clock.

### Recommendation
Extend the scheduler with timer job scheduling based on `due_duration`.

---

## Summary

| Category | Features | Hours | Blocked By |
|---|---|---|---|
| Choreography | 5 | 48 | Scope — needs dedicated executor |
| Conversation | 1 | 16 | Scope — needs dedicated executor |
| Pool/Lane | 1 | 12 | Architectural — scoping logic |
| DMN | 1 | 16 | Scope — DRG parsing |
| Gateway | 1 | 4 | Simple addition |
| Refactoring | 1 | 80 | Architectural — all handlers |
| Connectors | 1 | 4 | External dependency |
| Notifications | 1 | 12 | External framework |
| Validation | 1 | 20 | External schema |
| Diagram | 1 | 16 | Presentation layer |
| **Total** | **15** | **248** | — |

### Truly Impossible (External Blockers)

| Feature | Reason |
|---|---|
| Mobile SDK | Requires native iOS/Android development |
| K8s/Helm deployment | Infrastructure concern |
| WASM plugins | Requires `wasmtime` runtime |
| gRPC sidecar | Requires `grpcio` + proto definitions |
| Process Landscape Viz | Requires graph rendering library |
