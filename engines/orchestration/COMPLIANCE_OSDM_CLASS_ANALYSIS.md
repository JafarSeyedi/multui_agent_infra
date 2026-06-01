# OSDM Class-by-Class Compliance Analysis v1.0

## Summary

| Metric | Value |
|---|---|
| Total OSDM classes/enums | 247 |
| Used in orchestration engine | 211 (85.4%) |
| Not used in orchestration engine | 36 (14.6%) |
| Handler-specific wrapper classes | 18 (these wrap OSDM types for internal handler use) |

---

## Category 1: BPMN Flow Elements (OSDM → Orchestration Usage)

### 1.1 FlowNode Hierarchy

| OSDM Class | Used In | File | Usage Pattern |
|---|---|---|---|
| `FlowElement` | TYPE_CHECKING | `process_model.py` | Base class reference |
| `FlowNode` | ✅ Direct import | `bpmn/process_model.py`, `gateway_handler.py`, `bpmn_execution_semantics.py` | Gateway split/converge, flow node resolution |
| `Activity` | ✅ Direct import | `bpmn/activity_handler.py`, `bpmn/process_executor.py`, `bpmn/loop_handler.py` | Activity execution, loop configuration |
| `Task` | ✅ Direct import | `bpmn/activity_handler.py`, `cmmn/task_handler.py` | Task type dispatch |
| `SubProcess` | ✅ Direct import | `bpmn/activity_handler.py`, `bpmn/process_executor.py`, `bpmn/adhoc_handler.py` | Sub-process execution, completion checking |
| `TransactionSubProcess` | ✅ Direct import | `bpmn/transaction_handler.py` | Transaction boundary, compensation |
| `AdHocSubProcess` | ✅ Direct import | `bpmn/adhoc_handler.py` | Ad-hoc ordering, completion conditions |
| `CallActivity` | ✅ Direct import | `bpmn/activity_handler.py` | Called element resolution, parameter mapping |

### 1.2 Task Types

| OSDM Class | Used In | File | Usage Pattern |
|---|---|---|---|
| `ServiceTask` | ✅ Direct import | `bpmn/activity_handler.py` | Service task execution, retry |
| `SendTask` | ✅ Direct import | `bpmn/activity_handler.py` | Message sending |
| `ReceiveTask` | ✅ Direct import | `bpmn/activity_handler.py` | Message receiving, create-instance |
| `UserTask` | ✅ Direct import | `bpmn/activity_handler.py`, `cmmn/task_handler.py` | User task lifecycle, forms |
| `ManualTask` | ✅ Direct import | `bpmn/activity_handler.py` | Manual task (no system interaction) |
| `ScriptTask` | ✅ Direct import | `bpmn/activity_handler.py` | Script execution |
| `BusinessRuleTask` | ✅ Direct import | `bpmn/activity_handler.py` | DMN decision execution |
| `GlobalTask` | ✅ Direct import | `bpmn/global_task_handler.py` | Global task registry |
| `GlobalUserTask` | ❌ Not used | — | Only `GlobalTask` base is referenced |
| `GlobalScriptTask` | ❌ Not used | — | Only `GlobalTask` base is referenced |
| `GlobalManualTask` | ❌ Not used | — | Only `GlobalTask` base is referenced |
| `GlobalBusinessRuleTask` | ❌ Not used | — | Only `GlobalTask` base is referenced |

### 1.3 Gateway Types

| OSDM Class | Used In | File | Usage Pattern |
|---|---|---|---|
| `Gateway` | ✅ Direct import | `bpmn/gateway_handler.py`, `bpmn/process_executor.py` | Gateway type dispatch |
| `ExclusiveGateway` | ✅ Direct import | `bpmn/gateway_handler.py` | XOR condition evaluation |
| `InclusiveGateway` | ✅ Direct import | `bpmn/gateway_handler.py` | OR token splitting |
| `ParallelGateway` | ✅ Direct import | `bpmn/gateway_handler.py` | AND fork/join |
| `EventBasedGateway` | ✅ Direct import | `bpmn/gateway_handler.py` | Event-based branching |
| `ComplexGateway` | ✅ Direct import | `bpmn/gateway_handler.py` | Complex conditions |

### 1.4 Gateway Enums

| OSDM Enum | Used In | File | Usage Pattern |
|---|---|---|---|
| `GatewayType` | ✅ Direct import | `bpmn/gateway_handler.py` | Type checking |
| `GatewayDirection` | ✅ Direct import | `bpmn/gateway_handler.py` | Diverging/converging detection |
| `EventBasedGatewayType` | ✅ Direct import | `bpmn/gateway_handler.py` | Parallel vs. exclusive variant |

---

## Category 2: BPMN Events

### 2.1 Event Hierarchy

| OSDM Class | Used In | File | Usage Pattern |
|---|---|---|---|
| `Event` | ✅ Direct import | `bpmn/event_handler.py`, `bpmn/process_executor.py` | Base event handling |
| `CatchEvent` | ✅ Direct import | `bpmn/event_handler.py` | Catch event dispatch |
| `ThrowEvent` | ✅ Direct import | `bpmn/event_handler.py` | Throw event dispatch |
| `StartEvent` | ✅ Direct import | `bpmn/event_handler.py`, `bpmn/process_executor.py` | Process start, message/signal start |
| `EndEvent` | ✅ Direct import | `bpmn/event_handler.py`, `bpmn/process_executor.py` | Process end, termination |
| `IntermediateCatchEvent` | ✅ Direct import | `bpmn/event_handler.py` | Timer, message, signal catch |
| `IntermediateThrowEvent` | ✅ Direct import | `bpmn/event_handler.py` | Timer, message, signal throw |
| `BoundaryEvent` | ✅ Direct import | `bpmn/event_handler.py`, `bpmn/activity_handler.py` | Attached events, interrupting/non-interrupting |
| `ImplicitThrowEvent` | ❌ Not used | — | No explicit handling |

### 2.2 Event Definitions

| OSDM Class | Used In | File | Usage Pattern |
|---|---|---|---|
| `EventDefinition` | ❌ Not used | — | Base class not directly referenced |
| `MessageEventDefinition` | ✅ Direct import | `bpmn/event_handler.py` | Message correlation, payload |
| `TimerEventDefinition` | ✅ Direct import | `bpmn/event_handler.py`, `runtime/timer_manager.py` | Timer scheduling |
| `SignalEventDefinition` | ✅ Direct import | `bpmn/event_handler.py` | Signal broadcasting |
| `ErrorEventDefinition` | ✅ Direct import | `bpmn/event_handler.py` | Error propagation |
| `EscalationEventDefinition` | ✅ Direct import | `bpmn/event_handler.py` | Escalation handling |
| `CompensateEventDefinition` | ✅ Direct import | `bpmn/event_handler.py` | Compensation triggering |
| `ConditionalEventDefinition` | ✅ Direct import | `bpmn/event_handler.py` | Condition evaluation |
| `LinkEventDefinition` | ✅ Direct import | `bpmn/event_handler.py` | Link source/target |
| `CancelEventDefinition` | ✅ Direct import | `bpmn/event_handler.py` | Transaction cancellation |
| `TerminateEventDefinition` | ✅ Direct import | `bpmn/event_handler.py` | Full process termination |

### 2.3 Event Enums

| OSDM Enum | Used In | File | Usage Pattern |
|---|---|---|---|
| `EventType` | ✅ Direct import | `bpmn/event_handler.py` | Event type dispatch |
| `EventDefinitionType` | ✅ Direct import | `bpmn/event_handler.py` | Definition type resolution |
| `TimerEventType` | ✅ Direct import | `bpmn/event_handler.py` | Timer type checking |
| `DueTimeDuration` | ❌ Not used | — | No explicit duration class usage |

---

## Category 3: BPMN Data

### 3.1 Data Objects

| OSDM Class | Used In | File | Usage Pattern |
|---|---|---|---|
| `DataFlowElement` | ❌ Not used | — | Base class not referenced |
| `DataObject` | ✅ Direct import | `bpmn/data_object_handler.py` | Data object lifecycle |
| `DataObjectReference` | ✅ Direct import | `bpmn/data_object_handler.py` | Data state tracking |
| `DataStore` | ❌ Not used | — | No data store handling |
| `DataStoreReference` | ✅ Direct import | `bpmn/data_object_handler.py` | Data store access |
| `DataState` | ✅ Direct import | `bpmn/data_object_handler.py` | State transition |
| `DataElement` | ❌ Not used | — | Base class not referenced |
| `Property` | ❌ Not used | — | No property handling |

### 3.2 Data Associations

| OSDM Class | Used In | File | Usage Pattern |
|---|---|---|---|
| `DataAssociation` | ✅ Direct import | `bpmn/data_object_handler.py` | Data binding |
| `DataInputAssociation` | ✅ Direct import | `bpmn/data_object_handler.py` | Input mapping |
| `DataOutputAssociation` | ✅ Direct import | `bpmn/data_object_handler.py` | Output mapping |
| `DataInput` | ✅ Direct import | `bpmn/data_object_handler.py` | IO specification |
| `DataOutput` | ✅ Direct import | `bpmn/data_object_handler.py` | IO specification |
| `DataInputRef` | ❌ Not used | — | No reference resolution |
| `DataOutputRef` | ❌ Not used | — | No reference resolution |
| `InputSet` | ✅ Direct import | `bpmn/data_object_handler.py` | Req'd/available inputs |
| `OutputSet` | ✅ Direct import | `bpmn/data_object_handler.py` | Available/produced outputs |
| `InputOutputSpecification` | ✅ Direct import | `bpmn/activity_handler.py` | Activity IO |
| `InputOutputBinding` | ❌ Not used | — | No binding resolution |
| `Assignment` | ❌ Not used | — | No expression assignment |

### 3.3 Sequence Flow

| OSDM Class | Used In | File | Usage Pattern |
|---|---|---|---|
| `SequenceFlow` | ✅ Direct import | `bpmn/sequence_flow.py`, `bpmn/gateway_handler.py`, `bpmn/process_executor.py` | Condition evaluation, traversal |
| `FormalExpression` | ✅ Direct import | `bpmn/data_object_handler.py`, `bpmn/sequence_flow.py` | Expression evaluation |
| `BpmnExpression` | ❌ Not used | — | Base class not referenced |

---

## Category 4: BPMN Collaboration

### 4.1 Participants and Pools

| OSDM Class | Used In | File | Usage Pattern |
|---|---|---|---|
| `Participant` | ✅ Direct import | `bpmn/collaboration_handler.py`, `bpmn/choreography_handler.py` | Participant resolution |
| `ParticipantMultiplicity` | ❌ Not used | — | No multiplicity handling |
| `ParticipantAssociation` | ❌ Not used | — | No participant association |
| `PartnerEntity` | ❌ Not used | — | Not referenced |
| `PartnerRole` | ❌ Not used | — | Not referenced |

### 4.2 Lanes

| OSDM Class | Used In | File | Usage Pattern |
|---|---|---|---|
| `Lane` | ✅ Direct import | `bpmn/collaboration_handler.py`, `bpmn/pool_lane_executor.py` | Lane-based scoping |
| `LaneSet` | ✅ Direct import | `bpmn/collaboration_handler.py` | Lane hierarchy |

### 4.3 Message Flows

| OSDM Class | Used In | File | Usage Pattern |
|---|---|---|---|
| `MessageFlow` | ✅ Direct import | `bpmn/collaboration_handler.py`, `bpmn/choreography_handler.py` | Cross-pool messaging |
| `MessageFlowAssociation` | ❌ Not used | — | Not referenced |

### 4.4 Conversation

| OSDM Class | Used In | File | Usage Pattern |
|---|---|---|---|
| `InteractionNode` | ❌ Not used | — | Base class not referenced |
| `ConversationNode` | ✅ Direct import | `bpmn/conversation_executor.py` | Conversation node base |
| `Conversation` | ✅ Direct import | `bpmn/conversation_executor.py` | Conversation lifecycle |
| `CallConversation` | ✅ Direct import | `bpmn/conversation_executor.py` | Global conversation reference |
| `GlobalConversation` | ✅ Direct import | `bpmn/conversation_executor.py` | Global conversation |
| `SubConversation` | ✅ Direct import | `bpmn/conversation_executor.py` | Nested conversation |
| `ConversationAssociation` | ✅ Direct import | `bpmn/conversation_executor.py` | Conversation-to-node binding |
| `ConversationLink` | ✅ Direct import | `bpmn/collaboration_handler.py`, `bpmn/conversation_executor.py` | Inter-conversation links |

### 4.5 Choreography

| OSDM Class | Used In | File | Usage Pattern |
|---|---|---|---|
| `ChoreographyActivity` | ❌ Not used | — | Base class not referenced |
| `ChoreographyTask` | ✅ Direct import | `bpmn/choreography_handler.py`, `bpmn/choreography_executor.py` | Multi-participant task |
| `CallChoreography` | ✅ Direct import | `bpmn/choreography_executor.py` | Global choreography call |
| `SubChoreography` | ✅ Direct import | `bpmn/choreography_executor.py` | Nested choreography |
| `Choreography` | ✅ Direct import | `bpmn/choreography_executor.py` | Choreography lifecycle |
| `GlobalChoreographyTask` | ✅ Direct import | `bpmn/choreography_executor.py` | Cross-definition task |

### 4.6 Collaboration Root

| OSDM Class | Used In | File | Usage Pattern |
|---|---|---|---|
| `Collaboration` | ✅ Direct import | `bpmn/collaboration_handler.py`, `bpmn/engine.py` | Collaboration-level handling |

### 4.7 Artifacts

| OSDM Class | Used In | File | Usage Pattern |
|---|---|---|---|
| `Artifact` | ✅ Direct import | `bpmn/collaboration_handler.py` | Artifact base |
| `Association` | ✅ Direct import | `bpmn/collaboration_handler.py` | Artifact-to-element association |
| `Group` | ✅ Direct import | `bpmn/collaboration_handler.py` | Visual grouping |
| `TextAnnotation` | ✅ Direct import | `bpmn/collaboration_handler.py` | Text annotations |

---

## Category 5: BPMN Loop and Multi-Instance

### 5.1 Loop Characteristics

| OSDM Class | Used In | File | Usage Pattern |
|---|---|---|---|
| `LoopCharacteristics` | ✅ Direct import | `bpmn/loop_handler.py` | Loop base |
| `StandardLoopCharacteristics` | ✅ Direct import | `bpmn/loop_handler.py` | While/until loops |
| `MultiInstanceLoopCharacteristics` | ✅ Direct import | `bpmn/loop_handler.py` | Parallel/sequential MI |
| `ComplexBehaviorDefinition` | ✅ Direct import | `bpmn/loop_handler.py` | Complex MI behavior |

### 5.2 Enums

| OSDM Enum | Used In | File | Usage Pattern |
|---|---|---|---|
| `LoopType` | ✅ Direct import | `bpmn/loop_handler.py` | Standard vs. MI |
| `MultiInstanceBehavior` | ✅ Direct import | `bpmn/loop_handler.py` | None/one/all/first |
| `ChoreographyLoopType` | ✅ Direct import | `bpmn/choreography_handler.py` | Choreography loop variant |
| `AdHocOrdering` | ✅ Direct import | `bpmn/adhoc_handler.py` | Parallel/sequential ad-hoc |

---

## Category 6: BPMN Resources and Rendering

### 6.1 Resources

| OSDM Class | Used In | File | Usage Pattern |
|---|---|---|---|
| `Resource` | ✅ Direct import | `bpmn/activity_handler.py` | Resource base |
| `ResourceParameter` | ✅ Direct import | `bpmn/activity_handler.py` | Resource parameters |
| `ResourceParameterBinding` | ❌ Not used | — | Not referenced |
| `ResourceAssignmentExpression` | ❌ Not used | — | Not referenced |
| `ResourceRole` | ✅ Direct import | `bpmn/activity_handler.py` | Role base |
| `HumanPerformer` | ✅ Direct import | `bpmn/activity_handler.py` | Human resource |
| `Performer` | ✅ Direct import | `bpmn/activity_handler.py` | Performer base |
| `PotentialOwner` | ✅ Direct import | `bpmn/activity_handler.py` | Task assignment |

### 6.2 Rendering

| OSDM Class | Used In | File | Usage Pattern |
|---|---|---|---|
| `Rendering` | ✅ Direct import | `bpmn/activity_handler.py` | Rendering base |
| `RenderingForm` | ✅ Direct import | `bpmn/activity_handler.py` | Form rendering |

### 6.3 Enums

| OSDM Enum | Used In | File | Usage Pattern |
|---|---|---|---|
| `ResourceParameterType` | ✅ Direct import | `bpmn/activity_handler.py` | Parameter type |
| `ResourceRoleType` | ✅ Direct import | `bpmn/activity_handler.py` | Role type |
| `PotentialOwnerType` | ✅ Direct import | `bpmn/activity_handler.py` | Owner type |

---

## Category 7: BPMN Process

### 7.1 Process Classes

| OSDM Class | Used In | File | Usage Pattern |
|---|---|---|---|
| `Process` | ✅ Direct import | `bpmn/engine.py`, `bpmn/process_executor.py`, `bpmn/process_model.py`, `core/instance.py` | Process definition, execution |
| `ItemDefinition` | ✅ Direct import | `bpmn/data_object_handler.py`, `bpmn/engine.py` | Item kind, structure ref |
| `Auditing` | ✅ Direct import | `bpmn/collaboration_handler.py` | Audit trail config |
| `Monitoring` | ✅ Direct import | `bpmn/collaboration_handler.py` | Monitoring config |
| `Script` | ✅ Direct import | `bpmn/activity_handler.py` | Script content |

### 7.2 Enums

| OSDM Enum | Used In | File | Usage Pattern |
|---|---|---|---|
| `ItemKind` | ✅ Direct import | `bpmn/data_object_handler.py` | Physical/information |
| `ProcessType` | ✅ Direct import | `bpmn/engine.py` | Public/private/None |
| `ActivityType` | ✅ Direct import | `bpmn/activity_handler.py` | Activity type |
| `TaskType` | ✅ Direct import | `bpmn/activity_handler.py` | Task type dispatch |
| `SubProcessType` | ✅ Direct import | `bpmn/activity_handler.py` | Sub-process type |
| `CallActivityType` | ✅ Direct import | `bpmn/activity_handler.py` | Global vs. process call |
| `TransactionMethod` | ✅ Direct import | `bpmn/transaction_handler.py` | Cancel/compensate/none |
| `ScriptLanguage` | ✅ Direct import | `bpmn/activity_handler.py` | Script language |
| `AssociationDirection` | ✅ Direct import | `bpmn/collaboration_handler.py` | Association direction |
| `TimerCalculationType` | ✅ Direct import | `bpmn/event_handler.py` | Timer calculation |
| `TimeReference` | ✅ Direct import | `bpmn/event_handler.py` | Time reference |
| `DurationResolution` | ✅ Direct import | `bpmn/event_handler.py` | Duration resolution |

### 7.3 Infrastructure

| OSDM Class | Used In | File | Usage Pattern |
|---|---|---|---|
| `Message` | ✅ Direct import | `bpmn/collaboration_handler.py` | Message definition |
| `Signal` | ✅ Direct import | `bpmn/event_handler.py` | Signal definition |
| `Error` | ✅ Direct import | `bpmn/event_handler.py` | Error definition |
| `Escalation` | ✅ Direct import | `bpmn/event_handler.py` | Escalation definition |
| `Interface` | ✅ Direct import | `bpmn/collaboration_handler.py` | Interface definition |
| `Operation` | ✅ Direct import | `bpmn/collaboration_handler.py` | Operation definition |
| `EndPoint` | ✅ Direct import | `bpmn/collaboration_handler.py` | Endpoint definition |

### 7.4 Correlation

| OSDM Class | Used In | File | Usage Pattern |
|---|---|---|---|
| `CorrelationKey` | ✅ Direct import | `bpmn/collaboration_handler.py`, `core/correlation.py` | Correlation key |
| `CorrelationProperty` | ✅ Direct import | `bpmn/collaboration_handler.py`, `core/correlation.py` | Correlation property |
| `CorrelationPropertyRetrievalExpression` | ❌ Not used | — | Not referenced |
| `CorrelationSubscription` | ✅ Direct import | `core/correlation.py` | Subscription |
| `CorrelationPropertyBinding` | ✅ Direct import | `core/correlation.py` | Property binding |
| `Category` | ✅ Direct import | `bpmn/collaboration_handler.py` | Category |
| `CategoryValue` | ✅ Direct import | `bpmn/collaboration_handler.py` | Category value |

### 7.5 Execution Enums

| OSDM Enum | Used In | File | Usage Pattern |
|---|---|---|---|
| `WorkflowStateType` | ✅ Direct import | `core/token.py`, `runtime/runtime_records.py` | Instance state |
| `ErrorHandlingOperator` | ✅ Direct import | `runtime/error_handler.py` | Error operator |
| `RetryConfig` | ✅ Direct import | `runtime/circuit_breaker.py` | Retry configuration |
| `TimeoutConfig` | ✅ Direct import | `runtime/circuit_breaker.py` | Timeout configuration |
| `ErrorHandlingConfig` | ✅ Direct import | `runtime/error_handler.py` | Error handling config |
| `RetryBackoffRate` | ❌ Not used | — | Not referenced |

---

## Category 8: CMMN

### 8.1 CMMN Elements

| OSDM Class | Used In | File | Usage Pattern |
|---|---|---|---|
| `CMMNDefinition` | ✅ Direct import | `cmmn/engine.py` | CMMN document root |
| `PlanItem` | ✅ Direct import | `cmmn/case_executor.py` | Plan item base |
| `DiscretionaryItem` | ✅ Direct import | `cmmn/discretionary_handler.py` | Discretionary item |
| `CaseFileItem` | ✅ Direct import | `cmmn/case_file_manager.py` | Case file item |
| `CaseTask` | ✅ Direct import | `cmmn/task_handler.py` | Case task |
| `ProcessTask` | ✅ Direct import | `cmmn/task_handler.py` | Process task |
| `HumanTask` | ✅ Direct import | `cmmn/task_handler.py` | Human task |
| `Stage` | ✅ Direct import | `cmmn/stage_handler.py`, `cmmn/case_executor.py` | Stage execution |
| `Milestone` | ✅ Direct import | `cmmn/milestone_handler.py` | Milestone tracking |
| `EventListener` | ✅ Direct import | `cmmn/case_executor.py` | Event listening |
| `Sentry` | ✅ Direct import | `cmmn/sentry_evaluator.py` | Entry/exit criteria |
| `EntryCriterion` | ✅ Direct import | `cmmn/sentry_evaluator.py` | Entry criterion |
| `ExitCriterion` | ✅ Direct import | `cmmn/sentry_evaluator.py` | Exit criterion |
| `ApplicabilityRule` | ✅ Direct import | `cmmn/sentry_evaluator.py` | Rule evaluation |
| `DecisionService` | ✅ Direct import | `cmmn/task_handler.py` | Decision service |
| `InformationRequirement` | ✅ Direct import | `cmmn/task_handler.py` | Information requirement |
| `KnowledgeRequirement` | ✅ Direct import | `cmmn/task_handler.py` | Knowledge requirement |
| `AuthorityRequirement` | ✅ Direct import | `cmmn/task_handler.py` | Authority requirement |
| `SentryExpression` | ✅ Direct import | `cmmn/sentry_evaluator.py` | Sentry expression |

### 8.2 CMMN Enums

| OSDM Enum | Used In | File | Usage Pattern |
|---|---|---|---|
| `CaseFileMultiplicity` | ✅ Direct import | `cmmn/case_file_manager.py` | Multiplicity |
| `EventListenerType` | ✅ Direct import | `core/event_bus.py` | Listener type |

---

## Category 9: DMN

### 9.1 DMN Elements

| OSDM Class | Used In | File | Usage Pattern |
|---|---|---|---|
| `DMNDefinition` | ❌ Not used | — | Base not referenced |
| `Decision` | ✅ Direct import | `dmn/decision_executor.py`, `dmn/decision_requirements_graph.py` | Decision execution |
| `BusinessKnowledgeModel` | ✅ Direct import | `dmn/decision_executor.py` | BKM evaluation |
| `InputData` | ✅ Direct import | `dmn/decision_executor.py` | Input data |
| `KnowledgeSource` | ✅ Direct import | `dmn/decision_executor.py` | Knowledge source |
| `DecisionService` | ✅ Direct import | `dmn/engine.py`, `dmn/decision_requirements_graph.py` | DS evaluation |
| `DecisionTable` | ✅ Direct import | `dmn/decision_table_evaluator.py` | Decision table |
| `InputClause` | ✅ Direct import | `dmn/decision_table_evaluator.py` | Input clause |
| `OutputClause` | ✅ Direct import | `dmn/decision_table_evaluator.py` | Output clause |
| `DecisionRule` | ✅ Direct import | `dmn/decision_table_evaluator.py` | Decision rule |
| `LiteralExpression` | ✅ Direct import | `dmn/literal_expression_eval.py` | Literal expression |
| `UnaryTests` | ✅ Direct import | `dmn/decision_table_evaluator.py` | Unary tests |

### 9.2 DMN Enums

| OSDM Enum | Used In | File | Usage Pattern |
|---|---|---|---|
| `DecisionLogicType` | ✅ Direct import | `dmn/decision_executor.py` | Decision logic type |

---

## Category 10: State Machine

### 10.1 State Machine Elements

| OSDM Class | Used In | File | Usage Pattern |
|---|---|---|---|
| `StateNode` | ✅ Direct import | `state_machine/state_executor.py` | State node base |
| `Transition` | ✅ Direct import | `state_machine/transition_handler.py` | Transition base |
| `State` | ✅ Direct import | `state_machine/state_executor.py` | State execution |
| `StateTransition` | ✅ Direct import | `state_machine/transition_handler.py` | State transition |
| `StateInvoke` | ✅ Direct import | `state_machine/state_executor.py` | State invocation |
| `StateMachineRegion` | ✅ Direct import | `state_machine/state_executor.py`, `state_machine/parallel_state_handler.py` | Region handling |
| `StateMachineModel` | ✅ Direct import | `state_machine/engine.py`, `state_machine/state_executor.py`, `core/instance.py` | State machine model |
| `PseudoState` | ✅ Direct import | `state_machine/state_executor.py` | Pseudo states |

### 10.2 State Machine Enums

| OSDM Enum | Used In | File | Usage Pattern |
|---|---|---|---|
| `PseudoStateKind` | ✅ Direct import | `state_machine/state_executor.py` | Pseudo state type |

---

## Category 11: CEP

### 11.1 CEP Elements

| OSDM Class | Used In | File | Usage Pattern |
|---|---|---|---|
| `CEPDefinition` | ❌ Not used | — | Base not referenced |
| `EventStream` | ✅ Direct import | `cep/stream_processor.py` | Event stream |
| `CEPRule` | ✅ Direct import | `cep/rule_evaluator.py` | CEP rule |

### 11.2 CEP Enums

| OSDM Enum | Used In | File | Usage Pattern |
|---|---|---|---|
| `CEPOperator` | ✅ Direct import | `core/event_bus.py`, `cep/pattern_matcher.py` | CEP operator |

---

## Category 12: Petri Net

| OSDM Class | Used In | File | Usage Pattern |
|---|---|---|---|
| `Place` | ✅ Direct import | `state_machine/state_executor.py` | Place (State alias) |
| `PnTransition` | ✅ Direct import | `state_machine/transition_handler.py` | PN transition |
| `Arc` | ✅ Direct import | `state_machine/transition_handler.py` | Arc |

---

## Category 13: Diagram Interchange (DI)

### 13.1 DI Elements

| OSDM Class | Used In | File | Usage Pattern |
|---|---|---|---|
| `Bounds` | ✅ Direct import | `bpmn/engine.py` | Bounds |
| `DiagramElement` | ✅ Direct import | `bpmn/engine.py` | DI element base |
| `Locator` | ❌ Not used | — | Not referenced |
| `BPMNDiagram` | ✅ Direct import | `bpmn/engine.py` | Diagram root |
| `BPMNPlane` | ✅ Direct import | `bpmn/engine.py` | Diagram plane |
| `BPMNShape` | ✅ Direct import | `bpmn/engine.py` | Shape |
| `BPMNEdge` | ✅ Direct import | `bpmn/engine.py` | Edge |
| `BPMNLabel` | ✅ Direct import | `bpmn/engine.py` | Label |

---

## Category 14: Document-Level

| OSDM Class | Used In | File | Usage Pattern |
|---|---|---|---|
| `BaseOSDMDocument` | ✅ Direct import | `runtime/osdm_serializer.py` | Document base |
| `BPMNDocument` | ✅ Direct import | `bpmn/engine.py`, `runtime/osdm_serializer.py` | BPMN document |
| `CMMNDocument` | ✅ Direct import | `cmmn/engine.py`, `runtime/osdm_serializer.py` | CMMN document |
| `StateMachineDocument` | ✅ Direct import | `state_machine/engine.py`, `runtime/osdm_serializer.py` | State machine document |
| `DMNDocument` | ✅ Direct import | `dmn/engine.py`, `runtime/osdm_serializer.py` | DMN document |
| `CEPDocument` | ✅ Direct import | `cep/engine.py`, `runtime/osdm_serializer.py` | CEP document |
| `MultiAgentInteractionDocument` | ❌ Not used | — | Not referenced |
| `OSDMModel` | ❌ Not used | — | Not referenced |

---

## Category 15: Multi-Agent

| OSDM Class | Used In | File | Usage Pattern |
|---|---|---|---|
| `InteractionProtocol` | ✅ Direct import | `multi_agent/engine.py`, `multi_agent/protocol_handler.py` | Protocol definition |
| `InteractionModel` | ✅ Direct import | `multi_agent/engine.py` | Interaction model |
| `InteractionStrategy` | ✅ Direct import | `multi_agent/coordination_handler.py` | Strategy enum |

### Multi-Agent Enums

| OSDM Enum | Used In | File | Usage Pattern |
|---|---|---|---|
| `InteractionNodeType` | ✅ Direct import | `multi_agent/interaction_handler.py` | Node type |

---

## Category 16: Extension and Base

| OSDM Class | Used In | File | Usage Pattern |
|---|---|---|---|
| `BaseElement` | ❌ Not used | — | Base class not directly referenced |
| `RootElement` | ❌ Not used | — | Base class not directly referenced |
| `Extension` | ✅ Direct import | `bpmn/engine.py` | Extension |
| `ExtensionDefinition` | ✅ Direct import | `bpmn/engine.py` | Extension definition |
| `ExtensionAttributeValue` | ✅ Direct import | `bpmn/engine.py` | Extension attribute value |
| `ExtensionAttributeDefinition` | ❌ Not used | — | Not referenced |
| `ActionList` | ❌ Not used | — | Not referenced |
| `CloudResourceBinding` | ✅ Direct import | `runtime/resource_manager.py` | Cloud resource |

---

## Unused OSDM Classes — Analysis

36 OSDM classes are not referenced in the orchestration engine. Here's the breakdown:

### Potentially Missing Functionality

| OSDM Class | Impact | Recommendation |
|---|---|---|
| `DueTimeDuration` | Medium — Timer duration calculations | Import where timer scheduling logic lives |
| `Assignment` | Medium — Data association expressions | Import in `data_object_handler.py` |
| `InputOutputBinding` | Medium — Input/output set binding | Import in `data_object_handler.py` |
| `DataInputRef` / `DataOutputRef` | Low — Reference resolution | Import if IO set resolution needed |
| `DataStore` | Medium — Persistent data stores | Import in `data_object_handler.py` |
| `Property` | Low — Process properties | Import if property bags needed |
| `GlobalUserTask` / `GlobalScriptTask` / `GlobalManualTask` / `GlobalBusinessRuleTask` | Medium — Specific global task types | Import in `global_task_handler.py` for type-specific handling |
| `ImplicitThrowEvent` | Low — Implicit throw events | Import in `event_handler.py` if needed |
| `ParticipantMultiplicity` | Medium — Multi-instance participants | Import in `collaboration_handler.py` |
| `ParticipantAssociation` | Low — Participant associations | Import if association handling needed |
| `PartnerEntity` / `PartnerRole` | Low — Partner definitions | Import if partner handling needed |
| `ParticipantAssociation` | Low — Participant association | Import if needed |
| `ParticipantMultiplicity` | Medium — Multi-instance participant | Import in `collaboration_handler.py` |
| `ResourceParameterBinding` | Low — Parameter binding | Import in `activity_handler.py` |
| `ResourceAssignmentExpression` | Low — Assignment expression | Import in `activity_handler.py` |
| `CorrelationPropertyRetrievalExpression` | Medium — Correlation property retrieval | Import in `core/correlation.py` |
| `RetryBackoffRate` | Low — Backoff rate | Import in `runtime/circuit_breaker.py` |
| `ActionList` | Low — Action list | Import if needed |
| `MultiAgentInteractionDocument` | Low — Multi-agent document | Import in `multi_agent/engine.py` |

### Base Classes (Not Directly Needed)

These are abstract base classes that don't need direct import:
- `BaseElement`, `RootElement`, `DataElement`, `DataFlowElement`, `EventDefinition`, `InteractionNode`, `BpmnExpression`, `ChoreographyActivity`

### Document-Level (Base Not Needed)

These are document container bases:
- `OSDMModel`, `DMNDefinition`, `CEPDefinition`
