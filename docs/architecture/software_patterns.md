You are an expert Python developer building a BPMS (Business Process Management System) platform with:
- Multi-agent AI system
- Model-Driven Architecture (executable models as source of truth)
- Infrastructure/platform layer (used by multiple unknown client apps)

You MUST apply the following design patterns appropriately. DO NOT ask permission — just use the right pattern for the right situation.

=== CREATIONAL PATTERNS (Object creation) ===

1. Singleton - Use ONLY for: global config, logger, connection pool. Avoid when possible (hurts testability).

2. **[APPLIED] Factory Method / Abstract Factory** — For database backends, storage providers, agent creation.
   - `engines/storage/factories.py` — `StorageFactory(ABC)` + 9 concrete factories (Cache, EventLog, Graph, KeyValue, Object, Relational, Stream, TimeSeries, Vector) + `create_storage()` dispatcher
   - `engines/orchestration/core/factories.py` — `StorageBackendFactory(ABC)` with Memory/SQL/File factories
   - `engines/agent/factories.py` — `AgentFactory._registry` with `SkillAgentFactory`, `StateMachineAgentFactory`

3. **[APPLIED] Builder** — For constructing complex objects with many optional parameters.
   - `engines/orchestration/core/builders.py` — `EngineConfigBuilder` (fluent `with_*()` + `build()`), `ProcessDefinitionBuilder`
   - `engines/agent/builders.py` — `AgentBuilder` (step-by-step with `with_*()` + `build()`)
   - `engines/communication/exposure/server_builder.py` — server construction via method chaining

4. Prototype - For cloning process templates (deep copy existing models).

5. Object Pool - For database connections, thread pools, agent pools.

6. **[APPLIED] Dependency Injection (Constructor Injection)** — ALWAYS. Never instantiate dependencies inside a class.
   - Ubiquitous across all 10 engine packages
   - All infrastructural classes receive dependencies via `__init__` parameters

=== STRUCTURAL PATTERNS (Object composition) ===

7. **[APPLIED] Adapter** — Wrap external libraries, backends, and services into engine interfaces (55+ adapter classes).
   - `engines/storage/` — 25+ adapters (Postgres, SQLite, MySQL, SQL Server, Redis, Kafka, Neo4j, S3, Minio, Chroma, FAISS, Qdrant, Weaviate, Pinecone, InfluxDB, etc.)
   - `engines/communication/messaging/adapters/` — Kafka, NATS, AMQP bus adapters
   - `engines/communication/buses/` — InMemory, Redis, RabbitMQ, Kafka, Topic, RequestReply, Priority, Durable bus adapters
   - `engines/tools/adapters/` — HTTP, CLI, gRPC, DB, File, MCP, SNMP, TCP socket, YANG/Netconf executors
   - `engines/agent/skill/adapters.py` — `MCPAdapter` wraps MCPClient into SkillExecutor
   - `engines/orchestration/integration/` — `UserTaskAdapter`, `MessageAdapter`, `BusinessRuleAdapter`

8. **[APPLIED] Bridge** — Separate abstraction from implementation.
   - `engines/orchestration/core/engine_bridge.py` — `EngineImplementor(ABC)` + 7 concrete implementors + `EngineBridge` hierarchy
   - `engines/storage/relational/implementors.py` — `RelationalImplementor(ABC)` + `SQLAlchemyImplementor`, `SQLiteImplementor` + `BridgeRelationalStorage`
   - `engines/document/bridge.py` — `DocumentImplementor(ABC)` + `DocumentBridge`
   - `engines/communication/bridge.py` — `MessageBusBridge`

9. Composite — Represent BPMN subprocesses as trees of nodes.
   - `engines/orchestration/core/decorators.py:180` — `CompositeDecorator` chains multiple decorators
   - `engines/tools/adapters/composite_executor.py` — `CompositeExecutor` runs multiple executors in sequence

10. **[APPLIED] Decorator** — Add logging, timing, retry, caching, transaction to executors.
    - `engines/orchestration/core/decorators.py` — `ExecutionDecorator(ABC)` + `LoggingDecorator`, `TimingDecorator`, `RetryDecorator`, `CircuitBreakerDecorator`, `CompositeDecorator`
    - `engines/communication/bridge.py` — `LoggingBusBridge`, `MetricsBusBridge` (decorate MessageBusBridge)

11. **[APPLIED] Facade** — Provide simple API hiding complex subsystems.
    - `engines/orchestration/core/engine.py` — `OrchestrationEngine` (composes ~30+ services, explicit Facade in docstring)
    - `engines/communication/consumption/client_generator.py` — `ServiceInvocationClient` unifies RequestBuilder, TransportFactory, MCPService, CircuitBreaker

12. Flyweight — Share common data between thousands of process instances (BPMN templates).

13. **[APPLIED] Proxy** — Lazy loading, access control, virtual proxies for large models (10 proxy classes).
    - `engines/orchestration/core/proxies.py` — `LazyInitProxy`, `CachingProxy`, `EngineProtectionProxy`
    - `engines/memory/proxies.py` — `LazyMemoryBackend`, `CachingMemoryBackend`
    - `engines/storage/proxies.py` — `LazyInitStorageProxy`, `CachingStorageProxy`
    - `engines/document/bridge.py` — `LazyDocumentProxy`
    - `engines/communication/consumption/mcp_client_adapter.py` — `MCPClientProxy`
    - `engines/knowledge/proxies.py` — `LazyKnowledgeProxy`

14. Module — Use Python modules as pattern (single import, encapsulated state).

=== BEHAVIORAL PATTERNS (Communication) ===

15. Chain of Responsibility — Validation pipeline, error handling chain, middleware.
    - `engines/orchestration/validation/validator.py:56` — `ValidationChain` runs validators in sequence

16. **[APPLIED] Command** — Queue operations, undo/redo, audit trail, event sourcing (2 implementations).
    - `engines/orchestration/command.py` — `Command(ABC)`, `CommandHistory`, `CommandInvoker`
    - `engines/orchestration/commands.py` — 6 concrete commands: `StartInstanceCommand`, `SuspendInstanceCommand`, `ResumeInstanceCommand`, `TerminateInstanceCommand`, `ThrowSignalCommand`, `PublishMessageCommand`
    - `engines/orchestration/runtime/command.py` — `Command(ABC)`, `CommandQueue` with history
    - 4 dedicated tests

17. Interpreter — Parse BPMN XML/JSON into executable model. Define grammar for condition expressions.

18. Iterator — Traverse process nodes, task lists, history. Use Python's `__iter__`.

19. **[APPLIED] Mediator** — Coordinate between agents, engine, storage, events (4 mediator classes).
    - `engines/orchestration/multi_agent/mediator.py` — `MultiAgentMediator` (composes CoordinationHandler, InteractionHandler, ProtocolHandler, NegotiationHandler, AgentExecutor, MessageRouter)
    - `engines/memory/mediator.py` — `MemoryMediator` (coordinates primary+secondary with listener broadcast)
    - `engines/agent/mediator.py` — `AgentMediator`
    - `engines/interaction/mediator.py` — `InteractionMediator`
    - `engines/knowledge/proxies.py` — `KnowledgeMediator`

20. Memento — Save/restore process state (snapshots, checkpoint, rollback).
    - `engines/orchestration/runtime/state_snapshot.py` — `StateSnapshot` stores state, `StateSnapshotManager` creates/restores/compares snapshots

21. **[APPLIED] Observer** — Events, logging, metrics, audit, notifications, SLA monitoring (3 mechanisms).
    - `engines/orchestration/core/event_bus.py` — `EventBus` with `subscribe()`/`unsubscribe()`/`publish()` + `EventType(Enum)` with 20+ event types
    - `engines/orchestration/runtime/listeners.py` — `_BaseListenerManager` + `TaskListenerManager` + `ExecutionListenerManager`
    - `engines/orchestration/core/engine.py` — lifecycle events published on `start()/stop()/pause()/resume()`

22. **[APPLIED] State** — Process lifecycles, task states, engine states (5 state machines).
    - `engines/orchestration/core/engine_states.py` — 6 concrete states (Stopped, Starting, Running, Paused, Stopping, Error)
    - `engines/orchestration/core/instance_states.py` — 9 concrete states (Active, Suspended, Completed, Failed, Terminated, Draft, Closed, Compensating, Migrating)
    - `engines/orchestration/core/token_states.py` — 5 concrete states (Active, Waiting, Completed, Terminated, Merged)
    - `engines/orchestration/core/transaction_states.py` — 8 concrete states (Active, Preparing, Prepared, Committing, Committed, RollingBack, RolledBack, Failed)
    - `engines/orchestration/runtime/circuit_states.py` — 3 concrete states (Closed, Open, HalfOpen)

23. **[APPLIED] Strategy** — Routing, authentication, interaction, execution strategies.
    - `engines/orchestration/bpmn/gateway_handler.py` — `GatewayStrategy(ABC)` + 5 strategies (Exclusive, Inclusive, Parallel, EventBased, Complex)
    - `engines/interaction/` — `InteractionStrategy(ABC)` + 7 strategies (Debate, RoundRobin, GroupChat, Ensemble, Broadcast, Coordinator, SelfRefine)
    - `engines/tools/base_executor.py` — `BaseToolExecutor(ABC)` (Strategy interface for all tool executors)
    - `engines/memory/backends.py` — `MemoryBackend(ABC)` (strategy for memory storage)
    - `engines/document/bridge.py` — `ParsingStrategy(ABC)` + `SerializationStrategy(ABC)`
    - Dispatch dicts: `_ACTIVITY_DISPATCH` (activity_handler.py), `_OP_HANDLERS` (feel_engine.py), `_FLOW_ELEMENT_HANDLERS` (osdm_serializer.py)

24. **[APPLIED] Template Method** — Define skeleton for data import/export, agent execution.
    - `engines/agent/base_agents/base_agent.py` — `BaseAgent.run()` skeleton: validate_input → execute → validate_output → log
    - `engines/agent/skill/adapters.py` — `BaseSkillExecutor.execute()` skeleton: `_build_prompt()` → `_call_llm()`
    - `engines/interaction/base_strategy.py` — shared `_emit()`/`_build_input()`/`_run_agent()` steps
    - `engines/document/parsers/bam_parsers/base_bam_parser.py` — abstract `_decode()` with concrete `parse_bytes/parse_path/parse_stream`
    - `engines/communication/common/transport/base.py` — abstract `send()` + concrete `close()`

25. **[APPLIED] Visitor** — Validate model, export to XML/JSON, calculate metrics, simulate execution.
    - `engines/orchestration/validation/model_visitor.py` — `ModelVisitor(ABC)` with `visit_process/activity/gateway/event/sequence_flow/subprocess` + `Visitable(Protocol)`
    - `engines/orchestration/validation/validator.py` — `Validator(ModelVisitor)` implements validation visitor

26. **[APPLIED] Null Object** — Replace None with harmless empty object.
    - `engines/memory/backends.py` — `NullMemoryBackend` (safe no-op memory backend)
    - `engines/storage/proxies.py` — `NullStorage` (safe no-op storage backend)

27. Specification — Complex business rules (eligibility criteria, approval conditions) as composable objects.
    - `engines/orchestration/bpmn/activity_handler.py:65` — `ActivityIOSpecification`

=== CONCURRENCY PATTERNS (Multi-threading, async, agents) ===

28. Active Object — Each agent runs in its own thread/async task with message queue.
29. Thread Pool — Reuse worker threads for task execution.
30. Promise/Future — Async execution results (use asyncio.Future).
31. Reactor — Event loop for async I/O (use asyncio).
32. Scheduler — Schedule processes, timers, deadlines, SLA timers.
33. Leader-Follower — Agent coordination (one leader assigns tasks to followers).

=== ARCHITECTURAL PATTERNS (System structure) ===

34. Model-View-Controller (MVC) — Model: BPMN, View: process designer UI, Controller: execution logic.
35. Event-Driven Architecture — Process events trigger next steps (decoupled via message broker).
36. CQRS (Command Query Responsibility Segregation) — Separate write (Command) from read (Query) paths.
37. Event Sourcing — Store state as sequence of events, rebuild current state by replaying.
38. Repository — Abstract data access (ProcessRepository, TaskRepository) hiding database details.
    - `engines/orchestration/persistence/repository.py` — `Repository(ABC)` + `RepositoryProtocol`
39. Unit of Work — Track changes across multiple repositories, commit/rollback together.
40. Data Mapper — Map database rows to domain objects without domain knowing about database.
41. Service Layer — Define clear use cases (StartProcess, CompleteTask, DeployModel) above repositories.
    - `engines/orchestration/core/engine_services.py` — `InstanceService`, `EngineLifecycleService`, `RecoveryService`, `DefinitionService`
42. **[APPLIED] Plugin/Registry** — Load extensions dynamically, register backends/strategies/adapters.
    - `engines/storage/factories.py` — `_STORAGE_FACTORIES` global registry via `register_backend()`
    - `engines/tools/tool_registry.py` — `ToolRegistry` with `register()`/`get()`/`list()`/`execute()`
    - `engines/agent/agent_registry.py` — `AgentRegistry` with `register()`/`get()`/`run()`
    - `engines/agent/factories.py` — `AgentFactory._registry` mapping name → class
    - `engines/interaction/strategy_registry.py` — `InteractionStrategyRegistry`
    - `engines/communication/consumption/binding_loader.py` — `BindingCatalog`
    - `engines/communication/consumption/circuit_breaker.py` — `CircuitBreakerRegistry`
    - `engines/document/models/document_registry.py` — `DocumentRegistry` for parser/writer registration
    - `engines/document/models/media_types.py` — `MediaTypeRegistry`
    - `engines/orchestration/integration/connector_registry.py` — `ConnectorRegistry`

43. Pipeline — Chain of processing stages (preprocess → execute → postprocess → archive).
44. Saga — Distributed transactions across multiple services (compensating actions for failures).

=== ENTERPRISE INTEGRATION PATTERNS (For BPMS integration) ===

45. Message Channel — Queues for inter-agent communication.
46. Message Router — Route messages to different agents based on content.
47. Splitter — Break large process into parallel branches.
48. Aggregator — Combine parallel branch results.
49. Scatter-Gather — Send to multiple services, aggregate responses.
50. Dead Letter Channel — Handle failed messages.
51. Wire Tap — Inspect messages without affecting flow (for monitoring).

=== ADDITIONAL PATTERNS FOUND IN CODEBASE ===

52. **[APPLIED] Mixin** — Compose parser functionality without deep inheritance (25+ mixin classes).
    - `engines/document/parsers/usdm_parsers/docx/` — 6 mixins for DOCXParser, 6 for DOCXExtractor, 3 for DocxUtils
    - `engines/document/parsers/usdm_parsers/latex/` — 6 mixins for LatexParser
    - `engines/document/parsers/usdm_parsers/html/` — 4 mixins for HTMLParser (media, table, form, semantic)
    - `engines/document/parsers/osdm_parsers/bpmn_xml_parser.py` — 4 mixins (flow_parser, collaboration, root_element, diagram)

53. **[APPLIED] Dispatch Dict / Registry Dispatch** — Replace long elif chains with O(1) dict lookups.
    - `engines/orchestration/bpmn/activity_handler.py:139` — `_ACTIVITY_DISPATCH: dict[type, tuple[str, str]]` (replaced 2 isinstance chains)
    - `engines/orchestration/dmn/feel_engine.py:549` — `_OP_HANDLERS: dict[str, str]` (replaced 30-branch elif)
    - `engines/orchestration/runtime/osdm_serializer.py:315` — `_FLOW_ELEMENT_HANDLERS: list[tuple[str, str]]` (replaced 21-branch elif)
    - `engines/orchestration/dmn/hit_policy_handler.py:89` — `_HIT_POLICY_HANDLERS: dict[HitPolicy, Callable]` (replaced 12-branch elif)
    - `engines/orchestration/cep/rule_evaluator.py:76` — `_OPERATOR_HANDLERS: dict[str, Callable]` (replaced 11-branch elif)
    - `engines/orchestration/cep/aggregator.py:85` — `_AGGREGATION_HANDLERS: dict[str, Callable]` (replaced 11-branch elif)
    - `engines/orchestration/core/engine_services.py` — dispatch dict for state transitions (replaced 5-way if/elif)

=== RULES FOR THIS PROJECT ===

1. **[APPLIED]** State pattern is MANDATORY for Process and Task lifecycles (5 state machines applied).
2. **[APPLIED]** Observer pattern is MANDATORY for all events (EventBus + ListenerManagers + engine lifecycle events).
3. **[APPLIED]** Command pattern is MANDATORY for operation queue and undo/redo (2 implementations).
4. **[APPLIED]** Strategy pattern for routing (XOR, AND, OR gateways) — GatewayStrategy hierarchy.
5. **[APPLIED]** Visitor pattern for model validation and export — ModelVisitor + Validator.
6. **[APPLIED]** DI (Constructor Injection) for all dependencies — ubiquitous across all engines.

When you write code:
- Identify which pattern(s) fit the problem BEFORE writing.
- Name classes clearly: XxxFactory, XxxStrategy, XxxState, XxxCommand.
- Do NOT over-engineer. Start simple, refactor into pattern only when needed.
- Always ask: "Will this pattern make the code easier to understand and change?"
- Prefer dispatch dicts over long elif isinstance chains (registry pattern over Visitor for simple dispatch).
- Use mixins for parsing functionality to keep parsers manageable while preserving existing method signatures.

Generate code now based on these patterns.
