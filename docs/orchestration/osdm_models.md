# OSDM – Orchestration Standard Definition Model

## Complete Reference Documentation

---

## Table of Contents

1. [Supported Standards & Compliance](#part-1-supported-standards--compliance)
   - BPMN 2.0
   - CMMN 1.1
   - DMN 1.x
   - PNML (Petri Net Markup Language)
   - GraphML
   - Complex Event Processing (CEP)
   - UML State Machine
   - SCXML (State Chart XML)
   - Event‑driven Process Chain (EPC)
   - DAG Models (Prefect)
   - XPDL (XML Process Definition Language)
   - BPMN 2.0 Choreography & Collaboration (fully covered)
2. [Conceptual Hierarchy of OSDM](#part-2-osdm-conceptual-hierarchy)
   - Orchestration, Collaboration, Choreography, Coordination
   - State and Transition Concepts
   - Data, Resources, and Expressions
3. [Decision Guide – Which Model to Use](#part-3-decision-guide-which-model-to-use-for-new-designs)
4. [OSDM Design Guide for Multi‑Agent and AI‑Native BPMS](#part-4-osdm-design-guide-for-multi‑agent-and-ai‑native-bpms)
---

## Part 1: Supported Standards & Compliance

---

### 1.1 BPMN 2.0 (Business Process Model and Notation)

**Standard**: OMG BPMN 2.0  
**Description**: The de‑facto standard for business process modelling. BPMN 2.0 defines executable semantics, a rich set of flow elements, data handling, resource assignment, and message correlation.

| Concept / Object | OSDM Class(es) | Mapping / Notes |
|------------------|----------------|-----------------|
| Definitions | `BpmnDefinitions` | Root container for all BPMN elements |
| Process | `Process` | Orchestration of flow elements (private/public) |
| Collaboration | `Collaboration` | Multi‑participant interaction |
| Choreography | `Choreography` (extends `Collaboration`) | Message‑driven interaction between participants |
| Task (abstract) | `Task` | Atomic activity |
| Service Task | `ServiceTask` | Invokes a service (operation) |
| User Task | `UserTask` | Human interaction with rendering and work distribution |
| Manual Task | `ManualTask` | Physical work |
| Script Task | `ScriptTask` | Executes a script in a defined language |
| Business Rule Task | `BusinessRuleTask` | Evaluates business rules |
| Send Task | `SendTask` | Sends a message |
| Receive Task | `ReceiveTask` | Receives a message; can instantiate process |
| Sub‑Process (Embedded) | `SubProcess` | Composite activity |
| Event Sub‑Process | `SubProcess` (triggered_by_event=True) | Triggered by a start event |
| Transaction Sub‑Process | `TransactionSubProcess` | Transactional boundary with compensation |
| Ad‑Hoc Sub‑Process | `AdHocSubProcess` | Unordered activities |
| Call Activity | `CallActivity` | Calls a global Process or Global Task |
| Global Task | `GlobalTask`, `GlobalUserTask`, `GlobalScriptTask`, `GlobalManualTask`, `GlobalBusinessRuleTask` | Reusable task definitions |
| Start Event | `StartEvent` | Process instantiation |
| End Event | `EndEvent` | Process completion |
| Intermediate Catch Event | `IntermediateCatchEvent` | Waits for a trigger |
| Intermediate Throw Event | `IntermediateThrowEvent` | Produces a trigger |
| Boundary Event | `BoundaryEvent` | Attached to an activity (interrupting/non‑interrupting) |
| Exclusive Gateway | `ExclusiveGateway` | XOR split/merge |
| Inclusive Gateway | `InclusiveGateway` | OR split/merge |
| Parallel Gateway | `ParallelGateway` | AND split/merge |
| Event‑Based Gateway | `EventBasedGateway` | Waits for one of several events |
| Complex Gateway | `ComplexGateway` | Custom synchronisation logic |
| Sequence Flow | `SequenceFlow` | Control flow between nodes |
| Message Flow | `MessageFlow` | Communication between participants |
| Lane | `Lane` | Partition within a pool |
| LaneSet | `LaneSet` | Group of lanes |
| Data Object | `DataObject` | Process data |
| Data Store | `DataStore` | Persistent data |
| Data Input / Output | `DataInput`, `DataOutput` | Input/Output specification |
| Input / Output Set | `InputSet`, `OutputSet` | Grouping of data requirements |
| Data Association | `DataInputAssociation`, `DataOutputAssociation` | Data movement |
| Message | `Message` | Communication payload |
| Error | `Error` | Error definition |
| Escalation | `Escalation` | Escalation definition |
| Signal | `Signal` | Broadcast signal |
| Correlation Key | `CorrelationKey` | Conversation correlation |
| Correlation Subscription | `CorrelationSubscription` | Process‑specific correlation |
| Resource | `Resource` | Performer definition |
| Resource Role | `ResourceRole`, `Performer`, `HumanPerformer`, `PotentialOwner` | Role assignment and resource binding |
| Loop Characteristics | `StandardLoopCharacteristics`, `MultiInstanceLoopCharacteristics` | Repetition behaviour |
| Event Definitions | `MessageEventDefinition`, `TimerEventDefinition`, `ErrorEventDefinition`, `SignalEventDefinition`, `EscalationEventDefinition`, `CompensateEventDefinition`, `ConditionalEventDefinition`, `LinkEventDefinition`, `CancelEventDefinition`, `TerminateEventDefinition` | All event trigger types |
| Auditing / Monitoring | `Auditing`, `Monitoring` | Audit and monitoring hooks |
| Conversation | `Conversation`, `SubConversation`, `CallConversation`, `GlobalConversation` | Conversation groupings |
| Participant | `Participant`, `PartnerEntity`, `PartnerRole` | Collaboration participant |
| Choreography Activity | `ChoreographyActivity`, `ChoreographyTask`, `CallChoreography`, `SubChoreography` | Choreography activities |
| Formal Expression | `FormalExpression` | Executable expressions |
| Item Definition | `ItemDefinition` | Data structure reference (links to MSDM) |
| Diagram Interchange | `BPMNDiagram`, `BPMNShape`, `BPMNEdge`, `BPMNLabel` | Visual diagram representation |

**Coverage**: ✅ **Full** – every BPMN 2.0 element is represented with typed fields and proper inheritance.

---

### 1.2 CMMN 1.1 (Case Management Model and Notation)

**Standard**: OMG CMMN 1.1  
**Description**: Models knowledge‑intensive, unpredictable case work. Supports stages, milestones, event listeners, sentries, and planning items.

| Concept / Object | OSDM Class(es) | Mapping / Notes |
|------------------|----------------|-----------------|
| Case | `CMMNDefinition` / `Stage` | Root case definition |
| Stage | `Stage` | Group of tasks/milestones |
| Milestone | `Milestone` | Achievement condition |
| Event Listener | `EventListener` | Trigger on events |
| Sentry | `Sentry` | Entry/exit criterion |
| Plan Item | `PlanItem` | Reusable plan fragment |
| Discretionary Item | `DiscretionaryItem` | Optional planning |
| Case File Item | `CaseFileItem` | Case data element |
| Human Task | `HumanTask` | Manual activity |
| Process Task | `ProcessTask` | Calls a BPMN process |
| Case Task | `CaseTask` | Calls another case |
| Applicability Rule | `ApplicabilityRule` | When a discretionary item can be planned |
| Entry Criterion | `EntryCriterion` | When a plan item can start |
| Exit Criterion | `ExitCriterion` | When a plan item completes |

**Coverage**: ✅ **Full** – all CMMN 1.1 constructs are modelled. Entry/exit criteria link to sentries.

---

### 1.3 DMN 1.x (Decision Model and Notation)

**Standard**: OMG DMN 1.x  
**Description**: Separates decision logic from process flow. Supports decision tables, literal expressions, invocations, and reusable business knowledge models.

| Concept / Object | OSDM Class(es) | Mapping / Notes |
|------------------|----------------|-----------------|
| Decision | `Decision` | Decision node |
| Business Knowledge Model | `BusinessKnowledgeModel` | Reusable logic |
| Input Data | `InputData` | Input to a decision |
| Knowledge Source | `KnowledgeSource` | Authority for decisions |
| Decision Service | `DecisionService` | Group of decisions |
| Information Requirement | `InformationRequirement` | Decision → Input data |
| Knowledge Requirement | `KnowledgeRequirement` | Decision → BKM |
| Authority Requirement | `AuthorityRequirement` | Decision → Knowledge source |
| Decision Logic Types | `DecisionLogicType` enum | Decision table, literal expression, invocation, context, relation, function definition |

**Coverage**: ✅ **Full** – all DMN requirements diagrams and decision logic are supported.

---

### 1.4 PNML (Petri Net Markup Language)

**Standard**: ISO/IEC 15909‑2  
**Description**: Formal modelling of concurrent systems using places, transitions, and arcs. Supports hierarchical nets, inhibitor/reset arcs.

| Concept / Object | OSDM Class(es) | Mapping / Notes |
|------------------|----------------|-----------------|
| Net | `PetriNet` | Top‑level container |
| Page | `Page` | Sub‑net |
| Place | `Place` (extends `StateNode`) | State with tokens |
| Transition | `PnTransition` (extends `Transition`) | Firing rule |
| Arc | `Arc` | Directed edge with weight, inhibitor, reset |
| Reference Place | `ReferencePlace` | Cross‑page link |
| Reference Transition | `ReferenceTransition` | Cross‑page link |
| Tool‑Specific Extensions | `ToolSpecific` | Custom annotations |

**Coverage**: ✅ **Full for P/T nets**. Coloured and timed Petri nets can be represented via `ToolSpecific` extensions; dedicated fields for colours are not yet added.

---

### 1.5 GraphML

**De‑facto standard**: http://graphml.graphdrawing.org  
**Description**: Powerful, extendable graph format. Used for dependency graphs, multi‑agent systems, and any typed graph.

| Concept / Object | OSDM Class(es) | Mapping / Notes |
|------------------|----------------|-----------------|
| Graph | `Graph` | Root graph |
| Node | `GraphNode` (extends `StateNode`) | Typed node (`agent`, `interaction`, …) |
| Edge | `GraphEdge` (extends `Transition`) | Typed, directed edge (`dependency`, `messagePath`, …) |
| Port | `Locator` | Connection point |
| Nesting | `GraphNode.nested_graphs` | Hierarchical graphs |

**Coverage**: ✅ **Full** – multi‑agent orchestration with dependency and message flows.

---

### 1.7 CEP (Complex Event Processing)

**No single standard; industry patterns**  
**Description**: Detects patterns in event streams and triggers actions.

| Concept / Object | OSDM Class(es) | Mapping / Notes |
|------------------|----------------|-----------------|
| Event Stream | `EventStream` | Named stream with attribute types |
| CEP Rule | `CEPRule` | Pattern, window, filter, actions |
| Operator | `CEPRule.operator` (AND, OR, NOT, SEQUENCE, WINDOW, THRESHOLD, ABSENCE) | Pattern logic |
| Window | `CEPRule.window_duration` | Time‑based sliding/tumbling window |
| Filter | `CEPRule.filter_expression` | In‑stream filtering |
| Action | `CEPRule.actions` | List of action identifiers |

**Coverage**: ✅ **Full** – covers all common event patterns. Sliding/tumbling windows are specified via `window_duration` (duration string). Advanced patterns (every‑distinct, logical grouping) can be encoded in `pattern` expression.

---

### 1.8 UML State Machine

**Widely used de facto standard**  
**Description**: Part of UML, models states, transitions, guards, and composite states. Currently not explicitly modelled in OSDM.

| Concept / Object | OSDM Mapping | Notes |
|------------------|--------------|-------|
| State | `StateNode` (abstract) | Could be extended with `name`, `entry/exit` actions |
| Transition | `Transition` (abstract) | Already has source/target, condition, action |
| Guard | `Transition.condition` | String expression |
| Event trigger | Could be stored in `Transition` metadata | Not yet explicit |
| Composite State | `GraphNode.nested_graphs` or dedicated `CompositeState` | Not yet explicit |
| Pseudo‑states (fork, join, choice) | Not modelled | Could use BPMN gateways or dedicated pseudo‑state types |

**Coverage**: ⚠️ **Partial** – the underlying `StateNode`/`Transition` hierarchy is reusable. Full UML state machine support would require additional classes (e.g., `CompositeState`, `PseudoState`). These can be added as an extension.

---

### 1.9 SCXML (State Chart XML)

**W3C Recommendation**  
**Description**: XML language for describing state machines. Very similar to UML state charts.

| Concept / Object | OSDM Mapping | Notes |
|------------------|--------------|-------|
| State | `StateNode` | Basic state representation |
| Transition | `Transition` | Event/condition/action |
| Parallel states | Not modelled | Would need composite state support |
| History states | Not modelled | - |
| Invoke | Not modelled | Could reuse `CallActivity` semantics |

**Coverage**: ⚠️ **Partial** – the core state/transition model is present; SCXML‑specific constructs (parallel, history, invoke) are not yet explicitly modelled.

---

### 1.10 Event‑driven Process Chain (EPC)

**Widely used in ARIS / SAP**  
**Description**: Models processes as chains of events and functions connected by logical connectors.

| Concept / Object | OSDM Mapping | Notes |
|------------------|--------------|-------|
| Event | `Event` (BPMN) | Representable as plain events |
| Function | `Activity` (Task) | Representable as tasks |
| Connector (AND/OR/XOR) | `Gateway` (Parallel/Inclusive/Exclusive) | Direct mapping |
| Process path | `SequenceFlow` | Same semantics |
| Organisational unit | `Lane` / `ResourceRole` | - |

**Coverage**: ✅ **Full (via BPMN subset)** – EPC can be completely represented using BPMN elements already present in OSDM. A dedicated EPC writer could convert to/from EPC notation.

---

### 1.11 AWS Step Functions / Azure Logic Apps

**Proprietary cloud formats**  
**Description**: JSON‑based DAG/state‑machine workflows.
| Concept / Object | OSDM Mapping | Notes |
|------------------|--------------|-------|
| State machine | `ServerlessWorkflow` + `WorkflowState` | Core states map to operation/event/switch/delay |
| Choice state | `WorkflowState` with `state_type=SWITCH` | |
| Parallel state | Not explicitly in ServerlessWorkflow but can be represented via `Graph` (DAG) | |
| Error handling | `retry_policy`, `timeout` in `WorkflowState` | |
| Cloud‑specific resources | Store in annotations or extend `WorkflowState` | Not fully modelled |

**Coverage**: ⚠️ **Partial** – basic state machine constructs are covered. Cloud‑native resource bindings (Lambda ARN, Azure function ID) can be stored as annotations. Full round‑trip would require writer extensions.

---

### 1.12 DAG Models (Airflow, Prefect, etc.)

**Widely used, no single standard**  
**Description**: Directed Acyclic Graphs where nodes are tasks and edges are dependencies.

| Concept / Object | OSDM Mapping | Notes |
|------------------|--------------|-------|
| DAG | `Graph` with `directed=True` | Nodes are tasks, edges are dependencies |
| Task | `GraphNode` with `node_type="task"` | |
| Dependency | `GraphEdge` with `edge_type="dependency"` | |
| Scheduling | Store as annotation or use `DueTimeDuration` | Not explicit |
| Dynamic tasks | Not modelled | Would require runtime extension |

**Coverage**: ✅ **Full for structure** – the DAG topology is perfectly captured. Scheduling and runtime attributes can be added via annotations.

---

### 1.14 XPDL (XML Process Definition Language)

**WfMC standard**  
**Description**: XML‑based process definition interchange format. Very similar to BPMN 2.0 XML.

| Concept / Object | OSDM Mapping | Notes |
|------------------|--------------|-------|
| Process | `Process` | BPMN already covers XPDL semantics |
| Activity | `Activity` | |
| Transition | `SequenceFlow` | |
| Participant | `Participant` | |
| Data Field | `DataObject` / `Property` | |

**Coverage**: ✅ **Full (via BPMN mapping)** – XPDL 2.x aligns closely with BPMN; OSDM’s BPMN model can be used to generate/parse XPDL with an appropriate writer/parser.

---

## Part 2: OSDM Conceptual Hierarchy

### 2.1 Orchestration, Collaboration, Choreography, Coordination

- **Orchestration** – a single `Process` containing flow elements (tasks, gateways, events). It represents an executable workflow under one participant's control. The `Process` class inherits from `RootElement` and can be executed or non‑executable.
- **Collaboration** – multiple `Participant`s, each optionally referencing a `Process`. Communication happens via `MessageFlow`. A Collaboration can contain Choreographies through `choreography_refs`.
- **Choreography** – extends `Collaboration` and adds `ChoreographyActivity` nodes. Each choreography activity involves two or more participants and an initiating participant. Message exchanges are modelled without a central orchestrator.
- **Conversation** – a logical grouping of message flows. `ConversationNode` (and its subtypes) allow hierarchical grouping and correlation.
- **Coordination** – the distributed interaction captured by `MessageFlow`, `CorrelationKey`, and `ConversationNode`. Correlations allow messages to be routed to the correct process instance based on data keys.

### 2.2 State and Transition Concepts

- **`StateNode`** (abstract) – superclass for any node that holds state. Contains incoming/outgoing transition IDs. Used by `Place` (Petri net) and `GraphNode` (GraphML). Can be reused for UML state machines.
- **`Transition`** (abstract) – superclass for any directed edge. Contains `source_id`, `target_id`, `condition` (guard), and `action`. Used by `SequenceFlow`, `MessageFlow`, `Arc`, `PnTransition`, and `GraphEdge`.
- **`FlowNode`** – BPMN‑specific state/transition node that can be connected by `SequenceFlow`. It adds `incoming`/`outgoing` lists of `SequenceFlow` references.
- **`Event`** – specialisation of `FlowNode` that can catch/throw triggers. Event definitions determine the trigger type.

### 2.3 Data, Resources, and Expressions

- **Data** – modelled via `ItemDefinition` (references an MSDM entity), `DataObject`, `DataStore`, and `DataInput/Output`. Data associations (`DataInputAssociation`, `DataOutputAssociation`) define data movement between flow elements.
- **Resources** – actors (`Resource`, `ResourceRole`, `ResourceParameter`) that can be assigned to activities. Roles can be human performers, potential owners, cost centres, etc. Resource parameters allow runtime queries (e.g., findByRole).
- **Expressions** – `FormalExpression` captures executable conditions (e.g., on sequence flows) and assignments. The expression language defaults to XPath but can be overridden.
- **Decisions** – DMN decisions and business knowledge models can be referenced from BPMN tasks (via `BusinessRuleTask`) or used standalone.

---

## Part 3: Decision Guide: Which Model to Use for new designs

---

| Your core requirement | Recommended model | Why |
|-----------------------|-------------------|-----|
| Executable business process with human/service tasks, gateways, events, data | **BPMN 2.0** | Richest workflow semantics; built‑in scheduling (Timers) and dynamic parallelism (Multi‑Instance). |
| Multi‑party interaction without central orchestrator | **BPMN Choreography** | Observes message exchanges, not owned by any participant. |
| Unpredictable, human‑centric case work | **CMMN** | Discretionary items, sentries, planning tables – unique to case management. |
| Decision logic separated from process flow | **DMN** | Decision tables, BKMs, and the DRD are unique to DMN. |
| Formal mathematical analysis (liveness, reachability, deadlock) | **Petri nets (PNML)** | Only formalism that provides place invariants and coverability graphs. |
| Reactive, state‑based design (UI, protocols) | **UML State Machine** | Hierarchy, history, orthogonal regions – the most mature state‑chart language. |
| Must deploy natively to **AWS Step Functions** or **Azure Logic Apps** | **CloudWorkflowModel** | 1:1 mapping to cloud resources, catch/retry rules. |
| Must deploy natively to **Airflow** or **Prefect** | **DAGModel** | Native scheduling and dynamic task generation, platform‑specific operators. |
| Multi‑agent interaction protocols (broadcast, debate, etc.) | **InteractionModel** | No existing standard; our model captures conversation patterns explicitly. |
| Any other custom typed graph (dependencies, topologies) | **GraphML** | Maximum flexibility without execution semantics. |

This table gives clear, non‑overlapping reasons – each model is the only possible choice when that specific condition holds.

---

We'll now produce a comprehensive **Design Guide** for using OSDM in a multi‑agent or AI‑native BPMS. This guide explains the purpose of every model component, how it relates to agents/AI, and when to use it.

---
## Part 4: OSDM Design Guide for Multi‑Agent and AI‑Native BPMS

### 1. Introduction
OSDM is a unified model that captures workflows, state machines, cases, decisions, event processing, and multi‑agent interactions. In an **AI‑native BPMS**, you often have **intelligent agents** performing tasks, **human collaboration**, **decision services**, and **reactive event handling**. This guide shows how each OSDM component maps to real‑world requirements and how they work together.

---

### 2. Process Orchestration – BPMN 2.0
**What it models**:  
Sequential or parallel execution of tasks, gateways, events, data, and resources. BPMN 2.0 is the richest workflow language.

**Role in a multi‑agent system**:  
- A **Process** can be executed by a mix of human performers, AI agents, and services.  
- **ServiceTask** / **SendTask** / **ReceiveTask** can invoke external AI services or message other agents.  
- **ScriptTask** can run lightweight agent logic.  
- **BusinessRuleTask** can delegate to a DMN decision service.  
- **Multi‑Instance** activities handle data‑parallel pipelines (e.g., processing a batch of claims).  

**When to choose**:  
- When the primary requirement is a **structured, executable workflow** with branching, merging, and exception handling.  
- When you need to integrate with existing BPMN tools or human tasks.

**Why not just use BPMN for everything?**  
BPMN cannot model **unpredictable human‑centric case work** (CMMN) or **state‑oriented reactive behaviour** (UML/SCXML) without unnatural workarounds.

---

### 3. Collaboration and Choreography
**What they model**:  
- **Collaboration** shows how multiple participants (agents, people, systems) exchange messages.  
- **Choreography** models the **observable message exchanges** without a central orchestrator.

**Role in a multi‑agent system**:  
- **Collaboration** lets you define which agent participates in a process, and how they communicate (MessageFlows).  
- **Choreography** is perfect for **agent interaction contracts** – e.g., an auction protocol – where no single agent controls the flow.

**When to choose**:  
- When you need to define **inter‑agent communication** at the business level.  
- Choreography is the only OSDM component that captures **multi‑party contracts** without an orchestrator.

---

### 4. State Machines – UML / SCXML
**What they model**:  
States, transitions, events, guards, and actions. Supports hierarchy, history, orthogonal regions.

**Role in a multi‑agent system**:  
- Define the **internal life‑cycle of an agent** (e.g., idle, negotiating, committed).  
- Model **protocols** like FIPA contract‑net or a custom dialogue flow.  
- Reactive behaviour – change state based on events from the environment.

**When to choose**:  
- When the primary concern is **statefull, reactive behaviour**.  
- When you need to generate code for an agent’s state machine directly.

---

### 5. Petri Nets
**What they model**:  
Places, transitions, tokens. Formal mathematical analysis of concurrency, liveness, reachability.

**Role in a multi‑agent system**:  
- Rarely used directly by agent developers, but useful for **verification** of critical interaction protocols.  
- Can be converted to a state machine for execution.

**When to choose**:  
- Only when formal verification of the agent system is required (e.g., safety‑critical applications).

---

### 6. Case Management – CMMN
**What it models**:  
Unpredictable, human‑centric case work. Stages, tasks, milestones, sentries, and planning rules.

**Role in a multi‑agent system**:  
- Models a **case** handled by a team of agents and humans, where the sequence of tasks is not known in advance.  
- Agents can decide to plan discretionary items based on their own reasoning.  
- **Sentries** define when a task becomes available or a milestone is achieved – perfect for event‑driven agent activation.

**Interaction with Interaction Strategies**:  
CMMN does **not** prescribe *how* agents communicate – it only defines *when* they may act. The actual message exchange pattern (e.g., broadcast, coordinator) is defined by an **InteractionModel** that can be attached to the case.

**When to choose**:  
- When the workflow is **knowledge‑intensive** and cannot be fully predetermined.  
- When agents (or humans) need the flexibility to decide which tasks to perform next.

---

### 7. Decision Management – DMN
**What it models**:  
Decision logic (tables, expressions, invocations) separated from process flow. Business Knowledge Models (BKMs) for reusable logic.

**Role in a multi‑agent system**:  
- **Agent decision‑making** – an agent can call a DMN decision to evaluate rules, score options, or classify inputs.  
- Decision services can be invoked from BPMN `BusinessRuleTask` or directly by an agent’s state machine.

**When to choose**:  
- When you have complex, often‑changing business rules that should be maintained independently of agent logic.

---

### 8. Complex Event Processing – CEP
**What it models**:  
Event streams, pattern detection, windows, filters, and actions.

**Role in a multi‑agent system**:  
- **Sense‑respond** architectures – agents react to patterns over time (e.g., stock price surge → alert).  
- Can trigger agent actions or state transitions.

**When to choose**:  
- When the system must react to **temporal patterns** across multiple event sources.

---

### 9. Multi‑Agent Interaction Strategies
**What it models**:  
Communication protocols like broadcast, debate, coordinator, round‑robin, self‑refine, group chat.

**Role in a multi‑agent system**:  
- These are the **conversation patterns** that govern how agents exchange messages.  
- An `InteractionModel` can be referenced from a BPMN `Collaboration`, a CMMN case, or a state machine action.

**When to choose**:  
- When you want to standardise how your agents talk to each other, independent of the internal logic of each agent.

---

### 10. GraphML for Dependency Graphs
**What it models**:  
Typed, directed graphs with ports and nesting. Nodes can be anything; edges define relationships.

**Role in a multi‑agent system**:  
- **Agent interaction topology** – who can talk to whom.  
- **Dependency graphs** for task planning (e.g., Airflow‑style DAGs).  
- Can represent a **multi‑agent organisational structure**.

**When to choose**:  
- When you need maximum flexibility and your main concern is the structure of relationships rather than execution semantics.

---

### 12. Putting It All Together
In a full AI‑native BPMS built on OSDM, you might:

1. **Define each agent’s internal behaviour** with a `StateMachineModel`.  
2. **Model the business process** that invokes agents as `Process` (BPMN).  
3. **Capture decision logic** used by agents in `DMNDefinition`.  
4. **Define agent interaction protocols** with `InteractionModel`.  
5. **Use CMMN** for human‑in‑the‑loop cases where the flow is unpredictable.  
6. **React to real‑time events** with `CEPDefinition`.  
7. **Verify critical protocols** with Petri nets.  
8. **Visualise agent dependencies** with GraphML.  

All these components live inside a single `OSDMModel`, allowing a unified toolchain to manage the entire system.

---

This guide should help you select the right OSDM component for every part of your multi‑agent or AI‑native BPMS.