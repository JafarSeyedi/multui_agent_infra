# ARCHITECTURE DOCUMENT
## The Agentic, Model-Driven, Polymorphic Distributed BPMS

---

## Table of Contents

1. Introduction
2. Architectural Guiding Principles
3. The Engine Ecosystem
4. Strategic Domain Design (Model-Centric DDD)
5. Tactical DDD & Clean Architecture Implementation (.NET 10)
6. Declarative Model Repository & Versioning
7. Modular Monolith Structure
8. The Polymorphic Runtime Engine (Deployment-as-Code)
9. Communication & Service Discovery Abstraction
10. Transactions, Consistency, & The Outbox Pattern
11. Distributed Locking & Leader Election
12. State Management, Caching, & Time Abstraction
13. Security & Identity (mTLS, JWT, SPIFFE)
14. Observability (Tracing, Logs, Metrics, BAM, Process Mining)
15. Resilience Engineering (Bulkheads, Circuit Breakers, Retries)
16. Data Schema Evolution & Event Versioning
17. CI/CD & Infrastructure as Code (IaC)
18. Testing Strategy (Unit, Integration, Contract, Chaos)
19. Operational Runbooks & Disaster Recovery
20. Appendices (Configuration Schemas, Engine APIs, Code Samples)

---

## 1. Introduction

### 1.1 System Identity & Core Characteristics

The system is a business-critical, enterprise-grade **Agentic, Model-Driven Business Process Management Suite (BPMS)** . It is not a traditional code-first application. It is a meta-platform where business behavior is defined declaratively, stored as models, and executed by a fleet of specialized, pluggable engines.

The architecture is founded on the following core identities:

- **Agentic:** The system orchestrates a swarm of autonomous agents (both human-task and system-task) that interact, negotiate, and execute work. Agents are not passive components; they possess autonomy, reactivity, proactiveness, and social ability. They interact using standard protocols such as A2A (Agent-to-Agent) and MCP (Model Context Protocol).

- **Model-Driven:** Every piece of business logic—process flows, decision tables, case management, event patterns, state machines, UI forms, data semantics, artifact templates, and even agent interaction strategies—is defined in declarative file formats (standards-based or custom DSLs). The engines are pure interpreters. Business knowledge is externalized from code.

- **Domain-Driven Design (DDD):** The system is partitioned by business capabilities (Bounded Contexts). Each context owns its specific models, runtime state, and execution semantics. The Ubiquitous Language is defined in the models themselves and the canonical schemas exposed to agents.

- **Clean Architecture (Hexagonal):** Source code dependencies point inward. Engines and Use Cases depend only on Ports (interfaces). Infrastructure adapters (databases, message buses, caches, service meshes) are pluggable and isolated.

- **Modular Monolith:** The system is physically deployed as a single process (or container image) in development and staging, allowing for fast integration testing and single-step debugging. This single process contains strictly isolated modules that cannot violate each other's data boundaries. The same module boundaries are preserved when the system is distributed in production.

- **Polymorphic Runtime / Deployment Agnosticism:** The exact same compiled binaries can run as an in-memory library (for rapid development), as a set of Docker Compose services (for integration testing), or as a globally distributed Kubernetes fleet with Istio service mesh (for production). The runtime topology is switched purely via Dependency Injection (DI) configuration, driven by Infrastructure-as-Code (IaC) and environment variables.

- **Declarative Model Repository & Versioning:** All declarative models (BPMN, DMN, CMMN, forms, document templates, etc.) are stored in a version-controlled artifact registry. Every runtime execution references a specific model version, enabling canary deployments, A/B testing, and auditability of business logic changes independent of engine code.

- **Artifact Management:** The system includes a comprehensive artifact management capability. It parses, renders, generates, and transforms a wide range of artifact formats, including but not limited to: docx, pdf, xlsx, pptx, html, markdown, raw data, CAD files, and source code. Artifacts can be used as input to engines (e.g., document templates for contract generation) or as output of processes.

- **Complete Engine Ecosystem:** The system provides a full basket of execution engines that are independent of platform, industry, and business knowledge. These engines are extensible and configurable. They include, as examples: BPMN Engine, CMMN Engine, DMN Engine, CEP Engine, StateMachine Engine, Multi-Agent Interaction Engines and strategies, libraries for all message-bus and RPC strategies and tools integration, a full knowledge engine (RAG, graph, semantic, ML/data-mining, process mining), observation and monitoring (BAM), data ingest, and full context management. These engines are model-driven; their behavior is fully defined by declarative models.

- **Service Exposure and Consumption:** The system provides layers for exposing its capabilities as services (REST, gRPC, GraphQL, events) and for consuming external services. These layers are also model-driven, with entity definitions, BPMN models, form and UI definitions, and integration contracts defined declaratively per domain.

### 1.2 Scope

This document defines the definitive architectural standard for the system. It serves as the single source of truth for development teams, infrastructure engineers, model designers, and customer technical stakeholders. It describes not only what the system does, but how it adapts to its environment—from a developer's laptop to a globally distributed Kubernetes fleet.

The architecture covers:

- The engine ecosystem and their abstractions.
- Strategic and tactical DDD applied to models and runtime state.
- Clean Architecture implementation in .NET 10 with Aspect-Oriented Programming.
- The declarative model repository, artifact management, and versioning strategy.
- The polymorphic runtime engine and deployment-as-code.
- Distributed systems abstractions: communication, transactions, locks, state, time, security, observability, and resilience.
- Data schema evolution, event versioning, and schema registry integration.
- CI/CD pipelines, Infrastructure-as-Code, and environment toolchains.
- Testing strategy and operational runbooks.

### 1.3 Audience

- **Developers and Engine Engineers:** To understand boundaries, coding standards, abstraction layers, and engine extension points.
- **Model Designers and Citizen Developers:** To understand how their BPMN, DMN, and other declarative models are versioned, deployed, and executed.
- **Customer Technical Engineers:** To verify infrastructure compliance, security, scalability, and integration capabilities.
- **DevOps and SRE Teams:** To manage the polymorphic topology across Dev, Staging, and Production environments, and to understand the IaC contracts.

### 1.4 Glossary of Core Terms

| Term | Definition |
| :--- | :--- |
| **Bounded Context** | A logical boundary within which a specific domain model applies and has meaning. In this system, each context owns its models and runtime state. |
| **Aggregate** | A cluster of domain objects treated as a single unit for data changes. Aggregates are persisted as a whole. |
| **Domain Event** | A fact about something that happened within the domain. Domain events are the primary mechanism for cross-context communication and eventual consistency. |
| **Port** | An interface defined in the Core or Application layer that the outer layers implement (Clean Architecture). |
| **Adapter** | The concrete implementation of a Port in the Infrastructure layer. |
| **Polymorphic Runtime** | The ability for a single compiled artifact to switch between in-memory, synchronous RPC (gRPC/HTTP), or asynchronous message-bus (Kafka) communication strategies based on environment configuration. |
| **Deployment-as-Code** | The practice of defining the runtime topology (pods, scaling, infrastructure patterns, service mesh configuration, and adapter selection) in declarative IaC scripts, which are version-controlled alongside the application code. |
| **Declarative Model** | A file (BPMN XML, DMN XML, JSON Schema, etc.) that defines business logic, rules, UI, or data structures independently of engine implementation. |
| **Engine** | A stateless interpreter that reads declarative models and produces commands and events. Engines contain zero business logic. |
| **Artifact** | Any file or data payload that is managed by the system, including documents, templates, generated files, and raw data. |
| **Agent** | An autonomous entity that executes tasks, makes decisions, and interacts with other agents using A2A or MCP protocols. |
| **A2A** | Agent-to-Agent communication protocol. |
| **MCP** | Model Context Protocol for providing context to agents. |

---

## 2. Architectural Guiding Principles

### 2.1 Model-Engine Separation (The Law of Interpreters)

Engines are pure, stateless interpreters. They take a declarative model and a current state (context) as input and produce a set of commands and domain events as output. All business knowledge is externalized into declarative model files. Updating business logic does not require recompilation or redeployment of the engine binaries; it only requires updating the model in the repository and triggering a hot-reload or version switch.

This principle applies to all engines:

- **BPMN Engine:** Interprets process models, advances tokens, triggers tasks, and emits events.
- **DMN Engine:** Evaluates decision tables and returns decisions.
- **CMMN Engine:** Interprets case models, handles ad-hoc tasks, and manages milestones.
- **CEP Engine:** Matches event patterns over time windows.
- **StateMachine Engine:** Processes state transitions based on events.
- **Multi-Agent Engine:** Executes interaction protocols (negotiation, auctions, delegation).
- **Knowledge Engine:** Interprets semantic queries, performs RAG retrievals, and executes graph traversals.
- **Artifact Engine:** Interprets templates and data bindings to generate documents.

All engines operate on generic data structures. They do not contain any platform-specific, industry-specific, or business-specific knowledge.

### 2.2 Domain-Driven Design (DDD) Applied to Models

Bounded Contexts are defined by business capabilities. Each context owns:

- A **Model Repository** folder containing all declarative definitions (BPMN, DMN, Forms, UI schemas, Artifact templates) specific to that capability.
- A dedicated **Database Schema** for its runtime state (process instances, decision execution logs, case instances, state machine states).
- A dedicated **Event Topic Prefix** in the message bus (Kafka) for its domain events.
- A dedicated set of **Aggregates** that represent the runtime execution state.

The Ubiquitous Language is defined in the models themselves and the canonical schemas exposed to agents and external consumers. Models are authored in collaboration with business stakeholders.

### 2.3 Clean Architecture (Hexagonal)

The architecture strictly adheres to the Dependency Rule: source code dependencies point inward.

- **Domain Layer (Core):** Contains Aggregates, Entities, Value Objects, and Domain Events. Has no external dependencies.
- **Application Layer:** Contains Use Cases, Ports (interfaces), and Engine interpreters. Depends only on Domain.
- **Infrastructure Layer:** Contains concrete Adapters (repositories, message buses, caches, service discovery, locks, clocks, security providers). Depends on Application and Domain.
- **Presentation / Delivery Layer:** Contains REST/gRPC/GraphQL controllers, model endpoints, and UI backend. Depends on Infrastructure.

Cross-cutting concerns (logging, tracing, resilience, security) are implemented via Aspect-Oriented Programming (AOP) using .NET 10 source generators and interceptors, keeping the core layers clean.

### 2.4 Modular Monolith as the Physical Container

The system is deployed as a single process (one executable, one container image) in development and staging. This allows for lightning-fast integration testing, single-step debugging across domain boundaries, and simplified deployment pipelines.

However, this single process contains strictly isolated modules. Modules are physically separated at the project level. Compile-time rules prevent cross-module references. Communication between modules occurs exclusively through:

- **Message Bus (Events):** For asynchronous, eventually consistent communication.
- **Query Interfaces (gRPC/HTTP):** For synchronous read-only queries (e.g., "Get order status").

Direct method calls, shared database tables, or shared domain entities between modules are forbidden.

### 2.5 Deployment Agnosticism (The Polymorphic Core)

The system is designed to run on multiple topological planes. The same compiled binary adapts its behavior based on the runtime environment.

| Environment | Communication Topology | Transaction Strategy | Locking Strategy | Service Discovery |
| :--- | :--- | :--- | :--- | :--- |
| **Development (Local)** | In-memory direct method calls | Outbox Polling (synchronous mock) | In-Memory Reentrant Locks | Localhost / File-based |
| **Docker Compose** | In-memory or gRPC/HTTP (optional) | Outbox with local transactional mock | Redis (local container) | Consul (local container) |
| **Staging (K8s)** | gRPC/HTTP + Kafka | Outbox + Debezium + Saga Coordinator | Redis / etcd | Consul + Istio |
| **Production (K8s)** | gRPC/HTTP + Kafka | Outbox + Debezium + Saga Coordinator | etcd (leases) or Redis Redlock | Consul + Istio + K8s DNS |

The compilation output is identical for all environments. The topology is switched via Dependency Injection (DI) container configuration, driven by environment variables set by Infrastructure-as-Code (IaC).

### 2.6 Versioned Declarative Repository

All declarative models (BPMN, DMN, CMMN, Forms, UI configurations, Artifact templates, data schemas) are stored in a version-controlled artifact repository (similar to Git LFS or a dedicated Model Registry). The repository exposes a versioning API:

- **Semantic Versioning** is applied to every model artifact.
- **Immutable Versions:** Once a model version is marked `RELEASED`, it cannot be modified. Bug fixes require a new version (`patch` increment).
- **Canary Deployments:** The IaC topology maps specific `VersionTags` to specific engine pods. 90% of traffic uses `v1.0`, 10% uses `v1.1` (canary) without recompiling the engine.
- **Audit Trail:** Every execution references the exact model version that was used, enabling full traceability.

### 2.7 Zero Business Logic in Infrastructure

Infrastructure adapters (databases, caches, message buses, service meshes, security providers) contain zero business logic. They implement generic interfaces defined in the Application layer. This enables:

- **Framework Independence:** The core engines do not depend on any specific ORM, messaging library, or cloud SDK.
- **Testability:** Business logic can be unit-tested with in-memory stubs.
- **Portability:** The system can be moved from on-premise to any cloud without changing a single line of engine code.

### 2.8 Engine Independence from Platform and Business Knowledge

All engines are designed to be completely independent of:

- **Platform:** The engines do not know if they are running on Windows, Linux, or Kubernetes. They only interact with the environment through well-defined Ports.
- **Industry:** The engines do not contain any industry-specific rules (healthcare, finance, manufacturing, etc.). Those rules are expressed solely in declarative models.
- **Business Knowledge:** The engines do not contain any business logic. They interpret models. Business knowledge is injected at runtime via the Model Repository.

Each layer and engine has its own file format standards. Examples include:
- BPMN Engine: BPMN 2.0 XML.
- DMN Engine: DMN 1.3 XML.
- CMMN Engine: CMMN 1.1 XML.
- StateMachine Engine: SCXML or custom Statechart JSON.
- CEP Engine: Custom DSL or Drools/Flink rule sets.
- Artifact Engine: Microsoft Open XML (docx, xlsx, pptx), PDF/A, HTML5, Markdown, CAD formats, source code files, raw data formats.
- UI Engine: JSON Schema based forms, Vue/React component definitions.
- Knowledge Engine: OpenAPI, GraphQL, SPARQL, vector index schemas.

The system is extensible to support additional engines and file formats beyond these examples.

---

## 3. The Engine Ecosystem

The system provides a comprehensive, extensible basket of execution engines. Engines are stateless domain services. They are invoked by Use Cases and produce commands and events.

### 3.1 Engine Abstraction

Every engine in the system conforms to a common abstraction:

```csharp
public interface IEngine<TModel, TContext, TResult>
{
    Task<TResult> ExecuteAsync(TModel model, TContext context, CancellationToken ct);
}
```

- `TModel` is the declarative model (e.g., BpmnModel, DmnModel).
- `TContext` is the execution context (variables, current state, agent identity, etc.).
- `TResult` contains the commands generated, events emitted, and any decision outcomes.

Engines are stateless. All state is passed in via the context and stored by the caller (Use Case) after execution.

### 3.2 Examples of Engines (Non-Exhaustive List)

The system includes, but is not limited to, the following engines. Additional engines can be developed and plugged in using the same extension model.

#### 3.2.1 BPMN Engine

- **Purpose:** Orchestrates long-running, stateful process flows (human tasks, system tasks, sub-processes, event sub-processes).
- **Standards:** BPMN 2.0 XML.
- **Capabilities:** Token-based execution, parallel gateways, event-based gateways, timer events, error boundaries, compensation, call activities.
- **Inputs:** Process model (BPMN), process variables, current active node.
- **Outputs:** Next nodes to activate, tasks to assign, timers to schedule, events to emit.

#### 3.2.2 CMMN Engine

- **Purpose:** Manages dynamic, case-based work (ad-hoc tasks, milestones, planning stages).
- **Standards:** CMMN 1.1 XML.
- **Capabilities:** Case file items, manual activation, discretionary tasks, sentry conditions, milestone completion.
- **Inputs:** Case model, case file state, active stages.
- **Outputs:** Tasks to offer, milestones to complete, events to emit.

#### 3.2.3 DMN Engine

- **Purpose:** Evaluates complex business rules and decision tables.
- **Standards:** DMN 1.3 XML.
- **Capabilities:** Decision tables, FEEL expressions, context mapping, input data binding, decision requirements graphs.
- **Inputs:** Decision model, input data (variables).
- **Outputs:** Decision outputs (scalar, table, context).

#### 3.2.4 CEP Engine

- **Purpose:** Detects complex event patterns over streaming data (time windows, correlations, aggregations, sequence patterns).
- **Standards:** Custom DSL (based on Drools/Flink ruleset or custom JSON-based event pattern language).
- **Capabilities:** Sliding windows, tumbling windows, event correlation, temporal constraints, pattern matching, alert generation.
- **Inputs:** Event streams, pattern definitions.
- **Outputs:** Pattern matches, alerts, derived events.

#### 3.2.5 StateMachine Engine

- **Purpose:** Manages finite-state transitions for entities.
- **Standards:** SCXML (State Chart XML) or custom Statechart JSON.
- **Capabilities:** Hierarchical states, parallel states, guards, actions, transitions, history states.
- **Inputs:** Statechart model, current state, triggering event.
- **Outputs:** New state, actions to execute, events to emit.

#### 3.2.6 Multi-Agent Interaction Engine

- **Purpose:** Coordinates agent-to-agent interaction protocols (negotiation, auction, contract-net, delegation, argumentation).
- **Standards:** A2A (Agent-to-Agent) protocol, MCP (Model Context Protocol), custom negotiation DSL.
- **Capabilities:** Protocol execution, bidding, proposal evaluation, contract establishment, agent role assignment.
- **Inputs:** Agent definitions, protocol model, participant state.
- **Outputs:** Protocol steps, messages to agents, agreements, contracts.

#### 3.2.7 Knowledge Engine

- **Purpose:** Provides context, semantic understanding, and analytical insights.
- **Standards:** OpenAPI, GraphQL, SPARQL, vector index APIs.
- **Sub-components:**
  - **RAG (Retrieval-Augmented Generation):** Retrieves relevant documents from vector stores and provides them as context to LLMs.
  - **Graph Traversal:** Executes queries against graph databases (Neo4j, AWS Neptune) to find relationships.
  - **Semantic Search:** Uses embeddings to find semantically similar content.
  - **ML / Data-Mining:** Executes predictive models (ML.NET, ONNX) and clustering algorithms.
  - **Process Mining:** Analyses XES event logs to discover process variations, bottlenecks, and conformance violations.
- **Inputs:** Query (text, vector, graph pattern), analytical model.
- **Outputs:** Context bundles (documents, graph paths, predictions, mining insights).

#### 3.2.8 Observation & BAM (Business Activity Monitoring) Engine

- **Purpose:** Monitors execution logs, metrics, and events to provide real-time dashboards, alerts, and performance indicators.
- **Standards:** Custom OLAP cubes, XES logs, Prometheus metrics, OpenTelemetry spans.
- **Capabilities:** SLA monitoring, KPI tracking, anomaly detection, trend analysis, root-cause analysis.
- **Inputs:** Telemetry data (traces, metrics, logs), monitoring dashboards.
- **Outputs:** Dashboards, alerts, aggregated reports.

#### 3.2.9 Data Ingest Engine

- **Purpose:** Receives, validates, transforms, and routes incoming data from external sources into the system's storage or processing pipelines.
- **Standards:** REST, gRPC, Kafka, MQTT, file uploads (multipart).
- **Capabilities:** Data validation (schema validation), transformation (mapping, enrichment), deduplication, routing to Bounded Contexts.
- **Inputs:** Raw data payloads (JSON, XML, CSV, binary).
- **Outputs:** Normalized domain events, stored artifacts, notifications.

#### 3.2.10 Context Management Engine

- **Purpose:** Manages the lifecycle of execution contexts, including variable persistence, context inheritance, and context sharing across agents and processes.
- **Standards:** JSON Schema, custom context definition models.
- **Capabilities:** Context creation, snapshots, merging, versioning, permission control.
- **Inputs:** Context definitions, parent contexts, updates.
- **Outputs:** Context instances, context history.

#### 3.2.11 Artifact Management Engine

- **Purpose:** Parses, renders, generates, and transforms artifacts of various formats.
- **Standards / Formats (examples):** Microsoft Open XML (docx, xlsx, pptx), PDF/A, HTML5, Markdown, plain text, raw binary data, CAD formats (e.g., STEP, IGES), source code files (cs, py, java, etc.), JSON, XML, CSV, Avro, Protobuf.
- **Capabilities:**
  - **Parsing:** Extract structured data from artifacts (e.g., table data from xlsx, text from pdf).
  - **Rendering / Generation:** Populate templates with data and produce artifacts (e.g., generate a contract docx from a template and variables).
  - **Transformation:** Convert between formats (e.g., docx to pdf, markdown to html).
  - **Validation:** Validate artifacts against schemas or business rules.
- **Inputs:** Artifact template, data bindings, source artifacts.
- **Outputs:** Generated artifacts, parsed data structures.

#### 3.2.12 Service Exposure Layer

- **Purpose:** Exposes the capabilities of the system as external services (REST APIs, gRPC services, GraphQL endpoints, event streams).
- **Standards:** OpenAPI (Swagger), gRPC Protobuf, GraphQL Schema, AsyncAPI.
- **Capabilities:** Request routing, input validation, authentication/authorization, rate limiting, versioning, documentation generation.
- **Inputs:** Incoming requests (HTTP, gRPC).
- **Outputs:** Responses (JSON, Protobuf), emitted events.

#### 3.2.13 Service Consumption Layer

- **Purpose:** Consumes external services (third-party APIs, legacy systems, partner services) as part of engine execution.
- **Standards:** REST, gRPC, SOAP, GraphQL, Kafka (for consuming external events).
- **Capabilities:** Connection management, retry policies, circuit breakers, request transformations, response mapping.
- **Inputs:** External request definitions (models).
- **Outputs:** Data mapped into the system's domain.

#### 3.2.14 Multi-Agent Interaction Strategies

- **Purpose:** Provides configurable strategies for agent interaction protocols.
- **Examples:** Auction (forward/reverse), Contract-Net, Negotiation (bargaining), Delegate/Re-delegate, Vote, Argue.
- **Inputs:** Protocol configuration, agent capabilities, proposal history.
- **Outputs:** Protocol outcomes (winner, contract, agreement).

#### 3.2.15 Libraries for Message-Bus and RPC Strategies and Tools Integration

- **Purpose:** Provides adapters for standard message-bus and RPC tools.
- **Examples:** Kafka, RabbitMQ, Azure Service Bus, AWS SQS/SNS, gRPC, HTTP/REST, GraphQL subscriptions.
- **Capabilities:** Publish/Subscribe, Request/Reply, Fire-and-Forget, Streaming, Schema Registry integration, message serialization (Avro, Protobuf, JSON).

### 3.3 Engine Interoperability and Composition

Engines can be composed to handle complex scenarios. For example:

- A BPMN process contains a **Business Rule Task** that invokes the DMN Engine.
- A CMMN case contains a **StateMachine** that manages the case file item state.
- A BPMN process sends a message to a **Multi-Agent Interaction Engine** to negotiate a contract.
- The **CEP Engine** detects an anomaly and triggers a **BPMN sub-process** for exception handling.

Composition is achieved through the Use Case layer. Use Cases orchestrate multiple engines and manage their interaction via commands and events.

### 3.4 Engine Extension Model

To add a new engine:

1. Define the declarative model schema (JSON, XML, or custom).
2. Implement the `IEngine<TModel, TContext, TResult>` interface.
3. Register the engine in the DI container.
4. Add a model loader to the `IModelRepository` for the new model type.
5. (Optional) Add an AOP interceptor for tracing/resilience specific to the engine.

No changes to the core architecture are required.

---

## 4. Strategic Domain Design (Model-Centric DDD)

### 4.1 Generic Domain Definition

In this architecture, Bounded Contexts are defined as containers for correlated declarative models and runtime state. A context is not defined by a fixed set of business entities (like "Billing" or "Inventory"); rather, it is defined by the set of models it owns and the runtime instances it manages.

The system provides the ability to create, modify, and version Bounded Contexts dynamically through a provisioning layer. The definition of a Bounded Context includes:

1. **Model Repository Folder:** A logical directory in the model registry containing all declarative models (BPMN, DMN, CMMN, UI forms, document templates, data schemas) for that context.
2. **Database Schema:** A dedicated schema (or set of tables) for storing runtime state (process instances, case instances, decision logs, state machine states, artifact history).
3. **Message Bus Prefix:** A dedicated prefix for Kafka topics or RabbitMQ exchanges. All domain events emitted by this context are scoped to this prefix.
4. **Service Endpoint:** A base path for REST/gRPC endpoints exposed by the context.
5. **Agent Pools:** The set of agent roles and instances that operate within this context.

### 4.2 Context Ownership Rules

- **Model Ownership:** Each model artifact belongs to exactly one Bounded Context. The owning context is responsible for the model's lifecycle, versioning, and validation.
- **State Ownership:** Each runtime aggregate (process instance, case file, state machine instance) belongs to exactly one context. The owning context is the sole writer for that state.
- **Event Ownership:** Each domain event belongs to the context that emits it. The event schema is versioned alongside the context's models.

### 4.3 Context Mapping (Inter-Context Communication)

Contexts are decoupled and communicate through well-defined contracts.

#### 4.3.1 Asynchronous Event-Based Communication

This is the primary communication mechanism for state changes and workflow transitions.

- A context emits a Domain Event (e.g., `ContractSigned`, `OrderPlaced`, `CustomerOnboarded`).
- The event is published to the message bus (Kafka) with the event schema registered in the Schema Registry.
- Other contexts subscribe to events of interest via their event handlers.
- The event handler translates the event into a command for the receiving context.
- Communication is eventually consistent. There are no synchronous dependencies between contexts.

#### 4.3.2 Synchronous Query Communication

This is used for read-only, real-time information retrieval.

- A context exposes a gRPC or REST query endpoint (e.g., `GetContractStatus`, `GetCustomerBalance`).
- Another context or an external client invokes the endpoint synchronously.
- The endpoint uses a dedicated read model or projection (eventually consistent) to serve the query.
- This pattern is used when real-time response is required and eventual consistency is acceptable.

#### 4.3.3 Command-Based (Synchronous) Communication

This is discouraged for cross-context communication due to coupling. However, for operations that require immediate consistency across contexts (rare), a synchronous command pattern with a distributed transaction (Saga) can be used.

### 4.4 Anti-Corruption Layers (ACL)

Each context implements an Anti-Corruption Layer at its boundary. The ACL:

- Translates incoming events from external contexts into the receiving context's Ubiquitous Language.
- Translates outgoing commands and events from the sending context into the canonical schemas expected by consumers.
- Handles protocol mismatches (e.g., JSON vs. Avro, HTTP vs. gRPC).
- Protects the internal domain model from external changes.

The ACL is implemented as an infrastructure adapter that maps between external schemas and internal domain events.

### 4.5 Provisioning of New Contexts

New contexts are provisioned through a bootstrap process:

1. A new context is defined in the IaC repository (namespace, database schema, service endpoints).
2. The Model Repository is seeded with initial models (empty BPMN processes, starter DMN tables).
3. The context is registered with the DI container via a feature flag.
4. The context becomes available for model designers to populate.

This enables the platform to support arbitrary business domains without code changes.

---

## 5. Tactical DDD & Clean Architecture Implementation (.NET 10)

### 5.1 Project Structure (Vertical Slices per Engine / Module)

The physical codebase is organized into vertical slices, each representing a module (which may contain one or more engines). Within each module, Clean Architecture layers are enforced.

```
src/
├── Modules/
│   ├── ProcessEngine.BPMN/
│   │   ├── ProcessEngine.BPMN.Domain/                    # No dependencies
│   │   │   ├── Aggregates/
│   │   │   │   ├── ProcessDefinition.cs
│   │   │   │   ├── ProcessInstance.cs
│   │   │   │   └── ProcessToken.cs
│   │   │   ├── Entities/
│   │   │   │   ├── TaskInstance.cs
│   │   │   │   └── TimerInstance.cs
│   │   │   ├── ValueObjects/
│   │   │   │   ├── ProcessId.cs
│   │   │   │   ├── TaskId.cs
│   │   │   │   └── VariableSet.cs
│   │   │   └── DomainEvents/
│   │   │       ├── ProcessStartedEvent.cs
│   │   │       ├── TaskAssignedEvent.cs
│   │   │       └── ProcessCompletedEvent.cs
│   │   ├── ProcessEngine.BPMN.Application/              # Depends only on Domain
│   │   │   ├── UseCases/
│   │   │   │   ├── StartProcess/
│   │   │   │   │   ├── StartProcessCommand.cs
│   │   │   │   │   ├── StartProcessUseCase.cs
│   │   │   │   │   └── StartProcessResult.cs
│   │   │   │   ├── CompleteTask/
│   │   │   │   │   ├── CompleteTaskCommand.cs
│   │   │   │   │   └── CompleteTaskUseCase.cs
│   │   │   │   └── ExecuteTimer/
│   │   │   │       └── ExecuteTimerUseCase.cs
│   │   │   ├── Ports/
│   │   │   │   ├── IProcessInstanceRepository.cs
│   │   │   │   ├── IModelRepository.cs (BPMN models)
│   │   │   │   ├── IUserTaskHandler.cs
│   │   │   │   ├── ITimerScheduler.cs
│   │   │   │   └── IMessageBus.cs
│   │   │   ├── Engines/
│   │   │   │   ├── BpmnEngine.cs (implements IEngine)
│   │   │   │   ├── BpmnParser.cs
│   │   │   │   └── BpmnValidator.cs
│   │   │   ├── DTOs/
│   │   │   │   ├── ProcessDefinitionDto.cs
│   │   │   │   └── TaskAssignmentDto.cs
│   │   │   └── DomainEventHandlers/
│   │   │       ├── SignalEventHandler.cs
│   │   │       └── TimerEventHandler.cs
│   │   ├── ProcessEngine.BPMN.Infrastructure/           # Depends on App + Domain
│   │   │   ├── Adapters/
│   │   │   │   ├── Repositories/
│   │   │   │   │   ├── EFCoreProcessInstanceRepository.cs
│   │   │   │   │   ├── InMemoryProcessInstanceRepository.cs
│   │   │   │   │   └── OutboxRepository.cs
│   │   │   │   ├── ModelRepository/
│   │   │   │   │   ├── FileSystemModelRepository.cs
│   │   │   │   │   └── GitLabModelRepository.cs
│   │   │   │   ├── UserTaskHandler/
│   │   │   │   │   ├── InMemoryTaskHandler.cs
│   │   │   │   │   └── KafkaTaskHandler.cs (publishes to agent task queue)
│   │   │   │   ├── TimerScheduler/
│   │   │   │   │   ├── InMemoryTimerScheduler.cs
│   │   │   │   │   └── QuartzTimerScheduler.cs (distributed)
│   │   │   │   ├── MessageBus/
│   │   │   │   │   ├── InMemoryBus.cs
│   │   │   │   │   └── KafkaBus.cs
│   │   │   │   └── Cache/
│   │   │   │       ├── LocalCacheAdapter.cs
│   │   │   │       └── RedisCacheAdapter.cs
│   │   │   ├── DI/
│   │   │   │   └── BpmnModuleCompositionRoot.cs
│   │   │   ├── Migrations/
│   │   │   │   └── (EF Core migrations for process instances)
│   │   │   └── Outbox/
│   │   │       ├── OutboxProcessor.cs
│   │   │       └── DebeziumOutboxRelay.cs
│   │   └── ProcessEngine.BPMN.Api/                      # Depends on Infrastructure
│   │       ├── Controllers/
│   │       │   ├── ProcessController.cs
│   │       │   └── TaskController.cs
│   │       ├── Middleware/
│   │       │   ├── ErrorHandlingMiddleware.cs
│   │       │   └── TraceMiddleware.cs
│   │       └── OpenAPI/
│   │           └── OpenApiDocumentation.cs
│   ├── DecisionEngine.DMN/                               # Similar structure
│   ├── CMMNEngine/                                      # Similar structure
│   ├── StateMachineEngine/                              # Similar structure
│   ├── CEPEngine/                                       # Similar structure
│   ├── MultiAgentEngine/                                # Similar structure
│   ├── KnowledgeEngine/                                 # Similar structure
│   ├── ArtifactEngine/                                  # Similar structure
│   ├── ContextManagementEngine/                         # Similar structure
│   ├── DataIngestEngine/                                # Similar structure
│   ├── ObservationEngine/                               # Similar structure
│   ├── ServiceExposure/                                 # Similar structure
│   └── ServiceConsumption/                              # Similar structure
├── Shared/
│   ├── Shared.Abstractions/                             # Core Ports
│   │   ├── Messaging/
│   │   │   ├── IMessageBus.cs
│   │   │   └── IEventPublisher.cs
│   │   ├── Persistence/
│   │   │   ├── IUnitOfWork.cs
│   │   │   └── IRepository.cs
│   │   ├── Locking/
│   │   │   └── IDistributedLock.cs
│   │   ├── Caching/
│   │   │   └── ICacheManager.cs
│   │   ├── Time/
│   │   │   └── IClock.cs
│   │   ├── Security/
│   │   │   ├── ISecurityContext.cs
│   │   │   └── IIdentityProvider.cs
│   │   ├── Observability/
│   │   │   ├── ITracer.cs
│   │   │   └── ILogger.cs
│   │   ├── Resilience/
│   │   │   ├── ICircuitBreaker.cs
│   │   │   └── IRetryPolicy.cs
│   │   ├── ModelRepository/
│   │   │   └── IModelRepository.cs
│   │   └── Artifact/
│   │       ├── IArtifactParser.cs
│   │       ├── IArtifactGenerator.cs
│   │       └── IArtifactStorage.cs
│   ├── Shared.Infrastructure/                           # Shared Adapters
│   │   ├── Persistence/
│   │   │   ├── EFCoreUnitOfWork.cs
│   │   │   ├── DapperRepository.cs
│   │   │   ├── OutboxProcessor.cs
│   │   │   └── DebeziumRelay.cs
│   │   ├── Messaging/
│   │   │   ├── KafkaBus.cs
│   │   │   ├── RabbitMqBus.cs
│   │   │   ├── InMemoryBus.cs
│   │   │   └── SchemaRegistryClient.cs
│   │   ├── Locking/
│   │   │   ├── RedisDistributedLock.cs
│   │   │   ├── EtcdDistributedLock.cs
│   │   │   └── LocalReentrantLock.cs
│   │   ├── Caching/
│   │   │   ├── RedisCacheManager.cs
│   │   │   ├── LocalMemoryCache.cs
│   │   │   └── HazelcastCacheManager.cs
│   │   ├── Time/
│   │   │   ├── SystemClock.cs
│   │   │   └── NtpSynchronizedClock.cs
│   │   ├── Security/
│   │   │   ├── JwtValidator.cs
│   │   │   ├── SpiffeIdentityProvider.cs
│   │   │   └── PassthroughIdentityProvider.cs
│   │   ├── ServiceDiscovery/
│   │   │   ├── ConsulServiceDiscovery.cs
│   │   │   ├── KubernetesServiceDiscovery.cs
│   │   │   └── LocalhostServiceDiscovery.cs
│   │   ├── Observability/
│   │   │   ├── OpenTelemetryTracer.cs
│   │   │   ├── ConsoleLogger.cs
│   │   │   └── ElasticLogger.cs
│   │   ├── Resilience/
│   │   │   ├── PollyRetryPolicy.cs
│   │   │   ├── PollyCircuitBreaker.cs
│   │   │   └── NoOpResiliencePolicy.cs
│   │   ├── Artifact/
│   │   │   ├── DocxParser.cs
│   │   │   ├── PdfGenerator.cs
│   │   │   ├── XlsxParser.cs
│   │   │   ├── HtmlRenderer.cs
│   │   │   ├── MarkdownParser.cs
│   │   │   ├── CadParser.cs
│   │   │   ├── CodeParser.cs
│   │   │   ├── MinioArtifactStorage.cs
│   │   │   └── LocalFileArtifactStorage.cs
│   │   ├── Knowledge/
│   │   │   ├── Neo4jGraphClient.cs
│   │   │   ├── MilvusVectorClient.cs
│   │   │   ├── ElasticSearchClient.cs
│   │   │   └── LocalLuceneIndex.cs
│   │   └── ModelRepository/
│   │       ├── GitLabModelRepository.cs
│   │       ├── FileSystemModelRepository.cs
│   │       └── ModelCache.cs
│   └── Shared.Modeling/                                 # Base classes for models
│       ├── ModelMetadata.cs
│       ├── ModelVersion.cs
│       └── ModelValidationResult.cs
└── Hosts/
    └── Main.AppHost/                                    # The Modular Monolith Entry Point
        ├── Program.cs
        ├── CompositionRoot.cs
        ├── appsettings.json
        ├── appsettings.Development.json
        ├── appsettings.Production.json
        └── RuntimeTopology.json                          # Injected via IaC
```

### 5.2 The Domain Layer

- **Aggregates:** Aggregate roots represent the primary stateful entities. For the BPMN Engine: `ProcessDefinition`, `ProcessInstance`. For the DMN Engine: `DecisionDefinition`, `DecisionExecution`.
- **Entities:** Non-root entities within an aggregate (e.g., `TaskInstance`, `ProcessToken`).
- **Value Objects:** Immutable types such as `ProcessId`, `TaskId`, `VariableSet`, `Money`, `Address`.
- **Domain Events:** Facts that have occurred. They are raised by aggregates and collected by the domain event collector.
- **Invariants:** Aggregates enforce their own invariants. For example, a `ProcessInstance` cannot transition to a completed state if there are active tokens.

**No external dependencies** are allowed in the Domain layer. Only the .NET Base Class Library (BCL) and system namespaces are referenced.

### 5.3 The Application Layer

- **Use Cases (Commands/Queries):** Implement the `IRequestHandler<TCommand, TResult>` pattern (abstracted via MediatR or similar). Use Cases orchestrate the flow of data to/from entities and engines.
- **Ports (Interfaces):** Defined purely in Domain/Application terms. Examples:
  - `IProcessInstanceRepository` operates on `ProcessInstance` objects, not `DbConnection`.
  - `IMessageBus` operates on `IDomainEvent` objects, not `ProducerRecord`.
  - `IModelRepository` returns `ModelDefinition` objects, not file paths.
- **Cross-Cutting Abstractions:** The Application layer relies on the following interfaces for distributed concerns:
  - `IDistributedLock`
  - `IMessageBus`
  - `IClock`
  - `ICacheManager`
  - `IUnitOfWork` (only for intra-module transaction boundaries)
- **Engine Interpreters:** The engines are implemented in the Application layer. They are stateless and depend only on Ports.
- **AOP Attributes:** Use Cases and engine methods are decorated with attributes such as `[TraceSpan]`, `[CircuitBreaker]`, `[RetryPolicy]`, `[RateLimit]`. These are intercepted at compile time by .NET 10 source generators.

### 5.4 The Infrastructure Layer

This layer contains concrete implementations of all Ports. The selection of which adapter to use is determined by the DI container based on the `RuntimeTopology` configuration.

| Port Interface | Development Adapter | Docker Compose Adapter | Production Adapter |
| :--- | :--- | :--- | :--- |
| `IProcessInstanceRepository` | `InMemoryProcessInstanceRepository` | `EFCoreProcessInstanceRepository` (SQL Server container) | `EFCoreProcessInstanceRepository` (SQL Server cluster) |
| `IMessageBus` | `InMemoryBus` (synchronous) | `KafkaBus` (local Kafka container) | `KafkaBus` (Confluent Kafka cluster) |
| `IModelRepository` | `FileSystemModelRepository` | `GitLabModelRepository` (local GitLab) | `GitLabModelRepository` (production GitLab) |
| `IDistributedLock` | `LocalReentrantLock` | `RedisDistributedLock` (local Redis) | `EtcdDistributedLock` (etcd cluster) |
| `ICacheManager` | `LocalMemoryCache` | `RedisCacheManager` (local Redis) | `RedisCacheManager` (Redis cluster) |
| `IClock` | `SystemClock` | `SystemClock` | `NtpSynchronizedClock` |
| `ISecurityContext` | `PassthroughIdentityProvider` | `JwtValidator` (local STS) | `SpiffeIdentityProvider` (with Istio mTLS) |
| `IServiceDiscovery` | `LocalhostServiceDiscovery` | `ConsulServiceDiscovery` (local Consul) | `ConsulServiceDiscovery` (Consul cluster) + `KubernetesServiceDiscovery` |
| `ITracer` | `ConsoleLogger` (no spans) | `OpenTelemetryTracer` (local Jaeger) | `OpenTelemetryTracer` (Tempo/Jaeger cluster) |
| `ICircuitBreaker` | `NoOpResiliencePolicy` | `PollyCircuitBreaker` (local) | `PollyCircuitBreaker` (with distributed metrics) |
| `IArtifactStorage` | `LocalFileArtifactStorage` | `MinioArtifactStorage` (local MinIO) | `MinioArtifactStorage` (MinIO cluster) or `S3ArtifactStorage` |
| `IGraphQueryPort` | `LocalLuceneGraph` (embedded) | `Neo4jClient` (local Neo4j) | `Neo4jClient` (Neo4j cluster) or `AwsNeptuneClient` |
| `IVectorSearchPort` | `LocalLuceneIndex` | `MilvusClient` (local Milvus) | `MilvusClient` (Milvus cluster) or `PineconeClient` |
| `ITimerScheduler` | `InMemoryTimerScheduler` | `QuartzTimerScheduler` (local DB) | `QuartzTimerScheduler` (distributed DB) |
| `IOutboxProcessor` | `NoOpOutboxProcessor` (direct send) | `OutboxProcessor` (local DB polling) | `DebeziumOutboxRelay` (CDC to Kafka) |

### 5.5 Aspect-Oriented Programming (AOP) in .NET 10

We leverage .NET 10's enhanced source generators and interceptors to implement cross-cutting concerns without cluttering the core Use Cases or engine code.

**Attributes:**

- `[TraceSpan]`: Automatically starts and ends an OpenTelemetry span around the method.
- `[CircuitBreaker]`: Wraps the method with a circuit breaker policy.
- `[RetryPolicy]`: Applies a retry policy (exponential backoff, jitter).
- `[RateLimit]`: Applies rate limiting (token bucket, sliding window).
- `[Bulkhead]`: Restricts concurrent executions of the method.

**Interceptors:**

At compile time, interceptors generate code that wraps the target method with the specified policies. The interceptor reads the current `RuntimeEnvironment` from configuration:

- In **Development** and **Unit Tests**, `[RetryPolicy]` does nothing (immediate pass-through), `[CircuitBreaker]` is disabled, and `[TraceSpan]` only logs to the console.
- In **Production**, all policies are fully active with production-grade configurations (retry counts, timeout durations, circuit breaker thresholds) loaded from `RuntimeTopology.json`.

This approach ensures that the core logic remains pure and testable, while the hardening is applied at the boundary.

### 5.6 The Composition Root (DI Container)

The `Main.AppHost` is responsible for composing the DI container. It reads the `RuntimeTopology` configuration (from `appsettings.json` + environment overrides) and registers the appropriate adapters.

```csharp
// Program.cs
var builder = WebApplication.CreateBuilder(args);
var topology = builder.Configuration.Get<RuntimeTopology>();

builder.Services.AddSingleton(topology);

// Register shared infrastructure adapters
builder.Services.AddSingleton<IMessageBus>(sp => topology.CommunicationMode switch
{
    CommunicationMode.InMemory => new InMemoryBus(),
    CommunicationMode.Kafka => new KafkaBus(topology.KafkaOptions),
    _ => new InMemoryBus()
});

builder.Services.AddSingleton<IDistributedLock>(sp => topology.LockStrategy switch
{
    LockStrategy.Local => new LocalReentrantLock(),
    LockStrategy.Redis => new RedisDistributedLock(topology.RedisOptions),
    LockStrategy.Etcd => new EtcdDistributedLock(topology.EtcdOptions),
    _ => new LocalReentrantLock()
});

// Register modules (each module registers its own adapters)
builder.Services.AddBpmnModule(topology);
builder.Services.AddDmnModule(topology);
builder.Services.AddCmmnModule(topology);
builder.Services.AddStateMachineModule(topology);
builder.Services.AddCepModule(topology);
builder.Services.AddMultiAgentModule(topology);
builder.Services.AddKnowledgeModule(topology);
builder.Services.AddArtifactModule(topology);
builder.Services.AddContextManagementModule(topology);
builder.Services.AddDataIngestModule(topology);
builder.Services.AddObservationModule(topology);
builder.Services.AddServiceExposureModule(topology);
builder.Services.AddServiceConsumptionModule(topology);

builder.Services.AddScoped<IUnitOfWork, EFCoreUnitOfWork>();

var app = builder.Build();
app.Run();
```

Modules are self-contained. Each module's `AddXxxModule` extension method registers its own repositories, handlers, and engine implementations, using the shared topology to decide which concrete adapters to use.

---

## 6. Declarative Model Repository & Versioning

### 6.1 Model Repository Abstraction

The `IModelRepository` port provides a uniform interface for accessing declarative models.

```csharp
public interface IModelRepository
{
    Task<ModelDefinition> GetModelAsync(string context, string modelKey, string versionTag, CancellationToken ct);
    Task<ModelDefinition> GetLatestModelAsync(string context, string modelKey, CancellationToken ct);
    Task<IEnumerable<ModelVersion>> ListVersionsAsync(string context, string modelKey, CancellationToken ct);
    Task<ModelValidationResult> ValidateModelAsync(string context, string modelKey, string content, CancellationToken ct);
}
```

- `ModelDefinition` contains the raw content (XML, JSON, binary) and metadata (type, version, checksum).
- `ModelVersion` is a Semantic Versioning tag.

### 6.2 Artifact Types and Supported Formats

The Artifact Engine and the Model Repository support a wide range of artifact types and file formats. The following list is exemplary and not exhaustive. The system is extensible to support additional formats.

| Engine / Layer | Artifact Type | File Formats / Standards |
| :--- | :--- | :--- |
| BPMN Engine | Process Model | BPMN 2.0 XML |
| CMMN Engine | Case Model | CMMN 1.1 XML |
| DMN Engine | Decision Model | DMN 1.3 XML |
| StateMachine Engine | Statechart | SCXML, JSON Statechart |
| CEP Engine | Event Pattern | Custom DSL (JSON/YAML), Drools DRL, Flink SQL |
| Multi-Agent Engine | Agent Protocol | A2A JSON, MCP Schema, Custom Negotiation DSL |
| UI Engine | Form / Screen | JSON Schema, Vue/React component definitions (JSON), XForms |
| Artifact Engine | Document Template | DOCX (Microsoft Open XML), XLSX, PPTX, PDF/A, HTML5, Markdown, Plain Text |
| Artifact Engine | Data Artifact | JSON, XML, CSV, Avro, Protobuf, Parquet |
| Artifact Engine | CAD Artifact | STEP, IGES, STL, DWG (via plugins) |
| Artifact Engine | Source Code | C#, Python, Java, JavaScript, TypeScript, SQL |
| Knowledge Engine | Ontology / Graph Schema | RDF, OWL, SPARQL, GraphQL Schema, OpenAPI |
| Knowledge Engine | Vector Index Schema | Custom JSON (field mappings, embedding configurations) |
| Data Ingest Engine | Ingestion Mapping | JSON Mapping, XSLT (XML), Groovy scripts |
| Service Exposure | API Contract | OpenAPI (Swagger) 3.0, gRPC Protobuf, GraphQL Schema, AsyncAPI |
| Service Consumption | External API Binding | OpenAPI Client, gRPC Client, SOAP WSDL, Kafka Topic Binding |
| Observation Engine | Dashboard Definition | JSON Dashboard (e.g., Grafana Dashboard JSON, custom OLAP cube definition) |
| Process Mining Engine | Mining Configuration | XES export configuration, Celonis process definition |

### 6.3 Versioning Strategy

- **Semantic Versioning (MAJOR.MINOR.PATCH):** Applied to every model artifact.
- **MAJOR:** Breaking changes (e.g., changed BPMN node types, removed DMN inputs).
- **MINOR:** Backward-compatible additions (e.g., new DMN decision, new BPMN event handler).
- **PATCH:** Bug fixes or non-functional changes (e.g., corrected DMN expression, updated error message).
- **Immutable Versions:** Once a model version is marked `RELEASED`, it cannot be modified. Any change requires a new version.
- **Version Resolution:** Engines resolve models by `(context, modelKey, versionTag)`. If versionTag is omitted, the latest `RELEASED` version is used.

### 6.4 Model Validation Pipeline

Upon commit to the model repository (Git), a CI pipeline runs:

1. **Syntax Validation:** Ensure the artifact conforms to its schema (e.g., BPMN XSD, DMN XSD, JSON Schema).
2. **Semantic Validation:** Ensure referential integrity (e.g., all DMN input data is referenced, all BPMN service tasks have implementation bindings).
3. **Engine-Specific Validation:** Simulate execution of the model in a sandbox environment to catch runtime errors (e.g., FEEL expression errors, script compilation errors).
4. **Artifact Rendering Test:** For document templates, render a sample document with dummy data to ensure the template compiles.
5. **Security Scan:** Scan the model for malicious content (e.g., script injection, remote code execution in script tasks).

Failed models are rejected and never promoted to the production Model Registry. The validation results are reported back to the model designer.

### 6.5 Model Repository Implementation

- **Development:** `FileSystemModelRepository` reads models from a local directory. Supports hot-reload (file watcher).
- **Production:** `GitLabModelRepository` (or Azure DevOps, GitHub Packages) connects to a centralized model registry API. Supports version listing, content retrieval, and validation.
- **Caching:** A model cache (in-memory or Redis) stores recently accessed models to reduce repository calls.

### 6.6 Model Lifecycle

1. **Draft:** Model is being authored. Not yet validated.
2. **Validated:** Model has passed the validation pipeline.
3. **Staged:** Model is promoted to a staging environment for integration testing.
4. **Released:** Model is promoted to production. Immutable.
5. **Deprecated:** Model is no longer recommended for new instances. Existing instances continue to use it.
6. **Archived:** Model is no longer in use. Retained for historical audit.

---

## 7. Modular Monolith Structure

### 7.1 Module Isolation (Hard Boundaries)

Despite being in a single process, modules are isolated via:

- **Compile-Time Rules:** Project references are restricted. `Ordering.Domain` cannot reference `Billing.Domain`. Module projects cannot reference other module's Domain or Application projects.
- **Strong Names:** Each module is strong-named to prevent accidental assembly collisions.
- **Interface-Based Communication:** Cross-module communication is *only* allowed through `IMessageBus` (events) or explicit Query interfaces defined in `Shared.Abstractions`. Direct method calls between modules are **forbidden**.
- **Database Schemas:** Each module has its own dedicated database schema (or table prefix). Modules do not share tables. Foreign key constraints across modules are prohibited.
- **Event-Driven Decoupling:** Modules communicate via domain events. A module may subscribe to events from other modules, but it never directly manipulates the state of another module.

### 7.2 Module Registration (Composition Root)

Each module provides an extension method for registering its services with the DI container. The registration method accepts the `RuntimeTopology` configuration.

```csharp
public static IServiceCollection AddBpmnModule(this IServiceCollection services, RuntimeTopology topology)
{
    // Register repositories
    if (topology.PersistenceMode == PersistenceMode.InMemory)
        services.AddScoped<IProcessInstanceRepository, InMemoryProcessInstanceRepository>();
    else
        services.AddScoped<IProcessInstanceRepository, EFCoreProcessInstanceRepository>();

    // Register message bus
    if (topology.CommunicationMode == CommunicationMode.InMemory)
        services.AddScoped<IMessageBus, InMemoryBus>();
    else
        services.AddScoped<IMessageBus, KafkaBus>();

    // Register handlers and use cases
    services.AddScoped<IRequestHandler<StartProcessCommand, StartProcessResult>, StartProcessUseCase>();
    services.AddScoped<IRequestHandler<CompleteTaskCommand, CompleteTaskResult>, CompleteTaskUseCase>();

    // Register engines
    services.AddScoped<IBpmnEngine, BpmnEngine>();

    // Register AOP interceptors
    services.AddInterceptors<TraceInterceptor>();
    services.AddInterceptors<CircuitBreakerInterceptor>();

    return services;
}
```

### 7.3 Module Dependencies and Communication Patterns

Modules are organized in a layered dependency graph. Dependencies are directional and only go from higher-level modules to lower-level modules via events and queries.

| Module | Dependencies (Outgoing) | Communication |
| :--- | :--- | :--- |
| BPMN Engine | DMN Engine (for business rule tasks), ServiceConsumption (for service tasks), ArtifactEngine (for document generation) | Synchronous command (via DI) for DMN; Async event for long-running service tasks. |
| Multi-Agent Engine | BPMN Engine (for agent workflows), KnowledgeEngine (for context), ArtifactEngine (for message generation) | Async events and queries. |
| Knowledge Engine | ObservationEngine (for mining), ArtifactEngine (for data export) | Async events. |
| Observation Engine | All modules (for telemetry) | Subscribes to all domain events and metrics. |
| Service Exposure Layer | All modules (to expose their APIs) | Queries and commands. |

### 7.4 Intra-Process vs. Inter-Process Transparency

The Use Cases and engines are completely agnostic to whether they are running in a single process or across multiple processes.

- **In-Memory Mode:** `InMemoryBus` routes events to handlers synchronously (on the same thread or a dedicated async task). `InMemoryTimerScheduler` uses `System.Threading.Timer`. `LocalReentrantLock` uses `Monitor.Enter`. This provides sub-millisecond latency and simplifies debugging.
- **Distributed Mode:** `KafkaBus` serializes events and produces to Kafka. `QuartzTimerScheduler` uses a distributed database for scheduled jobs. `RedisDistributedLock` uses Redis Redlock.

The Use Case code remains unchanged. It calls `_messageBus.PublishAsync(event)` and assumes eventual consistency. The `InMemoryBus` simulates eventual consistency by executing handlers asynchronously (with a small delay) to surface concurrency issues early.

### 7.5 Benefits of the Modular Monolith Approach

- **Developer Productivity:** No need to run 20 containers locally. Compile and run the entire system in seconds.
- **Instant Integration Testing:** Cross-module integration tests run in-memory without network calls.
- **Single-Step Debugging:** Set breakpoints across modules and step through end-to-end flows.
- **Simplified Deployment Pipeline:** One binary, one container image, one Helm chart.
- **Graceful Migration to Microservices:** If a module needs to scale independently, it can be extracted into a separate service without changing the core logic (only the infrastructure adapters change).

---

## 8. The Polymorphic Runtime Engine (Deployment-as-Code)

### 8.1 Definition

The Polymorphic Runtime Engine is the set of infrastructure components and DI configurations that enable a single compiled binary to adapt its runtime behavior based on the environment. It is the physical implementation of the "Deployment Agnosticism" principle.

### 8.2 RuntimeTopology Configuration

The `RuntimeTopology` is a JSON configuration file that defines which adapters to use for each infrastructure concern. It is injected into the DI container at startup.

Example `RuntimeTopology.json` for **Production**:

```json
{
  "Environment": "Production",
  "CommunicationMode": "Kafka_gRPC",
  "LockStrategy": "Etcd",
  "PersistenceMode": "EFCore_SQLServer",
  "CachingMode": "Redis",
  "ServiceDiscoveryMode": "Consul_K8s",
  "SecurityMode": "Spiffe_mTLS",
  "ObservabilityMode": "OpenTelemetry",
  "ResilienceMode": "Production",

  "KafkaOptions": {
    "BootstrapServers": "kafka-cluster:9092",
    "SchemaRegistryUrl": "http://schema-registry:8081",
    "ClientId": "bpms-producer"
  },
  "EtcdOptions": {
    "Endpoints": ["etcd-1:2379", "etcd-2:2379", "etcd-3:2379"],
    "LeaseTtlSeconds": 30
  },
  "RedisOptions": {
    "ConnectionString": "redis-cluster:6379,password=..."
  },
  "ConsulOptions": {
    "Address": "consul-server:8500",
    "Datacenter": "dc1"
  },
  "DatabaseOptions": {
    "ConnectionString": "Server=sql-cluster;Database=BPMS;...",
    "Provider": "SqlServer"
  },
  "ModelRepositoryOptions": {
    "Type": "GitLabRegistry",
    "BaseUrl": "https://model-registry.internal/api/v4",
    "Token": "..."
  },
  "ArtifactStorageOptions": {
    "Type": "Minio",
    "Endpoint": "minio-cluster:9000",
    "Bucket": "artifacts"
  },
  "TracingOptions": {
    "Exporter": "Otlp",
    "Endpoint": "http://tempo:4317"
  },
  "RetryOptions": {
    "MaxRetries": 3,
    "ExponentialBackoff": true,
    "BaseDelaySeconds": 1
  },
  "CircuitBreakerOptions": {
    "FailureThreshold": 0.5,
    "SamplingDurationSeconds": 30,
    "MinimumThroughput": 100,
    "BreakDurationSeconds": 60
  }
}
```

Example `RuntimeTopology.json` for **Development**:

```json
{
  "Environment": "Development",
  "CommunicationMode": "InMemory",
  "LockStrategy": "Local",
  "PersistenceMode": "InMemory",
  "CachingMode": "Local",
  "ServiceDiscoveryMode": "Localhost",
  "SecurityMode": "Passthrough",
  "ObservabilityMode": "Console",
  "ResilienceMode": "None",

  "KafkaOptions": null,
  "EtcdOptions": null,
  "RedisOptions": null,
  "ConsulOptions": null,
  "DatabaseOptions": null,
  "ModelRepositoryOptions": {
    "Type": "FileSystem",
    "BasePath": "./Models"
  },
  "ArtifactStorageOptions": {
    "Type": "LocalFile",
    "BasePath": "./Artifacts"
  },
  "TracingOptions": null,
  "RetryOptions": null,
  "CircuitBreakerOptions": null
}
```

### 8.3 Adapter Selection Logic

The Composition Root reads the `RuntimeTopology` and selects adapters accordingly. The selection logic is centralized in each module's `AddXxxModule` method.

```csharp
// Example: Selecting the message bus adapter
if (topology.CommunicationMode == CommunicationMode.InMemory)
    services.AddSingleton<IMessageBus, InMemoryBus>();
else if (topology.CommunicationMode == CommunicationMode.Kafka)
    services.AddSingleton<IMessageBus>(sp => 
        new KafkaBus(topology.KafkaOptions));
else if (topology.CommunicationMode == CommunicationMode.RabbitMQ)
    services.AddSingleton<IMessageBus>(sp => 
        new RabbitMqBus(topology.RabbitMqOptions));
```

### 8.4 Environment-Specific Deployment Manifests

The IaC (Terraform, Helm) generates the `RuntimeTopology.json` based on the target environment.

- **Development Environment (Local):** The developer runs the app with `ASPNETCORE_ENVIRONMENT=Development`. The `appsettings.Development.json` overrides the topology to use in-memory adapters. No containers required.
- **Docker Compose Environment:** The `docker-compose.yml` spins up containers for Kafka, Redis, Consul, Postgres, etc. The topology is configured to use these local containers.
- **Staging Environment:** Kubernetes namespace `staging`. The Helm chart injects a topology that uses the same production adapters but with reduced replicas and resource limits.
- **Production Environment:** Kubernetes namespace `production`. The Helm chart injects a fully hardened topology with multiple replicas, Istio mesh, etcd cluster, and Kafka cluster.

The same container image is deployed to all environments. Only the configuration (`RuntimeTopology.json`) changes.

### 8.5 Canary Deployments and Traffic Splitting

Because the topology is decoupled from the code, canary deployments of new engine versions can be performed without code changes.

1. A new version of the engine binary is deployed as a separate pod (canary).
2. The Istio `VirtualService` routes 90% of traffic to the stable pods and 10% to the canary pods.
3. Both pods read the same `RuntimeTopology` but may have different model version mappings (the canary uses a new model version).
4. If the canary performs well, the traffic split is gradually shifted to 100%.
5. If a failure occurs, Istio instantaneously routes all traffic back to the stable pods.

This is achieved without redeploying the entire system or altering the engine code.

---

## 9. Communication & Service Discovery Abstraction

### 9.1 Communication Modes

The architecture supports multiple communication modes, selected via `RuntimeTopology.CommunicationMode`:

- **InMemory:** Direct method calls via DI.
- **gRPC:** Synchronous, high-performance RPC for queries and commands.
- **HTTP/REST:** Synchronous REST APIs for external integrations.
- **Kafka:** Asynchronous, durable, high-throughput event streaming.
- **RabbitMQ:** Asynchronous messaging with flexible routing.
- **Azure Service Bus / AWS SQS:** Cloud-native messaging.

All communication is abstracted behind the `IMessageBus` (events) and `IQueryDispatcher` (queries) ports.

### 9.2 Service Discovery Abstraction

The `IServiceDiscovery` port provides service resolution:

```csharp
public interface IServiceDiscovery
{
    Task<string> GetServiceEndpointAsync(string serviceName, string environment, CancellationToken ct);
    Task<IEnumerable<ServiceInstance>> GetInstancesAsync(string serviceName, CancellationToken ct);
}
```

**Adapters:**

| Mode | Adapter | Description |
| :--- | :--- | :--- |
| **Localhost** | `LocalhostServiceDiscovery` | Resolves to `localhost:port` based on configuration. Used in development. |
| **Consul** | `ConsulServiceDiscovery` | Resolves services using Consul DNS or HTTP API. Supports health checks, Datacenter awareness. |
| **Kubernetes** | `KubernetesServiceDiscovery` | Resolves services using K8s DNS (`service.namespace.svc.cluster.local`). Supports label selectors. |
| **Istio** | `IstioServiceDiscovery` | Uses Istio's service entry and destination rule configurations. Supports mTLS and traffic splitting. |
| **File-Based** | `FileBasedServiceDiscovery` | Reads a static JSON file mapping service names to endpoints. Used in development and testing. |

### 9.3 Service Mesh Integration (Istio)

When running in Kubernetes with Istio, the system leverages:

- **mTLS:** Automatic encryption and authentication between services via Istio sidecars. The `ISecurityContext` adapter integrates with the Istio SPIFFE workload identity.
- **Traffic Management:** Istio `VirtualServices` and `DestinationRules` are configured via IaC (Helm). Traffic splitting, timeouts, retries, and fault injection are managed at the mesh level, not in application code.
- **Circuit Breaking:** Istio's outbound circuit breakers complement the application-level circuit breakers (Polly), providing defense-in-depth.
- **Observability:** Istio's telemetry (HTTP/gRPC metrics, TCP metrics) is exported to Prometheus and integrates with the Observability layer.

### 9.4 Client-Side Load Balancing and Retry

For synchronous gRPC/HTTP calls, the `ServiceClient` adapter uses:

- **Load Balancer:** Round-robin or least-connections, based on Consul/K8s endpoint list.
- **Retry Policy:** Exponential backoff with jitter, configured via `RuntimeTopology.RetryOptions`. In Development, retries are disabled.
- **Timeout Policy:** Configurable per service. In Production, timeouts are strict (e.g., 5 seconds) to prevent cascading failures.

### 9.5 Service Exposure (Incoming)

The system exposes its capabilities via multiple protocols:

| Protocol | Use Case | Example |
| :--- | :--- | :--- |
| **REST** | External UI, third-party integrations | `POST /api/process/start` |
| **gRPC** | High-performance internal services, inter-module queries | `GetProcessStatus` RPC method |
| **GraphQL** | Flexible queries for UI dashboards | Query for process instance variables |
| **Event Streams** | External consumers subscribing to domain events | Kafka topics for all domain events |

The Service Exposure Layer is model-driven. API contracts (OpenAPI, Protobuf, GraphQL schema) are generated from declarative models (entity definitions, process models) and versioned in the Model Repository.

### 9.6 Service Consumption (Outgoing)

The Service Consumption Layer consumes external services. Adapters are provided for:

- **REST:** `HttpClient` with Polly retries and circuit breakers.
- **gRPC:** gRPC client with automatic connection management.
- **SOAP:** `WCF` / `System.ServiceModel` client (for legacy integration).
- **GraphQL:** GraphQL client with caching.
- **Kafka:** Consumer clients for subscribing to external events.
- **Database:** Ad-hoc query via Dapper/EF Core (for consuming data from external schemas).

The consumption configuration (endpoints, credentials, retry policies) is stored in the Model Repository as declarative bindings, not in application code.

---

## 10. Transactions, Consistency, & The Outbox Pattern

### 10.1 Intra-Module Transactions

Within a single module, ACID transactions are supported using the `IUnitOfWork` abstraction. The UnitOfWork coordinates multiple repositories and ensures that all changes are committed atomically.

**In Development (InMemory):** The `InMemoryUnitOfWork` uses `System.Transactions.TransactionScope` (or a custom in-memory transaction manager) to simulate ACID behavior.

**In Production (SQL Server / Postgres):** The `EFCoreUnitOfWork` uses the underlying database's transaction support. All repositories within the module share the same `DbContext` and transaction.

**Important:** Transactions are scoped strictly to a single module. They never span multiple modules. Cross-module consistency is achieved via the Outbox pattern and Sagas.

### 10.2 Cross-Module Consistency (Eventual Consistency)

When a Use Case in Module A emits a domain event that must be processed by Module B, the system relies on **eventual consistency**:

1. Module A saves its aggregate state and writes the domain event to an **Outbox** table in the same local ACID transaction.
2. The Outbox table is polled or streamed (via Debezium CDC) to the message bus.
3. Module B consumes the event from the message bus and processes it, updating its own state.

This pattern ensures that Module A's state is never inconsistent with the fact that an event was emitted. If Module B fails to process the event, the Outbox guarantees that the event will be retried.

### 10.3 The Outbox Pattern Implementation

**Port:** `IOutboxProcessor`

**Adapters:**

- **InMemory (Dev):** `NoOpOutboxProcessor`. Events are published directly without an Outbox table. This simplifies development but does not test eventual consistency.
- **Polling (Staging/Prod alternative):** `OutboxProcessor` runs a background task that polls the Outbox table every N seconds and publishes events to Kafka.
- **Debezium CDC (Production):** `DebeziumOutboxRelay` uses Debezium's PostgreSQL or SQL Server connector to stream Outbox table changes directly to Kafka. This is the preferred production approach because it provides exactly-once delivery, low latency, and no polling overhead.

**Outbox Table Schema:**

```sql
CREATE TABLE Outbox (
    Id BIGINT IDENTITY(1,1) PRIMARY KEY,
    AggregateId NVARCHAR(255) NOT NULL,
    EventType NVARCHAR(255) NOT NULL,
    EventContent NVARCHAR(MAX) NOT NULL,
    EventVersion INT NOT NULL,
    OccurredOn DATETIME2 NOT NULL,
    Published BIT NOT NULL DEFAULT 0,
    PublishedOn DATETIME2 NULL,
    RetryCount INT NOT NULL DEFAULT 0
);
```

**Consumer Idempotency:** Each consumer maintains an **Inbox** table to prevent duplicate processing. The consumer stores the `EventId` (or `Offset` + `Partition`) in the Inbox before processing. If the same event is received again, it is ignored.

### 10.4 Saga Orchestration

For workflows that span multiple modules and require compensation (e.g., Reserve Stock -> Confirm Order -> Collect Payment), a **Saga Orchestrator** is used.

- The orchestrator is a state machine (implemented using the StateMachine Engine) that manages the Saga execution.
- The orchestrator sends commands to individual modules (via the message bus) and listens for their responses (events).
- If a step fails, the orchestrator sends compensation commands to undo previous steps.

The Saga Orchestrator is implemented as a domain service in the Application layer. It is driven by a declarative Saga definition model (JSON or custom DSL), which is versioned in the Model Repository.

**Adapters for Saga Storage:**

- **Dev:** `InMemorySagaRepository` (stores sagas in memory).
- **Prod:** `EFCoreSagaRepository` (stores saga instances in the database).

### 10.5 Two-Phase Commit (2PC) Is Not Used

The architecture explicitly avoids distributed two-phase commit (XA/JTA) across modules due to:

- **Blocking nature:** 2PC holds locks until the coordinator decides, leading to deadlocks and poor availability.
- **CAP Theorem:** 2PC sacrifices Availability for Consistency. In a distributed system, Availability is prioritized (AP system).
- **Network Failures:** 2PC fails if the coordinator or any participant is unreachable.

Instead, the system uses **Sagas with compensation** for cross-module consistency, which is resilient and non-blocking.

---

## 11. Distributed Locking & Leader Election

### 11.1 Distributed Lock Abstraction

The `IDistributedLock` port provides a uniform interface for acquiring and releasing locks across processes.

```csharp
public interface IDistributedLock
{
    Task<LockHandle> AcquireAsync(string resourceId, TimeSpan expiry, CancellationToken ct);
    Task ReleaseAsync(LockHandle handle, CancellationToken ct);
    Task<bool> IsLockedAsync(string resourceId, CancellationToken ct);
}
```

**Adapters:**

| Mode | Adapter | Description |
| :--- | :--- | :--- |
| **Local** | `LocalReentrantLock` | Uses `System.Threading.ReaderWriterLockSlim`. Fastest, but only works within a single process. Used in Dev. |
| **Redis** | `RedisDistributedLock` | Implements Redlock algorithm using Redis. Works across multiple pods. Used in Docker Compose and Staging. |
| **etcd** | `EtcdDistributedLock` | Uses etcd leases. Provides strong consistency, TTL, and watch capabilities. Preferred for Production. |
| **ZooKeeper** | `ZookeeperDistributedLock` | Uses ZooKeeper ephemeral nodes. Alternative to etcd. |
| **Azure/Cloud** | `AzureTableLock` / `DynamoDbLock` | Cloud-native locking services. |

### 11.2 Lock Usage Scenarios

| Scenario | Example | Required Lock |
| :--- | :--- | :--- |
| **Idempotent Processing** | Processing a Kafka message exactly once for a given order ID. | Lock on `OrderId` during processing. |
| **Timed Task Execution** | Ensuring a BPMN timer event is executed by only one pod. | Lock on `ProcessInstanceId` before executing timer. |
| **StateMachine Transition** | Preventing concurrent transitions of the same state machine instance. | Lock on `StateMachineInstanceId`. |
| **Model Cache Refresh** | Updating the model cache from the repository. Only one pod should refresh. | Lock on `ModelCacheRefresh`. |

### 11.3 Leader Election

For components that require a single active instance (e.g., the Debezium Outbox relay, the Timer Scheduler, the Process Mining batch job), the system uses **leader election**.

**Port:** `ILeaderElector`

**Adapters:**

- **etcd:** `EtcdLeaderElector` uses etcd's session and lease mechanisms.
- **Kubernetes:** `KubernetesLeaderElector` uses K8s `Lease` API (via `coordination.k8s.io/v1`).
- **Local (Dev):** `LocalLeaderElector` always returns `true` (the single instance is the leader).

**Usage:** The component attempts to acquire the leadership lease. If successful, it starts processing. If it loses the lease (e.g., pod crash), another pod takes over.

### 11.4 Lock and Lease Expiry

All distributed locks and leases have a configurable TTL. When the TTL expires, the lock is automatically released. This prevents deadlocks if a pod crashes while holding a lock.

In the `RuntimeTopology`, the TTL is configured:

```json
"EtcdOptions": {
    "LeaseTtlSeconds": 30
}
```

For long-running operations (e.g., Saga execution), the lock is renewed periodically using a heartbeat (keep-alive).

---

## 12. State Management, Caching, & Time Abstraction

### 12.1 State Management

State (process instances, case instances, state machine instances, aggregated views) is stored in a persistent store (SQL Server, Postgres, or NoSQL). The `IUnitOfWork` and `IRepository` interfaces provide transactional state management.

**State Repositories:**

- **Write Repositories:** Used by Use Cases to mutate state. Changes are tracked and committed via `IUnitOfWork.CommitAsync()`.
- **Read Repositories (Projections):** Used by queries and APIs. These read from materialized views or separate read databases to avoid contention.

**Event Sourcing:** The system supports event sourcing as an optional persistence strategy for aggregates. If enabled, aggregates are reconstituted by replaying their domain events. Event sourcing uses the same Outbox table for event storage.

### 12.2 Caching Abstraction

The `ICacheManager` port provides a uniform interface for caching:

```csharp
public interface ICacheManager
{
    Task<T> GetOrAddAsync<T>(string key, Func<Task<T>> factory, TimeSpan ttl, CancellationToken ct);
    Task RemoveAsync(string key, CancellationToken ct);
    Task ClearAsync(CancellationToken ct);
}
```

**Adapters:**

| Mode | Adapter | Description |
| :--- | :--- | :--- |
| **Local** | `LocalMemoryCache` | Uses `Microsoft.Extensions.Caching.Memory`. Fast, but inconsistent across pods. Used in Dev. |
| **Redis** | `RedisCacheManager` | Uses Redis. Consistent across pods. Used in Staging/Prod. |
| **Hazelcast** | `HazelcastCacheManager` | In-memory data grid. Consistent and distributed. Alternative to Redis. |

### 12.3 Cache Invalidation via CDC (Change Data Capture)

When state changes in the database (e.g., a process instance completes), the cache must be invalidated to avoid stale reads.

**Pattern: Cache-Aside with CDC Invalidation**

1. When a Use Case modifies state, it writes to the database via `IUnitOfWork`.
2. Debezium captures the change from the database transaction log.
3. The Debezium event is streamed to Kafka.
4. A dedicated cache invalidation consumer listens to the Kafka topic and invalidates the corresponding cache keys (e.g., `process:{instanceId}`).

**In Development:** The `LocalMemoryCache` is invalidated manually via the `IUnitOfWork` after commit (synchronous invalidation). This simulates the CDC pattern without requiring Kafka/Debezium.

### 12.4 Time Abstraction

The `IClock` port provides a uniform interface for obtaining the current time.

```csharp
public interface IClock
{
    DateTime UtcNow { get; }
    DateTimeOffset UtcNowOffset { get; }
    Task<DateTime> GetSynchronizedUtcAsync(CancellationToken ct); // For high-precision use
}
```

**Adapters:**

| Mode | Adapter | Description |
| :--- | :--- | :--- |
| **Local** | `SystemClock` | Uses `DateTime.UtcNow`. Fast, but subject to clock skew. Used in Dev. |
| **NTP-Synchronized** | `NtpSynchronizedClock` | Synchronizes with NTP servers periodically. Provides bounded clock drift. Used in Staging/Prod. |
| **Cloud Time Service** | `AwsTimeSyncClock` / `AzureTimeSyncClock` | Uses cloud provider's time synchronization service. |
| **Test** | `FakeClock` | Allows deterministic time for unit tests. |

**Why this matters in distributed systems:** When using distributed locks with TTL or scheduling timers, clock skew can cause premature expiration or missed events. The `NtpSynchronizedClock` ensures that all pods have a consistent view of time.

**Timeouts and Deadlines:** All operations that cross the network (synchronous calls, message bus operations) have configurable timeouts. The timeout values are driven by `RuntimeTopology.TimeoutOptions`. In Development, timeouts are long (e.g., 60 seconds) to allow debugging; in Production, timeouts are strict (e.g., 5 seconds) to prevent cascading failures.

### 12.5 Distributed Timers and Scheduled Jobs

The `ITimerScheduler` port allows scheduling one-time or recurring jobs (e.g., BPMN timer events, CMMN milestones).

```csharp
public interface ITimerScheduler
{
    Task ScheduleAsync(string jobId, DateTimeOffset fireTime, IDictionary<string, object> payload, CancellationToken ct);
    Task CancelAsync(string jobId, CancellationToken ct);
}
```

**Adapters:**

| Mode | Adapter | Description |
| :--- | :--- | :--- |
| **Local** | `InMemoryTimerScheduler` | Uses `System.Threading.Timer`. Not persistent. Used in Dev. |
| **Distributed** | `QuartzTimerScheduler` | Uses Quartz.NET with database persistence. Supports cluster mode. Used in Staging/Prod. |
| **Cloud** | `AzureTimerScheduler` / `AWS EventBridge` | Cloud-native scheduled jobs. |

---

## 13. Security & Identity (mTLS, JWT, SPIFFE)

### 13.1 Security Abstraction

The `ISecurityContext` port provides authentication and authorization information.

```csharp
public interface ISecurityContext
{
    IIdentity CurrentIdentity { get; }
    bool IsAuthenticated { get; }
    bool IsAuthorized(string permission, IDictionary<string, object> context);
}
```

### 13.2 Authentication Adapters

| Mode | Adapter | Description |
| :--- | :--- | :--- |
| **Passthrough (Dev)** | `PassthroughIdentityProvider` | Always returns a default identity (admin). No validation. |
| **JWT** | `JwtValidator` | Validates JWT tokens from incoming requests. Uses public keys from identity provider. |
| **SPIFFE (mTLS)** | `SpiffeIdentityProvider` | Extracts identity from mTLS certificates (Istio/SPIFFE). Uses workload identity. |
| **OAuth2/OIDC** | `OAuth2IdentityProvider` | Validates OAuth2 access tokens against an authorization server. |
| **Client Certificate** | `ClientCertificateIdentityProvider` | Validates X.509 client certificates. |

### 13.3 Authorization (Permissions)

The authorization model is based on **roles** and **permissions**. Permissions are defined per context. For example, a user may have `Process.Start` permission in the `ContractLifecycle` context.

The `ISecurityContext.IsAuthorized()` method checks the user's permissions against a policy. The policy is loaded from the Model Repository (declarative) or from the identity provider.

**In Development:** Authorization checks are bypassed (`NoOpAuthorizationPolicy`).

### 13.4 Service-to-Service Authentication (mTLS)

In production, service-to-service communication (gRPC/HTTP) is secured using **mTLS** via Istio or Consul Connect.

- Each pod has a sidecar proxy (Istio Envoy) that terminates mTLS.
- The sidecar presents a SPIFFE-compliant certificate issued by the Kubernetes CA.
- The `SpiffeIdentityProvider` extracts the workload identity (e.g., `spiffe://cluster.local/ns/default/sa/bpmn-engine`) and maps it to a service account.

**Dev Environment:** mTLS is disabled. The `PassthroughIdentityProvider` assumes the caller is trusted.

### 13.5 Secret Management

Secrets (database credentials, API keys, Kafka certificates) are stored in:

- **Dev:** User secrets (`.NET UserSecrets`) or environment variables.
- **Prod:** Kubernetes Secrets (encrypted at rest) or HashiCorp Vault. The `SecretProvider` adapter retrieves secrets from Vault or K8s Secrets.

---

## 14. Observability (Tracing, Logs, Metrics, BAM, Process Mining)

### 14.1 Observability Pillars

The system provides comprehensive observability across four pillars:

1. **Distributed Tracing:** OpenTelemetry spans for every engine execution, Use Case, and external call.
2. **Structured Logging:** JSON logs with correlation IDs, trace IDs, and severity levels.
3. **Metrics:** Prometheus metrics for request rates, errors, latency, queue depths, lock contention.
4. **Business Activity Monitoring (BAM):** Dashboards and alerts for business KPIs (e.g., process completion rates, SLA breaches).
5. **Process Mining:** Export of XES logs for offline process mining and discovery.

### 14.2 Tracing Abstraction

The `ITracer` port provides a uniform interface for creating spans.

```csharp
public interface ITracer
{
    ISpan StartSpan(string operationName, IDictionary<string, object> tags = null);
    void InjectTraceContext(IDictionary<string, string> carrier);
    string CurrentTraceId { get; }
}
```

**Adapters:**

| Mode | Adapter | Description |
| :--- | :--- | :--- |
| **Console (Dev)** | `ConsoleTracer` | Logs span start/end to console. No external dependency. |
| **OpenTelemetry (Prod)** | `OpenTelemetryTracer` | Exports spans via OTLP to Tempo/Jaeger/AWS X-Ray. |

**Automatic Instrumentation:** Using AOP interceptors, all Use Cases and engine methods are automatically wrapped with `[TraceSpan]`. This provides end-to-end visibility from the API gateway down to the database queries.

### 14.3 Logging Abstraction

The `ILogger` port is a structured logger that accepts severity levels, message templates, and structured properties. In Production, logs are shipped to Elastic/Loki or Azure Log Analytics.

**Correlation:** All logs include the `TraceId` and `SpanId` from the current context, enabling correlation between logs and traces.

### 14.4 Metrics (Prometheus)

The system exposes metrics via the `IMetricsRegistry` port. Metrics are collected by Prometheus and visualized in Grafana.

Key metrics include:

- **Engine Metrics:** Number of BPMN instances started, completed, failed; DMN decisions evaluated.
- **Infrastructure Metrics:** Kafka lag, Redis cache hit/miss, database connection pool usage.
- **Business Metrics:** Process completion time percentiles, task backlog, SLA breach rate.
- **Resilience Metrics:** Circuit breaker state, retry count, lock acquisition time.

### 14.5 Business Activity Monitoring (BAM)

The Observation Engine provides BAM dashboards that display real-time business KPIs. Dashboards are defined declaratively (JSON) and stored in the Model Repository.

- **Data Sources:** The BAM engine queries the OLAP cubes or the read models of the system.
- **Alerts:** The BAM engine can trigger alerts (via the Message Bus) when a KPI exceeds a threshold (e.g., "Average order processing time > 5 minutes").

### 14.6 Process Mining

The system exports **XES (eXtensible Event Stream)** logs that conform to the IEEE 1849 standard.

- **Export Frequency:** Daily or on-demand.
- **Export Target:** Celonis, UiPath Process Mining, or custom ML pipelines.
- **Event Data:** Each log entry contains: `CaseId`, `Activity`, `Timestamp`, `Resource`, `LifecycleTransition`, and custom attributes.

The Process Mining Engine (part of the Knowledge Engine) can also perform on-demand process mining to discover bottlenecks, conformance violations, and improvement opportunities.

---

## 15. Resilience Engineering (Bulkheads, Circuit Breakers, Retries)

### 15.1 Resilience Pipeline

Every external call (synchronous RPC, database access, cache access, message bus publish) passes through a resilience pipeline:

1. **Retry Policy:** Exponential backoff with jitter.
2. **Circuit Breaker:** Prevents cascading failures.
3. **Bulkhead:** Restricts concurrent access.
4. **Timeout:** Prevents hanging operations.

These policies are applied via AOP interceptors. The configuration is driven by `RuntimeTopology.ResilienceOptions`.

### 15.2 Retry Policy

The `IRetryPolicy` port provides retry behavior.

**Adapters:**

- **NoOp (Dev):** No retries.
- **Polly Retry (Prod):** Uses Polly library. Retries on transient faults (e.g., network timeouts, database deadlocks). Configurable for max retries, base delay, exponential factor, and jitter.

### 15.3 Circuit Breaker

The `ICircuitBreaker` port provides circuit breaker behavior.

**Adapters:**

- **NoOp (Dev):** Never opens.
- **Polly CircuitBreaker (Prod):** Opens after a configurable number of failures within a sampling window. When open, calls fail fast with a `CircuitBreakerOpenException`. After a duration, the circuit transitions to half-open to test if the service has recovered.

The circuit breaker state is stored in a distributed store (e.g., Redis) so that all pods share the same circuit state. This prevents a single pod from opening the circuit while others continue to hammer a failing service.

### 15.4 Bulkhead

The `IBulkhead` port restricts the number of concurrent operations.

**Adapters:**

- **NoOp (Dev):** Unlimited concurrency.
- **Semaphore Bulkhead (Prod):** Uses a semaphore to limit concurrency to a configurable number (e.g., 10 concurrent outbound requests). Prevents thread pool exhaustion.

### 15.5 Timeout

Every external call has a configurable timeout. The timeout is applied at the infrastructure adapter level (e.g., `HttpClient.Timeout`, `KafkaProducer.SendTimeout`).

**Timeout Configuration:**

```json
"TimeoutOptions": {
    "DefaultMilliseconds": 5000,
    "DatabaseMilliseconds": 30000,
    "KafkaMilliseconds": 10000,
    "HttpMilliseconds": 5000
}
```

### 15.6 Graceful Degradation and Fallbacks

For critical operations, fallback behavior is defined declaratively in the `RuntimeTopology`:

- **Cache Miss:** If the cache is unavailable, the system falls back to database reads.
- **Kafka Unavailability:** The engine continues to operate locally and stores events in the Outbox for later delivery.
- **External Service Failure:** The circuit breaker opens and the system returns a cached response or a default value.

Fallback logic is implemented in the Use Case layer using the `IFallbackHandler` port, which provides alternative results when resilience policies fail.

---

## 16. Data Schema Evolution & Event Versioning

### 16.1 Database Schema Migration (Expand & Contract)

When database schemas need to change (e.g., adding a column to a process instance table), the system uses the **Expand & Contract** pattern to avoid downtime.

**Phase 1: Expand (Additive)**
- The new column is added as `NULLABLE` or with a default value.
- Old and new engine versions can coexist because the old code ignores the new column.

**Phase 2: Migrate (Gradual)**
- A background migration job backfills the new column for existing records.
- Once all records are backfilled, the column can be made `NOT NULL`.

**Phase 3: Contract (Removal)**
- After all old engine versions are retired, the old column can be dropped.
- This phase is optional if the old column is no longer used.

**Implementation:** The `IUnitOfWork` and `IMigrationManager` ports execute migration scripts during deployment. The scripts are versioned in the Model Repository.

### 16.2 Event Schema Versioning (Schema Registry)

Domain events evolve over time. The system uses a **Schema Registry** (Confluent Schema Registry, Azure Schema Registry, or custom) to manage event schemas.

- **Avro / Protobuf / JSON Schema** are used to define event payloads.
- Each event type has a `version` field.
- **Forward Compatibility:** New fields can be added without breaking old consumers.
- **Backward Compatibility:** Removed fields are still present (but ignored) in new events.

**Consumer Strategy:**
- Consumers specify the schema version they support.
- The `KafkaBus` adapter fetches the appropriate schema from the Schema Registry before serializing/deserializing.
- If a consumer receives an event with an unsupported major version, it sends the event to a dead-letter queue for manual handling.

### 16.3 API Versioning

The Service Exposure layer supports multiple API versions (e.g., `/api/v1/process`, `/api/v2/process`).

- **Versioning Strategy:** URL path or header-based.
- **Deprecation:** Old versions are deprecated gradually. Deprecation headers (e.g., `Deprecation: true`) are returned in responses.
- **Sunset Policy:** Minimum support duration for each API version is documented in the Model Repository.

### 16.4 Model Version Propagation

When a new model version (e.g., BPMN 2.0) is released, existing process instances continue to use the old model version. New instances use the new version. The engine resolves the model version at runtime based on the `ProcessDefinitionId` or a version tag.

- **Version Mapping:** Each process instance stores its `ModelVersionTag`.
- **Canary:** A subset of instances can be routed to the new model version using Istio traffic splitting or explicit feature flags.

---

## 17. CI/CD & Infrastructure as Code (IaC)

### 17.1 CI Pipeline

The CI pipeline (Azure DevOps / GitLab CI / GitHub Actions) performs:

1. **Code Compilation:** Builds the .NET 10 solution.
2. **Static Analysis:** SonarQube / Roslyn analyzers for code quality.
3. **Unit Tests:** Runs all unit tests (in-memory mode).
4. **Model Validation:** Validates all declarative models in the Model Repository.
5. **Integration Tests:** Runs integration tests against Docker Compose (Kafka, Redis, SQL Server containers).
6. **Container Build:** Builds the container image and tags it with the build ID.
7. **Push:** Pushes the image to the container registry (ACR / ECR / Docker Hub).

### 17.2 CD Pipeline (IaC)

The CD pipeline deploys the container image to the target environment using **Helm** and **Terraform**.

**Terraform** provisions the infrastructure:

- Kubernetes cluster (AKS / EKS / GKE).
- Service Mesh (Istio).
- Kafka cluster (Confluent / Azure Event Hubs / AWS MSK).
- Redis/etcd clusters.
- SQL Server / Postgres database (Azure SQL / RDS / GCP Cloud SQL).
- Object storage (Azure Blob / AWS S3 / MinIO).
- Model Registry (GitLab / Azure DevOps / custom).

**Helm Charts** deploy the application:

- Kubernetes `Deployment` with replicas, resource limits, and health probes.
- Kubernetes `Service` (ClusterIP) for internal communication.
- Kubernetes `VirtualService` and `DestinationRule` (Istio) for traffic management.
- Kubernetes `ConfigMap` containing the `RuntimeTopology.json`.
- Kubernetes `Secret` containing secrets (retrieved from Vault).

**Environment Promotion:** The same Helm chart is used for all environments. Environment-specific overrides are managed in separate `values-dev.yaml`, `values-staging.yaml`, `values-prod.yaml` files.

### 17.3 Canary Deployment with Istio

The IaC supports canary deployments:

1. The new image is deployed as a new deployment (e.g., `bpmn-engine-v2`).
2. The Istio `VirtualService` routes a small percentage of traffic (e.g., 5%) to the new deployment.
3. Metrics and traces are monitored for errors and latency.
4. If successful, the traffic percentage is gradually increased to 100%.
5. If a problem is detected, traffic is rerouted back to the stable deployment instantly.

### 17.4 Model Deployment Pipeline

The Model Repository has its own CI/CD pipeline:

1. Model changes are committed to Git (e.g., in the `models/` folder).
2. The Model Validation pipeline runs (syntax, semantic, sandbox tests).
3. If validation passes, the model is promoted to the Staging environment.
4. Integration tests are run against the staging deployment.
5. If successful, the model is promoted to Production (released).
6. The model is cached in Redis for fast access by the engines.

---

## 18. Testing Strategy (Unit, Integration, Contract, Chaos)

### 18.1 Unit Tests

- **Scope:** Domain models, Value Objects, Engine interpreters (in isolation).
- **Tools:** xUnit / NUnit, Moq / NSubstitute.
- **Mode:** In-memory only. No network, no database.
- **Run Frequency:** Every commit.

### 18.2 Integration Tests

- **Scope:** Use Cases, Repositories, Message Bus (end-to-end within a module).
- **Tools:** Testcontainers (for Kafka, Redis, Postgres), WebApplicationFactory.
- **Mode:** The system runs as a single process (in-memory or with Testcontainers).
- **Run Frequency:** Every merge to main.

### 18.3 Contract Tests

- **Purpose:** Verify that the system adheres to its API contracts (OpenAPI, Protobuf, AsyncAPI).
- **Tools:** Pact / Spring Cloud Contract.
- **Mode:** Consumer-driven contract tests ensure that changes to an API do not break consumers.

### 18.4 Chaos Tests

- **Purpose:** Verify the system's resilience to infrastructure failures.
- **Tools:** Chaos Mesh / Gremlin / Azure Chaos Studio.
- **Scenarios:** Pod kill, network latency, packet loss, node failure, Kafka broker failure, Redis failover.
- **Metrics:** The system must recover gracefully without data loss. The Outbox ensures event durability; the Circuit Breakers prevent cascading failures.

### 18.5 Performance & Load Tests

- **Purpose:** Validate scalability and identify bottlenecks.
- **Tools:** k6 / JMeter / Locust.
- **Scenarios:** Simulate hundreds of process instances started concurrently, high event throughput, large document generations.
- **Metrics:** Latency percentiles (p50, p95, p99), throughput, error rate.

### 18.6 Model Simulation Tests

- **Purpose:** Validate declarative models before deployment.
- **Tools:** Custom sandbox engine that executes models in a simulated environment.
- **Mode:** Runs in the Model Validation pipeline.

---

## 19. Operational Runbooks & Disaster Recovery

### 19.1 Health Checks

The system provides readiness and liveness probes for Kubernetes:

- **Readiness Probe:** Checks that the module can accept traffic (dependencies are healthy, cache is warm, model repository is accessible).
- **Liveness Probe:** Checks that the module is not deadlocked. Restarts if unresponsive.

Health endpoints are exposed at `/health/ready` and `/health/live`.

### 19.2 Scalability

- **Horizontal Scaling:** Each module (deployment) can be scaled to N replicas. The system handles distributed locking and leader election to ensure only one replica performs certain operations.
- **Vertical Scaling:** Resource limits (CPU, memory) are configured in the Helm chart. The system is optimized for low memory overhead.

### 19.3 Disaster Recovery

- **Database Backup:** The database is backed up daily. Point-in-time recovery is enabled.
- **Outbox Redelivery:** If the Outbox fails to publish events, they remain in the Outbox table until they are successfully published. The Outbox processor retries indefinitely.
- **Model Repository:** The model repository is backed up daily. Models are immutable, so restoration is straightforward.
- **Artifact Storage:** Artifacts are replicated across availability zones (S3/Blob storage).

### 19.4 Observability Dashboards

- **Grafana Dashboards:** Pre-built dashboards for system health, engine metrics, BAM KPIs.
- **Alerting:** Alerts are configured in Prometheus / Azure Monitor for:
  - High error rate (> 1% for any endpoint).
  - High latency (p95 > 1 second).
  - Circuit breaker open.
  - Outbox backlog > 1000 events.
  - Kafka consumer lag > 1000 messages.

### 19.5 On-Call and Incident Response

- **Runbooks:** Documented in the Model Repository (operational runbooks are also stored as declarative artifacts).
- **Log Analysis:** Correlated logs and traces provide the root cause quickly.
- **Rollback:** Quick rollback of the container image (via Kubernetes rolling update) or model version (via Istio traffic splitting).

---

## 20. Appendices

### Appendix A: RuntimeTopology JSON Schema

The full JSON schema for `RuntimeTopology` is available in the `Shared.Infrastructure/Schemas` folder. It defines all possible options for each adapter.

### Appendix B: Engine API Reference

Each engine exposes a set of commands and queries. The API documentation is generated from the Model Repository and OpenAPI/Protobuf contracts.

### Appendix C: Model Repository Sample Structure

```
ModelRepository/
├── ContractLifecycle/
│   ├── BPMN/
│   │   ├── ApprovalWorkflow.bpmn (v1.0.0)
│   │   ├── ApprovalWorkflow.bpmn (v1.1.0)
│   │   └── ApprovalWorkflow.bpmn (v2.0.0)
│   ├── DMN/
│   │   └── RiskScoring.dmn (v1.0.0)
│   ├── Forms/
│   │   └── ApprovalForm.uiform (v1.0.0)
│   └── Artifacts/
│       └── ContractTemplate.docx (v1.0.0)
└── CustomerOnboarding/
    ├── BPMN/
    │   └── OnboardingProcess.bpmn (v1.0.0)
    └── DMN/
        └── EligibilityCheck.dmn (v1.0.0)
```

### Appendix D: Code Samples

#### Sample BPMN Engine Use Case

```csharp
public class StartProcessUseCase : IRequestHandler<StartProcessCommand, StartProcessResult>
{
    private readonly IProcessInstanceRepository _repository;
    private readonly IBpmnEngine _engine;
    private readonly IModelRepository _modelRepo;
    private readonly IMessageBus _bus;
    private readonly IUnitOfWork _uow;

    public async Task<StartProcessResult> Handle(StartProcessCommand cmd, CancellationToken ct)
    {
        var model = await _modelRepo.GetModelAsync(cmd.Context, cmd.ProcessKey, cmd.Version, ct);
        var instance = new ProcessInstance(cmd.ProcessKey, cmd.Variables);
        var context = new BpmnExecutionContext(instance);
        
        var result = await _engine.ExecuteAsync(model, context, ct);
        
        foreach (var @event in result.Events)
        {
            instance.ApplyEvent(@event);
            await _bus.PublishAsync(@event, ct);
        }
        
        await _uow.CommitAsync(ct);
        return new StartProcessResult(instance.Id);
    }
}
```

#### Sample AOP Interceptor for Circuit Breaker

```csharp
[AttributeUsage(AttributeTargets.Method)]
public class CircuitBreakerAttribute : Attribute
{
    public string PolicyName { get; set; }
}

// Interceptor (source generator)
public class CircuitBreakerInterceptor
{
    public T Intercept<T>(Func<T> func, CircuitBreakerAttribute attribute)
    {
        var circuitBreaker = GetCircuitBreaker(attribute.PolicyName);
        if (circuitBreaker.State == CircuitState.Open)
            throw new CircuitBreakerOpenException();
        
        try
        {
            var result = func();
            circuitBreaker.RecordSuccess();
            return result;
        }
        catch (Exception ex)
        {
            circuitBreaker.RecordFailure();
            throw;
        }
    }
}
```

---

*This document represents the definitive architectural standard for the system. All development, deployment, and operational activities must adhere to these principles and patterns. Questions or deviations should be raised to the Architecture Review Board.*

---

*End of Architecture Document*