# Orchestration Internal Model Refactoring (Phase 2)

## Motivation

Following Phase 1 (engine-specific SDM migration), the orchestration engine still has a monolithic `osdm_models.py` (1766 lines, 184 classes) and a flat `models/parsers/` + `models/writers/` directory where all engine-specific parsers/writers live together. As noted in `refactoring.md`:

> "osdm models have some shared objects, but there are some engine specific models (DMN/CMMN, CEP, State machine, BPMN, bam, ...), these models and their parsers and writers codes must be separated and moved near their engines"

## Import Style

All imports between orchestration engine modules use **relative paths** (e.g., `from ..models.shared_models import BaseElement`). External imports from other engines use absolute paths.

## Target Structure

```
engines/orchestration/
    ├── models/
    │   ├── __init__.py
    │   └── shared_models.py            ← shared base classes across all engines
│
├── bpmn/
│   ├── __init__.py
│   ├── models/
│   │   ├── bpmn_models.py          ← BPMN-specific classes
│   │   └── agentic_models.py       ← Agentic BPMN extension classes
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── bpmn_xml_parser.py
│   │   ├── bpmn_collaboration.py
│   │   ├── bpmn_constants.py
│   │   ├── bpmn_diagram.py
│   │   ├── bpmn_flow_parser.py
│   │   ├── bpmn_reference_resolver.py
│   │   ├── bpmn_root_element.py
│   │   ├── epc_parser.py
│   │   ├── graphml_xml_parser.py
│   │   ├── pnml_xml_parser.py
│   │   ├── prefect_dag_parser.py
│   │   ├── scxml_parser.py
│   │   └── xpd_parser.py
│   ├── writers/
│   │   ├── __init__.py
│   │   ├── bpmn_xml_writer.py
│   │   ├── epc_writer.py
│   │   ├── graphml_xml_writer.py
│   │   ├── pnml_xml_writer.py
│   │   ├── prefect_dag_writer.py
│   │   ├── scxml_writer.py
│   │   └── xpd_writer.py
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_bpmn_xml_parse.py
│       ├── test_bpmn_xml_write.py
│       ├── test_bpmn_diagram.py
│       ├── test_bpmn_reference_resolver.py
│       └── test_bpmn_collaboration.py
│
├── dmn/
│   ├── __init__.py
│   ├── models/
│   │   └── dmn_models.py           ← DMN-specific classes
│   ├── parsers/
│   │   ├── __init__.py
│   │   └── dmn_xml_parser.py
│   ├── writers/
│   │   ├── __init__.py
│   │   └── dmn_xml_writer.py
│   └── tests/
│       ├── __init__.py
│       └── test_dmn.py
│
├── cmmn/
│   ├── __init__.py
│   ├── models/
│   │   └── cmmn_models.py          ← CMMN-specific classes
│   ├── parsers/
│   │   ├── __init__.py
│   │   └── cmmn_xml_parser.py
│   ├── writers/
│   │   ├── __init__.py
│   │   └── cmmn_xml_writer.py
│   └── tests/
│       ├── __init__.py
│       └── test_cmmn.py
│
├── cep/
│   ├── __init__.py
│   ├── models/
│   │   └── cep_models.py           ← CEP-specific classes
│   ├── parsers/
│   │   ├── __init__.py
│   │   └── cep_parser.py
│   ├── writers/
│   │   ├── __init__.py
│   │   └── cep_writer.py
│   └── tests/
│       ├── __init__.py
│       └── test_cep.py
│
├── state_machine/
│   ├── __init__.py
│   ├── models/
│   │   └── state_machine_models.py ← State Machine + SCXML classes
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── uml_state_machine_parser.py
│   │   └── scxml_parser.py
│   ├── writers/
│   │   ├── __init__.py
│   │   ├── uml_state_machine_writer.py
│   │   └── scxml_writer.py
│   └── tests/
│       ├── __init__.py
│       └── test_state_machine.py
│
├── multi_agent/
│   ├── __init__.py
│   ├── engine.py
│   ├── mediator.py
│   ├── agent_executor.py
│   ├── coordination_handler.py
│   ├── interaction_handler.py
│   ├── message_router.py
│   ├── negotiation_handler.py
│   ├── protocol_handler.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── multi_agent_models.py   ← Multi-agent interaction models
│   └── tests/                      (stays at root tests/)
│
└── bam/
    ├── __init__.py
    ├── engine.py
    ├── models/
    │   ├── __init__.py
    │   └── bam_models.py           ← BAM models (moved from models/)
    ├── parsers/
    │   ├── __init__.py
    │   ├── bam_json_parser.py
    │   ├── bam_yaml_parser.py
    │   └── base_bam_parser.py
    ├── writers/
    │   ├── __init__.py
    │   ├── bam_json_writer.py
    │   ├── bam_yaml_writer.py
    │   └── base_bam_writer.py
    ├── tests/
    │   ├── __init__.py
    │   └── test_bam*.py            ← 11 files from tests/test_bam/
    ├── agents/
    ├── alerting/
    ├── collector/
    ├── dashboard/
    ├── persistence/
    ├── realtime/
    └── slas/
```

## Class Distribution

### `shared_models.py` (stays in `models/`)

Truly shared base types, enums, and infrastructure used across multiple orchestration engines:

- **Shared enums**: `ParticipantBandKind`, `MessageVisibleKind`, `AlignmentKind`, `TimerCalculationType`, `TimeReference`, `DurationResolution`, `EscapeType`, `CorrelationPropertyType`, `CaseFileMultiplicity`, `ItemKind`, `TimerEventType`, `RelationshipDirection`, `ResourceParameterType`, `WorkflowStateType`, `PseudoStateKind`
- **Base infrastructure**: `BaseElement`, `RootElement`, `ExtensionAttributeDefinition`, `ExtensionDefinition`, `ExtensionAttributeValue`, `Extension`, `Bounds`, `Locator`, `DiagramElement`, `Edge`, `Shape`
- **Error handling**: `ErrorHandlingOperator`, `RetryBackoffRate`, `CloudResourceBinding`, `ErrorHandlingConfig`, `RetryConfig`, `TimeoutConfig`
- **Document roots**: `BaseOSDMDocument`, `OSDMModel`, `ActionList`
- **`SentryExpression`** (CMMN uses but is a `FormalExpression` subclass — re-exported from shared)

### `bpmn_models.py` (moves to `bpmn/models/`)

All BPMN 2.0 specific classes — enums, base elements, activities, events, gateways, flows, data, conversation/choreography, and BPMN diagram types:

- **BPMN enums**: `ActivityType`, `TaskType`, `SubProcessType`, `GatewayType`, `EventType`, `LoopType`, `MultiInstanceBehavior`, `AdHocOrdering`, `ScriptLanguage`, `CallActivityType`, `ProcessType`, `GatewayDirection`, `AssociationDirection`, `EventBasedGatewayType`, `EventDefinitionType`, `ChoreographyLoopType`, `TransactionMethod`, `EventListenerType`, `InteractionNodeType`, `ResourceRoleType`, `PotentialOwnerType`
- **BPMN base types**: `StateNode`, `Transition`, `BpmnExpression`, `FormalExpression`, `ItemDefinition`, `Resource`, `ResourceParameter`, `ResourceAssignmentExpression`, `ResourceParameterBinding`, `ResourceRole`, `HumanPerformer`, `Performer`, `PotentialOwner`
- **Flow**: `FlowElement`, `FlowNode`, `Activity`, `Task`, `ServiceTask`, `SendTask`, `ReceiveTask`, `UserTask`, `ManualTask`, `Script`, `ScriptTask`, `BusinessRuleTask`, `CallActivity`, `SubProcess`, `TransactionSubProcess`, `AdHocSubProcess`, `GlobalTask`, `GlobalUserTask`, `GlobalScriptTask`, `GlobalManualTask`, `GlobalBusinessRuleTask`, `Pool`, `Rendering`, `ResourceRendering`, `RenderingForm`
- **Loop**: `LoopCharacteristics`, `StandardLoopCharacteristics`, `MultiInstanceLoopCharacteristics`, `ComplexBehaviorDefinition`
- **Input/Output**: `InputOutputSpecification`, `DataInput`, `DataOutput`, `InputSet`, `OutputSet`, `DataInputRef`, `DataOutputRef`, `InputOutputBinding`
- **Events**: `Event`, `CatchEvent`, `ThrowEvent`, `StartEvent`, `EndEvent`, `IntermediateCatchEvent`, `IntermediateThrowEvent`, `BoundaryEvent`, `ImplicitThrowEvent`, `EventDefinition`, `MessageEventDefinition`, `TimerEventDefinition`, `SignalEventDefinition`, `ErrorEventDefinition`, `EscalationEventDefinition`, `CompensateEventDefinition`, `ConditionalEventDefinition`, `LinkEventDefinition`, `CancelEventDefinition`, `TerminateEventDefinition`, `DueTimeDuration`
- **Data**: `DataFlowElement`, `DataObject`, `DataObjectReference`, `DataStore`, `DataStoreReference`, `DataState`, `DataElement`, `Property`, `DataAssociation`, `DataInputAssociation`, `DataOutputAssociation`, `Assignment`
- **Flows**: `SequenceFlow`, `MessageFlow`
- **Gateways**: `Gateway`, `ExclusiveGateway`, `InclusiveGateway`, `ParallelGateway`, `EventBasedGateway`, `ComplexGateway`
- **Lanes/Process**: `Lane`, `LaneSet`, `Process`, `Collaboration`
- **Artifacts/Extensions**: `Artifact`, `Association`, `Group`, `TextAnnotation`, `Auditing`, `Monitoring`
- **Services/Messages**: `Interface`, `Operation`, `EndPoint`, `Message`, `Signal`, `Error`, `Escalation`
- **Correlation**: `CorrelationKey`, `CorrelationProperty`, `CorrelationPropertyRetrievalExpression`, `CorrelationSubscription`, `CorrelationPropertyBinding`
- **Categories**: `Category`, `CategoryValue`
- **Conversation/Choreography**: `InteractionNode`, `MessageFlowAssociation`, `Participant`, `ParticipantMultiplicity`, `ParticipantAssociation`, `PartnerEntity`, `PartnerRole`, `ConversationNode`, `Conversation`, `CallConversation`, `GlobalConversation`, `SubConversation`, `ConversationAssociation`, `ConversationLink`, `ChoreographyActivity`, `ChoreographyTask`, `CallChoreography`, `SubChoreography`, `Choreography`, `GlobalChoreographyTask`
- **Diagram**: `BPMNDiagram`, `BPMNPlane`, `BPMNShape`, `BPMNEdge`, `BPMNLabel`
- **Document**: `BPMNDocument`

### `dmn_models.py` (moves to `dmn/models/`)

- **DMN enums**: `DecisionLogicType`
- **Classes**: `InformationRequirement`, `KnowledgeRequirement`, `AuthorityRequirement`, `DecisionService`, `LiteralExpression`, `UnaryTests`, `InputClause`, `OutputClause`, `DecisionRule`, `DecisionTable`, `Decision`, `BusinessKnowledgeModel`, `InputData`, `KnowledgeSource`, `DMNDefinition`, `Binding`, `Invocation`, `ContextEntry`, `Context`, `Relation`, `FormalParameter`, `FunctionDefinition`, `DMNDocument`

### `cmmn_models.py` (moves to `cmmn/models/`)

- **CMMN enums**: `EventListenerType` (already in shared or... actually used by CMMN)
- **Classes**: `PlanItem`, `DiscretionaryItem`, `CaseFileItem`, `CaseTask`, `ProcessTask`, `HumanTask`, `ApplicabilityRule`, `EntryCriterion`, `ExitCriterion`, `Stage`, `Milestone`, `MilestoneKind`, `DecisionTask`, `EventListener`, `Sentry`, `CMMNDefinition`, `CMMNDocument`

### `cep_models.py` (moves to `cep/models/`)

- **CEP enums**: `CEPOperator`
- **Classes**: `EventStream`, `CEPRule`, `CEPDocument`

### `state_machine_models.py` (moves to `state_machine/models/`)

- **State Machine**: `PseudoState`, `Place`, `PnTransition`, `Arc`, `State`, `StateTransition`, `StateInvoke`, `StateMachineRegion`, `StateMachineModel`, `StateMachineDocument`

### `agentic_models.py` (moves to `bpmn/models/`)

- **Agentic BPMN enums**: `ReflectionStrategy`, `CollaborationStrategyType`, `MergeStrategyType`, `VotingRule`, `RoleStrategyType`, `CompetitionRule`
- **Agentic configs**: `VotingConfig`, `RoleConfig`, `CompetitionConfig`, `CollaborationStrategy`, `MergeStrategy`
- **Agentic BPMN classes**: `AgenticTask`, `AgenticMessageFlow`, `DivergingAgenticGateway`, `MergingAgenticGateway`, `AgenticLane`

### `multi_agent_models.py` (moves to `multi_agent/models/`)

- **Multi-agent enum**: `InteractionStrategy`
- **Classes**: `InteractionProtocol`, `InteractionModel`, `MultiAgentInteractionDocument`

## Parser/Writer Moves

All parsers and writers move from `models/parsers/` and `models/writers/` to their respective engine subdirectories as shown in the target structure above. The `bam/` parsers/writers move to `bam/parsers/` and `bam/writers/`.

The `base_osdm_parser.py` and `base_osdm_writer.py` stay in their current locations in `models/parsers/` and `models/writers/` as shared infrastructure.

## Import Style

All imports within `engines/orchestration/` use **relative imports** (e.g., `from ..models.shared_models import BaseElement`). All imports from other engine packages (e.g., `engines/knowledge/`, `engines/agent/`, `tests/`) use absolute imports pointing to the new locations.

## Import Updates

Total: ~188 import sites to update across 3 categories:

### Orchestration internal (175 sites, all relative imports)
Every `from engines.orchestration.models.osdm_models import X` or `from .osdm_models import X` within `engines/orchestration/` must be updated to the appropriate engine-local model, shared_models, agentic_models, or multi_agent_models path.

### Other engines (7 sites)
- `engines/knowledge/` (process_mining, ksdm_models)
- `engines/agent/` (state_machine_agent, models)
- `engines/tools/`

These use absolute imports pointing to the new locations.

### Root tests (6 sites)
- `tests/document/test_bam_*.py` (5 files)

These use absolute imports to the engine-local bam paths.

## No Backward Compatibility

Like Phase 1, backward-compat wrappers will NOT be provided. All imports must be updated to point to the new locations.

## Test Relocation

All test files move from `engines/orchestration/tests/` into engine-specific `tests/` subdirectories:

| Current | Target |
|---------|--------|
| `tests/test_bpmn/` (5 files) | `bpmn/tests/` |
| `tests/test_dmn/` (3 files) | `dmn/tests/` |
| `tests/test_cmmn/` (1 file) | `cmmn/tests/` |
| `tests/test_cep/` (1 file) | `cep/tests/` |
| `tests/test_state_machine/` (3 files) | `state_machine/tests/` |
| `tests/test_bam/` (11 files) | `bam/tests/` |
| `tests/test_core/` (4 files) | Keep in `tests/test_core/` (core is not engine-specific) |
| `tests/test_multi_agent/` (1 file) | Keep in `tests/test_multi_agent/` |
| `tests/test_command.py` | Keep at root tests/ |

## Testing

Run full orchestration test suite from the engine package:
```bash
python3 -m pytest engines/orchestration/ -v
```

Also run dependent engine tests:
```bash
python3 -m pytest engines/knowledge/tests/ -v
python3 -m pytest tests/document/test_bam* -v
```

## Pre-existing Failures

Out of scope for this refactoring:
- `test_bpmn_message_wait_path_persists_waiting_token_and_subscription` (engine completes instead of waiting)
- `tests/agent/interaction/interaction_performance/` (missing fixtures)
