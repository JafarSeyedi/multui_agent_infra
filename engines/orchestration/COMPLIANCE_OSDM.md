# OSDM Compliance Analysis Document (4.1)

## Executive Summary

This document provides a comprehensive analysis of compliance between the `engines/orchestration` runtime implementation and the OSDM (Orchestration Standard Definition Model) defined in `engines/document/models/osdm_models.py`. The analysis covers all classes, types, and fields defined in OSDM and evaluates whether they are properly utilized, referenced, or extended in the orchestration runtime layer.

---

## 1. OSDM Model Structure Overview

### 1.1 Document Types
| OSDM Document Class | Purpose | Used in Orchestration | Status |
|---|---|---|---|
| `BPMNDocument` | BPMN 2.0 XML document wrapper | `bpmn/engine.py` - parsed via `BPMNXMLParser` | ✅ Used |
| `CMMNDocument` | CMMN 1.1 XML document wrapper | Not yet imported | ⚠️ Missing |
| `StateMachineDocument` | UML State Machine document | Not yet imported | ⚠️ Missing |
| `DMNDocument` | DMN 1.3 XML document wrapper | Not yet imported | ⚠️ Missing |
| `CEPDocument` | CEP event processing document | Not yet imported | ⚠️ Missing |
| `MultiAgentInteractionDocument` | Multi-agent interaction document | Not yet imported | ⚠️ Missing |
| `OSDMModel` | Unified OSDM model root | Not yet imported | ⚠️ Missing |

### 1.2 Core Process Elements (BPMN)

#### 1.2.1 Flow Elements
| OSDM Class | Fields | Orchestration Usage | Compliance |
|---|---|---|---|
| `FlowElement` | `id`, `name`, `documentation`, `categoryValues`, `auditing`, `monitoring` | Base for all flow elements | ✅ Via OSDM imports |
| `FlowNode` | `incoming`, `outgoing`, `input_state_id`, `output_state_id` | Used in process traversal | ✅ Via OSDM imports |
| `Activity` | `activity_type`, `loop_characteristics`, `io_specification`, `resources`, `properties`, `data_inputs`, `data_outputs`, `data_associations` | `activity_handler.py` | ✅ Imported |
| `Task` | Base task class | Used in activity handler | ✅ Via OSDM imports |
| `ServiceTask` | `implementation`, `operation_ref` | Activity handler `_execute_service_task` | ⚠️ Logic exists but doesn't use OSDM ServiceTask class directly |
| `UserTask` | `form_key`, `assignee`, `candidate_groups`, etc. | Activity handler `_execute_user_task` | ⚠️ Fields checked via dict access, not OSDM UserTask |
| `ManualTask` | Base manual task | Activity handler `_execute_manual_task` | ✅ Handled |
| `ScriptTask` | `script`, `script_format` | Activity handler `_execute_script_task` | ⚠️ Doesn't use OSDM ScriptTask class |
| `BusinessRuleTask` | `called_decision` | Activity handler `_execute_business_rule_task` | ✅ Handles decision_ref |
| `SendTask` | Base send task | Activity handler `_execute_send_task` | ✅ Handled |
| `ReceiveTask` | Base receive task | Activity handler `_execute_receive_task` | ✅ Handled |
| `CallActivity` | `called_element`, `call_activity_type`, `io_binding` | Activity handler `_execute_call_activity` | ⚠️ Doesn't use OSDM CallActivity class |
| `SubProcess` | `sub_process_type`, `flow_elements`, `lane_sets`, `artifacts`, `triggered_by_event` | Activity handler `_execute_sub_process` | ⚠️ Doesn't use OSDM SubProcess class |
| `TransactionSubProcess` | `method` | Transaction handler | ⚠️ Doesn't use OSDM TransactionSubProcess |
| `AdHocSubProcess` | `ordering`, `completion_condition`, `cancel_remaining_instances` | Adhoc handler | ⚠️ Doesn't use OSDM AdHocSubProcess |
| `GlobalTask` | `task_type`, `resources` | Global task handler | ⚠️ Doesn't use OSDM GlobalTask class |

#### 1.2.2 Events
| OSDM Class | Fields | Orchestration Usage | Compliance |
|---|---|---|---|
| `Event` | `event_type`, `event_definitions`, `properties` | EventHandler dispatch | ✅ Imported as `BPMNEventType` |
| `StartEvent` | `is_interrupting` | `handle_start` | ✅ Handled |
| `EndEvent` | Base end event | `handle_end` | ✅ Handles error, escalation, signal, terminate |
| `IntermediateCatchEvent` | Base catch event | `handle_intermediate_catch` | ✅ Handled |
| `IntermediateThrowEvent` | Base throw event | `handle_intermediate_throw` | ✅ Handled |
| `BoundaryEvent` | `attached_to_ref`, `cancel_activity` | `handle_boundary` | ⚠️ Doesn't use OSDM BoundaryEvent class |

#### 1.2.3 Event Definitions
| OSDM Class | Fields | Orchestration Usage | Compliance |
|---|---|---|---|
| `EventDefinition` | `type` | Base for event definitions | ✅ Imported as `EventDefinitionType` |
| `MessageEventDefinition` | `message_ref`, `operation_ref` | Message event handling | ✅ Event type checked |
| `TimerEventDefinition` | `timer_type`, `time_date`, `time_cycle`, `time_duration`, `due_duration` | Timer event handling | ⚠️ Doesn't use OSDM TimerEventDefinition class |
| `SignalEventDefinition` | `signal_ref` | Signal event handling | ✅ Event type checked |
| `ErrorEventDefinition` | `error_ref` | Error event handling | ✅ Event type checked |
| `EscalationEventDefinition` | `escalation_ref` | Escalation handling | ✅ Event type checked |
| `CompensateEventDefinition` | `activity_ref`, `wait_for_completion` | Compensation handling | ✅ Event type checked |
| `ConditionalEventDefinition` | `condition` | Conditional event handling | ✅ Event type checked |
| `LinkEventDefinition` | `sources`, `target` | Link event handling | ✅ Event type checked |
| `CancelEventDefinition` | None | Cancel handling | ✅ Event type checked |
| `TerminateEventDefinition` | None | Terminate handling | ✅ Event type checked |

#### 1.2.4 Gateways
| OSDM Class | Fields | Orchestration Usage | Compliance |
|---|---|---|---|
| `Gateway` | `gateway_type`, `gateway_direction` | Gateway handler | ✅ Imported `GatewayType`, `GatewayDirection` |
| `ExclusiveGateway` | Inherits Gateway | Exclusive routing | ✅ Handled via GatewayType |
| `InclusiveGateway` | Inherits Gateway | Inclusive routing | ✅ Handled via GatewayType |
| `ParallelGateway` | Inherits Gateway | Parallel routing | ✅ Handled via GatewayType |
| `EventBasedGateway` | `event_based_gateway_type` | Event-based routing | ⚠️ Doesn't use OSDM EventBasedGatewayType |
| `ComplexGateway` | `activation_condition` | Complex routing | ✅ Handled via GatewayType |

#### 1.2.5 Sequence & Data Flow
| OSDM Class | Fields | Orchestration Usage | Compliance |
|---|---|---|---|
| `SequenceFlow` | `source_ref`, `target_ref`, `condition_expression`, `is_immediate` | Sequence flow engine | ✅ Imported as `OSDMSequenceFlow` |
| `MessageFlow` | `source_ref`, `target_ref`, `message_ref` | Collaboration handler | ✅ Imported as `OSDMMessageFlow` |
| `DataObject` | `is_collection`, `item_subject_ref` | Data object handler | ✅ Imported |
| `DataObjectReference` | `data_object` | Data object handler | ✅ Imported |
| `DataStoreReference` | `data_store` | Data object handler | ✅ Imported |
| `DataAssociation` | `source_ref`, `target_ref`, `transformation` | Data object handler | ✅ Imported |
| `DataInputAssociation` | Inherits DataAssociation | Data object handler | ✅ Imported |
| `DataOutputAssociation` | Inherits DataAssociation | Data object handler | ✅ Imported |

#### 1.2.6 Loop Characteristics
| OSDM Class | Fields | Orchestration Usage | Compliance |
|---|---|---|---|
| `LoopCharacteristics` | Base class | Loop handler | ✅ Imported |
| `StandardLoopCharacteristics` | `loop_condition`, `loop_maximum`, `test_before` | Loop handler | ✅ Imported |
| `MultiInstanceLoopCharacteristics` | `is_sequential`, `loop_cardinality`, `completion_condition`, `loop_data_input_ref`, `loop_data_output_ref` | Loop handler | ✅ Imported |

#### 1.2.7 Enums
| OSDM Enum | Values | Usage Location | Compliance |
|---|---|---|---|
| `ActivityType` | `TASK`, `SUB_PROCESS`, `CALL_ACTIVITY` | Activity handler | ✅ Imported |
| `TaskType` | `NONE`, `SERVICE`, `USER`, `MANUAL`, `SCRIPT`, `BUSINESS_RULE`, `SEND`, `RECEIVE` | Activity handler | ✅ Imported |
| `SubProcessType` | `EMBEDDED`, `EVENT`, `TRANSACTION`, `AD_HOC` | Activity handler | ✅ Imported |
| `GatewayType` | `EXCLUSIVE`, `INCLUSIVE`, `PARALLEL`, `COMPLEX`, `EVENT_BASED` | Gateway handler | ✅ Imported |
| `EventType` | `START`, `END`, `INTERMEDIATE_CATCH`, `INTERMEDIATE_THROW`, `BOUNDARY` | Event handler | ✅ Imported |
| `EventDefinitionType` | `NONE`, `MESSAGE`, `TIMER`, `SIGNAL`, `ERROR`, `ESCALATION`, `CONDITIONAL`, `LINK`, `CANCEL`, `TERMINATE`, `COMPENSATION` | Event handler | ✅ Imported |
| `LoopType` | `NONE`, `STANDARD`, `MULTI_INSTANCE` | Loop handler | ✅ Imported |
| `MultiInstanceBehavior` | `NONE`, `ONE`, `ALL`, `COMPLEX` | Loop handler | ✅ Imported |
| `AdHocOrdering` | `PARALLEL`, `SEQUENTIAL` | Adhoc handler | ✅ Imported |
| `ChoreographyLoopType` | `NONE`, `STANDARD`, `MULTI_INSTANCE_PARALLEL`, `MULTI_INSTANCE_SEQUENTIAL` | Choreography handler | ✅ Imported |
| `TransactionMethod` | `COMPENSATE`, `STORE`, `IMAGE` | Transaction handler | ✅ Imported |
| `ScriptLanguage` | `JS`, `PYTHON` | (Available for use) | ⚠️ Not yet used |
| `GatewayDirection` | `UNSPECIFIED`, `CONVERGING`, `DIVERGING`, `MIXED` | Gateway handler | ✅ Imported |
| `AssociationDirection` | `NONE`, `ONE`, `BOTH` | (Available for use) | ⚠️ Not yet used |
| `EventBasedGatewayType` | `EXCLUSIVE`, `PARALLEL` | Gateway handler | ⚠️ Not yet used |
| `TimerEventType` | (Timer event types) | (Available for use) | ⚠️ Not yet used |
| `CallActivityType` | `PROCESS`, `GLOBAL_TASK` | (Available for use) | ⚠️ Not yet used |
| `ProcessType` | `NONE`, `PUBLIC`, `PRIVATE` | (Available for use) | ⚠️ Not yet used |
| `ItemKind` | `INFORMATION` | (Available for use) | ⚠️ Not yet used |

#### 1.2.8 Collaboration Elements
| OSDM Class | Fields | Usage | Compliance |
|---|---|---|---|
| `Process` | `process_type`, `is_executable`, `is_closed`, `flow_elements`, `lane_sets`, `artifacts`, `correlation_subscriptions`, etc. | BPMN engine | ⚠️ Used via dict, not OSDM Process class |
| `Collaboration` | `participants`, `message_flows`, `conversation_links` | Collaboration handler | ⚠️ Doesn't use OSDM Collaboration class |
| `Participant` | `name`, `process_ref`, `interface_refs` | Collaboration handler | ✅ Imported |
| `MessageFlow` | `source_ref`, `target_ref`, `message_ref` | Collaboration handler | ✅ Imported |
| `ConversationLink` | `source_ref`, `target_ref`, `name` | Collaboration handler | ✅ Imported |
| `Conversation` | `participants`, `message_flows` | (Available for use) | ⚠️ Not yet used |
| `LaneSet` | `lanes` | Collaboration handler | ✅ Imported |
| `Lane` | `name`, `flow_node_refs`, `child_lane_sets` | Collaboration handler | ✅ Imported |
| `Association` | `direction`, `source_ref`, `target_ref` | (Available for use) | ⚠️ Not yet used |
| `Group` | `category_value` | (Available for use) | ⚠️ Not yet used |
| `TextAnnotation` | `text`, `text_format` | (Available for use) | ⚠️ Not yet used |

#### 1.2.9 Choreography Elements
| OSDM Class | Fields | Usage | Compliance |
|---|---|---|---|
| `ChoreographyActivity` | `initiating_participant_ref`, `participant_refs`, `message_flows` | Choreography handler | ⚠️ Doesn't use OSDM class |
| `ChoreographyTask` | Inherits ChoreographyActivity | Choreography handler | ✅ Imported |
| `SubChoreography` | `flow_elements` | (Available for use) | ⚠️ Not yet used |
| `CallChoreography` | `called_choreography_ref` | (Available for use) | ⚠️ Not yet used |
| `GlobalChoreographyTask` | `initiating_participant_ref` | (Available for use) | ⚠️ Not yet used |
| `Choreography` | `participants`, `message_flows` | (Available for use) | ⚠️ Not yet used |

#### 1.2.10 Data Types & Structures
| OSDM Class | Fields | Usage | Compliance |
|---|---|---|---|
| `ItemDefinition` | `item_kind`, `structure_ref` | Data object handler | ✅ Imported |
| `DataInput` | `name`, `is_required`, `data_type` | (Available for use) | ⚠️ Not yet used in handlers |
| `DataOutput` | `name`, `data_type` | (Available for use) | ⚠️ Not yet used in handlers |
| `InputSet` | `names` | (Available for use) | ⚠️ Not yet used |
| `OutputSet` | `names` | (Available for use) | ⚠️ Not yet used |
| `DataState` | `name` | Data object handler | ✅ Imported |
| `DataFlowElement` | `item_subject_ref`, `data_state` | (Available for use) | ⚠️ Not yet used |
| `InputOutputSpecification` | `data_inputs`, `data_outputs`, `input_sets`, `output_sets` | (Available for use) | ⚠️ Handlers use dict-based approach |
| `FormalExpression` | `language`, `body`, `evaluates_to_type_ref` | (Available for use) | ⚠️ Not yet used |

#### 1.2.11 CMMN Elements
| OSDM Class | Fields | Usage | Compliance |
|---|---|---|---|
| `Stage` | `auto_complete`, `entry_criteria`, `exit_criteria` | Stage handler | ⚠️ Doesn't use OSDM Stage class |
| `Milestone` | Milestone properties | Milestone handler | ⚠️ Doesn't use OSDM Milestone class |
| `CaseFileItem` | `item_subject_ref`, `multiplicity`, `definition_ref` | Case file handler | ⚠️ Doesn't use OSDM CaseFileItem class |
| `CaseTask` | `case_ref`, `io_mapping` | Case executor | ⚠️ Doesn't use OSDM CaseTask class |
| `ProcessTask` | `called_element`, `io_mapping` | Case executor | ⚠️ Doesn't use OSDM ProcessTask class |
| `HumanTask` | `role_ref` | Case executor | ⚠️ Doesn't use OSDM HumanTask class |
| `Sentry` | `on_parts`, `if_parts` | Sentry evaluator | ⚠️ Doesn't use OSDM Sentry class |
| `EntryCriterion` | `sentry_ref` | (Available for use) | ⚠️ Not yet used |
| `ExitCriterion` | `sentry_ref` | (Available for use) | ⚠️ Not yet used |
| `PlanItem` | Base plan item | (Available for use) | ⚠️ Not yet used |
| `DiscretionaryItem` | `definition_ref`, `entry_criteria` | Discretionary handler | ⚠️ Doesn't use OSDM class |
| `SentryExpression` | Inherits FormalExpression | (Available for use) | ⚠️ Not yet used |

#### 1.2.12 State Machine Elements
| OSDM Class | Fields | Usage | Compliance |
|---|---|---|---|
| `State` | `name`, `is_initial`, `is_final` | State executor | ⚠️ Doesn't use OSDM State class |
| `StateNode` | Base state node | State executor | ⚠️ Doesn't use OSDM StateNode class |
| `PseudoState` | `kind` | State executor (PseudoStateKind enum used) | ✅ Enum used, class not used |
| `StateTransition` | `trigger`, `guard`, `effect` | Transition handler | ⚠️ Doesn't use OSDM StateTransition class |
| `StateMachineRegion` | `states`, `initial_state` | State executor | ⚠️ Doesn't use OSDM class |
| `StateMachineModel` | `states`, `transitions`, `regions` | State executor | ⚠️ Doesn't use OSDM class |
| `StateInvoke` | `operation` | (Available for use) | ⚠️ Not yet used |
| `Place` | Inherits State | (Available for use) | ⚠️ Not yet used |
| `PnTransition` | Inherits Transition | (Available for use) | ⚠️ Not yet used |
| `Arc` | Inherits Transition | (Available for use) | ⚠️ Not yet used |

#### 1.2.13 DMN Elements
| OSDM Class | Fields | Usage | Compliance |
|---|---|---|---|
| `Decision` | `name`, `question`, `allowed_answer` | Decision executor | ⚠️ Doesn't use OSDM Decision class |
| `BusinessKnowledgeModel` | Encapsulated logic | (Available for use) | ⚠️ Not yet used |
| `InputData` | Input data elements | (Available for use) | ⚠️ Not yet used |
| `KnowledgeSource` | Authority source | (Available for use) | ⚠️ Not yet used |
| `DecisionService` | `output_decisions` | (Available for use) | ⚠️ Not yet used |
| `DecisionTable` | `input`, `output`, `rules`, `hit_policy` | Decision table evaluator | ✅ Imported |

#### 1.2.14 CEP Elements
| OSDM Class | Fields | Usage | Compliance |
|---|---|---|---|
| `CEPRule` | Rule definition | Rule evaluator | ⚠️ Doesn't use OSDM CEPRule class |
| `EventStream` | Event stream | (Available for use) | ⚠️ Not yet used |

#### 1.2.15 Multi-Agent Elements
| OSDM Class | Fields | Usage | Compliance |
|---|---|---|---|
| `InteractionProtocol` | Protocol definition | Protocol handler | ⚠️ Doesn't use OSDM class |
| `InteractionModel` | Model definition | (Available for use) | ⚠️ Not yet used |

#### 1.2.16 Core Infrastructure
| OSDM Class | Fields | Usage | Compliance |
|---|---|---|---|
| `Message` | `name`, `item_subject_ref` | Data object handler | ✅ Imported |
| `Signal` | `name`, `item_subject_ref` | (Available for use) | ⚠️ Not yet used |
| `Error` | `name`, `structure_ref`, `error_code` | (Available for use) | ⚠️ Not yet used |
| `Escalation` | `name`, `structure_ref`, `escalation_code` | (Available for use) | ⚠️ Not yet used |
| `CorrelationKey` | `name`, `correlation_property_ref` | (Available for use) | ⚠️ Not yet used |
| `CorrelationProperty` | `name`, `correlation_property_type`, `correlation_property_retrieval_expression` | (Available for use) | ⚠️ Not yet used |
| `CorrelationSubscription` | `correlation_key_ref`, `correlation_property_binding` | (Available for use) | ⚠️ Not yet used |
| `Category` | `name` | (Available for use) | ⚠️ Not yet used |
| `CategoryValue` | `value` | (Available for use) | ⚠️ Not yet used |
| `Resource` | `name`, `resource_parameters` | (Available for use) | ⚠️ Not yet used |
| `ResourceRole` | `resource_ref` | (Available for use) | ⚠️ Not yet used |
| `ResourceParameter` | `name`, `type` | (Available for use) | ⚠️ Not yet used |
| `Auditing` | `save_instances`, `generate_trace_log` | (Available for use) | ⚠️ Not yet used |
| `Monitoring` | Base monitoring | (Available for use) | ⚠️ Not yet used |
| `Interface` | `name`, `operations` | (Available for use) | ⚠️ Not yet used |
| `Operation` | `name`, `in_message_ref`, `out_message_ref` | (Available for use) | ⚠️ Not yet used |
| `EndPoint` | End point reference | (Available for use) | ⚠️ Not yet used |

---

## 2. Key Findings & Gaps

### 2.1 Critical Issues (Must Fix)
1. **Handler classes don't use OSDM model classes directly** - Most handlers work with `dict[str, Any]` instead of typed OSDM objects. This means type safety is lost and field validation is manual.
2. **Document types not imported** - `BPMNDocument`, `CMMNDocument`, `StateMachineDocument`, `DMNDocument`, `CEPDocument` are never imported or used.
3. **Many OSDM classes not referenced at all** - See table below.

### 2.2 OSDM Classes Not Referenced Anywhere in Orchestration
The following OSDM classes are defined but never imported or referenced:

| Category | Missing Classes |
|---|---|
| Documents | `BPMNDocument`, `CMMNDocument`, `StateMachineDocument`, `DMNDocument`, `CEPDocument`, `MultiAgentInteractionDocument`, `OSDMModel`, `BaseOSDMDocument` |
| Core Elements | `Process`, `Collaboration`, `TransactionSubProcess`, `AdHocSubProcess`, `SubProcess`, `CallActivity`, `ServiceTask`, `UserTask`, `ScriptTask`, `BusinessRuleTask`, `SendTask`, `ReceiveTask`, `GlobalTask`, `GlobalUserTask`, `GlobalScriptTask`, `GlobalManualTask`, `GlobalBusinessRuleTask` |
| Events | `StartEvent`, `EndEvent`, `IntermediateCatchEvent`, `IntermediateThrowEvent`, `BoundaryEvent`, `ImplicitThrowEvent`, `CatchEvent`, `ThrowEvent`, `Event` |
| Event Definitions | `TimerEventDefinition`, `MessageEventDefinition`, `SignalEventDefinition`, `ErrorEventDefinition`, `EscalationEventDefinition`, `CompensateEventDefinition`, `ConditionalEventDefinition`, `LinkEventDefinition`, `CancelEventDefinition`, `TerminateEventDefinition`, `EventDefinition` |
| Gateways | `ExclusiveGateway`, `InclusiveGateway`, `ParallelGateway`, `EventBasedGateway`, `ComplexGateway`, `Gateway` |
| Data | `DataStoreReference`, `DataFlowElement`, `DataOutput`, `DataInput`, `InputSet`, `OutputSet`, `InputOutputSpecification`, `FormalExpression`, `BpmnExpression`, `DataInputAssociation`, `DataOutputAssociation`, `DataAssociation` |
| Sequences | `SequenceFlow`, `MessageFlow` (used in collaboration but OSDM class not imported) |
| Collaboration | `Conversation`, `ConversationNode`, `CallConversation`, `GlobalConversation`, `SubConversation`, `ConversationAssociation`, `MessageFlowAssociation`, `ParticipantAssociation`, `ParticipantMultiplicity`, `PartnerEntity`, `PartnerRole`, `Association`, `Group`, `TextAnnotation` |
| Choreography | `ChoreographyActivity`, `SubChoreography`, `CallChoreography`, `GlobalChoreographyTask`, `Choreography` |
| CMMN | `Stage`, `Milestone`, `CaseFileItem`, `CaseTask`, `ProcessTask`, `HumanTask`, `PlanItem`, `DiscretionaryItem`, `Sentry`, `EntryCriterion`, `ExitCriterion`, `EventListener`, `ApplicabilityRule` |
| State Machine | `State`, `StateNode`, `PseudoState`, `StateTransition`, `StateMachineRegion`, `StateMachineModel`, `StateInvoke`, `Place`, `PnTransition`, `Arc` |
| DMN | `Decision`, `BusinessKnowledgeModel`, `InputData`, `KnowledgeSource`, `DecisionService`, `DecisionLogicType` |
| CEP | `CEPRule`, `EventStream`, `CEPOperator` |
| Multi-Agent | `InteractionProtocol`, `InteractionModel`, `InteractionNode`, `InteractionStrategy` |
| Infrastructure | `Message`, `Signal`, `Error`, `Escalation`, `CorrelationKey`, `CorrelationProperty`, `CorrelationSubscription`, `CorrelationPropertyBinding`, `CorrelationPropertyRetrievalExpression`, `Category`, `CategoryValue`, `Resource`, `ResourceRole`, `ResourceParameter`, `ResourceAssignmentExpression`, `ResourceParameterBinding`, `ResourceParameterType`, `ResourceRoleType`, `HumanPerformer`, `Performer`, `PotentialOwner`, `PotentialOwnerType`, `Auditing`, `Monitoring`, `Interface`, `Operation`, `EndPoint`, `Rendering`, `RenderingForm`, `CloudResourceBinding`, `ErrorHandlingConfig`, `RetryConfig`, `TimeoutConfig`, `ErrorHandlingOperator`, `Place`, `Arc` |

### 2.3 Issues in current implementation

1. **Dict-based processing**: The entire orchestration layer works with `dict[str, Any]` for process definitions instead of typed OSDM objects. This means:
   - No compile-time type checking
   - Field access via string keys (error-prone)
   - No IDE autocompletion
   - No validation against OSDM schema

2. **Handler result classes don't extend OSDM**: Classes like `ActivityExecutionResult`, `GatewayDecision`, etc. are handler-specific but don't relate to OSDM models.

3. **Engine classes extend dict patterns**: `BPMNEngine._normalize_model` converts to `ProcessModel(dict)` instead of using OSDM `Process` class.

---

## 3. Recommendations

### 3.1 Immediate Actions
1. Import and use OSDM document types (`BPMNDocument`, `CMMNDocument`, etc.) in engine parsers
2. Use typed OSDM classes for process traversal instead of dict access
3. Map handler results to/from OSDM types

### 3.2 Architectural Changes
1. Process `dict[str, Any]` → `OSDM Process` class traversal
2. Event handling should use OSDM `Event` subclasses
3. Gateway handling should use OSDM `Gateway` subclasses
4. Data objects should use OSDM `DataObject`, `DataAssociation` classes

### 3.3 Compliance Target
- **Phase A**: Import all relevant OSDM classes (enum imports already done in latest handler files)
- **Phase B**: Refactor handlers to accept OSDM-typed objects
- **Phase C**: Add OSDM validation layer between parsing and execution
- **Phase D**: Full OSDM serialization/deserialization for all runtime objects
