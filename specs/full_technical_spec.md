# Reverse-Engineered Specification: Multi-Agent Infra

**Date:** 2026-06-18
**Source:** https://github.com/anomalyco/opencode/blob/master/specs/multi-agent-infra

---

## Overview

A Python-based multi-agent orchestration platform that executes **workflow DAGs** (BPMN/CMMN/DMN/State Machines/CEP), coordinates **multi-agent interactions** (debate, group-chat, round-robin, ensemble, self-refine, broadcast), provides a **tool layer** (37+ executors: LLM, RAG, MCP, DB, file, cache, code execution, etc.), processes **documents** across 11 standards (USDM/PSDM/ESDM/DSDM/CSDM/MSDM/SSDM/TSDM/OSDM/KSDM/LSDM + BAM), supports **knowledge extraction** (semantic graphs, ML mining, BI aggregation, process mining, RAG), and provides **communication, storage, memory, session, observability, and TTS** infrastructure.

### Architecture Layers

```
Orchestration Engine (BPMN/CMMN/DMN/State Machine/CEP execution)
       │
       ▼
  Orchestration Tasks / Task Executor
       │
       ▼
Agent Layer (AgentRegistry → AgentAdapter → Agent → AgentOutput)
       │
       ▼
Tool Layer (37+ executors: LLM, RAG, MCP, DB, File, Cache, etc.)
       │
       ▼
Knowledge Layer (SemanticGraph, MLMining, BIAggregation, ProcessMining, RAG, Query)
       │
       ▼
Document Layer (11 standards for parse/write of all formats)
       │
       ▼
Storage/Communication/Memory/Observability Layer
```

### High-Level Data Flow

```
User Input → OrchestrationEngine → Workflow DAG
  → TaskExecutor → AgentTask/InteractionTask/ToolTask/SubWorkflowTask
    → AgentRegistry → AgentAdapter → Agent → AgentOutput
      → Tools (LLM, RAG, MCP, etc.)
```

---

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Language | Python | 3.11+ |
| Runtime | Async/Await (asyncio) | — |
| Workflow Standards | BPMN 2.0, CMMN 1.1, DMN 1.x, UML State Machines, CEP, SCXML, EPC, XPDL, Prefect DAG, PNML, GraphML | — |
| Multi-Agent | AutoGen (Microsoft), Native backends, Google A2A, FIPA ACL | 0.7.5 / 0.10.0 |
| LLM | OpenAI, LiteLLM (100+ providers), Anthropic, Gemini | — |
| RAG | LlamaIndex 0.14.16, LangChain 1.2.12, LangGraph 1.1.2 | — |
| Vector DBs | ChromaDB, FAISS, Qdrant, Pinecone, Weaviate | — |
| ORM | SQLAlchemy 2.0+ async | 2.0.48 |
| Migrations | Alembic | 1.18.4 |
| Models | Pydantic v2 | 2.12.5 |
| Validation | mypy, ruff | — |
| Message Buses | InMemory, Redis, Kafka, RabbitMQ, Priority, Topic, Request-Reply, Durable | — |
| Storage | SQLite, PostgreSQL, InfluxDB, Redis, Neo4j, S3/MinIO, local filesystem | — |
| Schema Standards | OSDM (BPMN/CMMN/DMN/SM), USDM, PSDM, ESDM, DSDM, CSDM, MSDM, SSDM, TSDM, KSDM, LSDM, BAM | — |
| ML/AI | PyTorch, scikit-learn, ONNX Runtime, transformers, numpy | — |
| Graph | RDF (Turtle), RML, NetworkX, Neo4j | — |
| Observability | OpenTelemetry, AgentOps, MLflow, Datadog, WandB, LangWatch, Freeplay, FutureAGI, Arize, Weave, Grafana | — |
| Messaging | RabbitMQ (aio-pika), Kafka (aiokafka), Redis Pub/Sub, AMQP | — |
| Document Processing | PDF (PyMuPDF, pdfplumber, camelot), DOCX (python-docx), XLSX (openpyxl), Images (Pillow, OpenCV), OCR (pytesseract) | — |
| MCP | MCP SDK (JSON-RPC 2.0 over stdio), 5 built-in server definitions | — |
| Testing | pytest (asyncio_mode=auto) | 9.0.2 |
| Distribution | pyproject.toml, requirements.txt | — |

---

## Directory Structure

```
multi_agent_infra/
├── engines/                          # All engine packages
│   ├── _types.py                     # Shared type aliases
│   ├── __init__.py                   # Empty
│   ├── orchestration/                # Workflow DAG execution engine
│   ├── interaction/                  # Thin re-export facade
│   ├── agent/                        # Agent definitions, registry, mediators
│   ├── tools/                        # Tool layer (37+ executors)
│   ├── document/                     # Document parsing/writing (11 standards)
│   ├── knowledge/                    # Knowledge extraction engines
│   ├── communication/                # Message buses, service consumption/exposure
│   ├── storage/                      # Storage backends (9 categories)
│   ├── session/                      # Session management
│   ├── memory/                       # Memory management
│   ├── observability/                # Distributed tracing/metrics
│   └── tts/                          # Text-to-speech
├── config/                           # Application configuration
├── migrations/                       # Alembic DB migrations
├── data/                             # Data directories
├── tools/                            # Utility scripts
├── docs/                             # Documentation
├── pyproject.toml                    # Project config
├── requirements.txt                  # Dependencies
├── alembic.ini                       # Alembic config
└── AGENTS.md                         # Agent instructions
```

---

## Engine-by-Engine Specification

---

### 1. ORCHESTRATION ENGINE (`engines/orchestration/`)

**Purpose:** Core workflow execution runtime supporting BPMN 2.0, CMMN 1.1, DMN 1.x, UML State Machines, CEP, and multi-agent interactions.

**Size:** 50+ files across BPMN, CMMN, DMN, CEP, State Machine, forms, deployment, monitoring, validation, multi-agent, persistence, runtime, and core subdirectories.

#### Core Engine (`core/`)

**OrchestrationEngine** (`core/engine.py:116`)
- Facade pattern — composes lifecycle, deployment, instance, recovery, and definition services
- State machine: STOPPED → STARTING → RUNNING → PAUSED | STOPPING → STOPPED | ERROR
- Key sub-components:
  - `InstanceManager` — manages process instance lifecycle, state transitions, hierarchy
  - `TokenManager` — BPMN token-based execution (parallel gateways, joins, forks)
  - `EventBus` — internal pub/sub for engine events
  - `CorrelationEngine` — message/event correlation for BPMN message/event activities
  - `ContextManager` — hierarchical variable scopes with MSDM schema binding
  - `TransactionManager` — transaction boundaries for compensation
  - `Scheduler` — timed/scheduled job execution
  - `StateManager` — persistence of engine/runtime state

**EngineConfig** (`core/engine.py:87`):
- `max_concurrent_instances: int = 1000`
- `enable_persistence: bool = True`
- `enable_bpmn/cmmn/dmn/state_machine/cep/multi_agent/bam: bool = True`
- `deployment_mode: DeploymentMode = VERSION` (REPLACE | VERSION | PARALLEL)
- `history_level: str = "full"`
- `agent_timeout_seconds: int = 300`
- `bam_metric_buffer_size: int = 100000`
- `metrics_interval_seconds: int = 60`

**ProcessInstance** (`core/instance.py:140`):
- Fields: `id`, `definition_id/key/version`, `business_key`, `tenant_id`, `state` (InstanceState enum), `instance_type`, `parent_id`, `root_instance_id`, `super_instance_id`, `variables`, `active_activities`, `completed_activities`, `incidents`, `execution_path`
- InstanceState: `ACTIVE | SUSPENDED | COMPLETED | TERMINATED | FAILED | DRAFT | CLOSED | COMPENSATING | MIGRATING`
- InstanceType: `ROOT | SUBPROCESS | CALL_ACTIVITY | EVENT_SUBPROCESS | TRANSACTION`
- Methods: `set_variable/get_variable/has_variable/remove_variable`, state transitions, activity tracking, incident management, DSDM serialization

**ProcessDefinition** (`core/_definition_models.py:15`):
- Fields: `id`, `key`, `name`, `version`, `deployment_id`, `resource_name`, `definition_type`, `definition_xml`, `diagram_resource_name`, `has_start_form_key`, `is_suspended`, `tenant_id`, `version_tag`, `history_time_to_live`, `deployed_at`, `metadata`

**ExecutionContext** (`core/context.py:170`):
- Hierarchical variable scopes: `GLOBAL → PROCESS → SUBPROCESS → ACTIVITY → LOCAL`
- Variable visibility: `PUBLIC | PROTECTED | PRIVATE`
- MSDM schema binding for type validation (`Variable.bind_schema(entity)`)
- DSDM serialization support
- Parent-child tree with propagation/copy semantics

**Deployment** (`core/_definition_models.py:37`):
- `deploy(name, resources_dict, source, tenant_id)` → parses definitions, stores them, publishes DEPLOYMENT_CREATED event
- Supports resource detection by name/extension → dispatches to correct BPMN/CMMN/DMN/SM/CEP parser

**Runtime Services** (`runtime/`):
- `RuntimeExecutor` — async/sync execution wrapper, `ExecutionOutcome(result, success, error)`
- `StateManager` — persistence of runtime state
- `VariableManager` — variable read/write with persistence
- `IncidentManager` — incident (failed job, external task, etc.) creation/resolution
- `RateLimiter` — throttling
- `TimerManager` — timer management for BPMN timer events
- `CircuitBreakerRegistry` + `RetryHandler` + `RetryConfig` — resilience patterns
- `ExternalTaskManager` + `ExternalTaskWorker` — external task pattern
- `TaskListenerManager` + `ExecutionListenerManager` — lifecycle hooks
- `StateSnapshotManager` + `CheckpointConfig` — checkpointing (30s interval, on activity start/complete/error)
- `ProcessInstanceMigrator` + `BatchOperationManager` — instance migration between versions
- `TenantManager` — multi-tenancy
- `OsdmSerializer` + `OsdmDeserializer` — OSDM serialization round-trip
- `AsyncContinuation` — continuation tokens for long-running waits

#### BPMN Execution (`bpmn/`)

**BPMNProcessExecutor** (`bpmn/process_executor.py:66`):
- Implements BPMN 2.0 Annex A execution semantics
- Token-based traversal with proper gateway join/fork synchronization
- Gateway types: exclusive (XOR), parallel (AND), inclusive (OR), event-based, complex
- Activity handler delegates to specialized handlers: task, service task, user task, send/receive task, business rule task, script task, sub-process, call activity, event sub-process (interrupting/non-interrupting)
- Boundary event activation (timer, message, error, signal, escalation, compensation)
- Transaction sub-process handling with compensation
- Ad-hoc sub-process completion condition evaluation
- Event sub-process (interrupting and non-interrupting)
- Correlation keys for message/event subscriptions
- Loop characteristics (standard, multi-instance parallel/sequential)
- **Guard:** max 200 steps per execution path (loop prevention)

**Activity Handler** — delegates to:
- Task handler (user, service, send, receive, business rule, script)
- Gateway handler (parallel, exclusive, inclusive, event-based, complex)
- Event handler (start, intermediate, boundary, end events)
- Sub-process manager (embedded, call activity, event sub-process, transaction, ad-hoc)
- Loop handler (standard loop, multi-instance parallel/sequential)
- Choreography handler (BPMN choreography diagram execution)
- Collaboration handler (message flow between pools/participants)
- Data object handler (data associations, data stores)
- Pool/lane executor (lanes, participant bands)
- Conversation executor (BPMN conversation diagrams)

**Models** (`bpmn/models/`):
- Full OSDM BPMN model: Process, Activity, Task (ServiceTask, UserTask, SendTask, ReceiveTask, BusinessRuleTask, ScriptTask), Event (StartEvent, EndEvent, IntermediateCatchEvent, IntermediateThrowEvent, BoundaryEvent), Gateway (ExclusiveGateway, ParallelGateway, InclusiveGateway, EventBasedGateway, ComplexGateway), SequenceFlow, MessageFlow, DataObject, DataStore, Resource, Lane, Participant, Collaboration, Choreography, Conversation, CorrelationKey, Error, Escalation, Signal, Timer, Compensate, Link, Terminate, Conditional

**Parsers/Writers** (`bpmn/parsers/`, `bpmn/writers/`):
- OSDM JSON/XML parsers and writers for BPMN
- BPMN 2.0 XML schema compliance

#### CMMN Case Management (`cmmn/`):
- CMMN 1.1 execution: Case, Stage, PlanItem, Task, HumanTask, ProcessTask, CaseTask, DecisionTask, Milestone, Sentry (entry/exit criteria), Criterion (OnPart), PlanItemDefinition, CaseFileItem, DiscretionaryItem
- State transitions: Case lifecycle (DRAFT → ACTIVE → COMPLETED → CLOSED)
- Plan item states: AVAILABLE → ENABLED → DISABLED → ACTIVE → COMPLETED → TERMINATED
- Sentry evaluation rules (AND/OR semantics)

#### DMN Decision Engine (`dmn/`):
- DMN 1.x evaluation: Decision, DecisionTable, InputClause, OutputClause, Rule, Expression, LiteralExpression, Context, Invocation, FunctionDefinition, Relation, List, BoxedExpression
- FEEL expression evaluator
- Hit policies: UNIQUE, FIRST, PRIORITY, ANY, COLLECT (SUM/COUNT/MIN/MAX), RULE ORDER, OUTPUT ORDER

#### State Machine (`state_machine/`):
- UML State Machine execution: State, PseudoState (initial/deepHistory/shallowHistory/join/fork/junction/choice/entryPoint/exitPoint/terminate), Transition, Region, Trigger, Guard, Effect, Entry/Exit/Do activities
- State entry/exit action execution
- Transition guard condition evaluation via `safe_expr_eval()` (AST-based whitelist)
- PseudoStateKind: INITIAL, DEEP_HISTORY, SHALLOW_HISTORY, JOIN, FORK, JUNCTION, CHOICE, ENTRY_POINT, EXIT_POINT, TERMINATE

#### CEP (Complex Event Processing) (`cep/`):
- Event stream processing: EventPattern, EventType, EventCorrelation, Window (time/tumbling/sliding), Filter, Transformation, Action
- Pattern matching with temporal constraints
- Event correlation across streams
- Buffer size config (default: 10,000 events)

#### Multi-Agent (`multi_agent/`):
- `MultiAgentEngine` — coordinates agent execution within orchestration workflows
- `InteractionHandler` — manages turn-taking, message routing
- `AgentExecutor` — agent lifecycle management with retry (default 3)
- `MessageRouter` — message routing with `RoutingResult`
- `InteractionStrategy` enum: `BROADCAST | DEBATE | COORDINATOR | ENSEMBLE | ROUND_ROBIN | SELF_REFINE | GROUP_CHAT`
- `InteractionProtocol` dataclass: strategy + participants + message_pattern + coordinator_ref
- `AgentState` enum: `IDLE | ACTIVE | WAITING | COMPLETED | FAILED`

#### BAM (Business Activity Monitoring) (`bam/`):
- Real-time metrics collection and dashboard
- KPI tracking, bottleneck detection, process heatmap
- Alerting with thresholds
- Persistence and predictive analytics
- Buffer size config (default: 100,000 metrics)

#### Expression Engine (`expression/`):
- FEEL expression evaluator (DMN-friendly)
- Python expression evaluator (PythonEvaluator with EvaluationContext)
- Used for gateway condition evaluation, script tasks

#### Forms (`forms/`):
- Form engine for user task forms (start form, task form)
- Form definition, rendering, validation

#### Monitoring (`monitoring/`):
- `MetricsCollector` — instance/activity/incident metrics
- `ProcessHeatmap` — hot-spot analysis
- `BottleneckDetection` — identify slow activities
- `KpiTracker` — key performance indicators

#### Validation (`validation/`):
- `BpmnOsdmValidator`, `CmmnOsdmValidator`, `DmnOsdmValidator`, `StateMachineOsdmValidator`
- BPMN/CMMN/OSDM compliance validation

#### Persistence (`persistence/`):
- `DefinitionRepository`, `InstanceRepository`, `TokenRepository`, `VariableRepository`, `EventRepository`, `HistoryRepository`, `AuditLog`
- Repository pattern for instance/definition/token/event persistence

#### Integration (`integration/`):
- Integration adapters for external systems (HTTP, gRPC, etc.)

#### OSDM Models (`models/`):
- `shared_models.py` — shared enums (ParticipantBandKind, TimerCalculationType, PseudoStateKind, etc.), base elements (BaseElement, RootElement), diagram interchange (Bounds, Shape, Edge), cloud extensions (CloudResourceBinding, ErrorHandlingConfig, RetryConfig, TimeoutConfig)
- `BaseOSDMDocument` — root document with root_elements, diagrams, extensions
- `OSDMModel` — container for processes, collaborations, choreographies, global_tasks, cmmn_definitions, state_machines, dmn_definitions, cep_definitions, interaction_models + MSDM/SSDM/TSDM refs
- `base_osdm_parser.py` / `base_osdm_writer.py` — abstract base classes

---

### 2. INTERACTION ENGINE (`engines/interaction/`)

**Purpose:** Ultra-thin re-export facade. ~2 files, no original implementation.

**Re-exports:**
- From `engines.agent.strategies` — all 7 strategy classes, `InteractionStrategy` ABC, `InteractionStrategyRegistry`
- From `engines.agent.interaction_models` — `InteractionRequest`, `InteractionResult`
- From `engines.communication.buses.message_models` — `AgentMessage`
- From `.mediator` — `AgentMediator`, `InteractionMediator` (alias)

---

### 3. AGENT ENGINE (`engines/agent/`)

**Purpose:** Agent registry, adapter pattern, interaction strategies, skill system, protocol adapters, plugin system, ~200+ content agent models.

#### Core Models (`models.py`):

**AgentInput** (line 54):
- `agent_name: str`, `message: str | None`, `payload: RawData`, `context: Metadata`, `metadata: Metadata`

**AgentOutput** (line 70):
- `agent_id: str | None`, `agent_name: str`, `message: str | None`, `payload: RawData`, `error: str | None`, `metadata: Metadata`

**AgentDefinition** (line 21):
- `name`, `description`, `type: AgentType` (INTERACTION | SKILL | STATE_MACHINE), `skill_id`, `state_machine`, `input_schema`, `output_schema`, `output_key`, `config`

**AgentType** enum (line 15):
- `INTERACTION = "interaction_agent"`, `SKILL = "skill_call_agent"`, `STATE_MACHINE = "state_machine_agent"`

**AgentExecutionRecord** (line 87):
- `execution_id`, `agent_name`, `agent_version`, `input_payload`, `output_payload`, `status`, `execution_time_ms`, `error_message`, `timestamp`

**AgentExecutionRecord** (line 87) - used for logging every execution.

**InteractionRequest** (`interaction_models.py:18`):
- `workflow_id: str = uuid4()`, `scenario: str = "pipeline"`, `agents: list[Any]`, `context: FeelContext`, `metadata: Metadata`

**InteractionResult** (`interaction_models.py:33`):
- `workflow_id`, `scenario`, `results: list[AgentOutput]`, `success: bool = True`, `final_context: FeelContext`, `backend_used: str = "native"`, `status: "success"|"partial"|"failed"`, `started_at`, `completed_at`, `notes: list[str]`, `metadata`

#### AgentRegistry (`agent_registry.py`):
- Agent methods: `register()`, `get()`, `run()`, `list_agents()`
- Strategy methods: `register_strategy()`, `get_strategy()`, `require_strategy()`, `list_strategies()`, `unregister_strategy()`
- Auto-injects shared `vector_db` and `storage` into registered agents

#### AgentMediator (`agent_mediator.py`):
- `send(sender, recipient, input_data)` — direct agent communication (protocol or registry)
- `broadcast(sender, input_data)` — send to all agents
- `execute_strategy(scenario, request)` — creates NativeOrchestrationBackend and delegates

#### BaseAgent (`base_agents/base_agent.py:27`):
- Generic: `BaseAgent[TInput, TOutput]` where TInput bound to AgentInput, TOutput bound to AgentOutput
- Entry point: `async run(input_data) -> TOutput`
- Lifecycle: validate_input → before_agent callbacks → execute → validate_output → log_execution → after_agent callbacks
- Callbacks can short-circuit execution (before_agent returns non-None)
- Sync wrapper: `run_sync()` — creates event loop if needed
- Auto-converts dicts/Pydantic models to TInput/TOutput

#### Concrete Agent Types:
- **InteractionAgent** — wraps NativeOrchestrationBackend, converts dict→InteractionRequest→backend.execute()
- **SkillAgent** (`SkillAgentInput/Output`) — single skill execution via BatchSkillExecutor or StepWiseSkillExecutor
- **StateMachineAgent** (`StateMachineAgentInput/Output`) — state machine orchestration with transition guard evaluation via `safe_expr_eval()`
- **RoutedAgent** — dispatch to sub-agents via routing function, with failover (excludes failed keys from re-selection)
- **StreamingAgent** — wraps another agent, provides token-by-token streaming via `run_streaming(token_separator=" ")`
- **TextRewriterAgent** — grade-level text adaptation via LLM, with fallback truncation

#### Interaction Strategies (7 total):

All extend `InteractionStrategy(ABC)` with:
- `__init__(agent_registry, message_bus=None, storage=None)`
- `async execute(request: InteractionRequest) -> InteractionResult`
- `_run_agent(agent_name, agent_id, context, payload, message) -> AgentOutput` — catches exceptions, returns error AgentOutput

| Strategy | File | Scenario | Behavior |
|----------|------|----------|----------|
| **BroadcastStrategy** | `broadcast_strategy.py` | `"broadcast"` | `asyncio.gather` all agents concurrently. Aggregation: `merge` (dict by name), `list`, `vote` (most frequent message). |
| **CoordinatorStrategy** | `coordinator_strategy.py` | `"manager"` | Sequential workers with optional validation + aggregation agents. |
| **DebateStrategy** | `debate_strategy.py` | `"debate"` | Proposer→Critic rounds, stops when critic `approved=True`. Default max_rounds=5. |
| **EnsembleStrategy** | `ensemble_strategy.py` | `"ensemble"` | All agents vote, majority wins. Optional custom aggregator agent. Vote key configurable. |
| **GroupChatStrategy** | `group_chat_strategy.py` | `"group_chat"` | Round-robin with message history. Supports `stop_on_role`, `stop_on_done`. Default max_rounds=8. |
| **RoundRobinStrategy** | `round_robin_strategy.py` | `"round_robin"` | Configurable rounds (default 1). Optional `stop_on_failure`. |
| **SelfRefineStrategy** | `self_refine_strategy.py` | `"self_refine"` | Generator→Critic→Refiner loop. Default max_refinements=3, quality_threshold=0.9. |

**InteractionStrategyRegistry** — thread-safe (RLock), `register/unregister/get/require/list_scenarios/all_strategies`

#### Orchestration Backends (backends/):

- **NativeOrchestrationBackend** (`native_backend.py`): maps scenario name to strategy class, instantiates, executes. Strategy map: broadcast, round_robin, group_chat, debate, ensemble, coordinator, self_refine
- **AutoGenOrchestrationBackend** (`autogen_backend.py`): wraps Microsoft AutoGen GroupChat. Falls back to Native on failure or missing import.

#### Agent Protocols (`protocols.py`):

- **AgentProtocol** ABC: `connect()`, `send_message()`, `receive_message()`, `disconnect()`
- **InMemoryProtocol**: in-process mediated communication via AgentMediator.send()
- **A2AProtocol**: Google Agent-to-Agent via `aiohttp` HTTP+JSON-RPC 2.0 (`agents.send` method)
- **FIPAProtocol**: FIPA ACL with handler fallback

#### Skill System (`skill/`):

- **SkillLoader** — scans directory recursively for SKILL.md files, parses YAML frontmatter
- **Skill** model: `name`, `description`, `version`, `author`, `tags`, `inputs`, `outputs`, `references`, `content`, `steps`, `execution_mode`
- **SkillInput/SkillOutput/SkillStep** — input/output schema definitions
- **BatchSkillExecutor** — single prompt with structured output (falls back to generate_text + JSON parse)
- **StepWiseSkillExecutor** — sequential step execution, accumulating context
- **LLMClient** ABC: `generate_structured_output(prompt, schema)`, `generate_text(prompt)`
- **BaseSkillExecutor** — Template Method pattern: `_build_prompt()`, `_call_llm()`
- **MCPAdapter** — adapter pattern wrapping MCPClient

#### MCP Client (`skill/mcp_client.py`):
- JSON-RPC 2.0 over stdio subprocess
- `connect/disconnect/list_tools/call_tool`
- Uses `mcp` Python SDK with graceful import fallback

#### Callback System (`callbacks.py`):
- `CallbackContext`: `agent_name`, `agent_id`, `session`, `session_service`, `invocation_id`, `state`
- `LlmRequest` / `LlmResponse` — model call interception
- `ToolContext(CallbackContext)` — tool call interception
- `CallbackRegistry` — lists of before/after hooks for agent, model, tool
- 6 callback types: `BeforeAgent`, `AfterAgent`, `BeforeModel`, `AfterModel`, `BeforeTool`, `AfterTool`

#### Plugin System (`plugins.py`):
- `AgentPlugin` ABC: `plugin_id()`, `plugin_type()` (AGENT|STRATEGY|TOOL|SKILL|PROTOCOL), `activate(registry)`, `deactivate()`
- `StrategyPlugin` / `ProtocolPlugin` extensions
- `PluginRegistry`: `register/unregister/get/get_by_type/list/load_from_manifest/activate_all`

#### Evaluators/Planners:
- `AgentEvaluator` — test suite runner with `TestCase(input, expected)` and `AgentEvaluationResult`
- `BasePlanner` / `BuiltInPlanner` / `PlanReActPlanner` — instruction augmentation

#### Content Agent Models (`content/models/`):
~200+ agent input/output pydantic models organized in 11 modules by agent group (Teaching Agents 1-8 → 101-110 Multimodal Agents). Cover: content generation, assessment, personalization, curriculum planning, analytics, evaluation, orchestration, memory, multimodal.

#### YAML Config (`yaml_config.py`):
- `AgentDefinitionYamlReader` / `AgentDefinitionYamlWriter` — serialize AgentDefinition to/from YAML

---

### 4. TOOLS ENGINE (`engines/tools/`)

**Purpose:** 37+ async tool executors with decorator-based registration, TSDM models, LLM gateway, MCP definitions, and central registry.

#### Architecture:

```
BaseToolExecutor (ABC)
  ├── @register(ToolKind) decorator
  ├── name -> str (abstract property)
  ├── description -> str (abstract property)
  ├── async execute(args) -> ToolResult (abstract)
  ├── param/arg helpers (type conversion)
  └── _kind_registry (class-level dict for ToolKind→class mapping)

ToolRegistry
  ├── register/get/unregister/list_tools
  └── execute_tool(tool_def)/execute(name, **kwargs)
```

**ToolResult** (`base_executor.py:14`): `success: bool`, `data: Any`, `error: str | None`

**ParameterMapper** (`parameter_mapper.py`): `map(params)` key transformation, `validate(params, required)` missing field detection

#### TSDM Models (`models/tools_def_models.py`):

| Model | Fields |
|-------|--------|
| **ToolKind** | 39 enum values: `DB_QUERY, DB_STATEMENT, HTTP_SERVICE, GRPC_SERVICE, GRAPHQL, TCP_SOCKET, MESSAGE_BUS, CLI, PYTHON_FUNCTION, MCP, YANG_NETCONF, MIB_SNMP, FILE_READ, FILE_WRITE, AI_MODEL, COMPOSITE, BIGQUERY, BIGTABLE, DATA_AGENT, APIGEE, CODE_EXECUTION, COMPUTER_USE, GEMINI_CODE_EXEC, GOOGLE_SEARCH, VERTEX_AI_SEARCH, CACHE, KEY_VALUE, OBJECT_STORAGE, STREAM, EVENT_LOG, TIME_SERIES, VECTOR_DB, GRAPH_STORAGE, SERVICE_INVOCATION, SERVICE_DISCOVERY, AUTH, BINDING, KNOWLEDGE_RAG, KNOWLEDGE_SEMANTIC_GRAPH, KNOWLEDGE_ML_MINING, KNOWLEDGE_BI_AGGREGATION, KNOWLEDGE_PROCESS_MINING, KNOWLEDGE_QUERY` |
| **ParameterName** | ~100+ enum values for setup params (host, port, url, model, temperature, api_key, etc.) |
| **ArgName** | ~30+ runtime argument names (ACTION, INPUT, MESSAGES, CODE, CONTENT, DATA, QUERY, etc.) |
| **ToolParameter** | `name, type(ParameterType), required, default, description, source, source_path, mapping_target` |
| **ToolOutput** | `name, type, description, mapping_from` |
| **Tool** | `id, name, description, version, kind, params, args, outputs, tags, annotations, retry_policy, timeout_ms(30000)` |
| **TSDMDocument** | extends BaseDocument with `kind=TSDM, tools: list[Tool]` |

#### MCP Definitions (`models/mcp/definitions/`):
- 5 built-in MCP server definitions: Dapr, DBOS, Daytona, Restate, Cisco AI Defense
- Each YAML file defines: `id`, `name`, `description`, `server_command` array, `tools` list
- `load_mcp_definitions()` / `get_mcp_definition(id)` loader

#### Complete Executor Catalog (37+ executors):

| Executor | File | ToolKind | Behavior |
|----------|------|----------|----------|
| **LiteLLMExecutor** | `executors/litellm.py` | AI_MODEL | Real LLM inference via `litellm.acompletion()`, 100+ providers. Params: model (gpt-4o-mini), temperature (0.7), max_tokens. |
| **AIModelExecutor** | `executors/ai_model.py` | AI_MODEL | Gateway or echo stub. Uses LLMGateway.route(). |
| **HTTPServiceExecutor** | `executors/http.py` | HTTP_SERVICE | Stub returns `{status: 200, body: ...}` |
| **HTTPToolExecutor** | `executors/http.py` | GRAPHQL | Stub with url/method/status echo |
| **GrpcToolExecutor** | `executors/grpc.py` | GRPC_SERVICE | Stub |
| **TCPSocketExecutor** | `executors/tcp_socket.py` | TCP_SOCKET | Send/receive raw data |
| **CLIExecutor** | `executors/cli.py` | CLI | `asyncio.create_subprocess_shell`, returns stdout/stderr/returncode |
| **DBQueryExecutor** | `executors/db.py` | DB_STATEMENT, DB_QUERY | SQL via storage factory (relational), returns rows/row_count |
| **FileExecutor** | `executors/file.py` | FILE_READ, FILE_WRITE | Object storage: read/write/check files |
| **MessageBusExecutor** | `executors/message_bus.py` | MESSAGE_BUS | Supports: publish, subscribe, unsubscribe. Bus types: in_memory, redis, kafka, rabbitmq |
| **PythonFunctionExecutor** | `executors/python_function.py` | PYTHON_FUNCTION | Execute registered Python callables by name |
| **MCPToolExecutor** | `executors/mcp.py` | MCP | Connects to MCP server via stdio (MCPClient), calls tool, disconnects |
| **CompositeExecutor** | `executors/composite.py` | COMPOSITE | Sequential child executor execution, fail-fast |
| **CodeExecutionExecutor** | `executors/code_execution.py` | CODE_EXECUTION | Tempfile-based sandbox: python3, node, npx tsx |
| **ComputerUseExecutor** | `executors/computer_use.py` | COMPUTER_USE | Playwright browser automation: navigate, click, type, screenshot, extract |
| **GeminiCodeExecutionExecutor** | `executors/gemini_code_exec.py` | GEMINI_CODE_EXEC | Google Gemini code execution |
| **GoogleSearchExecutor** | `executors/google_search.py` | GOOGLE_SEARCH | Google Custom Search JSON API |
| **VertexAiSearchExecutor** | `executors/vertex_ai_search.py` | VERTEX_AI_SEARCH | Google Discovery Engine enterprise search |
| **BigQueryExecutor** | `executors/bigquery.py` | BIGQUERY | Google BigQuery SQL queries |
| **BigtableExecutor** | `executors/bigtable.py` | BIGTABLE | Google Bigtable read_row operations |
| **ApigeeExecutor** | `executors/apigee.py` | APIGEE | Google Apigee API Hub search/get |
| **DataAgentExecutor** | `executors/data_agent.py` | DATA_AGENT | Google Discovery Engine natural language data agents |
| **CacheExecutor** | `executors/cache.py` | CACHE | get/set/delete/exists/list_keys |
| **KeyValueExecutor** | `executors/key_value.py` | KEY_VALUE | get/set/delete/exists/list_keys |
| **ObjectStorageExecutor** | `executors/object_storage.py` | OBJECT_STORAGE | get/put/delete/exists/generate_url |
| **StreamExecutor** | `executors/stream.py` | STREAM | publish/consume |
| **EventLogExecutor** | `executors/event_log.py` | EVENT_LOG | log_event/list_events/get_event/log_agent_execution |
| **TimeSeriesExecutor** | `executors/time_series.py` | TIME_SERIES | write (measurement/fields/tags), query |
| **VectorDBExecutor** | `executors/vector_db.py` | VECTOR_DB | upsert (id+vector+metadata), query (vector+top_k+filters), delete |
| **GraphStorageExecutor** | `executors/graph_storage.py` | GRAPH_STORAGE | add_node/add_edge/query (Cypher) |
| **ServiceInvocationExecutor** | `executors/service_invocation.py` | SERVICE_INVOCATION | Invoke external services via ServiceInvocationClient |
| **ServiceDiscoveryExecutor** | `executors/service_discovery.py` | SERVICE_DISCOVERY | Resolve operation IDs to endpoints |
| **AuthExecutor** | `executors/auth.py` | AUTH | Apply/validate authentication (api_key, bearer, basic, oauth2, mtls) |
| **BindingExecutor** | `executors/binding.py` | BINDING | Parse/write service bindings |
| **KnowledgeRagExecutor** | `executors/knowledge_rag.py` | KNOWLEDGE_RAG | retrieve/retrieve_rerank/decompose/plan/answer |
| **SemanticGraphKnowledgeExecutor** | `executors/semantic_graph.py` | KNOWLEDGE_SEMANTIC_GRAPH | load/get_node/find_nodes/get_edges/shortest_path/subgraph/statistics/validate/convert |
| **MlMiningKnowledgeExecutor** | `executors/ml_mining.py` | KNOWLEDGE_ML_MINING | load/info/get_fields/find_nodes/get_graph/predict/evaluate/convert/validate |
| **BiAggregationKnowledgeExecutor** | `executors/bi_aggregation.py` | KNOWLEDGE_BI_AGGREGATION | load/get_cubes/get_dimensions/get_measures/get_aggregations/aggregate/convert |
| **ProcessMiningKnowledgeExecutor** | `executors/process_mining.py` | KNOWLEDGE_PROCESS_MINING | load/get_statistics/validate |
| **QueryEngineKnowledgeExecutor** | `executors/query_engine.py` | KNOWLEDGE_QUERY | detect/load/parse/convert/to_table/to_cellset |
| **MIBSNMPExecutor** | `executors/mib_snmp.py` | MIB_SNMP | Stub for SNMP operations |
| **YANGNetconfExecutor** | `executors/yang_netconf.py` | YANG_NETCONF | Stub for NETCONF operations |

#### LLM Gateway (`llm_gateway/`):
- **LLMGateway** — backend registry + SHA256 cache (TTL configurable) + cost tracking
- **ModelResult**: `text`, `model`, `cost`, `tokens_input`, `tokens_output`, `latency_ms`, `cached`
- **LLMGatewayPlugin** — AgentPlugin registering Gateway + MLflow backend
- **MLflowGatewayBackend** — routes to MLflow AI Gateway

#### Error Handling Pattern:
- All executors wrap `execute()` in try/except → return `ToolResult(success=False, error=str(e))`
- Optional dependency imports wrapped in try/except for 15+ executors
- CompositeExecutor fails-fast on first child failure

---

### 5. DOCUMENT ENGINE (`engines/document/`)

**Purpose:** Document parsing and writing across 11 document standards, with chunking, embedding, ingestion pipelines, and bridge utilities.

#### Document Standards:

| Standard | Prefix | Purpose |
|----------|--------|---------|
| **USDM** | U | Unstructured document model (PDF, DOCX, HTML, Markdown, LaTeX, RTF, TXT) |
| **PSDM** | P | Presentation document model (PPTX, PPT, ODP) |
| **ESDM** | E | Spreadsheet/table document model (XLSX, XLS, ODS, CSV, TSV, Parquet, Arrow, Feather) |
| **DSDM** | D | Data/serialization document model (JSON, XML, YAML, TOML, BSON, CBOR, MessagePack) |
| **CSDM** | C | CAD/geometry document model (DXF, DWG, IFC, STL, STEP) |
| **MSDM** | M | Schema/model definition document model (JSON Schema, XSD, SQL DDL, ERD, UML XMI, PlantUML, Protobuf, Thrift, GraphQL, OWL, CQL, Mongo Schema, InfluxDB, ES Mapping, Neo4j, Python, TypeScript) |
| **SSDM** | S | Service definition document model (OpenAPI JSON/YAML, WSDL, YANG, AsyncAPI, MCP, Protobuf Service, Python Service, GraphQL Service) |
| **TSDM** | T | Tool definition document model (TSDM JSON) |
| **OSDM** | O | Orchestration definition model (BPMN XML, CMMN XML, DMN XML, PNML, GraphML, CEP JSON, UML State Machine, SCXML, EPC, Prefect DAG, XPDL) |
| **KSDM** | K | Knowledge extraction definition model (BI aggregation: CWM XMI, Mondrian, XMLA, MDX, TMSL, CDM, Calcite, AWXML, SAP CDS, Cognos FMF, Tableau Hyper; ML-Mining: PMML, ONNX, RDF Turtle, RML YAML; Process Mining: JPRM, YPRM; Query Models: XMLA Execute, MDX text, DAX, SQL Tabular, M Power Query, JPQL, OQL, GraphQL) |
| **LSDM** | L | Event log definition model (XES XML, Syslog, CEF, ES Bulk) |
| **BAM** | — | Business Activity Monitoring definitions (JSON, YAML) |

#### Base Models (`models/base.py`):

**BaseDocument** (Pydantic v2):
- `title`, `document_id`, `version`, `metadata`, `created_at`, `modified_at`
- `raw_binary: BinaryPayload | None`, `raw_text: str | None`
- `binary_encoding` (BASE64/RAW/BASE32/BASE16/ASCII85/URL_SAFE_BASE64)
- `compression_method` (NONE/GZIP/DEFLATE/BROTLI/LZ4/ZSTD)
- `media_type: MediaType`, `file_extension`
- `is_valid`, `validation_errors`

**BinaryPayload**: `media_type`, `encoding`, `bytes_content`, `data` (encoded string), `size_bytes`, `sha256`, `chunk_index/total_chunks`, `compressed`, `compression_algorithm`, `original_size`

#### Media Types (`models/media_types.py`):
- `DocumentFormat` enum — 130+ format values across all 11 standards + BAM
- `MediaContentKind` — TEXT, BINARY, STRUCTURED, TABULAR, HIERARCHICAL, MIXED, VECTOR, GEOMETRIC, PRESENTATION, SCHEMA_DEFINITION, SERVICE_DEFINITION, ORCHESTRATION_DEFINITION, KNOWLEDGE_EXTRACTION_DEFINITION, EVENT_LOG_DEFINITION
- `MediaType` model — `mime`, `format`, `standard`, `extensions`, `kind`, `raw_type`, `description`
- `MEDIA_TYPES` registry — 100+ entries mapping format keys to MediaType objects
- `MediaTypeRegistry` — lookup by format/extension/mime

#### Document Models by Standard:

| File | Content |
|------|---------|
| `usdm_models.py` | USDM: unstructured document elements (Paragraph, Heading, Section, Table, Image, List, etc.) |
| `psdm_models.py` | PSDM: slide, presentation elements |
| `esdm_models.py` | ESDM: spreadsheet, workbook, worksheet, cell, row, column, chart, pivot table |
| `dsdm_models.py` | DSDM: DataDocument, DataNode, DataSchemaReference, SchemaBinding, DataValue |
| `csdm_models.py` | CSDM core + entities + tables: CAD entities, drawing, layer, block |
| `msdm_models.py` | MSDM: Entity, Attribute, DataType, ScalarType, Relationship, Schema, Namespace, Constraint |
| `msdm_capabilities.py` / `msdm_registry.py` | MSDM capability definitions |
| `ssdm_models.py` | SSDM: ServiceOperation, ServiceBinding, ServiceEndpoint, AuthConfig, AuthMethod, MCPToolBinding, Transport |
| `ssdm_capabilities.py` / `ssdm_registry.py` | SSDM capability definitions |
| `lsdm_models.py` | LSDM: log event, event log, log source |
| `standard.py` | DocumentStandard enum |

#### Parsers and Writers:
- Each standard has parser writer subdirectories
- Concrete parsers for BPMN XML, CMMN XML, DMN XML, ROS (RDF), etc.
- OSDM writers: BPMN, CMMN, DMN, State Machine
- USDM writers: docx, pdf, markdown, html, txt
- ESDM writers: xlsx
- DSDM writers: json, xml, yaml
- SSDM writers: openapi, wsdl

#### Pipeline Services:
- `chunking/` — document chunking strategies (fixed-size, semantic, recursive)
- `embedding/` — embedding generation and management
- `ingestion/` — document ingestion pipeline (5 step files: parse, chunk, embed, index, store)
- `storage/` — document store implementations
- `utils/` — utility functions (file detection, format detection)
- `bridge.py` — DocumentBridge utility
- `model_tools/` — model manipulation helpers

#### Supported Formats:
- PDF (4 libraries: PyMuPDF, pdfplumber, camelot, pypdfium2)
- DOCX (python-docx)
- XLSX (openpyxl)
- Images (Pillow, OpenCV)
- OCR (pytesseract)
- Audio metadata (tinytag)
- CAD (ezdxf for DXF)
- HTML (beautifulsoup4, lxml)
- RTF (striprtf)
- Markdown

---

### 6. KNOWLEDGE ENGINE (`engines/knowledge/`)

**Purpose:** 5 stable sub-engines (bi_aggregation, ml_mining, process_mining, semantic_graph, graph) + query engine. RAG and memory engines are excluded from eager loading due to missing transitive dependencies.

**Eagerly loaded** (`__init__.py`): `BiAggregationEngine`, `QueryEngine`, `MlMiningEngine`, `SemanticGraphEngine`, `ProcessMiningEngine`

#### SemanticGraphEngine (`semantic_graph/`):
- RDF/OWL graph parsing (Turtle RDF, RML YAML)
- RdfParser: sync `parse()`, async `parse_bytes/path/stream`
- RmlParser: sync `parse()`, async `parse_bytes/path/stream`
- In-memory graph representation (NetworkX-based)
- Graph API: add/remove node/edge, find nodes/edges, neighbors, shortest path, subgraph extraction, statistics, validation, format conversion
- **Circular dependency fix:** UnifiedGraphEngine passes `unified_engine=self` to SemanticGraphEngine

#### UnifiedGraphEngine (`graph/`):
- Combines multiple graph engines into unified interface
- Delegates to SemanticGraphEngine internally

#### MlMiningEngine (`ml_mining/`):
- Parsers: PMML XML, ONNX Protobuf, sklearn models, PyTorch models
- ONNX Runtime inference pipeline: converter → ORT session → predict/evaluate
- Metrics computation, validation
- Phase E full pipeline: sklearn/PyTorch→ONNX→inference→metrics
- Test coverage: 67 ML mining tests + 36 Phase E tests = 103 total

#### BiAggregationEngine (`bi_aggregation/`):
- OLAP/Business Intelligence parsing: CWM XMI, Mondrian Schema, TMSL JSON, CDM JSON
- Cube/dimension/measure extraction
- Aggregation operations
- Format conversion
- Test coverage: 15 tests

#### ProcessMiningEngine (`process_mining/`):
- XES event log parsing
- Process mining statistics (variants, cases, events, activities, etc.)
- Validation
- Test coverage: 25 tests

#### QueryEngine (`query/`):
- Multi-language query support: SQL, MDX, DAX, JPQL, OQL, GraphQL
- Query language auto-detection
- Query parsing and conversion
- Table/cellset output formats

#### Knowledge RAG (`rag/`) — excluded from eager import:
- `KnowledgeRagEngine` — cannot be imported directly (missing `services`, `llm`, `research` submodules)
- Would need: vector store, LLM, embedding model
- Stub executors exist in tools engine that attempt to use it

#### Tests:
- 171 total knowledge tests (15 BI + 67 ML + 36 Phase E + 14 query + 44 semantic graph + 25 process mining)
- 2 tests skipped (RAG/memory) due to missing dependencies
- `conftest.py` has custom `event_loop` fixture per test

---

### 7. COMMUNICATION ENGINE (`engines/communication/`)

**Purpose:** Message buses, service consumption/exposure, MCP support, auth, serialization, bindings.

#### Message Buses (`buses/`):

| Bus | File | Transport | Features |
|-----|------|-----------|----------|
| **InMemoryMessageBus** | `in_memory_message_bus.py` | In-memory | `BROADCAST="*"`, asyncio.Lock, defaultdict subscriber lists |
| **DurableMessageBus** | `durable_message_bus.py` | In-memory async queue | Per-recipient asyncio.Queue, consumer tasks, configurable maxsize |
| **KafkaMessageBus** | `kafka_bus.py` | Apache Kafka | AIOKafkaProducer/Consumer, topic-based, model_dump_json serialization |
| **PriorityMessageBus** | `priority_message_bus.py` | In-memory heap | heapq priority queue, PrioritizedMessage(order=True) |
| **RabbitMQMessageBus** | `rabbitmq_bus.py` | RabbitMQ | aio-pika, DIRECT exchange, DeliveryMode.PERSISTENT, per-handler queues |
| **RedisMessageBus** | `redis_pub_sub_bus.py` | Redis Pub/Sub | redis.asyncio, get_message polling, channel-based dispatch |
| **RequestReplyBus** | `request_reply_bus.py` | In-memory RPC | dict-based handlers, `request()` with timeout |
| **TopicMessageBus** | `topic_message_bus.py` | In-memory topic | Topic-based pub/sub |

**MessageBus** ABC: `publish/subscribe/unsubscribe/start/stop`
**HandlerType**: `Callable[[AgentMessage], Awaitable[Optional[AgentMessage]]]`

#### Bridge Pattern (`bridge.py`):
- `MessageBusBridge` — delegation wrapper
- `LoggingBusBridge(MessageBusBridge)` — adds structured logging
- `MetricsBusBridge(MessageBusBridge)` — tracks publish_count, message_counts

#### Consumption (`consumption/`):
- **BindingCatalog** — load and query service bindings (from files, dicts, SSDM documents)
- **CircuitBreaker** — states: CLOSED → OPEN (after failure_threshold=5) → HALF_OPEN (after recovery_timeout_ms=30000) → CLOSED
- **ServiceInvocationClient** — facade: catalog → discovery → auth → transport → circuit breaker → execution
- **ServiceDiscovery** — backends: binding, static, DNS, Kubernetes (consul/eureka/etcd/zookeeper are stubs)
- **RequestBuilder** — builds TransportRequest from operation+binding+payload (header/cookie/body/path/query)
- **TransportFactory** — creates/caches transports by Transport enum (HTTP, gRPC, AMQP, Kafka)
- **MCPClientAdapter** / **MCPClientProxy** — JSON-RPC 2.0 over stdio for MCP consumption
- **MCPService** — manages MCPAdapter lifecycle per endpoint

#### Exposure (`exposure/`):
- **NorthBoundServerBuilder** — builds route dispatch tables for exposing operations as endpoints
- **DockerComposeWriter** — serializes DeploymentDescriptor to Compose YAML
- **KubernetesManifestWriter** — generates Deployment+Service manifests
- **GatewayConfigWriter** — gateway rule serialization
- **MCPServerWriter** — MCP north-bound binding config

#### Bindings (`bindings/`):
- **BindingParser** — parse JSON/YAML into SSDM ServiceBinding models (with graceful enum fallback)
- **BindingWriter** — serialize ServiceBinding to bytes (JSON or YAML)
- **MCPBindingWriter** — MCP-specific binding serialization

#### Messaging (`messaging/`):
- **MessageChannelManager** — register/publish/close message channels with lazy transport creation
- Adapters: AMQP, Kafka, NATS (stubs)

#### Common (`common/`):
- **Auth** (`common/auth/`): AuthManager for API key, Bearer/JWT, Basic, OAuth2, mTLS
- **Serialization** (`common/serialization/`): JSONSerializer, AvroSerializer (optional fastavro), ProtobufSerializer (dynamic class loading)
- **Transport** (`common/transport/`): HTTPTransport (aiohttp+retry), AMQPTransport (aio-pika), GRPCTransport (dynamic stubs), KafkaTransport (aiokafka), MCPAdapter (stdio/SSE)

---

### 8. STORAGE ENGINE (`engines/storage/`)

**Purpose:** 9 storage categories with factory pattern and proxy support.

#### Architecture:

```
BaseStorage (ABC)
  ├── connect() / disconnect() / health() / is_connected
  └── async context manager

StorageFactory (ABC)
  └── 9 concrete factories (Cache/EventLog/Graph/KeyValue/Object/Relational/Stream/TimeSeries/Vector)
  └── create_storage(category, backend, **kwargs) — convenience entry point
  └── register_backend(category, name, cls) — custom backends

Proxies:
  ├── LazyInitStorageProxy — factory-based deferred creation
  ├── CachingStorageProxy — OrderedDict LRU (get/set/delete/invalidate/clear_cache)
  └── NullStorage — Null Object pattern (get→None, set/delete→no-op, health→True)
```

#### Storage Backends:

| Category | Base Class | Backends |
|----------|-----------|----------|
| **Cache** | CacheStorage | InMemoryCacheStorage, RedisCacheStorage |
| **Key-Value** | KeyValueStorage | InMemoryKeyValueStorage, RedisStorageAdapter |
| **Relational** | RelationalStorage | BridgeRelationalStorage + Implementor (SQLAlchemy/SQLite) → SQLiteAdapter, PostgresAdapter, MySQLAdapter, SQLServerAdapter |
| **Vector** | VectorDBAdapter / VectorStorage | InMemoryVectorStore, ChromaAdapter, FaissAdapter, QdrantAdapter, PineconeAdapter, WeaviateAdapter |
| **Object** | ObjectStorage | LocalFileAdapter, S3Adapter, MinioAdapter |
| **Event Log** | LogStorage | SqlLogStorage, RSyslogStorage |
| **Stream** | StreamStorage | RedisStreamAdapter, KafkaStreamAdapter |
| **TimeSeries** | TimeSeriesStorage | InfluxDBStorageAdapter |
| **Graph** | GraphStorage | Neo4jAdapter |

- Relational storage uses Bridge pattern: `BridgeRelationalStorage(RelationalStorage)` delegates to `RelationalImplementor (ABC)` → `SQLAlchemyImplementor / SQLiteImplementor`
- Vector storage supports: HNSWConfig (m=16, ef_construction=200, ef_search=50), IVFConfig (nlist=100, nprobe=10), `normalize_embedding()` via numpy L2
- Factory system auto-registers all backends at import via `_register_builtins()`

---

### 9. MEMORY ENGINE (`engines/memory/`)

**Purpose:** Multi-agent memory management with backend strategy pattern and mediator.

- **BaseMemory** ABC: `remember(key, content, metadata)`, `recall(key)`, `search(query, limit)`, `forget(key)`, `stats()`
- **MemoryBackend** ABC (strategy): `store/retrieve/search/forget/clear/count`
  - `InMemoryBackend` — dict-based, Jaccard overlap scoring + metadata boost
  - `NullMemoryBackend` — safe no-ops
- **MemoryMediator** — coordinates primary + secondary backends; `store()` writes to both; `retrieve()` reads primary, falls back to secondary, promotes on miss; `_notify()` broadcasts events
- **MemoryItem** (dataclass): `id`, `key`, `content`, `metadata`, `timestamp`
- **MemoryQuery**: `query`, `limit(10)`, `threshold(0.0)`, `filter_metadata`
- **MemoryResult**: `items`, `total`, `took_ms`
- Proxies: `LazyMemoryBackend` (factory deferral), `CachingMemoryBackend` (LRU maxsize=128)

---

### 10. SESSION ENGINE (`engines/session/`)

**Purpose:** Session management for multi-agent conversations.

- **Session** (Pydantic): `id`, `app_name`, `user_id`, `session_id`, `state: dict`, `events: list[Event]`, `created_at/updated_at`
- **Event**: `id`, `invocation_id`, `author`, `content`, `actions: EventActions` (state_delta, artifact_delta, skip_summarization)
- **ArtifactPart**: `data: bytes`, `mime_type: str`
- **MemoryEntry**: `content`, `author`, `timestamp`, `custom_metadata`
- **BaseSessionService** ABC: `create_session/get_session/list_sessions/delete_session/append_event`
- **BaseArtifactService** ABC: `save_artifact/load_artifact/list_artifact_keys/delete_artifact`
- **BaseMemoryService** ABC: `add_session_to_memory/search_memory`
- All have InMemory implementations

---

### 11. OBSERVABILITY ENGINE (`engines/observability/`)

**Purpose:** Distributed tracing, metrics, and event recording with 9 pluggable backends.

**Core types:**
- **Span** (dataclass): `name`, `attributes`, `status`, `start_time`, `end_time`, `parent_id`, `span_id`, `trace_id`
- **Metric** (dataclass): `name`, `value`, `type` (counter), `tags`, `timestamp`
- **Event** (dataclass): `name`, `attributes`, `timestamp`, `severity` (info)

**ObservabilityBackend** ABC: `start_span/end_span/record_metric/record_event/shutdown`

**9 Backends:**

| Backend | Dependencies | Implementation |
|---------|-------------|----------------|
| AgentOpsBackend | agentops | Full: init, span, metric, event |
| DatadogBackend | ddtrace | Tracer + statsd gauge |
| MLflowBackend | mlflow | start_span/close/log_metric |
| WeaveBackend | wandb | wandb.Log + log |
| ArizeBackend | openinference | Stub (returns dict) |
| FreeplayBackend | freeplay | Stub (start_span only) |
| FutureAGIBackend | future_agi | Stub (start_span only) |
| LangWatchBackend | langwatch | Stub (start_span only) |
| GrafanaBackend | opentelemetry | OTel tracer start/end |

**Plugin:**
- `ObservabilityPlugin(AgentPlugin)` — loads config, discovers `trace_definitions.yaml` from all engines, creates backend, registers instrumentation
- `discover_trace_definitions()` — scans `engines/*/trace_definitions.yaml`

**Wrappers:**
- `wrap_registry()` — returns `TracedRegistry` proxy wrapping `run()`/`execute()` with spans
- `wrap_send()` / `wrap_broadcast()` — traced async wrappers

**Trace definitions per engine:**
- Orchestration: spans for instance/activity lifecycle, metrics for instance counts
- Agent: spans for `agent.run`, `mediator.send`, `mediator.broadcast`, metrics for duration/count
- Tools: spans for `tool.execute`, `tool.mcp.call`, metrics for count/duration/error

---

### 12. TTS ENGINE (`engines/tts/`)

**Purpose:** Text-to-speech with pluggable backends.

- **TTSEngine**: `register_backend/synthesize(text, voice, backend)/list_voices`
- **TTSPlugin(AgentPlugin)** ABC: `synthesize()`, `list_voices()`
- **VoiceSpec** (dataclass): `id`, `name`, `gender`, `language`, `description`
- Backends: Cartesia, ElevenLabs

---

### 13. CONFIGURATION (`config/`)

- `OPENAI_API_KEY`, `AZURE_OPENAI_API_KEY`
- `DATA_DIR = "data/documents"`, `PROCESSED_DATA_DIR = "data/processed"`, `VECTOR_DB_DIR = "data/vector_db_files"`
- `DEFAULT_LLM_MODEL = "gpt-4o"`, `EMBEDDING_MODEL = "text-embedding-3-small"`

---

### 14. DATABASE MIGRATIONS (`migrations/`)

- Alembic configured for `postgresql+asyncpg://user:password@localhost/learning_ai`
- Standard `env.py` (sync-based, offline + online modes)
- No version scripts yet (`target_metadata = None`)

---

### 15. UTILITY SCRIPTS (`tools/`)

| Script | Purpose |
|--------|---------|
| `analyze_architecture.py` | AST-based static analysis → `architecture.md` with class tables, inheritance maps |
| `clean_pycache.py` | Recursively removes all `__pycache__` directories |
| `generate_inits.py` | Auto-generates `__init__.py` with smart exports from AST analysis |
| `restore_py_modules.py` | Emergency venv recovery (freeze → uninstall all → reinstall from requirements) |

---

## Key Architectural Patterns

### 1. Agent Flow (Adapter Pattern)
```
Orchestrator → AgentInput → AgentAdapter → Agent → AgentOutput
                                ↓
                         AgentSpecificInput
                                ↓
                             (Agent.execute)
                                ↓
                         AgentSpecificOutput
```

### 2. Tool Flow (Registry + Execution)
```
Agent → ToolRegistry.get(name) → BaseToolExecutor.for_kind(kind)
  → executor = cls(tool.params) → executor.execute(tool.args) → ToolResult
```

### 3. Strategy Pattern (Interaction)
```
InteractionRequest(scenario) → NativeBackend._build_strategy(scenario)
  → BroadcastStrategy | DebateStrategy | GroupChatStrategy | etc.
  → strategy.execute(request) → InteractionResult
```

### 4. BPMN Token-Based Execution
```
ProcessInstance → Token at start node → traverse nodes
  → activity.execute() → next nodes (via SequenceFlow)
  → Gateway classification (exclusive/parallel/inclusive)
  → Fork/Join/Synchronization → Token state management
```

### 5. Document Model Hierarchy
```
BaseDocument
  ├── USDMDocument (unstructured)
  ├── PSDMDocument (presentation)
  ├── ESDMDocument (spreadsheet)
  ├── DSDMDocument (data/serialization)
  ├── CSDMDocument (CAD)
  ├── MSDMDocument (schema)
  ├── SSDMDocument (service)
  ├── TSDMDocument (tool definitions)
  ├── BaseOSDMDocument (orchestration)
  │   ├── BPMNDocument
  │   ├── CMMNDocument
  │   ├── DMNDocument
  │   ├── StateMachineDocument
  │   └── CEPDocument
  ├── KSDMDocument (knowledge)
  └── LSDMDocument (event log)
```

### 6. Storage Factory Pattern
```
create_storage(category, backend, **kwargs)
  → StorageFactory.for_category(category).create(backend, **kwargs)
  → Concrete Storage instance (e.g., InMemoryCacheStorage, Neo4jAdapter)
```

### 7. Duplicate Registration Handling
- Tool executors: `@BaseToolExecutor.register(ToolKind)` — decorator populates class-level `_kind_registry`
- Strategy registry: `InteractionStrategyRegistry` — thread-safe via `RLock`, raises `ValueError` on duplicate
- Plugin registry: `PluginRegistry.register()` — calls `activate()` on registration
- Agent factory: `AgentFactory.register(name, cls)` — class-level dict
- Storage factory: `StorageFactory.register_backend(category, name, cls)` — per-category dict

---

## Error Handling Patterns

| Pattern | Location | Behavior |
|---------|----------|----------|
| Error AgentOutput | All strategies | Agent exceptions → AgentOutput with `error` field |
| Gather normalization | BroadcastStrategy | BaseException → AgentOutput with error |
| Callback short-circuit | BaseAgent.run() | `before_agent` returns non-None → skip execution |
| RoutedAgent failover | RoutedAgent.execute() | Error → router recalled with ErrorContext (excludes failed key) |
| Safe expression eval | safe_eval.py | AST whitelist → transition guard evaluation |
| AutoGen fallback | autogen_backend.py | Missing/failed AutoGen → Native backend |
| ToolResult pattern | All tool executors | `ToolResult(success, data, error)` — never throw |
| ImportError guard | 15+ executors | try/except on optional deps → error ToolResult |
| Composite fail-fast | CompositeExecutor | First child failure stops execution |
| Storage disconnect | All storage backends | `connect()`/`disconnect()` lifecycle |
| Circuit breaker | Consumption | CLOSED→OPEN→HALF_OPEN state machine |

---

## Testing Framework

- **Framework:** pytest 9.0.2 with `asyncio_mode = auto`
- **No integration test prerequisites** (no DB, no external services)
- **Knowledge tests:** 171 total (15 BI + 67 ML mining + 36 Phase E + 14 query + 44 semantic graph + 25 process mining)
- **Interaction tests:** 11 unit + 8 performance tests per strategy
- **Agent tests:** ~30 unit tests across all subsystems
- **Tool tests:** 20+ test files covering all executors
- **Skipped tests:** 2 (RAG/memory) due to missing dependencies
- **Custom conftest:** `event_loop` fixture creates new asyncio loop per test

---

## Recommendations for C# Rewrite

### Suggested Architecture:

1. **Use .NET 8+ with ASP.NET Core** for the orchestration API layer
2. **Use Dapr** for the message buses, state management, service invocation (replaces communication engine)
3. **Use Temporal.io or Elsa Workflows** for the orchestration engine (BPMN-like workflow execution)
4. **Use Semantic Kernel** for LLM integration, RAG, and agent patterns
5. **Use AutoGen for .NET** (Microsoft.AutoGen) for multi-agent interaction
6. **Use Kernel Memory** for the knowledge/memory/RAG layer
7. **Use Entity Framework Core** with SQL Server/PostgreSQL for relational persistence
8. **Use Redis** for cache and pub/sub
9. **Use Neo4j Driver** for graph storage
10. **Use ONNX Runtime for .NET** (Microsoft.ML.OnnxRuntime) for ML inference
11. **Use OpenTelemetry .NET** for observability
12. **Use Serilog** for structured logging

### Suggested Namespace Structure:

```
MultiAgentInfra/
├── Orchestration/           # BPMN/CMMN/DMN execution
│   ├── Core/                # Engine, Instance, Token, Context
│   ├── Bpmn/                # BPMN models, executors, parsers
│   ├── Cmmn/                # CMMN models, executors
│   ├── Dmn/                 # DMN decision engine
│   ├── StateMachine/        # State machine execution
│   └── Expressions/         # FEEL expression evaluator
├── Agents/                  # Agent definitions, registry, adapters
│   ├── Core/                # AgentInput/Output, BaseAgent
│   ├── Strategies/          # Broadcast, Debate, GroupChat, etc.
│   ├── Backends/            # Native, AutoGen
│   └── Skills/              # SkillLoader, executors
├── Tools/                   # Tool layer executors
│   ├── Core/                # BaseToolExecutor, ToolResult
│   ├── Llm/                 # LLM completion, embedding
│   ├── Rag/                 # RAG, Retriever, Context Builder
│   ├── Mcp/                 # MCP client
│   └── Storage/             # DB, File, Cache, KV, Vector, etc.
├── Knowledge/               # Knowledge engines
│   ├── SemanticGraph/
│   ├── MlMining/
│   ├── BiAggregation/
│   └── ProcessMining/
├── Documents/               # Document processing
│   ├── Models/              # All SDM models
│   ├── Parsers/             # Per-standard parsers
│   └── Writers/             # Per-standard writers
├── Communication/           # Message buses, service invocation
├── Storage/                 # Storage backends
├── Memory/                  # Memory management
├── Session/                 # Session management
├── Observability/           # Tracing, metrics
└── Infrastructure/          # Configuration, DI, middleware
```

---

## Uncertainties and Questions

- [ ] The `engines/skill/` directory listed in AGENTS.md architecture table does not exist
- [ ] `KnowledgeRagEngine` depends on missing modules (`services`, `llm`, `research`) — stubs needed
- [ ] `UnifiedGraphEngine` class referenced in `graph/__init__.py.__all__` but not found in the tree
- [ ] `sample_skill/` directory referenced by test files does not exist
- [ ] Graph persistence (`research_graph.db`) creates local SQLite — not production-ready
- [ ] Exactly how the BPMN XML parser maps to OSDM models (deeper XML schema compliance)
- [ ] TableauHyperParser/TableauHyperWriter raise `RuntimeError` — need `tableauhyperapi` stubs
- [ ] 3 storage backends (consul, eureka, etcd, zookeeper) are stubs raising RuntimeError
- [ ] 5 message adapter files (AMQP, Kafka, NATS) are empty stubs
- [ ] OAuth2 token provider has stub for network exchange
