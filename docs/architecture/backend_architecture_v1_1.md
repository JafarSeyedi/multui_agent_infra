# ARCHITECTURE DOCUMENT

---

## Table of Contents

**Part 1: Foundations & The Golden Thread**
- Chapter 1: System Identity & Core Characteristics
- Chapter 2: Architectural Guiding Principles
- Chapter 3: The Polymorphic Runtime (Deployment-as-Code Engine)
- Chapter 4: Multi-Stage Environment Strategy
- Chapter 5: Document Structure & Domain Coverage

**Part 2: Core Runtime & Domain Orchestration**
- Chapter 6: Modular Monolith & Clean Architecture (.NET 10)
- Chapter 7: The Engine Ecosystem (BPMN, CMMN, DMN, CEP, StateMachine, Multi-Agent)
- Chapter 8: Declarative Model Repository & Versioning
- Chapter 9: Inter-Service Communication (Synchronous & Asynchronous)
- Chapter 10: Distributed Transactions (Saga, Outbox, Idempotency)
- Chapter 11: Service Discovery & Registry Abstraction

**Part 3: Data Fabric & Event Streaming**
- Chapter 12: Multi-Model Persistence (Relational, Document, Graph, Vector, Time-Series)
- Chapter 13: Event Streaming with Kafka/Pulsar & Schema Registry
- Chapter 14: Change Data Capture (CDC), Outbox Relay, and Eventual Consistency
- Chapter 15: Data Governance, Lineage, and Quality
- Chapter 16: Data Archival, Cold Storage, and Lifecycle Policies

**Part 4: API Management & Agentic Mesh**
- Chapter 17: Northbound Exposure (API Gateway, Ingress, BFF)
- Chapter 18: Southbound Integration (Protocol Adaptation, Legacy Connectivity)
- Chapter 19: Agentic Systems (A2A, MCP, Multi-Agent Orchestration)
- Chapter 20: Skills Engine & Plugin Management
- Chapter 21: UI Backend & Frontend Development Platform

**Part 5: Security, Identity, and Compliance**
- Chapter 22: Zero-Trust Architecture (SPIFFE/SPIRE, mTLS)
- Chapter 23: Authentication & Authorization (OAuth2, OIDC, OPA/Casbin)
- Chapter 24: Secrets Management & Hardware Security Modules (HSM)
- Chapter 25: Compliance Automation, Audit Trails, and Policy-as-Code
- Chapter 26: Data Privacy, Anonymization, and Quantum-Safe Cryptography

**Part 6: Cloud-Native Infrastructure & Operations**
- Chapter 27: Kubernetes Orchestration & Service Mesh (Istio/Linkerd)
- Chapter 28: Infrastructure-as-Code (Terraform/Crossplane) & Drift Management
- Chapter 29: Multi-Stage Environment Promotion (Helm/Kustomize)
- Chapter 30: Load Balancing, Traffic Routing, and Global Steering
- Chapter 31: FinOps, Cost Allocation, and Carbon Monitoring
- Chapter 32: Disaster Recovery & Multi-Region Active-Active

**Part 7: Observability, Testing & Resilience**
- Chapter 33: Observability (Logs, Metrics, Traces, Profiling)
- Chapter 34: Business Activity Monitoring (BAM) & Process Mining
- Chapter 35: Resilience Engineering (Circuit Breakers, Bulkheads, Retries)
- Chapter 36: Testing Strategy (Unit, Integration, Contract, Chaos, Performance)
- Chapter 37: Capacity Planning & Autoscaling
- Chapter 38: Scheduling, Cron Jobs, and Deferred Execution

**Part 8: Content, Knowledge & AI Pipelines**
- Chapter 39: Unified Document Abstraction (PDF, DOCX, CAD, Multimedia)
- Chapter 40: Retrieval-Augmented Generation (RAG) Pipelines
- Chapter 41: Knowledge Graphs, Semantic Search, and Digital Twins
- Chapter 42: Model Registry (MLflow) & LLM Observability (LangSmith)
- Chapter 43: Synthetic Data Generation & Test Data Management

**Appendices**
- Appendix A: RuntimeTopology JSON Schemas (Development → Production)
- Appendix B: Engine API Reference & Code Samples
- Appendix C: Security Hardening Checklist
- Appendix D: Tool Selection Matrix (Domains vs. Tools)
- Appendix E: Model Repository Sample Structure
- Appendix F: Deployment Pipeline Reference Architecture

---

# PART 1: FOUNDATIONS & THE GOLDEN THREAD

---

## Chapter 1: System Identity & Core Characteristics

### 1.1 System Overview

This document defines the definitive architectural standard for the platform. The system is an enterprise-grade, business-critical **Agentic, Model-Driven Business Process Management Suite (BPMS)** . It is not a traditional code-first application. It is a meta-platform where business behavior is defined declaratively, stored as models, and executed by a fleet of specialized, pluggable engines.

The architecture is designed to operate across the full spectrum of enterprise capabilities—from runtime orchestration and data persistence to agentic AI, content processing, and multi-cloud infrastructure—while maintaining a single unifying principle: **the same compiled binary runs identically in development, test, staging, and production, with its runtime topology defined purely by configuration.**

### 1.2 Core Identities

The platform is founded on the following core identities, which are immutable and non-negotiable across all domains and implementations:

**Agentic**
The system orchestrates a swarm of autonomous agents—both human-task and system-task—that interact, negotiate, and execute work. Agents are not passive components; they possess autonomy, reactivity, proactiveness, and social ability. They interact using standard protocols such as A2A (Agent-to-Agent) and MCP (Model Context Protocol). Agents are treated as first-class principals in the security model, with their own identities, credentials, and authorization policies.

**Model-Driven**
Every piece of business logic—process flows, decision tables, case management, event patterns, state machines, UI forms, data semantics, artifact templates, and even agent interaction strategies—is defined in declarative file formats (standards-based or custom DSLs). The engines are pure interpreters. Business knowledge is externalized from code. Updating business logic does not require recompilation or redeployment of the engine binaries; it only requires updating the model in the repository and triggering a hot-reload or version switch.

**Domain-Driven Design (DDD)**
The system is partitioned by business capabilities (Bounded Contexts). Each context owns its specific models, runtime state, and execution semantics. The Ubiquitous Language is defined in the models themselves and the canonical schemas exposed to agents and external consumers. Contexts communicate through well-defined contracts—asynchronous events for state changes, synchronous queries for read-only data retrieval—and never share database tables or domain entities.

**Clean Architecture (Hexagonal)**
Source code dependencies point inward. Engines and Use Cases depend only on Ports (interfaces). Infrastructure adapters (databases, message buses, caches, service meshes, security providers) are pluggable and isolated. The Domain and Application layers contain zero references to external frameworks, databases, or cloud SDKs. This ensures that business logic remains pure, testable, and independent of infrastructure changes.

**Polymorphic Runtime / Deployment Agnosticism**
This is the architectural centerpiece. The exact same compiled binaries can run as an in-memory library (for rapid development), as a set of Docker Compose services (for integration testing), or as a globally distributed Kubernetes fleet with Istio service mesh (for production). The runtime topology—communication mode, transaction strategy, locking mechanism, caching strategy, service discovery, and resilience policies—is switched purely via Dependency Injection (DI) container configuration, driven by Infrastructure-as-Code (IaC) and environment variables. The system is environment-aware and self-optimizing.

**Declarative Model Repository & Versioning**
All declarative models (BPMN, DMN, CMMN, Forms, UI configurations, Artifact templates, data schemas, API contracts, and Agent Skills) are stored in a version-controlled artifact registry. Every runtime execution references a specific model version, enabling canary deployments, A/B testing, and auditability of business logic changes independent of engine code. Models are immutable once released; bug fixes require a new version.

**Complete Artifact Management**
The system includes a comprehensive artifact management capability. It parses, renders, generates, and transforms a wide range of artifact formats, including but not limited to: DOCX, PDF, XLSX, PPTX, HTML, Markdown, raw data, CAD files, and source code. Artifacts can be used as input to engines (e.g., document templates for contract generation) or as output of processes. All artifacts are governed by lifecycle policies including retention, legal hold, and defensible deletion.

**Full Engine Ecosystem**
The system provides a complete, extensible basket of execution engines that are independent of platform, industry, and business knowledge. Engines include, but are not limited to: BPMN Engine, CMMN Engine, DMN Engine, CEP Engine, StateMachine Engine, Multi-Agent Interaction Engines and strategies, libraries for all message-bus and RPC strategies and tools integration, a full knowledge engine (RAG, graph, semantic, ML/data-mining, process mining), observation and monitoring (BAM), data ingest, and full context management. These engines are model-driven; their behavior is fully defined by declarative models.

**Service Exposure and Consumption**
The system provides layers for exposing its capabilities as services (REST, gRPC, GraphQL, events) and for consuming external services. These layers are also model-driven, with entity definitions, BPMN models, form and UI definitions, and integration contracts defined declaratively per domain. API contracts are versioned and governed through a full API lifecycle management process.

**Zero-Trust Security by Default**
Every interaction—between services, between agents, between users and the platform, and between the platform and external systems—is authenticated, authorized, and encrypted. Workload identity is based on SPIFFE/SPIRE. Secrets are dynamically rotated. Network policies enforce micro-segmentation. All actions are audited immutably.

**Observability as a First-Class Citizen**
Every engine execution, agent decision, tool call, and infrastructure event produces structured logs, dimensional metrics, and distributed traces. Business Activity Monitoring (BAM) provides real-time dashboards over business KPIs. Process mining exports XES logs for offline analysis. The system is self-observing and self-healing, with SLO-based alerting and automated incident response.

**Sustainability-Aware**
The platform measures, reports, and optimizes its carbon footprint. Workloads can be scheduled in low-carbon regions and during periods of low grid carbon intensity. Cost and carbon are considered equal constraints in capacity planning and autoscaling decisions.

### 1.3 Scope of the Architecture Document

This document covers the complete architectural definition of the platform across 65 distinct capability domains, organized into eight logical parts:

- **Part 1: Foundations & The Golden Thread** (this document)—Defines the system identity, guiding principles, the Polymorphic Runtime engine, and the multi-stage environment strategy.
- **Part 2: Core Runtime & Domain Orchestration**—Covers the Modular Monolith, Clean Architecture, the Engine Ecosystem, declarative models, distributed transactions, and service discovery.
- **Part 3: Data Fabric & Event Streaming**—Covers multi-model persistence, event streaming, CDC, data governance, and archival.
- **Part 4: API Management & Agentic Mesh**—Covers northbound exposure, southbound integration, agentic systems (A2A, MCP), skills engines, and UI/BFF.
- **Part 5: Security, Identity, and Compliance**—Covers zero-trust, IAM, secrets management, HSM, compliance automation, and quantum-safe cryptography.
- **Part 6: Cloud-Native Infrastructure & Operations**—Covers Kubernetes, service mesh, IaC, multi-stage environments, FinOps, disaster recovery, and multi-cloud.
- **Part 7: Observability, Testing & Resilience**—Covers observability, BAM, resilience engineering, testing strategy, capacity planning, and scheduling.
- **Part 8: Content, Knowledge & AI Pipelines**—Covers document abstraction, RAG, knowledge graphs, digital twins, MLOps, and synthetic data.

### 1.4 Audience

This document is the single source of truth for all stakeholders involved in the design, development, deployment, and operation of the platform:

- **Developers and Engine Engineers:** Understand the coding standards, abstraction layers, extension points, and integration patterns.
- **Model Designers and Citizen Developers:** Understand how declarative models (BPMN, DMN, CMMN, Forms, Artifacts) are versioned, deployed, and executed.
- **Infrastructure and SRE Teams:** Understand the IaC contracts, the Polymorphic Runtime configuration, service mesh integration, and operational runbooks.
- **Security and Compliance Teams:** Understand the zero-trust architecture, secrets management, audit trails, and compliance automation.
- **Customer Technical Engineers:** Verify infrastructure compliance, security posture, scalability characteristics, and integration capabilities.
- **Product Management and Business Stakeholders:** Understand the capabilities of the platform and the strategic architectural choices that enable rapid business model evolution.

### 1.5 Glossary of Core Terms

| Term | Definition |
| :--- | :--- |
| **Bounded Context** | A logical boundary within which a specific domain model applies and has meaning. Each context owns its models and runtime state. |
| **Aggregate** | A cluster of domain objects treated as a single unit for data changes. Aggregates are persisted as a whole and enforce invariants. |
| **Domain Event** | A fact about something that happened within the domain. Domain events are the primary mechanism for cross-context communication and eventual consistency. |
| **Port** | An interface defined in the Core or Application layer that the outer layers implement (Clean Architecture). |
| **Adapter** | The concrete implementation of a Port in the Infrastructure layer. |
| **Polymorphic Runtime** | The ability for a single compiled artifact to switch between in-memory, synchronous RPC (gRPC/HTTP), and asynchronous message-bus (Kafka) communication strategies based on environment configuration. |
| **Deployment-as-Code** | The practice of defining the runtime topology (pods, scaling, infrastructure patterns, service mesh configuration, and adapter selection) in declarative IaC scripts, which are version-controlled alongside the application code. |
| **Declarative Model** | A file (BPMN XML, DMN XML, JSON Schema, etc.) that defines business logic, rules, UI, or data structures independently of engine implementation. |
| **Engine** | A stateless interpreter that reads declarative models and produces commands, domain events, and state transitions. Engines contain zero business logic. |
| **Artifact** | Any file or data payload that is managed by the system, including documents, templates, generated files, and raw data. |
| **Agent** | An autonomous entity that executes tasks, makes decisions, and interacts with other agents using A2A or MCP protocols. |
| **A2A** | Agent-to-Agent communication protocol for discovery, messaging, and task handoff. |
| **MCP** | Model Context Protocol for providing structured context, tools, and resources to agents. |
| **RuntimeTopology** | The JSON configuration object that defines the entire runtime behavior of the system, including communication mode, transaction strategy, locking mechanism, caching strategy, service discovery mode, security mode, and resilience policies. |

---

## Chapter 2: Architectural Guiding Principles

The following principles are immutable. They guide every design decision, every implementation choice, and every operational procedure. No deviation from these principles is permitted without explicit approval from the Architecture Review Board.

### 2.1 Model-Engine Separation (The Law of Interpreters)

Engines are pure, stateless interpreters. They take a declarative model and a current state (context) as input and produce a set of commands and domain events as output. All business knowledge is externalized into declarative model files stored in the Model Repository.

**Implications:**

- Updating business logic (e.g., changing a process flow, modifying a decision table) does not require recompilation or redeployment of the engine binaries.
- Multiple model versions can run concurrently (canary deployments of business logic).
- Engines are generic and reusable across industries and domains.
- Model validation is enforced before promotion to production, preventing runtime errors.

**Application to All Engines:**

- **BPMN Engine:** Interprets process models, advances tokens, triggers tasks, and emits events.
- **DMN Engine:** Evaluates decision tables and returns decisions.
- **CMMN Engine:** Interprets case models, handles ad-hoc tasks, and manages milestones.
- **CEP Engine:** Matches event patterns over time windows.
- **StateMachine Engine:** Processes state transitions based on events.
- **Multi-Agent Engine:** Executes interaction protocols (negotiation, auctions, delegation).
- **Knowledge Engine:** Interprets semantic queries, performs RAG retrievals, and executes graph traversals.
- **Artifact Engine:** Interprets templates and data bindings to generate documents.

### 2.2 Domain-Driven Design (DDD) Applied to Models

Bounded Contexts are defined by business capabilities. Each context owns:

- A **Model Repository folder** containing all declarative definitions (BPMN, DMN, Forms, UI schemas, Artifact templates, API contracts) specific to that capability.
- A dedicated **Database Schema** for its runtime state (process instances, decision execution logs, case instances, state machine states).
- A dedicated **Event Topic Prefix** in the message bus for its domain events.
- A dedicated set of **Aggregates** that represent the runtime execution state.
- A dedicated **Service Discovery namespace** for its internal and exposed endpoints.

The Ubiquitous Language is defined in the models themselves and the canonical schemas exposed to agents and external consumers. Models are authored in collaboration with business stakeholders. Contexts are provisioned dynamically; new contexts can be added without code changes.

### 2.3 Clean Architecture (Hexagonal) – Strict Dependency Rule

Source code dependencies point inward. The rule is absolute:

- **Domain Layer (Core):** Contains Aggregates, Entities, Value Objects, and Domain Events. Has zero external dependencies (only the .NET Base Class Library).
- **Application Layer:** Contains Use Cases, Ports (interfaces), and Engine interpreters. Depends only on Domain.
- **Infrastructure Layer:** Contains concrete Adapters (repositories, message buses, caches, service discovery, locks, clocks, security providers). Depends on Application and Domain.
- **Presentation / Delivery Layer:** Contains REST/gRPC/GraphQL controllers, model endpoints, and UI backend. Depends on Infrastructure.

Cross-cutting concerns (logging, tracing, resilience, security) are implemented via Aspect-Oriented Programming (AOP) using .NET 10 source generators and interceptors, keeping the core layers clean.

### 2.4 Polymorphic Runtime – Environment Agnosticism

The system is designed to run on multiple topological planes. The same compiled binary adapts its behavior based on the runtime environment.

| Environment | Communication Topology | Transaction Strategy | Locking Strategy | Service Discovery |
| :--- | :--- | :--- | :--- | :--- |
| **Development (Local)** | In-memory direct method calls | Outbox Polling (synchronous mock) | In-Memory Reentrant Locks | Localhost / File-based |
| **Docker Compose** | In-memory or gRPC/HTTP (optional) | Outbox with local transactional mock | Redis (local container) | Consul (local container) |
| **Test (Kubernetes)** | gRPC/HTTP + Kafka | Outbox + Debezium + Saga Coordinator | Redis | Consul + Istio (mTLS disabled) |
| **Staging (Kubernetes)** | gRPC/HTTP + Kafka | Outbox + Debezium + Saga Coordinator | etcd | Consul + Istio (mTLS enabled) |
| **Production (Kubernetes)** | gRPC/HTTP + Kafka | Outbox + Debezium + Saga Coordinator | etcd (leases) | Consul + Istio (mTLS, traffic splitting) |

The compilation output is identical for all environments. The topology is switched via Dependency Injection (DI) container configuration, driven by environment variables set by Infrastructure-as-Code (IaC).

### 2.5 Build Once, Deploy Anywhere (Immutable Artifacts)

Every commit to the main branch produces a single immutable container image. This image is promoted through all environments (Dev → Test → Staging → Production) without any rebuilds. Environment-specific configuration is injected at runtime via `RuntimeTopology.json` (loaded from ConfigMaps/Secrets). There is no "rebuild for production."

### 2.6 Zero-Trust Security by Default

The platform assumes zero trust at every layer:

- **Network:** Default-deny network policies at the Kubernetes and service mesh levels.
- **Identity:** Every service, agent, and user has a verifiable identity (SPIFFE for workloads, OIDC for humans).
- **Authentication:** mTLS for service-to-service, OAuth2/OIDC for end-user access.
- **Authorization:** Policy-as-Code (OPA) enforces fine-grained access control (RBAC, ABAC) at every API boundary.
- **Secrets:** No long-lived static secrets. Dynamic credentials are injected just-in-time via HashiCorp Vault.
- **Audit:** Every action is logged immutably and cryptographically verifiable.

### 2.7 Eventual Consistency with Sagas

Cross-module consistency is never achieved via distributed transactions (2PC). Instead, the system relies on:

- **Transactional Outbox:** Write to local database and publish event atomically.
- **Saga Orchestration:** Durable, stateful sagas (implemented via the StateMachine Engine) orchestrate compensating transactions.
- **Idempotency:** Every event consumer is idempotent, ensuring exactly-once processing semantics.
- **Dead-Letter Queues:** Failed events are retried with exponential backoff; unprocessable events are routed to DLQs for manual intervention.

### 2.8 Observability-Driven Development

Every component—from engines to infrastructure adapters—must expose:

- **Structured Logs:** JSON logs with traceId, spanId, and correlationId.
- **Dimensional Metrics:** RED (Rate, Errors, Duration) and USE (Utilization, Saturation, Errors) metrics exposed via Prometheus.
- **Distributed Traces:** OpenTelemetry spans for every Use Case, Engine execution, and external call.
- **Business Activity Monitoring (BAM):** Business KPIs (process completion rates, SLA breaches) exposed as custom metrics and dashboards.

### 2.9 Infrastructure as Code (IaC) and Drift Management

All infrastructure—Kubernetes clusters, service mesh configuration, databases, message buses, caching layers, and network policies—is defined declaratively in code (Terraform, Crossplane, Helm) and stored in Git. Drift detection continuously reconciles the actual state with the desired state. Any manual change to infrastructure is automatically reverted by the reconciliation loop.

### 2.10 FinOps and Sustainability

Cost and carbon are first-class concerns in capacity planning and autoscaling:

- **Cost Allocation:** Every pod, namespace, and service is tagged with team, environment, and business unit. Costs are allocated via chargeback/showback.
- **Carbon Monitoring:** The platform measures carbon emissions using cloud provider carbon footprint tools and third-party calculators (Cloud Carbon Footprint, Kepler).
- **Carbon-Aware Scheduling:** Workloads that are not latency-sensitive can be scheduled in low-carbon regions or during periods of low grid carbon intensity.

### 2.11 API-First Design

All capabilities of the platform are exposed as well-defined APIs before any implementation begins:

- **Contract-First:** OpenAPI (REST), Protobuf (gRPC), and GraphQL schemas are designed, reviewed, and versioned before code is written.
- **Consumer-Driven Contracts:** Pact testing ensures that providers do not break consumers.
- **API Governance:** Spectral linting enforces API style guides in CI/CD pipelines.

### 2.12 Polyglot Persistence with Unified Access

Different workloads require different storage models:

- **Relational:** ACID transactions, complex joins (PostgreSQL).
- **Document:** Flexible schemas, high write throughput (MongoDB).
- **Graph:** Highly connected data, semantic relationships (Neo4j).
- **Vector:** High-dimensional embeddings for AI memory (pgvector, Qdrant).
- **Time-Series:** High-volume timestamped data (TimescaleDB, InfluxDB).
- **Object:** Unstructured blobs, large files (S3, MinIO).
- **Event Log:** Immutable append-only logs (Kafka, Pulsar).

All access to these stores is abstracted behind Ports (`IRepository`, `IEventStore`, `IVectorStore`, `IGraphStore`, `IBlobStorage`) in the Application layer.

---

## Chapter 3: The Polymorphic Runtime (Deployment-as-Code Engine)

### 3.1 Definition

The Polymorphic Runtime Engine is the set of infrastructure components, DI configurations, and IaC contracts that enable a single compiled binary to adapt its runtime behavior based on the environment. It is the physical implementation of the "Deployment Agnosticism" principle and the central "Golden Thread" that weaves through all 65 domains.

### 3.2 The RuntimeTopology Configuration

The `RuntimeTopology` is a JSON configuration file that defines which adapters to use for each infrastructure concern. It is the single source of truth for the runtime behavior of the system.

**Example: Production RuntimeTopology**

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
    "ClientId": "platform-producer"
  },
  "EtcdOptions": {
    "Endpoints": ["etcd-1:2379", "etcd-2:2379", "etcd-3:2379"],
    "LeaseTtlSeconds": 30
  },
  "RedisOptions": {
    "ConnectionString": "redis-cluster:6379",
    "Password": "${REDIS_PASSWORD}"
  },
  "ConsulOptions": {
    "Address": "consul-server:8500",
    "Datacenter": "dc1"
  },
  "DatabaseOptions": {
    "ConnectionString": "${DB_CONNECTION_STRING}",
    "Provider": "SqlServer"
  },
  "ModelRepositoryOptions": {
    "Type": "GitLabRegistry",
    "BaseUrl": "https://model-registry.internal/api/v4"
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

**Example: Development RuntimeTopology**

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

  "ModelRepositoryOptions": {
    "Type": "FileSystem",
    "BasePath": "./Models"
  },
  "ArtifactStorageOptions": {
    "Type": "LocalFile",
    "BasePath": "./Artifacts"
  }
}
```

### 3.3 Adapter Selection Logic (The Composition Root)

The Composition Root reads the `RuntimeTopology` and registers the appropriate adapters in the DI container. The selection logic is centralized and deterministic.

```csharp
// Example: Message Bus Adapter Selection
if (topology.CommunicationMode == CommunicationMode.InMemory)
    services.AddSingleton<IMessageBus, InMemoryBus>();
else if (topology.CommunicationMode == CommunicationMode.Kafka)
    services.AddSingleton<IMessageBus>(sp => 
        new KafkaBus(topology.KafkaOptions));
else if (topology.CommunicationMode == CommunicationMode.RabbitMQ)
    services.AddSingleton<IMessageBus>(sp => 
        new RabbitMqBus(topology.RabbitMqOptions));

// Example: Distributed Lock Adapter Selection
if (topology.LockStrategy == LockStrategy.Local)
    services.AddSingleton<IDistributedLock, LocalReentrantLock>();
else if (topology.LockStrategy == LockStrategy.Redis)
    services.AddSingleton<IDistributedLock>(sp => 
        new RedisDistributedLock(topology.RedisOptions));
else if (topology.LockStrategy == LockStrategy.Etcd)
    services.AddSingleton<IDistributedLock>(sp => 
        new EtcdDistributedLock(topology.EtcdOptions));

// Example: Cache Manager Adapter Selection
if (topology.CachingMode == CachingMode.Local)
    services.AddSingleton<ICacheManager, LocalMemoryCache>();
else if (topology.CachingMode == CachingMode.Redis)
    services.AddSingleton<ICacheManager>(sp => 
        new RedisCacheManager(topology.RedisOptions));
```

### 3.4 The Dependency Inversion Mechanism

The Polymorphic Runtime relies on the Dependency Inversion Principle:

- The **Application Layer** defines Ports (interfaces) such as `IMessageBus`, `IDistributedLock`, `ICacheManager`, `IServiceDiscovery`, `IClock`, `ISecurityContext`.
- The **Infrastructure Layer** provides concrete Adapters that implement these Ports.
- The **Composition Root** decides which Adapters to inject based on the `RuntimeTopology`.

This ensures that the engine code, Use Cases, and Domain Aggregates have absolutely no knowledge of whether they are running in-memory or against distributed infrastructure.

### 3.5 Environment Injection via IaC

The `RuntimeTopology.json` is never hardcoded in the application. It is injected at runtime via:

- **Development:** `appsettings.Development.json` (loaded automatically by ASP.NET Core).
- **Docker Compose:** Environment variables overrides in `docker-compose.override.yml`.
- **Kubernetes (Test, Staging, Production):** `ConfigMap` and `Secret` resources, generated by Helm/Terraform from environment-specific values files.

```yaml
# values-prod.yaml (Helm)
runtimeTopology:
  environment: Production
  communicationMode: Kafka_gRPC
  lockStrategy: Etcd
  persistenceMode: EFCore_SQLServer
  cachingMode: Redis
  serviceDiscoveryMode: Consul_K8s
  securityMode: Spiffe_mTLS
  observabilityMode: OpenTelemetry
  resilienceMode: Production
  kafkaOptions:
    bootstrapServers: "kafka-cluster:9092"
    schemaRegistryUrl: "http://schema-registry:8081"
  etcdOptions:
    endpoints: ["etcd-1:2379","etcd-2:2379","etcd-3:2379"]
    leaseTtlSeconds: 30
```

### 3.6 Canary Deployments and Traffic Splitting

Because the topology is decoupled from the code, canary deployments of new engine versions can be performed without code changes:

1. A new version of the engine binary is deployed as a separate pod (canary) alongside the stable pods.
2. The Istio `VirtualService` routes a percentage of traffic (e.g., 10%) to the canary pods.
3. Both stable and canary pods read the same `RuntimeTopology` from the `ConfigMap`.
4. The canary pods may be configured to use a different model version (via a separate `ModelVersionTag`), enabling canary deployments of business logic.
5. If the canary performs well, the traffic split is gradually shifted to 100%.
6. If a failure occurs, Istio instantaneously routes all traffic back to the stable pods.

This is achieved without redeploying the entire system or altering the engine code.

### 3.7 The Golden Thread: Consistency Across All Domains

The Polymorphic Runtime is the "Golden Thread" that weaves through all 65 domains:

- **Domain 1 (Orchestration):** The same Helm chart deploys to Dev, Test, Staging, and Prod with different values.
- **Domain 2 (Service Discovery):** `LocalhostDiscovery` in Dev, `ConsulDiscovery` in Prod.
- **Domain 3 (Communication):** `InMemoryBus` in Dev, `KafkaBus` in Prod.
- **Domain 7 (State/Caching):** `LocalMemoryCache` in Dev, `RedisCache` in Prod.
- **Domain 8 (Secrets):** UserSecrets in Dev, Vault in Prod.
- **Domain 10 (Transactions):** `LocalUnitOfWork` in Dev, `EFCoreUnitOfWork` with Outbox in Prod.
- **Domain 12 (Security):** `PassthroughIdentityProvider` in Dev, `SpiffeIdentityProvider` in Prod.
- **Domain 22 (CI/CD):** The same pipeline promotes the same immutable image.
- **Domain 58 (IaC):** The same Terraform modules provision different cluster sizes based on environment variables.

---

## Chapter 4: Multi-Stage Environment Strategy

### 4.1 The Build Once, Deploy Anywhere Pipeline

The platform implements a strict "Build Once, Deploy Anywhere" pipeline:

1. **Commit:** Developer commits code and declarative models to Git.
2. **CI Pipeline:**
   - Compiles the .NET 10 solution.
   - Runs static analysis, unit tests, and integration tests.
   - Validates all declarative models (BPMN, DMN, etc.) against their schemas.
   - Builds a single immutable container image.
   - Pushes the image to the container registry with a semantic version tag (e.g., `v1.2.3`).
   - Promotes the image to the Dev environment.
3. **Promotion Pipeline:**
   - **Dev:** Image is deployed with `RuntimeTopology` set to Development mode. Automated smoke tests run.
   - **Test:** Image is promoted to Test environment with Test-mode `RuntimeTopology`. Full integration and contract tests run.
   - **Staging:** Image is promoted to Staging with production-like `RuntimeTopology` (but with test data). Performance and chaos tests run.
   - **Production:** Image is promoted to Production with production `RuntimeTopology` after manual approval gates.

**The container image is identical in all environments.** Only the `RuntimeTopology` configuration changes.

### 4.2 Environment Definitions

| Environment | Purpose | `ASPNETCORE_ENVIRONMENT` | RuntimeTopology Profile | Data |
| :--- | :--- | :--- | :--- | :--- |
| **Local Development** | Developer coding and unit testing | `Development` | `InMemory`, `Local`, `Passthrough` | Synthetic seed data |
| **Docker Compose** | Integration testing on developer machine | `Development` | `Kafka/Redis` (containers) or `InMemory` | Synthetic seed data |
| **Test** | Automated integration, contract, and load testing | `Test` | `Kafka`, `Redis`, `Consul` (mTLS disabled) | Synthetic data + anonymized production subset |
| **Staging** | Pre-production validation, UAT, canary analysis | `Staging` | `Kafka`, `etcd`, `Consul`, `Istio` (mTLS enabled) | Anonymized production data (Tonic/Delphix) |
| **Production** | Live business operations | `Production` | `Kafka`, `etcd`, `Consul`, `Istio` (full hardening) | Live production data |

### 4.3 Configuration Hierarchy

Configuration is layered with strict precedence:

1. **Base:** `appsettings.json` (common defaults).
2. **Environment:** `appsettings.{Environment}.json` (environment-specific overrides).
3. **Machine/User Secrets:** `secrets.json` (development only, never committed).
4. **Environment Variables:** Injected by the orchestration platform (Kubernetes, Docker).
5. **Command-Line Arguments:** Highest precedence, used for emergency overrides.

In Kubernetes, the `RuntimeTopology` is injected via `ConfigMap` and `Secret`, which are mounted as environment variables or files.

### 4.4 Database Migration Strategy Across Stages

Database schema migrations are handled with the **Expand & Contract** pattern:

1. **Expand (Additive):** New columns are added as `NULLABLE` in all environments. Old code ignores them.
2. **Migrate (Gradual):** A background migration job backfills the new column for existing records.
3. **Contract (Removal):** After all old engine versions are retired, the old column is dropped.

Migrations are executed automatically during the deployment pipeline (using Flyway/Liquibase) and are idempotent. In Dev, the database is dropped and recreated from scratch on each deployment. In Prod, migrations are applied with backward compatibility guaranteed.

### 4.5 Model Version Promotion

Declarative models (BPMN, DMN, etc.) follow a separate promotion pipeline from the engine code:

1. Model designer commits a new model version to the Model Repository (Git).
2. CI pipeline validates the model (syntax, semantic, sandbox execution).
3. Model is promoted to Dev (available for local testing).
4. Model is promoted to Staging (validated against staging data).
5. Model is promoted to Production (immutable version tag).

Models can be promoted independently of engine code. A new model version can be deployed to Production while the engine remains unchanged.

---

## Chapter 5: Document Structure & Domain Coverage

### 5.1 The 65-Domain Capability Map

This architecture document covers 65 distinct capability domains, organized into eight logical parts. The following table provides a high-level mapping of domains to architectural pillars:

| Domain Cluster | Domains Covered | Architecturally Addressed In |
| :--- | :--- | :--- |
| **Runtime Infrastructure & Orchestration** | 1, 15, 27, 52 | Part 6 |
| **Service Discovery & Registry** | 2, 48 | Part 2, Part 6 |
| **Inter-Service Communication** | 3, 9 | Part 2 |
| **Service Mesh** | 4, 32, 57 | Part 6 |
| **Northbound Exposure** | 5, 14, 28 | Part 4 |
| **Southbound Integration** | 6, 19, 53 | Part 4 |
| **State & Caching** | 7, 49 | Part 3 |
| **Configuration & Secrets** | 8, 24 | Part 5 |
| **Event Streaming & EDA** | 9, 34 | Part 3 |
| **Data Consistency & Tx** | 10, 17 | Part 2 |
| **Observability** | 11, 34, 35, 36 | Part 7 |
| **Security** | 12, 24, 25, 33, 45, 56 | Part 5 |
| **Agentic Systems** | 13, 19, 20 | Part 4 |
| **UI & Frontend Platform** | 14, 21 | Part 4 |
| **Load Balancing & Routing** | 15, 30 | Part 6 |
| **Data Persistence** | 16, 47, 60, 61 | Part 3 |
| **Business Process & Workflow** | 17, 31, 36 | Part 2 |
| **Knowledge & Analytics** | 18, 40, 41 | Part 8 |
| **Tool Integration** | 19, 53 | Part 4 |
| **Content Processing** | 20, 55 | Part 8 |
| **Developer Experience** | 21, 22, 23, 41, 46 | Part 6, Part 7 |
| **CI/CD** | 22, 58, 59 | Part 6 |
| **Testing & QA** | 23, 31, 43, 46 | Part 7 |
| **IAM** | 24, 12, 33 | Part 5 |
| **Compliance & Governance** | 25, 47, 62 | Part 5 |
| **FinOps** | 26, 63 | Part 6 |
| **Disaster Recovery** | 27, 32, 52 | Part 6 |
| **API Lifecycle** | 28, 31 | Part 4 |
| **Multi-Tenancy** | 29, 39 | Part 5 |
| **Edge & IoT** | 30, 35 | Part 8 |
| **Service Versioning** | 31, 53 | Part 2, Part 3 |
| **High Availability** | 32, 27 | Part 6 |
| **Data Privacy** | 33, 43, 65 | Part 5, Part 8 |
| **Data Pipeline** | 34, 47 | Part 3 |
| **Digital Twins** | 35, 30 | Part 8 |
| **Scheduling** | 36, 46 | Part 7 |
| **Notifications** | 37, 50, 51 | Part 4 |
| **Localization** | 38 | Part 4 |
| **Licensing & Entitlement** | 39 | Part 5 |
| **Search** | 40, 47 | Part 3, Part 8 |
| **A/B Testing** | 41, 22 | Part 7 |
| **MLOps/LLMOps** | 42, 18 | Part 8 |
| **Synthetic Data** | 43, 65 | Part 8 |
| **Blockchain** | 44 | Part 5 |
| **Quantum-Safe Crypto** | 45 | Part 5 |
| **Capacity Planning** | 46, 26 | Part 7 |
| **Data Governance** | 47, 25, 60 | Part 3 |
| **Service Catalog** | 48, 21 | Part 4 |
| **Session Replication** | 49 | Part 3 |
| **Mobile Management** | 50, 14 | Part 4 |
| **Voice/Conversational** | 51, 13 | Part 4 |
| **Block Storage** | 52, 16 | Part 6 |
| **Message Transformation** | 53, 19 | Part 4 |
| **Time Synchronisation** | 54 | Part 5 |
| **Document Lifecycle** | 55, 20 | Part 8 |
| **HSM** | 56, 24 | Part 5 |
| **Network Policy** | 57, 12, 4 | Part 6 |
| **IaC** | 58, 59, 21 | Part 6 |
| **Environment Management** | 59, 21 | Part 6 |
| **Schema Migration** | 60, 16 | Part 3 |
| **Data Archival** | 61, 16 | Part 3 |
| **Incident Response** | 62, 25 | Part 5 |
| **Sustainability** | 63, 26 | Part 6 |
| **Multi-Cloud** | 64, 58 | Part 6 |
| **Data Masking** | 65, 33 | Part 5 |

### 5.2 How to Use This Document

This document is designed to be read in its entirety by architects and technical leads. For practitioners (developers, operators, model designers), the relevant chapters should be consulted based on their role:

- **Engine Developers:** Part 2 (Core Runtime) and Part 8 (Content/Knowledge).
- **Infrastructure Engineers:** Part 6 (Cloud-Native Infrastructure) and Part 7 (Observability/Testing).
- **Security Engineers:** Part 5 (Security, Identity, Compliance).
- **Model Designers:** Part 2 (Declarative Models) and Part 4 (Agentic Systems).
- **UI Developers:** Part 4 (API Management & UI/BFF).
- **Data Engineers:** Part 3 (Data Fabric) and Part 8 (Knowledge/AI).

### 5.3 Cross-Referencing

Throughout the document, cross-references to other parts and chapters are provided where relevant. For example, the discussion of the Transactional Outbox in Chapter 10 references the CDC implementation in Chapter 14, and the security implications are detailed in Chapter 22.

---

# PART 2: CORE RUNTIME & DOMAIN ORCHESTRATION

---

## Chapter 6: Modular Monolith & Clean Architecture (.NET 10)

### 6.1 Physical Project Structure (Vertical Slices per Module)

The codebase is organized into vertical slices, each representing a logical module (which may contain one or more engines). Within each module, Clean Architecture layers are strictly enforced at the project reference level.

```
src/
├── Modules/
│   ├── ProcessEngine.BPMN/
│   │   ├── ProcessEngine.BPMN.Domain/                    # No external dependencies
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
│   │   │   │   ├── IModelRepository.cs
│   │   │   │   ├── IUserTaskHandler.cs
│   │   │   │   ├── ITimerScheduler.cs
│   │   │   │   ├── IMessageBus.cs
│   │   │   │   ├── IDistributedLock.cs
│   │   │   │   └── IUnitOfWork.cs
│   │   │   ├── Engines/
│   │   │   │   ├── BpmnEngine.cs
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
│   │   │   │   │   └── KafkaTaskHandler.cs
│   │   │   │   ├── TimerScheduler/
│   │   │   │   │   ├── InMemoryTimerScheduler.cs
│   │   │   │   │   └── QuartzTimerScheduler.cs
│   │   │   │   ├── MessageBus/
│   │   │   │   │   ├── InMemoryBus.cs
│   │   │   │   │   └── KafkaBus.cs
│   │   │   │   └── Cache/
│   │   │   │       ├── LocalCacheAdapter.cs
│   │   │   │       └── RedisCacheAdapter.cs
│   │   │   ├── DI/
│   │   │   │   └── BpmnModuleCompositionRoot.cs
│   │   │   ├── Migrations/
│   │   │   │   └── (EF Core migrations)
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
│   ├── DecisionEngine.DMN/                               # Parallel structure
│   ├── CMMNEngine/                                      # Parallel structure
│   ├── StateMachineEngine/                              # Parallel structure
│   ├── CEPEngine/                                       # Parallel structure
│   ├── MultiAgentEngine/                                # Parallel structure
│   ├── KnowledgeEngine/                                 # Parallel structure
│   ├── ArtifactEngine/                                  # Parallel structure
│   ├── ContextManagementEngine/                         # Parallel structure
│   ├── DataIngestEngine/                                # Parallel structure
│   ├── ObservationEngine/                               # Parallel structure
│   ├── ServiceExposure/                                 # Parallel structure
│   └── ServiceConsumption/                              # Parallel structure
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
│   │   ├── Artifact/
│   │   │   ├── IArtifactParser.cs
│   │   │   ├── IArtifactGenerator.cs
│   │   │   └── IArtifactStorage.cs
│   │   ├── Agent/
│   │   │   ├── IAgentRegistry.cs
│   │   │   └── IAgentMessageBus.cs
│   │   └── ServiceDiscovery/
│   │       └── IServiceDiscovery.cs
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

### 6.2 The Domain Layer (Pure Logic)

The Domain layer contains the core business logic of the platform. It is independent of any infrastructure concerns.

**Aggregates:** Aggregate roots represent the primary stateful entities. For the BPMN Engine: `ProcessDefinition` and `ProcessInstance`. For the DMN Engine: `DecisionDefinition` and `DecisionExecution`. For the StateMachine Engine: `StateMachineDefinition` and `StateMachineInstance`.

**Entities:** Non-root entities within an aggregate. For the BPMN Engine: `TaskInstance`, `ProcessToken`, `TimerInstance`. For the DMN Engine: `DecisionInput`, `DecisionOutput`.

**Value Objects:** Immutable types such as `ProcessId`, `TaskId`, `VariableSet`, `Money`, `Address`, `Email`, `PhoneNumber`. Value objects encapsulate validation and behavior.

**Domain Events:** Facts that have occurred. They are raised by aggregates and collected by the domain event collector. Examples: `ProcessStartedEvent`, `TaskCompletedEvent`, `DecisionEvaluatedEvent`, `StateTransitionedEvent`.

**Invariants:** Aggregates enforce their own invariants. For example, a `ProcessInstance` cannot transition to a completed state if there are active tokens. A `StateMachineInstance` cannot transition to a state that is not defined in the statechart.

**No external dependencies** are allowed in the Domain layer. Only the .NET Base Class Library (BCL) and system namespaces are referenced.

### 6.3 The Application Layer (Use Cases & Ports)

The Application layer orchestrates the flow of data to/from entities and engines. It implements the business use cases of the system.

**Use Cases (Commands/Queries):** Implement the `IRequestHandler<TCommand, TResult>` pattern (abstracted via Wolverine/MediatR). Use Cases are responsible for:

- Loading aggregates from repositories.
- Invoking engines (interpreters) with the current state.
- Applying the resulting domain events to aggregates.
- Persisting the new state via `IUnitOfWork`.
- Publishing domain events via `IMessageBus`.

**Ports (Interfaces):** Defined purely in Domain/Application terms. Examples:

- `IProcessInstanceRepository` operates on `ProcessInstance` objects, not `DbConnection`.
- `IMessageBus` operates on `IDomainEvent` objects, not `ProducerRecord`.
- `IModelRepository` returns `ModelDefinition` objects, not file paths.
- `IDistributedLock` operates on `resourceId` strings, not Redis connections.
- `IClock` returns `DateTime`, not NTP timestamps.
- `ISecurityContext` returns `IIdentity`, not JWT claims.

**Cross-Cutting Abstractions:** The Application layer relies on the following interfaces for distributed concerns:

- `IDistributedLock` – for concurrency control across pods.
- `IMessageBus` – for publishing domain events.
- `IClock` – for obtaining the current time.
- `ICacheManager` – for caching frequently accessed data.
- `IUnitOfWork` – only for intra-module transaction boundaries.
- `ITracer` – for creating distributed trace spans.
- `ICircuitBreaker` – for preventing cascading failures.
- `IRetryPolicy` – for transient fault handling.

**Engine Interpreters:** The engines are implemented in the Application layer. They are stateless and depend only on Ports. For example, the `BpmnEngine` takes a `BpmnModel` and a `BpmnExecutionContext` and returns a `BpmnExecutionResult` containing commands and events.

**AOP Attributes:** Use Cases and engine methods are decorated with attributes such as `[TraceSpan]`, `[CircuitBreaker]`, `[RetryPolicy]`, and `[RateLimit]`. These are intercepted at compile time by .NET 10 source generators.

### 6.4 The Infrastructure Layer (Adapters)

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

### 6.5 Aspect-Oriented Programming (AOP) with .NET 10 Source Generators

The architecture leverages .NET 10's enhanced source generators and interceptors to implement cross-cutting concerns without cluttering the core Use Cases or engine code.

**Attributes:**

- `[TraceSpan]`: Automatically starts and ends an OpenTelemetry span around the method. The span name is derived from the method name and class name.
- `[CircuitBreaker]`: Wraps the method with a circuit breaker policy. The policy name is specified in the attribute.
- `[RetryPolicy]`: Applies a retry policy (exponential backoff with jitter). The max retries and base delay are configurable.
- `[RateLimit]`: Applies rate limiting (token bucket, sliding window).
- `[Bulkhead]`: Restricts concurrent executions of the method to a specified limit.

**Interceptors (Source Generation):**

At compile time, source generators produce interceptor code that wraps the target method with the specified policies. The interceptor reads the current `RuntimeEnvironment` from configuration:

- In **Development** and **Unit Tests**, `[RetryPolicy]` does nothing (immediate pass-through), `[CircuitBreaker]` is disabled, and `[TraceSpan]` only logs to the console.
- In **Production**, all policies are fully active with production-grade configurations (retry counts, timeout durations, circuit breaker thresholds) loaded from `RuntimeTopology.json`.

**Example:**

```csharp
[TraceSpan]
[CircuitBreaker(PolicyName = "BpmnEngine")]
[RetryPolicy(MaxRetries = 3, BaseDelayMs = 100)]
public async Task<StartProcessResult> Handle(StartProcessCommand cmd, CancellationToken ct)
{
    // Pure business logic
}
```

The generated interceptor wraps this method with OpenTelemetry span creation, circuit breaker state checks, and retry loops—all without the method itself having any knowledge of these concerns.

### 6.6 The Composition Root (DI Container)

The `Main.AppHost` is responsible for composing the DI container. It reads the `RuntimeTopology` configuration (from `appsettings.json` + environment overrides) and registers the appropriate adapters.

```csharp
public class Program
{
    public static void Main(string[] args)
    {
        var builder = WebApplication.CreateBuilder(args);
        var topology = builder.Configuration.GetSection("RuntimeTopology").Get<RuntimeTopology>();
        
        builder.Services.AddSingleton(topology);
        
        // Register shared infrastructure adapters based on topology
        builder.Services.AddSingleton<IMessageBus>(sp => topology.CommunicationMode switch
        {
            CommunicationMode.InMemory => new InMemoryBus(),
            CommunicationMode.Kafka => new KafkaBus(topology.KafkaOptions),
            CommunicationMode.RabbitMQ => new RabbitMqBus(topology.RabbitMqOptions),
            _ => new InMemoryBus()
        });
        
        builder.Services.AddSingleton<IDistributedLock>(sp => topology.LockStrategy switch
        {
            LockStrategy.Local => new LocalReentrantLock(),
            LockStrategy.Redis => new RedisDistributedLock(topology.RedisOptions),
            LockStrategy.Etcd => new EtcdDistributedLock(topology.EtcdOptions),
            _ => new LocalReentrantLock()
        });
        
        builder.Services.AddSingleton<ICacheManager>(sp => topology.CachingMode switch
        {
            CachingMode.Local => new LocalMemoryCache(),
            CachingMode.Redis => new RedisCacheManager(topology.RedisOptions),
            CachingMode.Hazelcast => new HazelcastCacheManager(topology.HazelcastOptions),
            _ => new LocalMemoryCache()
        });
        
        // Register modules
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
    }
}
```

### 6.7 Module Isolation (Hard Boundaries)

Despite being in a single process, modules are isolated via:

- **Compile-Time Rules:** Project references are restricted. `ModuleA.Domain` cannot reference `ModuleB.Domain`. Module projects cannot reference other module's Domain or Application projects.
- **Strong Names:** Each module is strong-named to prevent accidental assembly collisions.
- **Interface-Based Communication:** Cross-module communication is only allowed through `IMessageBus` (events) or explicit Query interfaces defined in `Shared.Abstractions`. Direct method calls between modules are forbidden.
- **Database Schemas:** Each module has its own dedicated database schema (or table prefix). Modules do not share tables. Foreign key constraints across modules are prohibited.
- **Event-Driven Decoupling:** Modules communicate via domain events. A module may subscribe to events from other modules, but it never directly manipulates the state of another module.

### 6.8 Intra-Process vs. Inter-Process Transparency

The Use Cases and engines are completely agnostic to whether they are running in a single process or across multiple processes.

- **In-Memory Mode:** `InMemoryBus` routes events to handlers synchronously (on the same thread or a dedicated async task). `InMemoryTimerScheduler` uses `System.Threading.Timer`. `LocalReentrantLock` uses `Monitor.Enter`. This provides sub-millisecond latency and simplifies debugging.
- **Distributed Mode:** `KafkaBus` serializes events and produces to Kafka. `QuartzTimerScheduler` uses a distributed database for scheduled jobs. `RedisDistributedLock` uses Redis Redlock.

The Use Case code remains unchanged. It calls `_messageBus.PublishAsync(event)` and assumes eventual consistency. The `InMemoryBus` simulates eventual consistency by executing handlers asynchronously (with a small delay) to surface concurrency issues early.

---

## Chapter 7: The Engine Ecosystem

### 7.1 Engine Abstraction

Every engine in the system conforms to a common abstraction:

```csharp
public interface IEngine<TModel, TContext, TResult>
{
    Task<TResult> ExecuteAsync(TModel model, TContext context, CancellationToken ct);
}
```

- `TModel` is the declarative model (e.g., `BpmnModel`, `DmnModel`, `CmmnModel`, `StatechartModel`, `CepPattern`, `AgentProtocol`).
- `TContext` is the execution context (variables, current state, agent identity, available tools, etc.).
- `TResult` contains the commands generated, events emitted, and any decision outcomes.

Engines are stateless. All state is passed in via the context and stored by the caller (Use Case) after execution. This enables horizontal scaling and replayability.

### 7.2 BPMN Engine

**Purpose:** Orchestrates long-running, stateful process flows (human tasks, system tasks, sub-processes, event sub-processes, compensation, escalation).

**Standards:** BPMN 2.0 XML.

**Capabilities:**
- Token-based execution (AND/OR/XOR gateways).
- Parallel gateways and event-based gateways.
- Timer events, error boundaries, escalation boundaries.
- Compensation and cancellation.
- Sub-processes (embedded, event, ad-hoc).
- Call activities (reusable processes).
- Signal and message events.

**Inputs:** Process model (BPMN XML), process variables (key-value map), current active node(s).

**Outputs:** Next nodes to activate, tasks to assign (user or system), timers to schedule, events to emit (process started, process ended, task assigned, signal raised).

**Model File Format:** BPMN 2.0 XML.

### 7.3 CMMN Engine

**Purpose:** Manages dynamic, case-based work (ad-hoc tasks, milestones, planning stages, discretionary activities).

**Standards:** CMMN 1.1 XML.

**Capabilities:**
- Case file items (data model for the case).
- Manual activation of discretionary tasks.
- Sentry conditions (entry/exit criteria).
- Milestone completion.
- Planning stages.
- Repetition rules.

**Inputs:** Case model (CMMN XML), case file state, active stages.

**Outputs:** Tasks to offer, milestones to complete, events to emit (case started, milestone reached, task completed).

**Model File Format:** CMMN 1.1 XML.

### 7.4 DMN Engine

**Purpose:** Evaluates complex business rules and decision tables.

**Standards:** DMN 1.3 XML.

**Capabilities:**
- Decision tables (hit policies: unique, first, priority, collect, rule order).
- FEEL expressions (Friendly Enough Expression Language).
- Context mapping, input data binding.
- Decision requirements graphs (DRG).
- Built-in functions (arithmetic, string, date/time, list, context).
- Decision literal expressions.

**Inputs:** Decision model (DMN XML), input data (variables).

**Outputs:** Decision outputs (scalar, table, context).

**Model File Format:** DMN 1.3 XML.

### 7.5 CEP Engine

**Purpose:** Detects complex event patterns over streaming data (time windows, correlations, aggregations, sequence patterns, anomaly detection).

**Standards:** Custom DSL (JSON/YAML-based) or Drools DRL/Flink SQL.

**Capabilities:**
- Sliding windows and tumbling windows.
- Event correlation (correlate events by key).
- Temporal constraints (event A must occur within 5 minutes of event B).
- Pattern matching (sequence, conjunction, disjunction).
- Aggregations (count, sum, avg, max, min).
- Alert generation and derived event emission.

**Inputs:** Event streams, pattern definitions.

**Outputs:** Pattern matches, alerts, derived events.

**Model File Format:** Custom JSON/YAML pattern definition or Drools DRL.

### 7.6 StateMachine Engine

**Purpose:** Manages finite-state transitions for entities (order states, approval states, lifecycle states).

**Standards:** SCXML (State Chart XML) or custom Statechart JSON.

**Capabilities:**
- Hierarchical states (nested states).
- Parallel states (orthogonal regions).
- Guards (transition conditions).
- Actions (entry, exit, transition).
- History states (deep and shallow).
- Event-driven transitions.
- Timeouts (delayed transitions).

**Inputs:** Statechart model, current state, triggering event.

**Outputs:** New state, actions to execute, events to emit (state transitioned).

**Model File Format:** SCXML or custom JSON Statechart.

### 7.7 Multi-Agent Interaction Engine

**Purpose:** Coordinates agent-to-agent interaction protocols (negotiation, auction, contract-net, delegation, argumentation, voting).

**Standards:** A2A (Agent-to-Agent) protocol, MCP (Model Context Protocol), custom negotiation DSL.

**Capabilities:**
- Protocol execution (initiate, respond, terminate).
- Bidding and proposal evaluation.
- Contract establishment.
- Agent role assignment (manager, worker, bidder, evaluator).
- Delegation and re-delegation.
- Argumentation and debate.
- Negotiation with offers and counter-offers.

**Inputs:** Agent definitions (capabilities, preferences), protocol model, participant state.

**Outputs:** Protocol steps, messages to agents, agreements, contracts, delegation assignments.

**Model File Format:** A2A JSON, MCP Schema, custom Negotiation DSL.

### 7.8 Knowledge Engine (RAG, Graph, Semantic, ML, Process Mining)

**Purpose:** Provides context, semantic understanding, analytical insights, and retrieval capabilities.

**Sub-Components:**

**RAG (Retrieval-Augmented Generation):**
- Ingests documents, chunks them, computes embeddings (via embedding models), stores in vector database.
- Retrieves relevant chunks based on semantic similarity to a query.
- Provides retrieved chunks as context to LLMs.

**Graph Traversal:**
- Executes queries against graph databases (Neo4j, AWS Neptune) to find relationships and paths.
- Supports property graph and RDF models.

**Semantic Search:**
- Uses embeddings to find semantically similar content across documents and data stores.
- Supports hybrid search (dense + sparse).

**ML / Data-Mining:**
- Executes predictive models (ML.NET, ONNX) for classification, regression, clustering.
- Executes data-mining algorithms (association rules, anomaly detection).

**Process Mining:**
- Analyses XES event logs to discover process variations, bottlenecks, conformance violations, and improvement opportunities.

**Inputs:** Query (text, vector, graph pattern), analytical model.

**Outputs:** Context bundles (documents, graph paths, predictions, mining insights).

**Model File Format:** OpenAPI, GraphQL, SPARQL, vector index schemas, MLflow models.

### 7.9 Observation & BAM (Business Activity Monitoring) Engine

**Purpose:** Monitors execution logs, metrics, and events to provide real-time dashboards, alerts, and performance indicators.

**Capabilities:**
- SLA monitoring (track process completion times against SLAs).
- KPI tracking (process throughput, error rates, decision outcomes).
- Anomaly detection (unusual process behaviour, sudden increase in errors).
- Trend analysis (process volume trends, seasonality).
- Root-cause analysis (drill down into failed processes).
- Live dashboards (REST API for UI consumption).

**Inputs:** Telemetry data (traces, metrics, logs, domain events), monitoring dashboards.

**Outputs:** Dashboards, alerts, aggregated reports.

**Model File Format:** JSON Dashboard (Grafana Dashboard JSON, custom OLAP cube definition).

### 7.10 Data Ingest Engine

**Purpose:** Receives, validates, transforms, and routes incoming data from external sources into the system's storage or processing pipelines.

**Capabilities:**
- Data validation (JSON Schema, XML Schema, custom validation rules).
- Data transformation (mapping, enrichment, normalization).
- Deduplication (check for duplicate incoming data).
- Routing to Bounded Contexts (based on data content or metadata).
- File upload handling (multipart, chunked uploads).
- Batch processing (large CSV/JSON files).

**Inputs:** Raw data payloads (JSON, XML, CSV, binary, multipart files).

**Outputs:** Normalized domain events, stored artifacts, notifications.

**Model File Format:** JSON Mapping, XSLT (XML), Groovy scripts.

### 7.11 Context Management Engine

**Purpose:** Manages the lifecycle of execution contexts, including variable persistence, context inheritance, and context sharing across agents and processes.

**Capabilities:**
- Context creation (initialize variables from model defaults).
- Context snapshots (point-in-time capture of context state).
- Context merging (merge two contexts, resolving conflicts).
- Context versioning (track changes to context over time).
- Permission control (read/write access per user/agent).
- Context inheritance (child contexts inherit from parent).

**Inputs:** Context definitions (JSON Schema), parent contexts, updates.

**Outputs:** Context instances, context history, merged contexts.

**Model File Format:** JSON Schema, custom context definition models.

### 7.12 Artifact Management Engine

**Purpose:** Parses, renders, generates, and transforms artifacts of various formats.

**Supported Formats (examples, non-exhaustive):**
- **Document Formats:** Microsoft Open XML (DOCX, XLSX, PPTX), PDF/A, HTML5, Markdown, Plain Text, LaTeX, RTF, ODT.
- **Data Formats:** JSON, XML, CSV, Avro, Protobuf, Parquet, YAML, BSON, CBOR, MessagePack.
- **CAD Formats:** STEP, IGES, STL, DWG, DXF, IFC.
- **Source Code:** C#, Python, Java, JavaScript, TypeScript, SQL, Go, Rust.
- **Multimedia:** Images (PNG, JPEG, SVG), Audio (WAV, MP3), Video (MP4, AVI).

**Capabilities:**
- **Parsing:** Extract structured data from artifacts (table data from XLSX, text from PDF, metadata from images).
- **Rendering / Generation:** Populate templates with data and produce artifacts (generate a contract DOCX from a template and variables).
- **Transformation:** Convert between formats (DOCX to PDF, Markdown to HTML, JSON to Avro).
- **Validation:** Validate artifacts against schemas or business rules (JSON Schema, XSD, business rule validation).
- **Chunking:** Split large documents into semantically coherent chunks for ingestion into RAG pipelines.
- **Embedding:** Compute vector embeddings for text chunks (using embedding models).

**Inputs:** Artifact template, data bindings, source artifacts.

**Outputs:** Generated artifacts, parsed data structures, chunks with embeddings.

**Model File Format:** Template files (DOCX, XLSX, HTML), JSON Schema, XSD.

### 7.13 Service Exposure Layer

**Purpose:** Exposes the capabilities of the system as external services (REST APIs, gRPC services, GraphQL endpoints, event streams).

**Capabilities:**
- Request routing (URL-based, header-based, host-based).
- Input validation (JSON Schema, Protobuf validation).
- Authentication/Authorization (OAuth2, JWT, mTLS).
- Rate limiting (token bucket, sliding window).
- API versioning (URL path, header, content-type).
- Documentation generation (OpenAPI, GraphQL Schema, Protobuf).
- Request/response logging.
- CORS configuration.

**Inputs:** Incoming requests (HTTP, gRPC, GraphQL).

**Outputs:** Responses (JSON, Protobuf), emitted events (WebSocket, SSE).

**Model File Format:** OpenAPI (Swagger) 3.0, gRPC Protobuf, GraphQL Schema, AsyncAPI.

### 7.14 Service Consumption Layer

**Purpose:** Consumes external services (third-party APIs, legacy systems, partner services) as part of engine execution.

**Capabilities:**
- Connection management (pooling, keep-alive).
- Retry policies (exponential backoff with jitter).
- Circuit breakers (prevent cascading failures).
- Request transformations (input mapping, header injection).
- Response mapping (extract relevant data from external response).
- Credential rotation (inject dynamic credentials from Vault).
- Idempotency (ensure duplicate requests are safe).
- Timeouts and deadlines.

**Inputs:** External request definitions (models).

**Outputs:** Data mapped into the system's domain.

**Model File Format:** OpenAPI Client, gRPC Client, SOAP WSDL, Kafka Topic Binding.

---

## Chapter 8: Declarative Model Repository & Versioning

### 8.1 Model Repository Abstraction

The `IModelRepository` port provides a uniform interface for accessing declarative models across all engines.

```csharp
public interface IModelRepository
{
    Task<ModelDefinition> GetModelAsync(string context, string modelKey, string versionTag, CancellationToken ct);
    Task<ModelDefinition> GetLatestModelAsync(string context, string modelKey, CancellationToken ct);
    Task<IEnumerable<ModelVersion>> ListVersionsAsync(string context, string modelKey, CancellationToken ct);
    Task<ModelValidationResult> ValidateModelAsync(string context, string modelKey, string content, CancellationToken ct);
    Task<ModelPromotionResult> PromoteModelAsync(string context, string modelKey, string versionTag, string targetEnvironment, CancellationToken ct);
}
```

- `ModelDefinition` contains the raw content (XML, JSON, binary) and metadata (type, version, checksum, model hash).
- `ModelVersion` is a Semantic Versioning tag (MAJOR.MINOR.PATCH).
- `ModelValidationResult` contains syntax and semantic validation results.

### 8.2 Supported Model Types and File Formats

The Model Repository supports a wide range of model types and file formats. This list is exemplary and extensible:

| Engine / Layer | Model Type | File Formats / Standards |
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
| Artifact Engine | CAD Artifact | STEP, IGES, STL, DWG, DXF, IFC |
| Artifact Engine | Source Code | C#, Python, Java, JavaScript, TypeScript, SQL, Go, Rust |
| Knowledge Engine | Ontology / Graph Schema | RDF, OWL, SPARQL, GraphQL Schema, OpenAPI |
| Knowledge Engine | Vector Index Schema | Custom JSON (field mappings, embedding configurations) |
| Data Ingest Engine | Ingestion Mapping | JSON Mapping, XSLT (XML), Groovy scripts |
| Service Exposure | API Contract | OpenAPI (Swagger) 3.0, gRPC Protobuf, GraphQL Schema, AsyncAPI |
| Service Consumption | External API Binding | OpenAPI Client, gRPC Client, SOAP WSDL, Kafka Topic Binding |
| Observation Engine | Dashboard Definition | JSON Dashboard (Grafana Dashboard JSON, custom OLAP cube definition) |
| Process Mining Engine | Mining Configuration | XES export configuration, Celonis process definition |
| Agent Engine | Skill Definition | JSON Skill Manifest, MCP Tool Definition |

### 8.3 Versioning Strategy

**Semantic Versioning (MAJOR.MINOR.PATCH):** Applied to every model artifact.

- **MAJOR:** Breaking changes (e.g., changed BPMN node types, removed DMN inputs, changed API contract).
- **MINOR:** Backward-compatible additions (e.g., new DMN decision, new BPMN event handler, new API endpoint).
- **PATCH:** Bug fixes or non-functional changes (e.g., corrected DMN expression, updated error message, performance optimization).

**Immutable Versions:** Once a model version is marked `RELEASED`, it cannot be modified. Any change requires a new version.

**Version Resolution:** Engines resolve models by `(context, modelKey, versionTag)`. If `versionTag` is omitted, the latest `RELEASED` version is used.

**Canary Deployments of Models:** Different model versions can be routed to different subsets of instances using Istio traffic splitting or feature flags. For example, 90% of traffic uses `v1.0`, 10% uses `v1.1` (canary) without recompiling the engine.

### 8.4 Model Validation Pipeline

Upon commit to the model repository (Git), a CI pipeline runs:

1. **Syntax Validation:** Ensure the artifact conforms to its schema (e.g., BPMN XSD, DMN XSD, JSON Schema, Protobuf syntax).
2. **Semantic Validation:** Ensure referential integrity (e.g., all DMN input data is referenced, all BPMN service tasks have implementation bindings, all API endpoints have valid schemas).
3. **Engine-Specific Validation:** Simulate execution of the model in a sandbox environment to catch runtime errors (e.g., FEEL expression errors, script compilation errors, infinite loops).
4. **Artifact Rendering Test:** For document templates, render a sample document with dummy data to ensure the template compiles and renders correctly.
5. **Security Scan:** Scan the model for malicious content (e.g., script injection, remote code execution in script tasks, excessive recursion).
6. **Performance Impact Assessment:** Estimate the performance impact of the new model (e.g., complexity of DMN decision tables, depth of BPMN process).

Failed models are rejected and never promoted to the production Model Registry. The validation results are reported back to the model designer with detailed error messages.

### 8.5 Model Repository Implementations

| Environment | Adapter | Description |
| :--- | :--- | :--- |
| **Development** | `FileSystemModelRepository` | Reads models from a local directory. Supports hot-reload (file watcher) for rapid iteration. |
| **Test / Staging** | `GitLabModelRepository` (or Azure DevOps, GitHub Packages) | Connects to a centralized model registry API. Supports version listing, content retrieval, and validation. |
| **Production** | `GitLabModelRepository` + `ModelCache` | Reads models from the model registry with a Redis or in-memory cache to reduce repository calls. Supports cache invalidation on new model versions. |

### 8.6 Model Lifecycle

1. **Draft:** Model is being authored. Not yet validated. Only available locally.
2. **Validated:** Model has passed the validation pipeline. Available in Dev environment.
3. **Staged:** Model is promoted to a staging environment for integration testing with production-like data.
4. **Released:** Model is promoted to production. Immutable. Available to all production workloads.
5. **Deprecated:** Model is no longer recommended for new instances. Existing instances continue to use it. Deprecation warnings are emitted in logs.
6. **Archived:** Model is no longer in use. Retained for historical audit. Not available for new executions.

---

## Chapter 9: Inter-Service Communication (Synchronous & Asynchronous)

### 9.1 Communication Modes

The architecture supports multiple communication modes, selected via `RuntimeTopology.CommunicationMode`:

| Mode | Description | Use Case |
| :--- | :--- | :--- |
| **InMemory** | Direct method calls via DI (synchronous or async). | Development, unit testing. |
| **gRPC** | Synchronous, high-performance RPC with typed contracts (Protobuf). | Internal service-to-service queries, real-time data retrieval. |
| **HTTP/REST** | Synchronous REST APIs with JSON payloads. | External integrations, legacy clients, UI BFF. |
| **Kafka** | Asynchronous, durable, high-throughput event streaming with exactly-once semantics. | Cross-module event propagation, event sourcing, pub/sub. |
| **RabbitMQ** | Asynchronous messaging with flexible routing (direct, topic, fanout, headers). | Work queues, RPC over messaging, low-latency pub/sub. |
| **NATS/JetStream** | High-performance messaging with at-least-once and exactly-once delivery. | Low-latency intra-cluster communication, IoT messaging. |
| **Azure Service Bus / AWS SQS** | Cloud-native managed messaging. | Integration with cloud ecosystems, managed services. |

All communication is abstracted behind the `IMessageBus` (events) and `IQueryDispatcher` (queries) ports.

### 9.2 Synchronous Communication (Request/Reply)

**Protocols:**
- **gRPC:** Preferred for internal service-to-service communication. Provides low latency, strong typing, and bidirectional streaming.
- **HTTP/REST:** Used for external integrations and UI BFF. JSON payloads, OpenAPI contracts.
- **GraphQL:** Used for complex queries where clients need to select specific fields and avoid over-fetching.

**Client Resilience:**
- **Circuit Breaker:** Prevents cascading failures. Wrapped around every synchronous call.
- **Retry Policy:** Exponential backoff with jitter. Configurable per service.
- **Timeout:** Strict timeouts to prevent hanging operations (e.g., 5 seconds for internal calls, 30 seconds for external).
- **Bulkhead:** Limits concurrent outbound requests to prevent thread pool exhaustion.

**Client-Side Load Balancing:**
- **In Development:** Localhost load balancing (single instance).
- **In Production:** Client-side load balancing using Consul endpoint list or Kubernetes DNS. Round-robin or least-connections algorithm.

### 9.3 Asynchronous Communication (Events & Messaging)

**Message Broker:** Apache Kafka is the primary message broker for production environments. RabbitMQ is supported as an alternative.

**Event Publishing:**
- Use Cases publish domain events via `IMessageBus.PublishAsync<TEvent>(TEvent @event)`.
- The event is serialized using the configured serializer (JSON, Avro, Protobuf) based on the Schema Registry.
- The event is produced to a Kafka topic named after the event type (or a configured routing key).

**Event Consumption:**
- Each module has a set of event handlers that implement `IEventHandler<TEvent>`.
- The handlers are registered in the DI container and automatically subscribed to the appropriate Kafka topics.
- In Development (InMemoryBus), the handlers are invoked directly (synchronously or via a task queue).

**Guaranteed Delivery:**
- **At-Least-Once:** Kafka provides at-least-once delivery. Consumers are idempotent to handle duplicates.
- **Exactly-Once:** Achieved through idempotent consumers + deduplication cache (Redis).
- **Dead-Letter Queue (DLQ):** Events that fail processing after retries are routed to a DLQ for manual inspection.

### 9.4 Cross-Module Communication

Modules communicate exclusively through:

1. **Asynchronous Domain Events:** For state changes that need to be propagated to other modules (e.g., `OrderConfirmed` -> `Inventory` reserves stock).
2. **Synchronous Queries:** For read-only data retrieval (e.g., `GetOrderStatus` query to `Ordering` module from the UI BFF).

**Forbidden Patterns:**
- Direct method calls between modules.
- Shared database tables between modules.
- Shared domain entities between modules.
- Distributed transactions (2PC) across modules.

### 9.5 Event Schemas and Schema Registry

All domain events have a defined schema (Avro, Protobuf, or JSON Schema). The schema is stored in the **Schema Registry** (Confluent Schema Registry, Apicurio, or AWS Glue Schema Registry).

**Compatibility Modes:**
- **Backward:** New schema can read old data (add fields with defaults).
- **Forward:** Old schema can read new data (ignore unknown fields).
- **Full:** Both backward and forward compatible.
- **None:** No compatibility checks (used for development).

**Event Versioning:**
- Each event type has a `version` field (integer).
- The Schema Registry tracks the version history of each event type.
- Consumers specify which schema version they support. The `KafkaBus` adapter fetches the appropriate schema from the Schema Registry before deserializing.
- If a consumer receives an event with an unsupported major version, it routes the event to a DLQ.

---

## Chapter 10: Distributed Transactions (Saga, Outbox, Idempotency)

### 10.1 Intra-Module Transactions (ACID)

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

| Environment | Adapter | Description |
| :--- | :--- | :--- |
| **Development** | `NoOpOutboxProcessor` | Events are published directly without an Outbox table. Simplifies development but does not test eventual consistency. |
| **Test / Staging** | `OutboxProcessor` (polling) | A background task polls the Outbox table every N seconds and publishes events to Kafka. |
| **Production** | `DebeziumOutboxRelay` | Debezium's PostgreSQL or SQL Server connector streams Outbox table changes directly to Kafka. Provides exactly-once delivery, low latency, and no polling overhead. |

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
    RetryCount INT NOT NULL DEFAULT 0,
    PartitionKey NVARCHAR(255) NULL
);
```

**Consumer Idempotency:** Each consumer maintains an **Inbox** table to prevent duplicate processing.

```sql
CREATE TABLE Inbox (
    Id BIGINT IDENTITY(1,1) PRIMARY KEY,
    EventId NVARCHAR(255) NOT NULL UNIQUE,
    ProcessedOn DATETIME2 NOT NULL
);
```

The consumer stores the `EventId` (or `Offset` + `Partition`) in the Inbox before processing. If the same event is received again, it is ignored.

### 10.4 Saga Orchestration

For workflows that span multiple modules and require compensation (e.g., Reserve Stock -> Confirm Order -> Collect Payment), a **Saga Orchestrator** is used.

**Implementation:**
- The orchestrator is a state machine (implemented using the StateMachine Engine) that manages the Saga execution.
- The orchestrator sends commands to individual modules (via the message bus) and listens for their responses (events).
- If a step fails, the orchestrator sends compensation commands to undo previous steps.
- The Saga state is persisted in a dedicated Saga repository (SQL Server or EventStoreDB).

**Saga Definition:** The Saga flow is defined declaratively in a JSON or YAML model, stored in the Model Repository. The model defines:

- Steps (commands to send to modules).
- Compensation steps (commands to undo).
- Event mappings (which events trigger which transitions).
- Timeouts (max duration for each step).

**Adapters for Saga Storage:**

- **Dev:** `InMemorySagaRepository` (stores sagas in memory).
- **Prod:** `EFCoreSagaRepository` (stores saga instances in the database).

### 10.5 Distributed Locking with Safety

**Purpose:** Prevent concurrent execution of critical sections across multiple pods (e.g., processing the same order ID simultaneously, executing the same timer event twice).

**Port:** `IDistributedLock`

**Adapters:**

| Environment | Adapter | Description |
| :--- | :--- | :--- |
| **Development** | `LocalReentrantLock` | Uses `System.Threading.ReaderWriterLockSlim`. Fastest, only works within a single process. |
| **Test / Staging** | `RedisDistributedLock` | Implements Redlock algorithm using Redis. Works across multiple pods. |
| **Production** | `EtcdDistributedLock` | Uses etcd leases. Provides strong consistency, TTL, and watch capabilities. Preferred for production. |

**Usage Pattern:**

```csharp
public async Task<ProcessResult> StartProcess(StartProcessCommand cmd)
{
    var lockKey = $"process:{cmd.ProcessId}";
    using var lockHandle = await _distributedLock.AcquireAsync(lockKey, TimeSpan.FromSeconds(30));
    if (!lockHandle.IsAcquired)
        throw new ConcurrencyException("Process is already being processed");
    
    // Critical section: load, execute, save
    var instance = await _repository.LoadAsync(cmd.ProcessId);
    var result = await _engine.ExecuteAsync(instance);
    await _repository.SaveAsync(instance);
    await _unitOfWork.CommitAsync();
}
```

**Fencing Tokens:** To prevent split-brain, etcd locks include a fencing token (monotonically increasing integer). The repository checks the token before writing, ensuring that a stale writer cannot overwrite a newer state.

### 10.6 Exactly-Once Processing

**Achieved through:**
1. **Idempotent Consumers:** Every event handler is idempotent. It checks if the event has already been processed (via Inbox table) before applying changes.
2. **Idempotency Keys:** For API endpoints, clients provide an idempotency key. The API stores the key and the result, returning the same result for duplicate requests.
3. **Kafka Transactions:** Producers use Kafka transactions to ensure that messages are written exactly once to the topic.
4. **Deduplication Cache:** A Redis cache stores processed event IDs for a configurable TTL to avoid duplicate processing even if the Inbox table fails.

---

## Chapter 11: Service Discovery & Registry Abstraction

### 11.1 Service Discovery Abstraction

The `IServiceDiscovery` port provides dynamic service resolution.

```csharp
public interface IServiceDiscovery
{
    Task<string> GetServiceEndpointAsync(string serviceName, string environment, CancellationToken ct);
    Task<IEnumerable<ServiceInstance>> GetInstancesAsync(string serviceName, CancellationToken ct);
    Task RegisterServiceAsync(ServiceRegistration registration, CancellationToken ct);
    Task DeregisterServiceAsync(string serviceId, CancellationToken ct);
}
```

- `ServiceInstance` contains: `InstanceId`, `Address`, `Port`, `Metadata` (version, environment, tags).
- `ServiceRegistration` contains: `ServiceName`, `InstanceId`, `Address`, `Port`, `HealthCheckEndpoint`, `Metadata`.

### 11.2 Service Discovery Adapters

| Environment | Adapter | Description |
| :--- | :--- | :--- |
| **Development** | `LocalhostServiceDiscovery` | Resolves to `localhost:port` based on configuration. No registration required. |
| **Test / Staging** | `ConsulServiceDiscovery` | Resolves services using Consul DNS or HTTP API. Supports health checks, datacenter awareness. Services register themselves on startup. |
| **Production** | `ConsulServiceDiscovery` + `KubernetesServiceDiscovery` | Uses Consul for service registry with health checks. Falls back to Kubernetes DNS if Consul is unavailable. |
| **Istio Integration** | `IstioServiceDiscovery` | Uses Istio's service entry and destination rule configurations. Supports mTLS and traffic splitting. |

### 11.3 Service Registration Lifecycle

**On Startup:**
1. The service reads its configuration (service name, port, metadata) from `RuntimeTopology`.
2. The service registers itself with the service registry (Consul or Kubernetes) via `IServiceDiscovery.RegisterServiceAsync()`.
3. The service starts a health check endpoint (`/health`).
4. The registry periodically pings the health endpoint. If it fails, the service is deregistered.

**On Shutdown:**
1. The service gracefully shuts down (draining connections).
2. The service deregisters itself via `IServiceDiscovery.DeregisterServiceAsync()`.

### 11.4 Client-Side Load Balancing

The `ServiceClient` adapter uses the service discovery information to perform client-side load balancing:

**Algorithms:**
- **Round-Robin:** Default algorithm.
- **Least-Connections:** Routes to the instance with the fewest active connections.
- **Consistent Hashing:** Routes requests for the same resource ID to the same instance (useful for stateful workloads).
- **Weighted:** Routes based on weights specified in the service metadata.

**Integration with Service Mesh:** When Istio is enabled, client-side load balancing is handled by the Envoy sidecar, not by the application code. The `IServiceDiscovery` implementation simply resolves the service name to `http://service-name` and relies on the sidecar to perform load balancing, circuit breaking, and retries.

### 11.5 Metadata-Based Routing

Services register with metadata tags (e.g., `version=v2`, `env=staging`, `region=us-east`). The client can specify metadata filters in the request:

```csharp
var instances = await _serviceDiscovery.GetInstancesAsync("OrderingService", filter => filter["version"] == "v2");
```

**Use Cases:**
- Canary deployments (route to `v2` for a subset of traffic).
- Multi-tenancy (route tenant-specific requests to dedicated instances).
- Region affinity (route to the nearest region).

---

# PART 3: DATA FABRIC & EVENT STREAMING

---

## Chapter 12: Multi-Model Persistence

### 12.1 The Polyglot Persistence Strategy

The platform recognizes that no single storage technology is optimal for all workloads. Different data models require different storage engines. The architecture employs a polyglot persistence strategy, where each data store is selected based on the access patterns, consistency requirements, and scalability needs of the specific workload.

All access to these stores is abstracted behind Ports (`IRepository`, `IEventStore`, `IVectorStore`, `IGraphStore`, `IBlobStorage`, `ITimeSeriesStore`) in the Application layer. This ensures that the choice of storage technology is an infrastructure concern, not a business logic concern.

### 12.2 Relational (SQL) Storage

**Purpose:** ACID transactions, complex queries, strict schemas, referential integrity, and reporting.

**Primary Use Cases:**
- Aggregates that require strong consistency and transactional integrity.
- Process instances, case instances, and state machine instances.
- Saga state and Outbox/Inbox tables.
- Reference data and configuration.
- Reporting and OLAP cubes.

**Implementation:**

| Environment | Adapter | Description |
| :--- | :--- | :--- |
| **Development** | `InMemoryRelationalStore` | Simulates relational behavior in memory. Fast, no persistence. |
| **Test** | `EFCorePostgresRepository` | PostgreSQL container with test data. |
| **Staging** | `EFCorePostgresRepository` | PostgreSQL cluster with staging data (anonymized). |
| **Production** | `EFCorePostgresRepository` | PostgreSQL cluster with high availability (streaming replication, automatic failover). |

**Schema Design:**
- Each module owns its own database schema (e.g., `ordering`, `inventory`, `billing`).
- Tables within a schema represent aggregates and their entities.
- Foreign keys are strictly within the schema. Cross-schema foreign keys are prohibited.
- Migration scripts are version-controlled and applied via Flyway/Liquibase.

**Database Selection Criteria:**

| Database | Use Case | Justification |
| :--- | :--- | :--- |
| **PostgreSQL** | Primary relational store | Open-source, ACID compliant, extensible (JSONB, pgvector, TimescaleDB extension), strong community, cloud-native managed options available. |
| **CockroachDB** | Distributed SQL for multi-region active-active | PostgreSQL wire-compatible, global distribution, strong consistency. Used for workloads requiring multi-region failover. |
| **MySQL** | Legacy compatibility | Supported for legacy migrations but not preferred. |

### 12.3 Document (NoSQL) Storage

**Purpose:** Flexible schema, high write throughput, JSON-centric data, and horizontal scaling.

**Primary Use Cases:**
- Event-sourced aggregates stored as JSON documents.
- User profiles and preferences.
- Content management (CMS) data.
- Logs and audit data (prior to archiving).

**Implementation:**

| Environment | Adapter | Description |
| :--- | :--- | :--- |
| **Development** | `InMemoryDocumentStore` | Simulates document store in memory. |
| **Test** | `MongoDbClient` | MongoDB container with test data. |
| **Production** | `MongoDbClient` | MongoDB cluster with sharding and replication. |

**Schema Design:**
- Collections are scoped to modules (e.g., `ordering.orders`, `inventory.items`).
- Documents are denormalized aggregates.
- Change streams are used to capture document changes for CDC.

### 12.4 Graph Storage

**Purpose:** Model highly connected data, semantic relationships, knowledge representation, and graph traversal queries.

**Primary Use Cases:**
- Knowledge graphs (ontology, RDF, property graphs).
- Digital twins (asset relationships).
- Semantic search and recommendation.
- Process mining (discovered process models).
- Agent memory (relationships between entities).

**Implementation:**

| Environment | Adapter | Description |
| :--- | :--- | :--- |
| **Development** | `LocalLuceneGraph` | Embedded graph store (in-memory). |
| **Test** | `Neo4jClient` | Neo4j container with test data. |
| **Production** | `Neo4jClient` | Neo4j cluster with causal clustering and high availability. |

**Graph Models:**
- **Property Graph:** Nodes, relationships, properties. Used for most operational graph queries.
- **RDF (Resource Description Framework):** Used for semantic web and ontology-based reasoning.

**Query Languages:**
- **Cypher:** For property graph traversal (Neo4j).
- **SPARQL:** For RDF querying (Amazon Neptune, Stardog).

### 12.5 Vector Storage

**Purpose:** Store and search high-dimensional embeddings for semantic similarity, RAG (Retrieval-Augmented Generation), and AI memory.

**Primary Use Cases:**
- Document embeddings for RAG pipelines.
- Agent memory (embedding of past conversations and decisions).
- Semantic search.
- Recommendation systems.
- Anomaly detection (embedding of system behaviour).

**Implementation:**

| Environment | Adapter | Description |
| :--- | :--- | :--- |
| **Development** | `LocalLuceneIndex` | Embedded vector index (in-memory). |
| **Test** | `MilvusClient` | Milvus container with test data. |
| **Production** | `MilvusClient` | Milvus cluster with sharding and replication. |

**Alternative Vector Stores:**

| Database | Use Case | Justification |
| :--- | :--- | :--- |
| **pgvector** | PostgreSQL extension | Simple vector search integrated with relational data. Suitable for small to medium workloads. |
| **Qdrant** | High-performance vector search | Open-source, high-performance, supports filtering and hybrid search. |
| **Pinecone** | Managed vector database | Cloud-native, fully managed, high availability. |
| **Weaviate** | Hybrid search (keyword + vector) | Built-in RAG capabilities, GraphQL interface. |

### 12.6 Time-Series Storage

**Purpose:** Ingest and query high-volume time-stamped metrics, sensor data, and financial ticks.

**Primary Use Cases:**
- System metrics (CPU, memory, request rates).
- Business metrics (process completion times, throughput).
- IoT sensor data.
- Financial transaction logs.

**Implementation:**

| Environment | Adapter | Description |
| :--- | :--- | :--- |
| **Development** | `InMemoryTimeSeriesStore` | Simulates time-series store in memory. |
| **Test** | `TimescaleDbClient` | TimescaleDB container with test data. |
| **Production** | `TimescaleDbClient` | TimescaleDB cluster (PostgreSQL extension) with automated partitioning. |

**Data Retention:**
- **Raw data:** 30 days.
- **Downsampled data (1-hour aggregates):** 1 year.
- **Downsampled data (daily aggregates):** 10 years.
- **Archival:** Data older than 10 years is moved to cold storage (S3 Glacier).

### 12.7 Object / File Storage

**Purpose:** Store unstructured blobs, large files, images, documents, backups, and artifacts.

**Primary Use Cases:**
- Artifact storage (generated documents, templates, uploads).
- Document images (scanned PDFs, images).
- Backup and archival.
- Build artifacts.

**Implementation:**

| Environment | Adapter | Description |
| :--- | :--- | :--- |
| **Development** | `LocalFileArtifactStorage` | File system storage in a local directory. |
| **Test / Staging** | `MinioArtifactStorage` | MinIO container (S3-compatible object store). |
| **Production** | `S3ArtifactStorage` | AWS S3 or MinIO cluster with cross-region replication. |

**Lifecycle Policies:**
- **Hot storage:** Frequently accessed artifacts (0-30 days). High-performance, lower latency.
- **Warm storage:** Infrequently accessed artifacts (30-90 days). Lower cost, slightly higher latency.
- **Cold storage:** Long-term archival (90+ days). S3 Glacier Deep Archive or similar.

### 12.8 Event Log / Stream Storage

**Purpose:** Append-only immutable log for event sourcing, stream processing, and audit trails.

**Primary Use Cases:**
- Event sourcing (reconstruct aggregates from events).
- Stream processing (Kafka Streams, Flink).
- Audit trails (immutable record of all state changes).
- Cross-module event propagation.

**Implementation:**

| Environment | Adapter | Description |
| :--- | :--- | :--- |
| **Development** | `InMemoryEventLog` | Simulates event log in memory. |
| **Test / Staging** | `KafkaEventLog` | Kafka container with test topics. |
| **Production** | `KafkaEventLog` | Kafka cluster with high availability, rack-aware replication, and exactly-once semantics. |

**Event Log Characteristics:**
- **Immutable:** Events are never modified or deleted.
- **Partitioned:** Events are partitioned by aggregate ID or key.
- **Ordered:** Events within a partition are strictly ordered.
- **Compacted:** Kafka log compaction retains the latest state for each key.
- **Retention:** Configurable retention policy (e.g., 7 days for operational topics, indefinite for audit topics).

### 12.9 Key-Value / Cache Store

**Purpose:** Low-latency access to transient or durable small-object state, session state, distributed cache, and distributed locks.

**Primary Use Cases:**
- Session state (HTTP sessions).
- Caching (cache-aside, read-through).
- Distributed locks.
- Leader election.
- Configuration storage.
- Temporary state (short-lived workflows).

**Implementation:**

| Environment | Adapter | Description |
| :--- | :--- | :--- |
| **Development** | `LocalMemoryCache` | In-memory cache (Microsoft.Extensions.Caching.Memory). |
| **Test / Staging** | `RedisCacheManager` | Redis container with cluster mode. |
| **Production** | `RedisCacheManager` | Redis cluster with sentinel or cluster mode, cross-region replication. |

---

## Chapter 13: Event Streaming with Kafka/Pulsar & Schema Registry

### 13.1 Event Streaming Architecture

The platform uses **Apache Kafka** as its primary event streaming backbone in production environments. Kafka provides:

- **Durability:** Events are persisted to disk and replicated across brokers.
- **Ordering:** Events within a partition are strictly ordered.
- **Scalability:** Kafka clusters can scale to handle millions of events per second.
- **Exactly-Once Semantics:** Kafka transactions and idempotent producers enable exactly-once processing.
- **Ecosystem:** Rich ecosystem of connectors (Kafka Connect), stream processors (Kafka Streams, ksqlDB, Flink), and Schema Registry.

**Alternative:** **Apache Pulsar** is supported as an alternative for workloads requiring geo-replication, multi-tenancy, and lower latency. The `IMessageBus` abstraction isolates the engine code from the specific event streaming implementation.

### 13.2 Topic Naming and Partitioning Strategy

**Naming Convention:** `{module}.{event_type}.{version}`

- Example: `ordering.order_confirmed.v1`, `inventory.stock_reserved.v1`, `billing.invoice_generated.v2`.

**Partitioning Strategy:**

- **Key-Based Partitioning:** Events for the same aggregate ID (e.g., `order_id`) are sent to the same partition. This ensures that events for a specific aggregate are processed in order.
- **Round-Robin (Default):** For events that do not require ordering, round-robin partitioning is used for even distribution.
- **Custom Partitioner:** For specific event types, a custom partitioner can be used (e.g., by tenant ID for multi-tenancy).

**Partition Count:**
- **Development:** 1 partition per topic (simplifies testing).
- **Production:** 10-100 partitions per topic, based on expected throughput and consumer parallelism.

### 13.3 Schema Registry Integration

The Schema Registry stores and manages the schemas for all events. It enforces compatibility checks when new versions are introduced.

**Schema Formats:**
- **Avro:** Preferred for its compact binary serialization, schema evolution support, and rich type system.
- **Protobuf:** Used for gRPC integration and where Protobuf is already used for APIs.
- **JSON Schema:** Used for simple events and external integrations.

**Compatibility Modes:**

| Mode | Description | When to Use |
| :--- | :--- | :--- |
| **Backward** | New schema can read old data (add fields with defaults). | Default, safe for most changes. |
| **Forward** | Old schema can read new data (ignore unknown fields). | When consumers are slower to upgrade. |
| **Full** | Both backward and forward compatible. | When both producers and consumers upgrade independently. |
| **Transitive** | Compatibility is checked across all previous versions, not just the immediate predecessor. | For strict governance. |

**Integration:**
- The `KafkaBus` adapter fetches the schema from the Schema Registry before serializing an event.
- The `KafkaBus` adapter caches schemas locally to reduce latency.
- If the schema is not found in the registry, the event is rejected with a `SchemaNotRegisteredException`.

### 13.4 Producer Configuration

**Idempotent Producers:** Enable `enable.idempotence=true` to ensure exactly-once delivery to a single partition.

**Transactions:** For workflows that require atomic writes to multiple topics, Kafka transactions are used.

**Message Headers:**
- `traceId`: Distributed tracing context.
- `eventType`: Fully qualified event type name.
- `eventVersion`: Schema version.
- `timestamp`: Event occurrence timestamp.
- `correlationId`: For request-response tracking.

**Error Handling:**
- **Transient errors (network timeouts, leader election):** Retry with exponential backoff.
- **Permanent errors (invalid schema, unreachable broker):** Fail fast and alert.

### 13.5 Consumer Configuration

**Consumer Group:** Each event handler defines a consumer group. The group name is derived from the module and the event handler (e.g., `inventory-stock-reserver`).

**Offset Management:**
- **At-Least-Once:** Default. Commits offset after processing.
- **Exactly-Once:** Achieved through idempotent consumers + transactional outbox.

**Error Handling:**
- **Transient errors:** Retry with exponential backoff.
- **Permanent errors (schema mismatch, processing logic failure):** Route to Dead-Letter Queue (DLQ).
- **Timeout:** If processing takes longer than the configured timeout, the consumer is considered failed, and the offset is not committed.

### 13.6 Stream Processing with Kafka Streams / Flink

For complex event processing and real-time analytics, the platform uses **Kafka Streams** and **Apache Flink**.

**Use Cases:**
- **Windowed Aggregations:** Calculate average process completion time over a sliding window.
- **Stateful Transformations:** Maintain state across events (e.g., count of active orders per tenant).
- **CEP (Complex Event Processing):** Detect patterns across multiple event types (e.g., "order placed" followed by "payment failed" within 5 minutes).
- **Materialized Views:** Maintain up-to-date views of state (e.g., current stock levels).

**Integration:**
- Kafka Streams applications run as separate pods in the Kubernetes cluster.
- State stores (RocksDB) are used for local state, replicated to Kafka for fault tolerance.
- The same `RuntimeTopology` configuration is used to switch between in-memory (Dev) and distributed (Prod) stream processors.

---

## Chapter 14: Change Data Capture (CDC), Outbox Relay, and Eventual Consistency

### 14.1 Change Data Capture (CDC) Overview

Change Data Capture (CDC) is the process of capturing changes made to a database and propagating them to downstream systems. The platform uses CDC for:

1. **Transactional Outbox Relay:** Capturing events from the Outbox table and publishing them to Kafka.
2. **Cache Invalidation:** Invalidating caches when data changes in the database.
3. **Materialized View Maintenance:** Updating read models and projections.
4. **Audit Trail:** Capturing all state changes for compliance and auditing.
5. **Data Synchronization:** Replicating data between modules or to external systems.

### 14.2 Debezium for CDC

**Debezium** is the primary CDC platform. It uses database transaction logs (binlog, WAL) to capture changes with minimal impact on the database.

**Supported Databases:**
- PostgreSQL (via logical decoding with pgoutput).
- SQL Server (via CDC tables).
- MongoDB (via change streams).
- MySQL (via binlog).

**Implementation:**

| Environment | Adapter | Description |
| :--- | :--- | :--- |
| **Development** | `NoOpCdc` | No CDC. Events are published directly. |
| **Test / Staging** | `DebeziumCdc` (polling mode) | Debezium polls the database log (simulated) for simplicity. |
| **Production** | `DebeziumCdc` (streaming mode) | Debezium streams changes via Kafka Connect. |

**Debezium Configuration:**

```json
{
  "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
  "database.hostname": "postgres-cluster",
  "database.port": "5432",
  "database.user": "debezium",
  "database.password": "${DB_PASSWORD}",
  "database.dbname": "platform",
  "database.server.name": "platform",
  "table.include.list": "public.outbox,public.process_instances,public.case_instances",
  "plugin.name": "pgoutput",
  "slot.name": "debezium_slot",
  "publication.name": "debezium_publication",
  "schema.include.list": "public",
  "key.converter": "org.apache.kafka.connect.json.JsonConverter",
  "value.converter": "org.apache.kafka.connect.json.JsonConverter",
  "value.converter.schemas.enable": "false"
}
```

### 14.3 Transactional Outbox Relay

The Outbox Relay reads the Outbox table and publishes events to Kafka. It uses the `IOutboxProcessor` port.

**Implementation:**

| Adapter | Method | Description |
| :--- | :--- | :--- |
| `NoOpOutboxProcessor` | Direct publish | Events are published directly without an Outbox table. Used in Development. |
| `OutboxProcessor` (polling) | Scheduled polling | Polls the Outbox table every N seconds and publishes events to Kafka. Used in Test/Staging. |
| `DebeziumOutboxRelay` | CDC streaming | Debezium captures Outbox table changes and streams them to Kafka. Used in Production. |

**Outbox Table Schema:**
(Referenced in Chapter 10, Section 10.3)

**Relay Process:**
1. Debezium captures an insert into the Outbox table.
2. The `DebeziumOutboxRelay` deserializes the Outbox record.
3. The event is published to Kafka with the appropriate headers (`traceId`, `eventType`, `eventVersion`).
4. The Outbox record is updated with `Published = true` and `PublishedOn = NOW()` (optional, for idempotency).

### 14.4 Eventual Consistency Guarantees

**The system guarantees eventual consistency across modules:**

- **Local ACID:** Each module's state is ACID consistent within its own database transaction.
- **Outbox:** Events are persisted atomically with the state change.
- **Relay:** Events are delivered to Kafka with at-least-once semantics.
- **Consumer:** Consumers are idempotent and process events exactly once.
- **Retry:** Failed events are retried with exponential backoff.
- **Dead-Letter Queue:** Events that fail permanently are routed to a DLQ for manual inspection.

**Ordering Guarantees:**
- Events for the same aggregate ID are sent to the same partition and processed in order.
- Events for different aggregates are processed concurrently (no ordering guarantee).

### 14.5 Cache Invalidation via CDC

When the database state changes, caches need to be invalidated to avoid stale reads.

**CDC-Based Invalidation Flow:**
1. A Use Case modifies an aggregate via `IUnitOfWork.CommitAsync()`.
2. The database commit triggers a CDC event (Debezium captures the change).
3. The CDC event is streamed to a Kafka topic (e.g., `platform.db_changes.process_instances`).
4. A cache invalidation consumer listens to the topic and invalidates the corresponding cache keys.
5. The cache invalidation consumer is idempotent (to handle duplicate CDC events).

**Cache Keys:**
- `process:{instanceId}` -> For process instance details.
- `case:{caseId}` -> For case instance details.
- `decision:{decisionId}` -> For decision outputs.
- `model:{context}:{modelKey}:{version}` -> For declarative models.

**Development Mode:**
- In Development, cache invalidation is performed synchronously after the database commit (no CDC required). This simplifies development but does not test the eventual consistency flow.

### 14.6 Materialized View Maintenance

Read models (materialized views) are maintained using CDC to keep them synchronized with the source of truth.

**Flow:**
1. CDC captures changes to the source aggregate (e.g., `ProcessInstance`).
2. A view updater consumer processes the CDC event.
3. The consumer updates the materialized view (denormalized table) in the read database.
4. The materialized view is used for queries (UI, reporting, API).

**Consistency:** The materialized view is eventually consistent with the source of truth (lag is typically sub-second).

---

## Chapter 15: Data Governance, Lineage, and Quality

### 15.1 Data Catalog and Metadata Management

The **Data Catalog** is a centralized repository of metadata about all data assets in the platform.

**Capabilities:**
- Discoverability: Search for tables, events, schemas, and artifacts.
- Business Glossary: Map technical metadata to business concepts.
- Data Profiling: Automatically profile data (null counts, distinct values, patterns).
- Data Lineage: Visualize the flow of data from source to consumption.
- Ownership: Identify the owner of each data asset.
- Access Control: Manage who can access which data assets.

**Implementation:**

| Environment | Adapter | Description |
| :--- | :--- | :--- |
| **Development** | `InMemoryDataCatalog` | Simulates data catalog in memory. |
| **Production** | `DataHubClient` | LinkedIn DataHub (open-source data catalog). |

**Integration:**
- **Automated Discovery:** DataHub crawls the PostgreSQL database, Kafka topics, and Schema Registry to automatically populate the catalog.
- **Lineage:** Data lineage is extracted from the orchestration pipeline (Airflow/Dagster) and CDC streams.

### 15.2 Data Lineage

Data lineage tracks the flow of data from source to consumption. It is essential for impact analysis, root-cause analysis, and compliance.

**Lineage Capture:**
- **ETL/ELT Pipelines:** Airflow/Dagster captures lineage at the task level.
- **Stream Processing:** Kafka Streams and Flink capture lineage at the operator level.
- **CDC:** Debezium captures lineage from database transactions.
- **Manual:** Model designers can manually annotate lineage for complex transformations.

**Visualization:** DataHub provides a graphical view of data lineage, showing how data flows from source tables to Kafka topics to materialized views.

### 15.3 Data Quality

Data quality is measured, monitored, and improved across all data assets.

**Quality Dimensions:**
- **Accuracy:** Data reflects the real-world entity.
- **Completeness:** All required fields are populated.
- **Timeliness:** Data is up-to-date.
- **Consistency:** Data is consistent across systems.
- **Validity:** Data conforms to defined constraints (format, range, business rules).

**Implementation:**

| Tool | Purpose | Description |
| :--- | :--- | :--- |
| **Great Expectations** | Data quality testing | Declarative expectations (e.g., "column X should not have nulls"). Integrated into CI/CD pipelines and scheduled jobs. |
| **dbt tests** | SQL-based quality checks | Custom SQL tests for data models. |
| **Soda** | Data quality monitoring | Continuous monitoring with alerts. |

**Quality Gates:**
- **CI/CD:** Models with failing quality tests are rejected.
- **Scheduled:** Regular quality scans (daily, weekly) with alerts for anomalies.
- **Real-time:** Stream processing jobs validate data in real-time.

### 15.4 Data Stewardship and Ownership

Each data asset has a designated owner responsible for its quality, security, and lifecycle.

**Roles:**
- **Data Owner:** Business owner of the data asset.
- **Data Steward:** Responsible for data quality, metadata, and governance.
- **Data Engineer:** Implements and maintains the data pipelines.

**Governance Workflow:**
1. Data asset is created and registered in the Data Catalog.
2. Owner is assigned.
3. Data quality expectations are defined.
4. Access policies are defined.
5. Data asset is reviewed periodically for quality and relevance.

### 15.5 Data Contracts

A data contract is a formal agreement between the producer and consumer of a data asset. It defines the schema, semantics, quality SLAs, and versioning policy.

**Elements of a Data Contract:**
- Schema (Avro, Protobuf, JSON Schema).
- Semantics (what each field means).
- Quality SLAs (accuracy, completeness, timeliness).
- Versioning policy (backward compatibility).
- Deprecation policy (notice period).
- Contact information (owner, steward).

**Implementation:**
- Contracts are stored as YAML files in the Model Repository.
- Schema Registry enforces contract compatibility.
- Pact testing verifies consumer-provider contracts.

---

## Chapter 16: Data Archival, Cold Storage, and Lifecycle Policies

### 16.1 Data Lifecycle Overview

Data in the platform follows a defined lifecycle:

1. **Creation:** Data is created (insert, event generated).
2. **Active:** Data is actively used for business operations (high access frequency).
3. **Warm:** Data is infrequently accessed but still needed (access frequency low).
4. **Cold:** Data is rarely accessed and retained for compliance or archival purposes.
5. **Deletion:** Data is permanently deleted (defensible deletion).

### 16.2 Lifecycle Tiers

| Tier | Storage Type | Access Frequency | Retention Period | Cost |
| :--- | :--- | :--- | :--- | :--- |
| **Hot** | SSD (Local or Cloud) | High (daily) | 0-30 days | High |
| **Warm** | Standard Object Storage (S3 Standard) | Medium (monthly) | 30-90 days | Medium |
| **Cold** | Object Storage (S3 Glacier) | Low (yearly) | 90 days - 10 years | Low |
| **Archive** | Tape / Off-Cloud (Glacier Deep Archive) | Very Low (on-demand) | 10+ years | Very Low |

### 16.3 Archival Policies

**Automated Archival:**
- **Age-based:** Data older than N days is automatically moved to the next tier.
- **Access-based:** Data that has not been accessed for N days is moved to cold storage.
- **Size-based:** Large datasets are archived earlier.

**Implementation:**
- **Object Storage:** S3 Lifecycle Policies automatically transition objects to colder tiers.
- **Database:** Custom archiving jobs (scheduled via Airflow) move old records to archive tables or export to object storage.
- **Event Log:** Kafka retention policies automatically delete old events or compact logs.

### 16.4 Data Retrieval from Cold Storage

**Retrieval Process:**
1. User requests data via the platform API.
2. A retrieval job is created in the archive system.
3. The data is rehydrated from cold storage to warm storage.
4. Notification is sent when data is ready.
5. Data is accessible for a defined period (e.g., 30 days) before moving back to cold storage.

**Retrieval Times:**
- **Expedited:** 1-5 minutes (higher cost).
- **Standard:** 3-5 hours.
- **Bulk:** 5-12 hours.

### 16.5 Defensible Deletion

When data is deleted, it must be done in a way that ensures it cannot be recovered (cryptographic shredding) and that the deletion is auditable.

**Process:**
1. Legal/compliance team approves the deletion.
2. The deletion process is initiated.
3. Data is cryptographically shredded (overwritten or encryption keys are destroyed).
4. A deletion certificate is generated and stored.
5. The deletion is logged in the audit trail.

**Implementation:**
- **Vault (Crypto Shredding):** The encryption key for the data is deleted. The encrypted data becomes unreadable.
- **S3 Versioning + Delete Markers:** For object storage, delete markers are used and versioning is disabled after a retention period.

### 16.6 Compliance and Legal Hold

**Legal Hold:** Data that is subject to legal discovery is placed on hold. It cannot be deleted or modified.

**Implementation:**
- **Object Storage:** S3 Object Lock with retention periods.
- **Database:** A `legal_hold` flag on tables, preventing deletion.
- **Audit:** All actions on held data are audited.

---

# PART 4: API MANAGEMENT & AGENTIC MESH

---

## Chapter 17: Northbound Exposure (API Gateway, Ingress, BFF)

### 17.1 Architecture Overview

The Northbound Exposure layer is responsible for securely exposing the platform's capabilities to external consumers (web applications, mobile applications, partner systems, and third-party integrations). It provides a unified entry point for all inbound traffic, handling authentication, authorization, rate limiting, request routing, and response transformation.

The architecture employs a layered approach:

1. **Edge Ingress:** TLS termination, DDoS protection, and basic routing at the network edge.
2. **API Gateway:** Advanced routing, rate limiting, authentication/authorization, request transformation, and API versioning.
3. **Backend-for-Frontend (BFF):** Aggregation layer that composes data from multiple downstream services into frontend-optimized responses.
4. **Service Mesh:** Internal routing, mTLS, and observability for east-west traffic.

### 17.2 Edge Ingress

**Purpose:** Provide the first line of defense and entry point for all external traffic.

**Capabilities:**
- TLS termination (SSL/TLS certificates managed via cert-manager).
- DDoS protection (cloud-native or third-party).
- IP whitelisting/blacklisting.
- Basic request filtering (malicious payload detection).
- Load balancing across multiple API Gateway instances.

**Implementation:**

| Environment | Adapter | Description |
| :--- | :--- | :--- |
| **Development** | `LocalIngress` | Direct access to API Gateway via localhost. |
| **Test / Staging** | `IngressNginx` | Kubernetes Ingress with ingress-nginx controller. |
| **Production** | `Cloudflare` + `IngressNginx` | Cloudflare for DDoS protection and WAF, with ingress-nginx for routing. |

**TLS Management:**
- **Development:** Self-signed certificates or mkcert.
- **Production:** Let's Encrypt via cert-manager, with automatic renewal.

### 17.3 API Gateway

**Purpose:** Manage the full API lifecycle, including routing, rate limiting, authentication, authorization, request transformation, and API versioning.

**Primary Responsibilities:**
- **Routing:** Route requests to the appropriate backend services (BFF, microservices, or external services) based on URL path, HTTP method, headers, or query parameters.
- **Rate Limiting:** Enforce rate limits per API key, tenant, or client IP to prevent abuse.
- **Authentication:** Validate OAuth2/OIDC tokens (JWT) and propagate identity to downstream services.
- **Authorization:** Enforce fine-grained access control (via OPA or custom policies) at the gateway level.
- **Request Transformation:** Modify request headers, body, or query parameters before forwarding to the backend.
- **Response Transformation:** Modify response headers, body, or status codes before returning to the client.
- **API Versioning:** Support multiple API versions simultaneously (URL path, header, or content-type based).
- **Caching:** Cache responses for GET requests to reduce backend load.
- **Observability:** Expose metrics (request rates, error rates, latency), logs, and traces.

**Implementation:**

| Environment | Gateway | Justification |
| :--- | :--- | :--- |
| **Development** | `YARP` (Yet Another Reverse Proxy) | Lightweight, high-performance, Microsoft-maintained. |
| **Production** | `YARP` with Consul integration | High-performance, flexible routing, integrates with service discovery. |

**Alternative Gateways:**
| Gateway | Use Case | Justification |
| :--- | :--- | :--- |
| **Kong** | Full API lifecycle management | Feature-rich, extensive plugin ecosystem, developer portal. |
| **Envoy** | High-performance edge proxy | Used in Istio, supports advanced traffic management. |
| **Traefik** | Kubernetes-native ingress | Simple configuration, integrates with Kubernetes services. |

**Gateway Configuration (YARP):**

```json
{
  "ReverseProxy": {
    "Routes": {
      "bff-route": {
        "ClusterId": "bff-cluster",
        "Match": {
          "Path": "/api/v1/{**catch-all}"
        }
      },
      "external-route": {
        "ClusterId": "external-cluster",
        "Match": {
          "Path": "/ext/{**catch-all}"
        }
      }
    },
    "Clusters": {
      "bff-cluster": {
        "Destinations": {
          "destination1": {
            "Address": "http://bff-service.default.svc.cluster.local:8080/"
          }
        }
      },
      "external-cluster": {
        "Destinations": {
          "destination1": {
            "Address": "https://external-api.example.com/"
          }
        }
      }
    }
  }
}
```

### 17.4 Backend-for-Frontend (BFF) Pattern

**Purpose:** Provide a per-client-type aggregation layer that composes data from multiple downstream services into frontend-optimized views.

**Rationale:**
- Frontends (web, mobile) often require data from multiple services.
- Aggregating on the client side leads to over-fetching and multiple network requests.
- The BFF aggregates data server-side, reducing client-side complexity and improving performance.

**Implementation:**

| Client Type | BFF Implementation | Description |
| :--- | :--- | :--- |
| **Web (React/SPA)** | `WebBFF` | Aggregates data for web clients, returns JSON responses. |
| **Mobile (React Native)** | `MobileBFF` | Optimized for mobile: smaller payloads, offline support, push notification registration. |
| **Partner API** | `PartnerBFF` | Dedicated BFF for partner integrations, with specific rate limits and data exposure policies. |

**BFF Architecture:**
- Each BFF is a separate service (or module) that consumes data from internal services via gRPC or REST.
- The BFF exposes a REST API (or GraphQL) for the frontend.
- The BFF handles authentication (extracting user identity from the JWT) and propagates it to downstream services.
- The BFF implements caching to reduce latency for frequently accessed data.

**Example: Web BFF Implementation:**

```csharp
[ApiController]
[Route("api/v1/web")]
public class WebBffController : ControllerBase
{
    private readonly IOrderQueryService _orderService;
    private readonly IInventoryQueryService _inventoryService;
    private readonly IUserProfileService _profileService;

    public async Task<IActionResult> GetOrderDashboard(string userId)
    {
        var orders = await _orderService.GetUserOrdersAsync(userId);
        var profile = await _profileService.GetUserProfileAsync(userId);
        var inventory = await _inventoryService.GetStockForItemsAsync(orders.SelectMany(o => o.Items));
        
        return Ok(new {
            orders = orders,
            profile = profile,
            inventory = inventory
        });
    }
}
```

### 17.5 GraphQL Gateway (Alternative)

For clients that require flexible query capabilities, a GraphQL gateway can be used.

**Capabilities:**
- **Federation:** Compose multiple GraphQL services into a single unified schema.
- **Query Optimization:** Execute only the necessary queries and avoid over-fetching.
- **Batching:** Batch multiple GraphQL queries into a single request.

**Implementation:**
- **Apollo Router:** High-performance GraphQL federation gateway.
- **Hot Chocolate (.NET):** Native .NET GraphQL implementation with federation support.
- **Hasura:** Realtime GraphQL over PostgreSQL, with fine-grained authorization.

### 17.6 Rate Limiting and Throttling

**Purpose:** Protect backend services from excessive request rates and ensure fair usage across tenants.

**Strategies:**
- **Token Bucket:** Fixed rate of requests per time window.
- **Sliding Window:** Track requests over a rolling time window.
- **Leaky Bucket:** Smooth out request bursts.

**Implementation:**
- **API Gateway:** Rate limiting at the gateway level (using built-in plugins or custom middleware).
- **Service Mesh:** Rate limiting at the sidecar level (Envoy rate limiting service).
- **Dedicated Service:** Global rate limiting service with a distributed cache (Redis) for stateful rate limiting.

**Configuration:**
- **Per API Key:** Limit requests per API key.
- **Per Tenant:** Limit requests per tenant ID.
- **Per IP:** Limit requests per client IP.
- **Global:** Limit total requests to the platform.

### 17.7 API Versioning and Deprecation

**Versioning Strategies:**
- **URL Path:** `/api/v1/orders`, `/api/v2/orders` (most explicit).
- **Header:** `API-Version: 1.0` (clean URLs).
- **Content-Type:** `Accept: application/vnd.company.v1+json` (RESTful).

**Deprecation Policy:**
- **Notice Period:** 6 months minimum for internal APIs, 12 months for external APIs.
- **Deprecation Headers:** `Deprecation: true`, `Sunset: Wed, 31 Dec 2025 23:59:59 GMT`.
- **Metrics:** Track usage of deprecated API versions. Alert when usage drops below a threshold.

**Migration Support:**
- **Changelog:** Maintain a changelog for each API version.
- **Migration Guide:** Provide a guide for consumers to migrate to the new version.
- **Graceful Degradation:** Support both old and new versions during the transition period.

---

## Chapter 18: Southbound Integration (Protocol Adaptation, Legacy Connectivity)

### 18.1 Architecture Overview

The Southbound Integration layer is responsible for consuming external services, legacy systems, third-party APIs, and file-based integrations. It provides a uniform abstraction for invoking any external capability, regardless of the underlying protocol or data format.

The architecture employs the **Adapter Pattern** combined with a **Canonical Data Model** to isolate the core platform from external systems.

### 18.2 Protocol Adaptation

**Supported Protocols:**
- **HTTP/REST:** JSON, XML, form-urlencoded.
- **gRPC:** Protobuf-based RPC.
- **SOAP:** XML-based web services (WSDL).
- **GraphQL:** Query and mutation over HTTP.
- **Database:** JDBC/ODBC, raw SQL.
- **File:** CSV, XML, JSON, fixed-width.
- **Messaging:** JMS, AMQP, MQTT, STOMP.
- **CLI:** Command-line execution (for legacy scripts).
- **SNMP:** Network device management.
- **WebSocket:** Real-time bidirectional communication.
- **FTP/SFTP:** File transfer.

**Implementation:**

| Protocol | Adapter Library | Description |
| :--- | :--- | :--- |
| **HTTP/REST** | `HttpClient` + `Polly` | Built-in .NET HttpClient with resilience policies. |
| **gRPC** | `Grpc.Net.Client` | High-performance gRPC client. |
| **SOAP** | `System.ServiceModel` | WCF client for SOAP web services. |
| **Database** | `Dapper` or `EF Core` | Lightweight or full ORM. |
| **File** | Custom parsers | CSV, XML, JSON, fixed-width file readers/writers. |
| **CLI** | `System.Diagnostics.Process` | Execute command-line tools. |
| **MQTT** | `MQTTnet` | MQTT client for IoT devices. |
| **WebSocket** | `System.Net.WebSockets` | WebSocket client. |

### 18.3 Canonical Data Model

**Purpose:** Ensure that the core platform does not become coupled to the specific data models of external systems.

**Implementation:**
- **Canonical Model:** A set of data structures (DTOs) defined in the Application layer that represent the internal representation of external data.
- **Transformation:** The infrastructure layer transforms between the external format and the canonical model.
- **Mapping:** Declarative mapping definitions (JSON mapping) stored in the Model Repository.

**Example:**
- **External:** SOAP XML (`<Customer><Name>John</Name></Customer>`)
- **Canonical:** `Customer` DTO (`{ Name = "John" }`)
- **Mapping:** XSLT or custom code.

### 18.4 Integration Framework

**Purpose:** Provide a structured approach to building integrations, including routing, transformation, error handling, and retry.

**Implementation:**

| Framework | Use Case | Justification |
| :--- | :--- | :--- |
| **Apache Camel** | Complex routing and mediation | Supports 300+ components, extensive DSL, proven in enterprise integration. |
| **Dapr Bindings** | Lightweight integration with external systems | Built-in bindings for common external systems (S3, Kafka, Redis). |
| **Custom Integration Service** | Simple or specific integrations | When the integration logic is simple and domain-specific. |

**Integration Pattern Examples:**
- **Content-Based Router:** Route messages based on content (e.g., route to different systems based on order type).
- **Message Enricher:** Enrich messages with additional data (e.g., add customer details to an order).
- **Splitter/Aggregator:** Split a large message into smaller messages and aggregate responses.
- **Dead-Letter Channel:** Route failed messages to a Dead-Letter Queue for manual inspection.

### 18.5 Change Data Capture (CDC) for Legacy Systems

**Purpose:** Integrate with legacy databases without modifying the legacy application.

**Implementation:**
- Debezium captures changes from the legacy database's transaction log.
- Changes are published to Kafka.
- The platform consumes the changes and updates its own state.

**Use Cases:**
- Migrating from a legacy system to the platform.
- Integrating with a third-party system that provides database-level access.

### 18.6 External API Consumption Resilience

**Resilience Patterns:**
- **Circuit Breaker:** Prevent cascading failures when an external API is unavailable.
- **Retry Policy:** Exponential backoff with jitter for transient failures.
- **Timeout:** Enforce strict timeouts to avoid hanging operations.
- **Bulkhead:** Limit concurrent outbound requests.
- **Fallback:** Provide default responses or cached data when the external API fails.

**Implementation:**
- **Polly:** .NET resilience library (circuit breaker, retry, bulkhead, timeout).
- **Service Mesh:** Istio/Envoy can handle retries, timeouts, and circuit breakers at the sidecar level.

### 18.7 Credential Management and Rotation

**Purpose:** Securely store and inject credentials for external systems without hardcoding them.

**Implementation:**
- **Vault:** Dynamic credentials (e.g., database credentials, API keys) are stored in Vault.
- **Vault Agent:** Credentials are injected as environment variables or mounted files at runtime.
- **Credential Rotation:** Vault auto-rotates credentials (e.g., database passwords) without restarting the application.
- **Secret Management:** Kubernetes Secrets are used for non-sensitive credentials in test/staging environments.

---

## Chapter 19: Agentic Systems (A2A, MCP, Multi-Agent Orchestration)

### 19.1 Architecture Overview

The platform treats AI agents as first-class citizens. Agents are autonomous entities that can execute tasks, make decisions, and interact with other agents and humans. The Agentic Systems layer provides the infrastructure for agent discovery, communication, tool invocation, and orchestration.

The architecture is built on three foundational protocols:
- **A2A (Agent-to-Agent):** Standardized protocol for agent discovery, messaging, and task handoff.
- **MCP (Model Context Protocol):** Standardized protocol for providing context, tools, and resources to agents.
- **Agent Registry:** Centralized registry for agent discovery and capability lookup.

### 19.2 Agent Abstraction

```csharp
public interface IAgent
{
    string AgentId { get; }
    string AgentType { get; }
    IReadOnlyList<AgentCapability> Capabilities { get; }
    
    Task<AgentResponse> ExecuteAsync(AgentRequest request, CancellationToken ct);
    Task<AgentResponse> DelegateAsync(AgentRequest request, IAgent targetAgent, CancellationToken ct);
    Task<AgentStatus> GetStatusAsync(CancellationToken ct);
}

public class AgentCapability
{
    public string Name { get; set; }
    public string Description { get; set; }
    public string InputSchema { get; set; } // JSON Schema
    public string OutputSchema { get; set; } // JSON Schema
}
```

### 19.3 Agent Registry

**Purpose:** Discoverable agent identities and capabilities.

**Capabilities:**
- **Registration:** Agents register their identity, capabilities, and endpoints with the registry.
- **Discovery:** Other agents or services query the registry for agents with specific capabilities.
- **Heartbeat:** Agents send heartbeats to indicate they are alive. Unresponsive agents are deregistered.
- **Metadata:** Agents can be tagged with metadata (e.g., version, environment, trust level).

**Implementation:**

| Environment | Adapter | Description |
| :--- | :--- | :--- |
| **Development** | `InMemoryAgentRegistry` | In-memory registry, used for development. |
| **Production** | `ConsulAgentRegistry` | Consul KV store as the agent registry. Agents register via the Consul API. |

**Agent Card (A2A Protocol):**

```json
{
  "agentId": "customer-support-agent-v1",
  "agentType": "CustomerSupport",
  "capabilities": [
    {
      "name": "resolve-issue",
      "description": "Resolves customer support issues",
      "inputSchema": {
        "type": "object",
        "properties": {
          "issueId": { "type": "string" },
          "description": { "type": "string" }
        }
      },
      "outputSchema": {
        "type": "object",
        "properties": {
          "resolution": { "type": "string" },
          "status": { "type": "string" }
        }
      }
    }
  ],
  "endpoint": "http://agent-service:8080",
  "trustLevel": "high"
}
```

### 19.4 Agent-to-Agent (A2A) Communication

**Purpose:** Enable agents to discover each other, exchange messages, negotiate tasks, and coordinate work.

**Communication Modes:**
- **Synchronous (gRPC/HTTP):** For request-response interactions between agents.
- **Asynchronous (Kafka):** For event-driven interactions (e.g., agent broadcasts a task).

**A2A Protocol Messages:**
- **TaskRequest:** An agent requests another agent to perform a task.
- **TaskStatus:** An agent reports the status of a task (in-progress, completed, failed).
- **Proposal:** An agent proposes a solution during negotiation.
- **Acceptance:** An agent accepts a proposal.
- **Delegation:** An agent delegates a sub-task to another agent.

**Implementation:**

| Environment | Adapter | Description |
| :--- | :--- | :--- |
| **Development** | `InMemoryAgentBus` | In-memory message bus for agent communication. |
| **Production** | `KafkaAgentBus` | Kafka as the transport for A2A messages. |

**Message Headers:**
- `agent-id`: Source agent ID.
- `target-agent-id`: Target agent ID.
- `correlation-id`: Correlation ID for tracking a conversation.
- `trace-id`: OpenTelemetry trace ID.

### 19.5 Model Context Protocol (MCP)

**Purpose:** Provide agents with structured context, tools, and resources at runtime.

**MCP Components:**
- **Resources:** Data or files (e.g., documents, images) that agents can access.
- **Tools:** Invokable functions (e.g., API calls, database queries) that agents can use.
- **Prompts:** Pre-defined prompts or instructions that guide agent behavior.

**MCP Client-Server:**
- **MCP Server:** Exposes resources, tools, and prompts to agents via a standardized API.
- **MCP Client:** The agent (or agent orchestrator) connects to the MCP server to discover and use tools/resources.

**Implementation:**
- **MCP Server:** Implemented as a separate service that exposes tools and resources via gRPC or HTTP.
- **Agent Integration:** The `IAgent` implementation includes an MCP client that connects to the MCP server at startup.

**Example MCP Tool Definition:**

```json
{
  "tool": {
    "name": "query-customer-data",
    "description": "Query customer data from the CRM",
    "parameters": {
      "type": "object",
      "properties": {
        "customerId": { "type": "string" }
      }
    }
  },
  "resource": {
    "uri": "customer://{customerId}",
    "description": "Customer profile data"
  }
}
```

### 19.6 Multi-Agent Orchestration

**Purpose:** Coordinate multiple agents to complete complex tasks that no single agent can accomplish alone.

**Orchestration Patterns:**
- **Manager-Worker:** A manager agent decomposes a task, assigns sub-tasks to worker agents, and aggregates the results.
- **Group Chat:** Agents collaborate by exchanging messages in a shared conversation (round-robin, broadcast).
- **Debate:** Agents critique each other's outputs, vote, and reach consensus.
- **Negotiation:** Agents negotiate resource allocation, prices, or task assignment using formal protocols (contract-net, auction).
- **Self-Refinement:** Agent improves its own output by receiving feedback from itself or another agent.

**Implementation:**
- **Orchestrator Agent:** A dedicated agent that manages the workflow of other agents.
- **Workflow Engine:** The BPMN Engine orchestrates agent interactions as a process flow (agent tasks are service tasks).

**Example: Manager-Worker Orchestration:**

```csharp
public class ManagerAgent : IAgent
{
    private readonly IAgentRegistry _registry;
    private readonly IMessageBus _bus;

    public async Task<AgentResponse> ExecuteAsync(AgentRequest request)
    {
        // Decompose task
        var tasks = DecomposeTask(request.Payload);
        
        // Discover workers
        var workers = await _registry.GetAgentsByCapabilityAsync("worker", request.Context);
        
        // Assign sub-tasks
        foreach (var task in tasks)
        {
            var worker = SelectWorker(workers, task);
            var taskRequest = new AgentRequest(task, request.Context);
            await _bus.PublishAsync(new TaskAssignmentEvent(worker.AgentId, taskRequest));
        }
        
        // Collect and aggregate results
        // ...
    }
}
```

### 19.7 Agent Identity and Security

**Purpose:** Ensure that agents are authenticated, authorized, and cannot impersonate humans or other agents.

**Authentication:**
- **SPIFFE/SPIRE:** Each agent has a SPIFFE-compliant workload identity.
- **JWT:** Agents present a JWT token (signed by the SPIFFE workload identity) for API calls.

**Authorization:**
- **OPA:** Policy-as-Code defines which agents can access which tools and resources.
- **Scopes:** Each agent has a set of scopes (e.g., `read:customer-data`, `write:orders`).

**Agent-to-Human Impersonation Prevention:**
- **Strict Labelling:** Agents must identify themselves in all communications (`agent-id` header, visual badge in UI).
- **Dedicated Channels:** Separate protocol for human-to-agent interaction.
- **Audit Trail:** All agent actions are logged immutably for compliance.

---

## Chapter 20: Skills Engine & Plugin Management

### 20.1 Architecture Overview

The Skills Engine provides a pluggable, discoverable set of agent capabilities (skills) that are packaged as reusable units. Skills encapsulate prompts, tools, and memory into a versioned, distributable package.

### 20.2 Skill Definition

**Skill Manifest:**

```json
{
  "skillId": "customer-support-skill-v1",
  "name": "Customer Support",
  "version": "1.0.0",
  "intent": "Resolve customer support issues",
  "parameters": {
    "customerId": { "type": "string" },
    "issue": { "type": "string" }
  },
  "promptTemplate": "You are a customer support agent. Help the customer with: {issue}",
  "requiredTools": [
    { "toolId": "query-customer-data", "version": "1.0.0" },
    { "toolId": "create-support-ticket", "version": "1.2.0" }
  ],
  "memory": {
    "type": "conversation",
    "ttl": 3600
  }
}
```

### 20.3 Skill Registry

**Purpose:** Centralized registry for discovering and binding skills.

**Capabilities:**
- **Skill Onboarding:** Model designers upload skill manifests to the registry.
- **Skill Discovery:** Agents query the registry based on intent or capabilities.
- **Skill Versioning:** Skills are versioned (semantic versioning). Agents can request specific versions.
- **Skill Recommendation:** The registry recommends skills based on task context.

**Implementation:**

| Environment | Adapter | Description |
| :--- | :--- | :--- |
| **Development** | `FileSystemSkillRegistry` | Skills are loaded from a local directory. |
| **Production** | `GitLabSkillRegistry` | Skills are stored in the Model Repository (GitLab) with versioning. |

### 20.4 Skill Composition and Chaining

**Purpose:** Combine multiple skills into a larger plan or workflow.

**Patterns:**
- **Plan-and-Execute:** The agent uses a planner to select and order skills based on the task.
- **Skill Chaining:** The output of one skill is used as input to another.
- **Parallel Execution:** Multiple skills are executed in parallel for performance.

**Implementation:**
- **LangGraph:** The agent uses LangGraph to define a graph of skill nodes.
- **Semantic Kernel Planner:** The agent uses Semantic Kernel's planner to chain skills.
- **Workflow Engine:** The BPMN Engine orchestrates skills as service tasks in a BPMN process.

### 20.5 Skill Lifecycle Management

**Stages:**
1. **Development:** Skill is authored and tested locally.
2. **Validation:** Skill manifest is validated (JSON Schema, dependency checking).
3. **Staged:** Skill is promoted to staging for integration testing.
4. **Released:** Skill is promoted to production (immutable).
5. **Deprecated:** Skill is no longer recommended for new tasks.
6. **Archived:** Skill is retired.

**CI/CD for Skills:**
- **GitOps:** Skill manifests are stored in Git. Pull requests trigger validation and automated testing.
- **Canary Release:** New skill versions are rolled out to a subset of agents before full release.

---

## Chapter 21: UI Backend & Frontend Development Platform

### 21.1 Architecture Overview

The UI Backend and Frontend Development Platform provides the infrastructure for building, serving, and maintaining web and mobile applications that interact with the platform. It includes:

- **Static Asset Serving:** CDN distribution of frontend assets (HTML, CSS, JS).
- **Server-Side Rendering (SSR):** Pre-rendered HTML for SEO and fast first paint.
- **Backend-for-Frontend (BFF):** Aggregation layer for frontend-specific data.
- **Design System:** Shared component library and design tokens.
- **Form Schema Tools:** Dynamic form rendering from JSON schemas.
- **Monorepo:** Code sharing across web and mobile (React/React Native).

### 21.2 Static Asset Serving & CDN Distribution

**Purpose:** Serve immutable static resources with minimal latency and global edge caching.

**Implementation:**
- **Build Process:** Frontend builds produce content-hashed filenames (e.g., `main.a1b2c3.js`).
- **CDN:** Assets are pushed to S3/CloudFront (or similar) with long TTLs (1 year) for caching.
- **Fallback:** The application serves static assets from the local server if the CDN is unavailable.

**Tools:**
- **AWS S3 + CloudFront:** Standard solution for static asset hosting.
- **Cloudflare Pages:** Modern alternative with built-in CDN and edge functions.
- **Vercel / Netlify:** Frontend hosting platforms with automatic CDN and preview environments.

### 21.3 Server-Side Rendering (SSR)

**Purpose:** Deliver pre-rendered HTML for SEO and fast first paint, then hydrate to a full SPA.

**Implementation:**
- **Next.js:** The primary framework for React SSR.
- **Remix:** Alternative framework with nested routing and progressive enhancement.
- **Hydration:** The client-side JavaScript takes over the server-rendered HTML.

**Data Fetching:**
- **Server-Side Data Fetching:** Data is fetched on the server before rendering.
- **Static Site Generation (SSG):** Pages are pre-rendered at build time.
- **Incremental Static Regeneration (ISR):** Pages are re-rendered periodically.

### 21.4 Form & UI Schema Tools

**Purpose:** Build complex, dynamic forms driven by JSON schemas, common in enterprise and agent-configuration UIs.

**Implementation:**
- **JSON Schema:** Forms are defined as JSON Schema (or similar).
- **Form Renderer:** A React component that renders a form from a JSON schema.
- **Validation:** Client-side and server-side validation.

**Tools:**
- **Alibaba Formily:** High-performance, schema-driven form library for React.
- **Formik + Yup:** Traditional React form library with schema-based validation.
- **react-json-schema-form:** Simple JSON schema to form renderer.
- **Retool / Appsmith:** Low-code platforms for building internal tools and admin UIs.

### 21.5 Design System & Component Collaboration

**Purpose:** Maintain consistency between design (Figma) and code, share UI components across web and mobile.

**Implementation:**
- **Design Tokens:** Tokens (colors, typography, spacing) are defined in Figma and exported to JSON via Tokens Studio.
- **Style Dictionary:** Tokens are transformed to CSS variables, SCSS, or platform-specific formats.
- **Component Library:** Shared components (React, React Native) in a monorepo.

**Tools:**
- **Figma + Tokens Studio:** Define and export design tokens.
- **Style Dictionary:** Build system for design tokens.
- **Storybook:** Component development and documentation environment.
- **Bit:** Component management and publishing.

### 21.6 Monorepo & Code Sharing (Web + Mobile)

**Purpose:** Manage multiple frontend packages (React web, React Native, shared) in a single repository with efficient builds.

**Implementation:**
- **Monorepo Tooling:** Nx or Turborepo for dependency graph, caching, and incremental builds.
- **Shared Package:** A shared component library and utilities package.
- **Workspace:** Separate applications for web and mobile (React Native) within the monorepo.

**Tools:**
- **Nx:** Comprehensive monorepo tool with built-in caching and dependency graph.
- **Turborepo:** High-performance monorepo build system.
- **Lerna + Yarn Workspaces:** Traditional monorepo setup.

### 21.7 Real-Time Communication to UI

**Purpose:** Push server-side events (agent progress, notifications) to the frontend without polling.

**Implementation:**
- **WebSocket:** Persistent bidirectional connection for real-time events.
- **Server-Sent Events (SSE):** Server-to-client event streaming.
- **GraphQL Subscriptions:** Subscriptions over WebSocket.

**Tools:**
- **SignalR (.NET):** Real-time web functionality for ASP.NET Core applications.
- **Socket.IO:** Cross-platform real-time library.
- **NATS WebSocket Gateway:** Message bus to WebSocket gateway for distributed real-time.

---

# PART 5: SECURITY, IDENTITY, AND COMPLIANCE

---

## Chapter 22: Zero-Trust Architecture (SPIFFE/SPIRE, mTLS)

### 22.1 Zero-Trust Principles

The platform implements a comprehensive zero-trust security model across all layers. The zero-trust model operates on the following immutable principles:

- **Never Trust, Always Verify:** Every request, regardless of origin, is authenticated and authorized.
- **Least Privilege:** Services and agents are granted only the minimum permissions required to perform their function.
- **Assume Breach:** The architecture assumes that an attacker has already gained access to the network and is actively trying to move laterally.
- **Micro-Segmentation:** Network policies enforce fine-grained segmentation at the pod, namespace, and service level.
- **Continuous Monitoring:** All actions are logged, audited, and monitored for anomalous behavior.

### 22.2 Workload Identity (SPIFFE/SPIRE)

**Purpose:** Provide a verifiable identity for every workload (service, agent, batch job) running in the platform.

**SPIFFE (Secure Production Identity Framework for Everyone):** An open standard for workload identity. SPIFFE IDs are of the form `spiffe://trust-domain/workload-identifier`.

**SPIRE (SPIFFE Runtime Environment):** The reference implementation of SPIFFE. SPIRE automatically issues short-lived X.509 certificates (or JWT tokens) to workloads based on their identity.

**Implementation:**

| Environment | Adapter | Description |
| :--- | :--- | :--- |
| **Development** | `PassthroughIdentityProvider` | Bypasses SPIFFE. Workloads use a fixed identity (e.g., `agent-dev`). |
| **Test / Staging** | `SpiffeIdentityProvider` (with local SPIRE) | SPIRE agent runs in the Kubernetes cluster, issuing certificates. |
| **Production** | `SpiffeIdentityProvider` | SPIRE with production configuration, certificate rotation, and audit logging. |

**Identity Workflow:**
1. **Workload Registration:** The workload (service pod, agent pod) is registered with SPIRE via a registration entry (e.g., Kubernetes service account -> SPIFFE ID).
2. **Certificate Issuance:** The SPIRE agent (sidecar or daemonset) issues a short-lived X.509 certificate (valid for 24 hours) to the workload.
3. **Certificate Rotation:** The SPIRE agent automatically rotates the certificate before it expires.
4. **Identity Propagation:** The SPIFFE ID is propagated to downstream services via mTLS (client certificate) or via JWT tokens in headers.

**SPIFFE ID Naming Convention:**
```
spiffe://platform.internal/ns/{namespace}/sa/{service-account}/{workload-type}
```
Example: `spiffe://platform.internal/ns/default/sa/bpmn-engine/bpmn-worker`

### 22.3 Mutual TLS (mTLS)

**Purpose:** Secure and authenticate service-to-service communication.

**Implementation:**
- **Service Mesh (Istio/Linkerd):** mTLS is enabled at the service mesh level. The sidecar proxy (Envoy/Linkerd-proxy) terminates and originates mTLS connections automatically.
- **Application Level:** For workloads that do not use a service mesh, the application code uses the SPIFFE certificate directly to establish mTLS connections via `HttpClient` or gRPC.

**mTLS Characteristics:**
- **Server Authentication:** The client verifies the server's certificate using the SPIFFE trust bundle.
- **Client Authentication:** The server verifies the client's certificate (SPIFFE ID) and enforces authorization policies.
- **Certificate Rotation:** Certificates are rotated automatically by SPIRE before expiry.
- **Mutual Authentication:** Both sides authenticate each other.

**Configuration:**
```yaml
# Istio PeerAuthentication
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: default
spec:
  mtls:
    mode: STRICT
```

### 22.4 Zero-Trust Network Policies

**Purpose:** Enforce micro-segmentation and default-deny network policies at the Kubernetes layer.

**Implementation:**
- **Kubernetes Network Policies:** Default-deny ingress and egress policies. Only explicitly allowed traffic is permitted.
- **CNI (Container Network Interface):** Cilium (eBPF-based) or Calico for advanced network policy enforcement.

**Network Policy Examples:**
- **Default-Deny:** All traffic is blocked unless explicitly allowed.
- **Allow Ingress to BPMN Engine:** Allow traffic from API Gateway to BPMN Engine on port 8080.
- **Allow Egress to PostgreSQL:** Allow traffic from BPMN Engine to PostgreSQL on port 5432.
- **Allow Istio Sidecar:** Allow traffic to/from the Istio sidecar (Envoy) on port 15001.

**Cilium Layer 7 Policies:** Cilium supports layer 7 policies (HTTP, gRPC, Kafka), enabling fine-grained authorization based on request metadata (path, method, topic).

### 22.5 Trust Bundles and CA Rotation

**Trust Bundle:** The collection of certificates that workloads trust for authentication. This includes the SPIFFE CA certificate and external CA certificates.

**CA Rotation:** The platform supports automatic rotation of the SPIFFE CA certificate without disrupting workloads. Workloads periodically fetch the updated trust bundle from SPIRE.

**Implementation:**
- **Trust Bundle Distribution:** The trust bundle is distributed via Kubernetes ConfigMaps or via the SPIRE endpoint.
- **Bundle Rotation:** SPIRE rotates the CA certificate and updates the trust bundle. Workloads (via the sidecar proxy) automatically pick up the new bundle.

---

## Chapter 23: Authentication & Authorization (OAuth2, OIDC, OPA/Casbin)

### 23.1 Authentication Architecture

The platform supports two types of authentication:

1. **End-User Authentication:** Human users (via web, mobile, or API) authenticate using OAuth2/OIDC.
2. **Workload Authentication:** Services and agents authenticate using SPIFFE/mTLS.

### 23.2 End-User Authentication (OAuth2/OIDC)

**Purpose:** Provide a single identity for users across all applications, with federation to external IdPs.

**Flow:**
1. The user authenticates with the Identity Provider (IdP) using OAuth2 Authorization Code flow (with PKCE for mobile/SPA).
2. The IdP returns an ID token (JWT) and access token (JWT).
3. The access token is sent to the API Gateway or BFF in the `Authorization: Bearer` header.
4. The API Gateway validates the JWT (signature, audience, expiry).
5. The user identity is extracted from the JWT and propagated to downstream services via headers (e.g., `X-User-Id`, `X-User-Roles`).

**Identity Providers (IdP):**

| IdP | Use Case | Justification |
| :--- | :--- | :--- |
| **Keycloak** | Internal enterprise SSO | Open-source, fully featured, supports OIDC, SAML, and LDAP federation. |
| **Azure AD** | Enterprise integration | Managed OIDC provider with enterprise features. |
| **Auth0** | External-facing APIs | Cloud-native, developer-friendly, extensive tenant management. |
| **Okta** | Enterprise SSO | Mature platform with extensive integrations. |
| **Ory Hydra/Kratos** | Self-hosted OIDC | Open-source, OIDC-certified, zero-trust principles. |

**Implementation:**

| Environment | Adapter | Description |
| :--- | :--- | :--- |
| **Development** | `PassthroughIdentityProvider` | No authentication required. A fixed test user is assumed. |
| **Test** | `KeycloakJwtValidator` | Local Keycloak container for integration testing. |
| **Production** | `KeycloakJwtValidator` | Production Keycloak cluster with high availability and LDAP federation. |

**JWT Validation:**
- **Signature:** Validates that the JWT is signed by the IdP (using public keys fetched from the well-known endpoint).
- **Audience:** Validates that the JWT is intended for the platform (`aud` claim).
- **Issuer:** Validates the `iss` claim matches the IdP URL.
- **Expiry:** Validates the `exp` claim.
- **Scopes:** Validates that the JWT includes the required scopes (e.g., `api:read`, `api:write`).

### 23.3 Authorization (RBAC, ABAC, ReBAC)

**Purpose:** Enforce fine-grained access control consistently across all layers.

**Authorization Models:**
- **RBAC (Role-Based Access Control):** Users are assigned roles. Roles have permissions.
- **ABAC (Attribute-Based Access Control):** Access is based on attributes (user attributes, resource attributes, environment attributes).
- **ReBAC (Relationship-Based Access Control):** Access is based on relationships (e.g., "user is owner of resource").

**Implementation:**

| Model | Tool | Justification |
| :--- | :--- | :--- |
| **RBAC/ABAC** | **OPA (Open Policy Agent)** | Policy-as-Code, declarative policies (Rego), high-performance, integrates with Istio and API Gateway. |
| **ReBAC** | **Casbin** | Flexible access control library with built-in RBAC, ABAC, and ReBAC support. |
| **ReBAC** | **Okta FGA** | Cloud-native relationship-based access control. |
| **ABAC** | **AWS Verified Permissions (Cedar)** | Managed policy service with fine-grained access control. |

**OPA Policy Example (Rego):**
```rego
package platform.authz

default allow = false

allow {
    input.method == "GET"
    input.path = ["api", "v1", "orders", order_id]
    input.user.roles[_] == "admin"
}

allow {
    input.method == "POST"
    input.path = ["api", "v1", "orders"]
    input.user.roles[_] == "order_manager"
}

allow {
    input.method == "GET"
    input.path = ["api", "v1", "orders", order_id]
    user_is_order_owner(input.user.id, order_id)
}

user_is_order_owner(user_id, order_id) {
    order := data.orders[order_id]
    order.customer_id == user_id
}
```

**OPA Integration:**
- **API Gateway:** The API Gateway calls OPA for every request (via the OPA REST API) to evaluate the policy.
- **Service Mesh (Istio):** Istio AuthorizationPolicy uses OPA (via Envoy external authorization filter) to enforce policies at the sidecar level.
- **Kubernetes:** OPA Gatekeeper enforces policies on Kubernetes resources (e.g., deny privileged containers, require specific labels).

### 23.4 Fine-Grained Authorization at the Data Layer

**Purpose:** Enforce row-level security (RLS) in the database.

**Implementation:**
- **PostgreSQL Row-Level Security (RLS):** Define RLS policies that restrict access to rows based on user identity.
- **Application-Level Filtering:** The repository layer filters data based on user identity (propagated from the JWT or SPIFFE ID).

**PostgreSQL RLS Example:**
```sql
-- Enable RLS
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own orders
CREATE POLICY user_orders ON orders
    USING (customer_id = current_setting('app.current_user_id')::uuid);
```

### 23.5 Identity Propagation

**Purpose:** Propagate the user identity (JWT claims) to downstream services.

**Mechanism:**
- **Headers:** The API Gateway or BFF forwards the JWT (or extracted claims) in request headers.
- **gRPC Metadata:** The gRPC client propagates the identity via gRPC metadata.
- **Kafka Headers:** The producer includes the user identity in Kafka message headers (for audit logging).

**Security:** The identity propagation mechanism is protected by mTLS (service-to-service authentication). The receiving service validates that the identity is trusted (via SPIFFE ID).

---

## Chapter 24: Secrets Management & Hardware Security Modules (HSM)

### 24.1 Secrets Management Overview

**Purpose:** Securely store, manage, and rotate secrets (passwords, API keys, certificates, database credentials) without hardcoding them in the application or environment variables.

**Principles:**
- **No Long-Lived Static Secrets:** All secrets are dynamic and short-lived.
- **Just-in-Time (JIT) Credentials:** Secrets are injected at runtime, not stored in the application.
- **Auditability:** All secret access is logged.
- **Automated Rotation:** Secrets are rotated automatically without application restart.

### 24.2 Secrets Management Implementation

**Tool:** **HashiCorp Vault** is the primary secrets management solution.

| Environment | Adapter | Description |
| :--- | :--- | :--- |
| **Development** | `.NET UserSecrets` | Local secrets for development (never committed). |
| **Test / Staging** | `VaultClient` (dev mode) | Vault container in development mode (unsealed, memory storage). |
| **Production** | `VaultClient` | Production Vault cluster with HSM backend, auto-unseal, and disaster recovery. |

**Secret Types:**

| Secret Type | Source | Rotation Strategy |
| :--- | :--- | :--- |
| **Database Credentials** | Vault Dynamic Database Secrets | Vault generates temporary database credentials with TTL (1 hour). |
| **API Keys (External)** | Vault K/V Store | Keys are stored encrypted. Rotated manually with Vault versioning. |
| **JWT Signing Keys** | Vault Transit Engine | Keys are stored in Vault. Applications use Vault's signing API. |
| **TLS Certificates** | Vault PKI Engine | Vault issues short-lived TLS certificates (24 hours) via the PKI engine. |
| **SPIFFE Certificates** | SPIRE (uses Vault as CA) | SPIRE issues workload certificates; Vault acts as the root CA. |

### 24.3 Vault Integration

**Secret Injection:**
- **Vault Agent Injector:** A sidecar container that authenticates to Vault (via Kubernetes service account) and injects secrets as environment variables or mounted files.
- **CSI Driver:** Kubernetes CSI driver (Secrets Store CSI) mounts secrets from Vault as volumes.

**Example: Vault Agent Injection:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bpmn-engine
spec:
  template:
    metadata:
      annotations:
        vault.hashicorp.com/agent-inject: "true"
        vault.hashicorp.com/role: "bpmn-engine"
        vault.hashicorp.com/agent-inject-secret-db-creds: "database/creds/bpmn-engine"
        vault.hashicorp.com/agent-inject-template-db-creds: |
          {{- with secret "database/creds/bpmn-engine" -}}
          DB_USERNAME={{ .Data.username }}
          DB_PASSWORD={{ .Data.password }}
          {{- end }}
```

**Vault Authentication:**
- **Kubernetes Auth:** Vault authenticates the workload using the Kubernetes service account token.
- **JWT/OIDC:** For non-Kubernetes workloads, Vault supports JWT/OIDC authentication.
- **SPIFFE/SPIRE:** Vault can authenticate using SPIFFE IDs (via the Vault SPIFFE auth method).

### 24.4 Hardware Security Modules (HSM)

**Purpose:** Provide FIPS 140-2 Level 3 certified hardware for cryptographic key generation and storage.

**HSM Use Cases:**
- **Root CA for SPIFFE/SPIRE:** The root CA private key is stored in the HSM.
- **JWT Signing:** The signing key for JWT tokens is stored in the HSM.
- **Encryption at Rest:** Data encryption keys are generated and stored in the HSM.
- **PCI-DSS Compliance:** HSM is required for payment card data.

**Implementation:**

| HSM Provider | Justification |
| :--- | :--- |
| **AWS CloudHSM** | Cloud-native, FIPS 140-2 Level 3, integrates with AWS KMS. |
| **Azure Dedicated HSM** | Azure-native, FIPS 140-2 Level 3, integrates with Azure Key Vault. |
| **GCP Cloud HSM** | Google-native, FIPS 140-2 Level 3, integrates with Google Cloud KMS. |
| **Thales / Utimaco** | On-premises HSM for air-gapped or highly sensitive environments. |

**HSM Integration with Vault:**
- Vault uses the HSM as the seal (root key) and as the PKI engine backend.
- Vault's PKI engine uses the HSM to sign certificates, ensuring the private key never leaves the HSM.

### 24.5 Secrets Rotation

**Dynamic Database Credentials:**
- Vault's database secrets engine generates credentials with a TTL (e.g., 1 hour).
- The application fetches new credentials from Vault before the current credentials expire.
- The connection pool uses the new credentials for new connections, while existing connections are drained gracefully.

**Certificate Rotation:**
- SPIRE auto-rotates workload certificates every 24 hours.
- Vault PKI engine auto-rotates TLS certificates for public-facing endpoints.
- The `cert-manager` controller in Kubernetes handles certificate renewal for ingress endpoints.

**Manual Secret Rotation:**
- Vault K/V Store supports versioning. A new version of a secret is created, and applications are updated to read the latest version.
- Rolling updates ensure that no application downtime occurs during rotation.

### 24.6 Audit and Compliance for Secrets

**Vault Audit Logs:**
- Vault logs every secret access, including the requesting identity, the path, and the timestamp.
- Audit logs are sent to a SIEM (Security Information and Event Management) system for analysis.

**Compliance:**
- **PCI-DSS:** HSM usage, audit logging, and periodic key rotation ensure compliance.
- **SOC2:** Controlled access to secrets, audit logging, and automated rotation.
- **ISO 27001:** Secrets management policies and procedures.

---

## Chapter 25: Compliance Automation, Audit Trails, and Policy-as-Code

### 25.1 Compliance Automation Overview

**Purpose:** Continuously enforce compliance with regulatory frameworks (SOC2, ISO 27001, HIPAA, PCI-DSS, GDPR, CCPA) through automated policies, evidence collection, and reporting.

### 25.2 Policy-as-Code

**Purpose:** Codify and automatically enforce compliance rules across the entire platform.

**Policy Domains:**
- **Infrastructure:** Encryption at rest, resource tagging, network policies.
- **Security:** Privileged containers, service account permissions, image vulnerability scanning.
- **Data:** Data classification, access control, retention policies.
- **Application:** Authentication, authorization, audit logging.

**Implementation:**

| Tool | Purpose | Justification |
| :--- | :--- | :--- |
| **OPA/Gatekeeper** | Kubernetes admission control | Enforce policies on Kubernetes resources (deployments, service accounts, network policies). |
| **Kyverno** | Kubernetes policy engine | Native Kubernetes policies with validation, mutation, and generation. |
| **Checkov** | IaC scanning | Static analysis of Terraform, CloudFormation, and Kubernetes manifests. |
| **tfsec** | Terraform security scanning | Security checks on Terraform code. |
| **AWS Config** | Cloud resource compliance | Continuous monitoring of AWS resources against compliance rules. |
| **Azure Policy** | Azure resource compliance | Continuous monitoring of Azure resources against compliance rules. |

**Example: Gatekeeper Policy (Disallow Privileged Containers):**
```rego
package kubernetes.admission

deny[msg] {
    input.review.object.spec.containers[_].securityContext.privileged == true
    msg := "Privileged containers are not allowed"
}
```

### 25.3 Audit Trails

**Purpose:** Provide an immutable, tamper-proof log of all actions for forensic analysis, compliance, and incident investigation.

**Audit Data Sources:**

| Source | Data Captured | Retention |
| :--- | :--- | :--- |
| **Application Logs** | Use Case execution, engine decisions, task assignments, agent actions. | 90 days (hot), 7 years (cold). |
| **Infrastructure Logs** | Kubernetes API events, pod lifecycle, network policy changes. | 30 days (hot), 1 year (cold). |
| **Database Audit Logs** | All SQL queries (SELECT, INSERT, UPDATE, DELETE) for sensitive tables. | 30 days (hot), 7 years (cold). |
| **Vault Audit Logs** | Secret access, credential generation, policy changes. | 30 days (hot), 7 years (cold). |
| **Kafka Audit Logs** | Event publishing and consumption. | 30 days (hot), 1 year (cold). |

**Audit Log Characteristics:**
- **Immutable:** Append-only. Deletion is not permitted.
- **Tamper-Proof:** Logs are cryptographically hashed and verified periodically.
- **Searchable:** Indexed by user identity, timestamp, and action.
- **Compliance-Ready:** Supports export to compliance systems.

**Implementation:**

| Component | Tool | Justification |
| :--- | :--- | :--- |
| **Log Storage** | Elasticsearch / OpenSearch | Centralized log storage, searchable, and scalable. |
| **Log Shipping** | Fluentd / Filebeat | Collects logs from all pods and ships to Elasticsearch. |
| **Cryptographic Chaining** | Custom implementation | Hash chain for tamper-proof verification. |
| **SIEM Integration** | Splunk / Microsoft Sentinel | For security analysis and alerting. |

### 25.4 Compliance Automation Frameworks

**Purpose:** Generate evidence packages for compliance frameworks (SOC2, ISO 27001, HIPAA) continuously.

**Implementation:**

| Framework | Tool | Justification |
| :--- | :--- | :--- |
| **SOC2 / ISO 27001** | **Vanta / Drata / Secureframe** | Automated evidence collection, control mapping, and reporting. |
| **HIPAA** | **Vanta / Azure Policy** | Automated controls for data encryption, access control, and audit logging. |
| **PCI-DSS** | **AWS Config / Azure Policy** | Automated controls for network security, encryption, and logging. |
| **GDPR / CCPA** | **Custom + Azure DLP** | Data classification, consent management, data subject access requests. |

**Evidence Collection:**
- **Infrastructure:** Automated scans of Kubernetes, AWS, or Azure resources.
- **Security:** Vulnerability scans (Trivy, Grype), penetration test reports.
- **Process:** Documented policies and procedures (stored in the Model Repository).
- **Audit Logs:** Continuous export of audit logs to the compliance platform.

### 25.5 Data Retention and Deletion Policies

**Purpose:** Ensure compliance with data retention and deletion regulations (GDPR, CCPA).

**Implementation:**
- **Retention Policies:** Data is retained for a defined period (e.g., 7 years for financial records). After the retention period, data is automatically deleted.
- **Data Subject Access Rights (DSAR):** Users can request a copy of their data or request deletion. Automated workflows handle DSAR requests.
- **Legal Hold:** Data that is subject to legal discovery is placed on hold. It cannot be deleted or modified.

**Tools:**
- **OneTrust / Transcend:** Consent management and DSAR automation.
- **Custom Workflows:** Implemented using the BPMN Engine and agentic workflows.

---

## Chapter 26: Data Privacy, Anonymization, and Quantum-Safe Cryptography

### 26.1 Data Privacy Overview

**Purpose:** Protect Personally Identifiable Information (PII) at rest, in transit, and during processing.

**PII Data Types:**
- **Sensitive:** Financial data, health records, biometric data.
- **Personal:** Name, address, phone number, email.
- **Identifiers:** ID numbers, account numbers.

### 26.2 Data Classification

**Purpose:** Identify and label sensitive data across all stores.

**Implementation:**
- **Automated Scanning:** Tools scan data stores for patterns (e.g., credit card numbers, phone numbers, SSN).
- **Manual Tagging:** Data stewards manually classify data assets in the Data Catalog.
- **Sensitivity Tiers:** Public, Internal, Confidential, Restricted.

**Tools:**
- **AWS Macie:** Scans S3 buckets for PII.
- **Google Cloud DLP:** Scans data for PII and sensitive information.
- **BigID:** Automated data discovery and classification for cloud and on-premises data.

### 26.3 Anonymization and Pseudonymization

**Purpose:** De-identify data for analytics, development, and non-production use.

**Techniques:**
- **Tokenization:** Replace sensitive data with a token (reversible).
- **Format-Preserving Encryption (FPE):** Encrypt data while preserving its format (e.g., a credit card number remains a 16-digit number).
- **k-Anonymity:** Ensure that each record is indistinguishable from at least k-1 other records.
- **Differential Privacy:** Add noise to query results to prevent re-identification.

**Implementation:**

| Technique | Tool | Justification |
| :--- | :--- | :--- |
| **Tokenization** | HashiCorp Vault Transform | Vault transforms data via tokenization, FPE, and other methods. |
| **k-Anonymity** | ARX | Open-source data anonymization tool. |
| **Differential Privacy** | Google Differential Privacy Library | Open-source library for differential privacy. |

### 26.4 Dynamic Data Masking

**Purpose:** Mask sensitive fields in real-time based on user role without copying data.

**Implementation:**
- **Database-Level Masking:** PostgreSQL RLS with masking functions.
- **Proxy-Based Masking:** A proxy (e.g., Proxysql) intercepts queries and masks sensitive fields.
- **Application-Level Masking:** The BFF masks sensitive fields before returning them to the client.

**Example: PostgreSQL Dynamic Data Masking:**
```sql
-- Mask SSN for non-admin users
CREATE FUNCTION mask_ssn(text) RETURNS text AS $$
    SELECT CASE
        WHEN current_setting('app.current_user_role') = 'admin' THEN $1
        ELSE 'XXX-XX-' || RIGHT($1, 4)
    END;
$$ LANGUAGE sql IMMUTABLE;
```

### 26.5 Consent Management

**Purpose:** Manage user consent for data collection and processing.

**Implementation:**
- **Consent Platform:** Users provide consent for specific purposes (e.g., marketing, analytics).
- **Consent Storage:** Consent is stored in the database (or a dedicated consent management platform).
- **Consent Enforcement:** Services check the consent status before processing PII.

**Tools:**
- **OneTrust:** Enterprise consent management.
- **Transcend:** Privacy operations platform.
- **Custom Workflows:** Implemented using the BPMN Engine (user consents to terms and conditions).

### 26.6 Quantum-Safe Cryptography

**Purpose:** Prepare for post-quantum threats by adopting quantum-resistant algorithms for encryption and signing.

**Threat Model:**
- **Harvest-Now-Decrypt-Later:** Attackers harvest encrypted data today and decrypt it when quantum computers are available.
- **Long-Lived Secrets:** Data with a 20+ year lifespan (e.g., legal documents, healthcare records) is at risk.

**Quantum-Safe Algorithms (NIST Standards):**
- **CRYSTALS-Kyber:** Key encapsulation mechanism (KEM) for encryption.
- **CRYSTALS-Dilithium:** Digital signature scheme.
- **SPHINCS+:** Stateless hash-based signature scheme.
- **FALCON:** Digital signature scheme.

**Implementation Strategy:**

| Phase | Action | Timeline |
| :--- | :--- | :--- |
| **Assessment** | Identify data that requires long-term confidentiality (e.g., legal documents, healthcare records). | Year 1 |
| **Hybrid Mode** | Use classical + PQC algorithms together (e.g., Kyber + RSA). | Years 1-3 |
| **Migration** | Replace classical algorithms with PQC algorithms as standards mature. | Years 3-5 |
| **Crypto-Agility** | Design the platform to support multiple crypto algorithms and allow hot-switching. | Year 0 (ongoing) |

**Tools:**
- **OpenQuantumSafe:** Open-source library for PQC algorithms in C, Python, and .NET.
- **Bouncy Castle PQC:** PQC algorithms for .NET, Java, and other languages.
- **AWS KMS (PQ-Hybrid):** AWS KMS supports hybrid PQC modes.

**Crypto-Agility Implementation:**
- **Abstraction:** The `ICryptoProvider` port abstracts the specific cryptographic algorithms.
- **Adapters:** `AesCryptoProvider` (classical), `KyberCryptoProvider` (PQC), `HybridCryptoProvider` (classical + PQC).
- **Configuration:** The `RuntimeTopology` selects which crypto provider to use.

```csharp
public interface ICryptoProvider
{
    byte[] Encrypt(byte[] data, byte[] key);
    byte[] Decrypt(byte[] data, byte[] key);
    byte[] Sign(byte[] data);
    bool Verify(byte[] data, byte[] signature);
}
```

---

# PART 6: CLOUD-NATIVE INFRASTRUCTURE & OPERATIONS

---

## Chapter 27: Kubernetes Orchestration & Service Mesh (Istio/Linkerd)

### 27.1 Kubernetes as the Orchestration Foundation

**Purpose:** Provide a declarative, self-healing, and scalable container orchestration platform for all workloads.

**Kubernetes Distribution:** The platform is designed to run on any CNCF-certified Kubernetes distribution:

| Environment | Distribution | Justification |
| :--- | :--- | :--- |
| **Development** | K3s or Kind (Kubernetes in Docker) | Lightweight, low resource consumption, suitable for local development. |
| **Test / Staging** | Amazon EKS / Azure AKS / Google GKE | Managed Kubernetes with automated upgrades and integrated observability. |
| **Production** | Amazon EKS / Azure AKS / Google GKE | Enterprise-grade, highly available, with multi-region support. |
| **On-Premises** | OpenShift / Rancher / TKG | On-premises Kubernetes with enterprise support. |

**Kubernetes Resources:**
- **Namespaces:** Logical separation for environments (dev, test, staging, prod) and teams.
- **Deployments:** Stateless workloads (API Gateway, BFF, engines).
- **StatefulSets:** Stateful workloads (databases, message brokers, caches).
- **Services:** Internal service discovery and load balancing (ClusterIP, NodePort, LoadBalancer).
- **Ingress:** External access to services.
- **ConfigMaps:** Environment-specific configuration (including RuntimeTopology).
- **Secrets:** Sensitive configuration (database credentials, API keys).
- **NetworkPolicies:** Micro-segmentation and zero-trust networking.
- **PodSecurityPolicies / PodSecurityStandards:** Security context for pods.

**Cluster Architecture:**
- **Control Plane:** API server, etcd, scheduler, controller manager (managed by cloud provider).
- **Worker Nodes:** Compute nodes running pods. Node pools for different workload types (CPU-intensive, memory-intensive, GPU).
- **Cluster Autoscaler:** Automatically scales worker nodes based on pod resource requests.
- **Node Problem Detector:** Detects node issues (disk pressure, memory pressure) and triggers remediation.

### 27.2 GitOps with ArgoCD

**Purpose:** Declarative, Git-driven deployment with automated reconciliation.

**Implementation:**
- **Git Repository:** The source of truth for all Kubernetes manifests (Helm charts, Kustomize overlays).
- **ArgoCD:** Pull-based controller that monitors the Git repository and syncs the cluster state.
- **Auto-Sync:** ArgoCD automatically syncs the cluster state with the Git repository (with optional manual approval gates).

**ArgoCD Workflow:**
1. Developer pushes changes to the Git repository (e.g., updates to a Helm chart).
2. ArgoCD detects the changes (webhook or polling).
3. ArgoCD syncs the changes to the target Kubernetes cluster.
4. Kubernetes applies the changes (rolling update, new pod creation).
5. ArgoCD monitors the health of the new deployment (readiness probes).

**Application of Patterns:**
- **App-of-Apps:** A single ArgoCD application that defines all other applications (a pattern for managing multiple microservices).
- **Sync Windows:** Define time windows for automatic syncing (e.g., no auto-sync during peak hours).
- **Rollback:** ArgoCD supports rolling back to previous versions.

### 27.3 Service Mesh (Istio / Linkerd)

**Purpose:** Provide a transparent infrastructure layer for service-to-service communication, including traffic management, resilience, observability, and security.

**Implementation:**
- **Data Plane:** Envoy sidecar proxies (Istio) or Linkerd-proxy sidecars (Linkerd) are injected into each pod.
- **Control Plane:** Manages the configuration of the sidecar proxies (Istio Pilot, Linkerd Controller).

**Istio Architecture:**

| Component | Purpose |
| :--- | :--- |
| **Envoy Proxy** | Sidecar proxy for each pod, handling all inbound and outbound traffic. |
| **Pilot** | Configures Envoy proxies with routing rules and service discovery. |
| **Citadel** | Manages mTLS certificates and workload identities (SPIFFE). |
| **Galley** | Validates and distributes configuration. |
| **Kiali** | Visualization of the service mesh topology and traffic flows. |
| **Jaeger / Tempo** | Distributed tracing integration. |

**Traffic Management (Istio):**
- **VirtualService:** Defines routing rules (e.g., route 10% of traffic to v2 for canary).
- **DestinationRule:** Defines load balancing, circuit breaking, and mTLS settings.
- **Gateway:** Defines ingress and egress gateways for external traffic.

**Istio VirtualService Example (Canary Deployment):**
```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bpmn-engine-vs
spec:
  hosts:
  - bpmn-engine
  http:
  - match:
    - headers:
        canary:
          exact: "true"
    route:
    - destination:
        host: bpmn-engine-v2
        subset: v2
      weight: 100
  - route:
    - destination:
        host: bpmn-engine-v1
        subset: v1
      weight: 90
    - destination:
        host: bpmn-engine-v2
        subset: v2
      weight: 10
```

**Security (Istio):**
- **mTLS:** STRICT mode (mutual TLS for all service-to-service communication).
- **AuthorizationPolicy:** Fine-grained authorization policies (e.g., only allow `bff-service` to call `bpmn-engine`).
- **PeerAuthentication:** Defines mTLS mode (STRICT, PERMISSIVE, DISABLE).

**Istio AuthorizationPolicy Example:**
```yaml
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: allow-bff-to-bpmn
spec:
  selector:
    matchLabels:
      app: bpmn-engine
  action: ALLOW
  rules:
  - from:
    - source:
        principals:
        - "spiffe://platform.internal/ns/default/sa/bff-service"
```

**Alternative: Linkerd**
- **Pros:** Simpler than Istio, lower resource overhead, faster startup time.
- **Cons:** Fewer traffic management features (no fine-grained routing, no authorization policies).
- **Decision:** Istio is the primary service mesh due to its comprehensive feature set (traffic management, security, observability). Linkerd may be used for lightweight workloads or where Istio complexity is not justified.

**Service Mesh Integration with Polymorphic Runtime:**
- **Development:** Service mesh is disabled (no sidecars). In-memory communication.
- **Staging:** Service mesh enabled with mTLS in PERMISSIVE mode (tolerates non-mTLS traffic).
- **Production:** Service mesh enabled with mTLS in STRICT mode. All traffic is authenticated and encrypted.

---

## Chapter 28: Infrastructure-as-Code (Terraform/Crossplane) & Drift Management

### 28.1 Declarative Infrastructure-as-Code (IaC)

**Purpose:** Define, provision, and manage infrastructure resources (Kubernetes clusters, databases, message brokers, caches, network resources) in a declarative, version-controlled, and repeatable manner.

**Implementation:**

| Tool | Purpose | Justification |
| :--- | :--- | :--- |
| **Terraform** | Infrastructure provisioning (cloud resources) | Mature, multi-cloud, large provider ecosystem, state management. |
| **Crossplane** | Control plane for infrastructure | Kubernetes-native, reconciles infrastructure state with Git, supports GitOps. |
| **Pulumi** | Infrastructure as code in programming languages | Modern alternative, uses real programming languages (C#, TypeScript, Python). |
| **AWS CloudFormation / Azure Bicep** | Cloud-native IaC | Managed by cloud providers, deeply integrated with their services. |

**IaC State Management:**
- **Remote State:** Terraform state is stored remotely (e.g., S3 bucket with DynamoDB state locking) to prevent conflicts.
- **State Locking:** Prevents multiple users from applying changes simultaneously.
- **State Versioning:** Enables rollback to previous infrastructure states.

### 28.2 Infrastructure Provisioning Pipeline

**Pipeline Flow:**
1. **Code Change:** Developer commits changes to Terraform or Crossplane manifests.
2. **Plan:** CI pipeline runs `terraform plan` (or equivalent) to show the changes.
3. **Review:** Plan is reviewed by a peer (or automated policy check).
4. **Apply:** Pipeline runs `terraform apply` (with approval gate for production).
5. **Reconciliation:** Crossplane (or ArgoCD) continuously reconciles the actual state with the desired state.

**Separation of Concerns:**
- **Platform Team:** Manages the core infrastructure (Kubernetes clusters, networking, databases).
- **Application Team:** Manages application-specific infrastructure (namespaces, service accounts, config maps) via Helm.

### 28.3 Crossplane for Kubernetes-Native IaC

**Purpose:** Extend Kubernetes to manage external infrastructure resources (cloud databases, message brokers, object storage) using the same GitOps principles.

**Crossplane Providers:**
- **AWS Provider:** Creates EC2 instances, RDS databases, S3 buckets, etc.
- **Azure Provider:** Creates Azure resources (VMs, SQL databases, storage accounts).
- **GCP Provider:** Creates GCP resources (Compute Engine, Cloud SQL, Cloud Storage).
- **Kubernetes Provider:** Creates Kubernetes resources (namespaces, service accounts, config maps).

**Crossplane Resource Definition Example:**
```yaml
apiVersion: database.aws.crossplane.io/v1beta1
kind: RDSInstance
metadata:
  name: platform-db
  namespace: default
spec:
  forProvider:
    region: us-west-2
    dbInstanceClass: db.t3.medium
    engine: postgres
    engineVersion: "15"
    masterUsername: platform
    masterPasswordSecretRef:
      name: rds-password
      key: password
    storageType: gp2
    allocatedStorage: 100
  providerRef:
    name: aws-provider
```

**Benefits of Crossplane:**
- **Unified GitOps:** Infrastructure and application configuration are managed in the same Git repository.
- **Reconciliation:** Crossplane continuously reconciles the state, ensuring no drift.
- **Self-Service:** Application teams can provision their own infrastructure (within policy boundaries).

### 28.4 Drift Detection and Remediation

**Purpose:** Detect when the actual infrastructure state deviates from the declared state (drift) and automatically remediate it.

**Drift Sources:**
- Manual changes made by operators.
- Cloud provider updates (e.g., auto-scaling groups, failover).
- Configuration drift (e.g., security group rules modified manually).

**Implementation:**
- **Terraform:** `terraform plan` detects drift. `terraform apply` remediates it.
- **Crossplane:** Continuous reconciliation loop (control loop) automatically reverts drift.
- **ArgoCD:** Detects drift in Kubernetes resources and syncs to the Git state.
- **AWS Config:** Detects drift in AWS resources and triggers remediation via AWS Systems Manager.

**Drift Prevention:**
- **Policy-as-Code:** OPA/Gatekeeper prevents manual changes to critical resources.
- **RBAC:** Restrict direct access to infrastructure (e.g., no direct console access for application teams).
- **Immutable Infrastructure:** Replace resources instead of modifying them (e.g., auto-scaling groups with rolling updates).

---

## Chapter 29: Multi-Stage Environment Promotion (Helm/Kustomize)

### 29.1 Environment Definition

**Purpose:** Manage multiple logical environments (dev, test, staging, prod) with environment-specific configuration and promotion pipelines.

**Environments:**

| Environment | Purpose | `ASPNETCORE_ENVIRONMENT` | RuntimeTopology Profile | Data Source |
| :--- | :--- | :--- | :--- | :--- |
| **Local Development** | Developer coding and unit testing | `Development` | `InMemory`, `Local`, `Passthrough` | Synthetic seed data |
| **Docker Compose** | Integration testing on developer machine | `Development` | `InMemory` or `LocalContainers` | Synthetic seed data |
| **Test (Kubernetes)** | Automated integration, contract, and load testing | `Test` | `Kafka`, `Redis`, `Consul` (mTLS disabled) | Anonymized production subset |
| **Staging** | Pre-production validation, UAT, canary analysis | `Staging` | `Kafka`, `etcd`, `Consul`, `Istio` (mTLS enabled) | Anonymized production data (Tonic/Delphix) |
| **Production** | Live business operations | `Production` | `Kafka`, `etcd`, `Consul`, `Istio` (full hardening) | Live production data |

### 29.2 Configuration Management (Helm)

**Purpose:** Package and deploy applications using declarative templates with environment-specific values.

**Implementation:**
- **Helm Charts:** Define the structure of the deployment (Deployments, Services, ConfigMaps, Ingress).
- **Values Files:** Environment-specific values (`values-dev.yaml`, `values-test.yaml`, `values-staging.yaml`, `values-prod.yaml`).

**Helm Chart Structure:**
```
bpmn-engine/
├── Chart.yaml
├── values.yaml
├── templates/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── configmap.yaml
│   ├── ingress.yaml
│   └── hpa.yaml
└── environments/
    ├── values-dev.yaml
    ├── values-test.yaml
    ├── values-staging.yaml
    └── values-prod.yaml
```

**Kustomize (Alternative):** For simpler configurations or when Helm complexity is not justified, Kustomize provides a Kubernetes-native overlay approach.

**Kustomize Example:**
```
bpmn-engine/
├── base/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── kustomization.yaml
├── overlays/
│   ├── dev/
│   │   ├── configmap-patch.yaml
│   │   └── kustomization.yaml
│   └── prod/
│       ├── configmap-patch.yaml
│       └── kustomization.yaml
```

**Decision:** Helm is the primary packaging tool due to its extensive ecosystem, templating capabilities, and integration with ArgoCD. Kustomize is used for simple overlays or when Helm is not suitable.

### 29.3 Environment Promotion Pipeline

**Purpose:** Automatically promote immutable artifacts through the environment pipeline.

**Pipeline Steps:**
1. **Build:** Build the container image (tagged with Git commit SHA).
2. **Push:** Push image to container registry (ECR, ACR, GCR).
3. **Deploy to Dev:** Deploy the image to the Dev environment (automated).
4. **Run Tests (Dev):** Run smoke tests, integration tests.
5. **Promote to Test:** Promote the image (identical tag) to Test environment (automated).
6. **Run Tests (Test):** Run full integration, contract, and load tests.
7. **Promote to Staging:** Promote the image to Staging (manual approval gate).
8. **Run Tests (Staging):** Run performance tests, chaos tests, UAT.
9. **Promote to Production:** Promote the image to Production (manual approval gate).

**Approval Gates:**
- **Manual Approval:** A designated approver (e.g., release manager) reviews the deployment plan and approves.
- **Automated Approval:** Approval is granted based on test results (e.g., all tests pass, performance metrics meet SLOs).
- **Conditional Approval:** Approval is granted only if specific conditions are met (e.g., no open critical bugs, feature flags are configured).

**GitOps Promotion:**
- **Environment Branches:** Each environment has a corresponding branch in Git (e.g., `dev`, `staging`, `prod`). ArgoCD watches the branch and syncs the cluster.
- **Pull Requests:** Promotion to production is done via a Pull Request to the `prod` branch. The PR triggers automated validation and requires approval.

### 29.4 Ephemeral Preview Environments

**Purpose:** Create temporary, disposable environments per pull request for testing and review.

**Implementation:**
- **Preview Namespaces:** Each pull request creates a new Kubernetes namespace (e.g., `pr-123`).
- **Infrastructure:** The preview environment includes a lightweight copy of the required infrastructure (database, cache, message bus).
- **TTL:** Preview environments have a time-to-live (e.g., 24 hours). They are automatically cleaned up after the TTL expires or the PR is closed.

**Tools:**
- **Qovery / Okteto / Uffizzi:** Dedicated tools for ephemeral environments.
- **Custom Controllers:** ArgoCD + Helm with a TTL controller (e.g., using Kubernetes CronJobs for cleanup).

**Preview Environment Configuration:**
- **RuntimeTopology:** Preview environments use the `Test` profile (Kafka, Redis) with smaller resource limits.
- **Database:** A lightweight database container (e.g., PostgreSQL container) with seed data.
- **Ingress:** A dedicated subdomain for the preview environment (e.g., `pr-123.platform.internal`).

---

## Chapter 30: Load Balancing, Traffic Routing, and Global Steering

### 30.1 Load Balancing Architecture

**Purpose:** Distribute incoming traffic across backend instances with configurable algorithms, health checking, and TLS termination.

**Layers:**
1. **Global Traffic Steering (DNS)** : Route users to the nearest healthy region.
2. **Edge / Reverse Proxy (L7)** : Terminate TLS, route based on URL/headers, apply rate limiting.
3. **Transport Layer (L4)** : Distribute raw TCP/UDP connections (for non-HTTP or high-throughput).
4. **Kubernetes Service** : Internal load balancing within the cluster (kube-proxy or eBPF).
5. **Service Mesh** : Client-side load balancing (Envoy/Linkerd-proxy) with fine-grained traffic control.

### 30.2 Global Traffic Steering (DNS)

**Purpose:** Route users to the nearest healthy data centre or region based on geolocation, latency, or weight.

**Implementation:**

| Tool | Justification |
| :--- | :--- |
| **AWS Route 53** | Geoproximity routing, latency-based routing, health checks. |
| **Cloudflare Load Balancing** | Global load balancing with Anycast, health checks, and failover. |
| **Azure Traffic Manager** | DNS-based traffic routing with multiple routing methods (performance, geographic, weighted). |
| **Google Cloud Load Balancing** | Global load balancing with anycast IP addresses. |

**Routing Methods:**
- **Geolocation:** Route users to the nearest region based on their IP address.
- **Latency:** Route users to the region with the lowest latency.
- **Weighted:** Route a percentage of traffic to specific regions (for canary or A/B testing).
- **Failover:** Active-passive failover to a secondary region when the primary region is unhealthy.

**Health Checks:**
- **Active Health Probes:** DNS-based health checks to validate that the endpoint is healthy.
- **Passive Health Checks:** Observing error rates (e.g., 5xx errors) to determine health.

### 30.3 Edge / Reverse Proxy (L7) Load Balancing

**Purpose:** Terminate TLS, distribute HTTP requests based on URL, headers, or cookies, and apply rate limiting and request buffering.

**Implementation:**

| Environment | Tool | Justification |
| :--- | :--- | :--- |
| **Development** | `YARP` (Yet Another Reverse Proxy) | Lightweight, high-performance, Microsoft-maintained. |
| **Production** | `YARP` / `Envoy` / `ingress-nginx` | High-performance, flexible routing, integrates with service discovery. |

**Load Balancing Algorithms (L7):**
- **Weighted Round-Robin:** Distribute requests based on weights.
- **Least-Connections:** Route to the backend with the fewest active connections.
- **Consistent Hashing:** Route requests for the same key (e.g., user ID) to the same backend (sticky sessions without shared state).
- **Random (Power of Two Choices):** Select two random backends and route to the one with fewer connections.

**Health Checks (L7):**
- **Active Probes:** The reverse proxy periodically sends HTTP requests (e.g., `/health`) to validate backend health.
- **Passive Checks:** Observing error rates (5xx, timeouts) to mark backends as unhealthy.
- **Slow Start:** Gradually ramp up traffic to newly added backends to avoid overload.

### 30.4 Transport Layer (L4) Load Balancing

**Purpose:** Distribute raw TCP/UDP connections before TLS termination, often for non-HTTP workloads or for higher throughput.

**Implementation:**
- **Cloud Managed L4:** AWS NLB, GCP TCP/UDP Load Balancer, Azure Load Balancer.
- **Software L4:** HAProxy (TCP mode), Envoy (TCP proxy).

**Algorithms:**
- **Round-Robin (TCP):** Simple distribution.
- **Least-Connections:** Route to the backend with the fewest active TCP connections.
- **Source IP Hash:** Route requests from the same source IP to the same backend.

**Use Cases:**
- **gRPC Traffic:** gRPC uses HTTP/2 over TCP. L4 load balancing distributes the raw TCP connections.
- **WebSocket Traffic:** WebSocket uses persistent TCP connections.
- **Non-HTTP Protocols:** Kafka, Redis, etcd.

### 30.5 Kubernetes-Native Load Balancing

**Purpose:** Distribute traffic to Kubernetes Pods using the built-in Service abstraction.

**Implementation:**
- **ClusterIP:** Internal cluster load balancing (via kube-proxy or eBPF with Cilium).
- **NodePort:** Expose the service on a static port on each node (for external access).
- **LoadBalancer:** Cloud provider load balancer (AWS NLB/ALB, GCP Load Balancer, Azure Load Balancer).
- **Ingress:** L7 load balancing with routing rules (host-based, path-based).

**eBPF-Based Load Balancing:**
- **Cilium:** Uses eBPF for high-performance load balancing (replaces kube-proxy).
- **Benefits:** Lower latency, higher throughput, and advanced features (e.g., DDoS protection, network policies).

### 30.6 Integration with Service Mesh

**Purpose:** Use the mesh's sidecar proxy for client-side load balancing with advanced traffic control.

**Istio Load Balancing:**
- **DestinationRule:** Defines the load balancing algorithm (ROUND_ROBIN, LEAST_CONN, RANDOM).
- **Outlier Detection:** Automatic circuit breaker (ejection) for unhealthy endpoints.

**Istio DestinationRule Example:**
```yaml
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: bpmn-engine-dr
spec:
  host: bpmn-engine
  trafficPolicy:
    loadBalancer:
      simple: LEAST_CONN
    connectionPool:
      tcp:
        maxConnections: 100
    outlierDetection:
      consecutive5xxErrors: 5
      interval: 30s
      baseEjectionTime: 30s
```

---

## Chapter 31: FinOps, Cost Allocation, and Carbon Monitoring

### 31.1 FinOps Overview

**Purpose:** Provide visibility into cloud and infrastructure spend, enable cost allocation, budgeting, anomaly detection, and resource optimization.

**Principles:**
- **No Surprises:** Teams have visibility into their cloud spend.
- **Cost Transparency:** Costs are allocated to teams, services, and environments.
- **Optimization:** Continuous rightsizing and optimization to minimize waste.

### 31.2 Cost Allocation (Tagging)

**Purpose:** Break down spend by team, service, environment, and feature.

**Tagging Strategy:**
- **Team:** The owning team of the resource.
- **Environment:** dev, test, staging, prod.
- **Service:** The service name (e.g., bpmn-engine, api-gateway).
- **Context:** The Bounded Context (e.g., ordering, inventory).
- **CostCenter:** The internal cost center for chargeback.

**Implementation:**
- **Kubernetes:** Kubecost / OpenCost automatically allocates costs to namespaces, pods, and services.
- **Cloud Resources:** AWS Cost Explorer, Azure Cost Management, GCP Cloud Billing use tags for cost allocation.
- **Chargeback/Showback:** Costs are allocated to teams via internal billing or reporting.

### 31.3 Cost Visibility and Budgeting

**Tools:**

| Tool | Purpose | Justification |
| :--- | :--- | :--- |
| **Kubecost / OpenCost** | Kubernetes cost monitoring | Real-time cost visibility per pod, namespace, and label. |
| **AWS Cost Explorer** | AWS cost visibility | Aggregate and filter AWS costs by tags, services, and regions. |
| **Vantage / CloudHealth** | Multi-cloud cost management | Unified view across AWS, Azure, GCP. |
| **Cast AI / Zesty** | Cloud cost optimization | Automated rightsizing and spot instance management. |

**Budgeting:**
- **Budgets:** Set budgets for teams, environments, and services.
- **Alerts:** Alert when spending exceeds a threshold (e.g., 80% of budget).
- **Forecasting:** Predict future spending based on historical usage.

### 31.4 Resource Optimization

**Purpose:** Right-size instances, use spot/preemptible VMs, and delete idle resources.

**Strategies:**
- **Rightsizing:** Automatically recommend instance types based on CPU/memory utilization.
- **Spot Orchestration:** Use spot/preemptible instances for non-critical workloads (batch jobs, development environments).
- **Idle Resource Deletion:** Automatically delete idle resources (e.g., unattached volumes, idle compute).
- **Scheduling:** Schedule non-production environments to shut down during off-hours (e.g., dev/test environments turned off at night).

**Tools:**
- **Karpenter:** Kubernetes node autoscaler with cost-aware scheduling (chooses the cheapest instance type).
- **KEDA:** Kubernetes-based event-driven autoscaling (scale to zero when no events).
- **Cast AI:** Automated rightsizing and spot orchestration.
- **StormForge:** Vertical autoscaling based on performance metrics.

### 31.5 Kubernetes Cost Management

**Purpose:** Accurately attribute costs within a shared cluster to namespaces, pods, and services.

**Implementation:**
- **OpenCost:** Open-source cost model for Kubernetes.
- **Kubecost:** Commercial (with free tier) cost management solution.
- **Pod-Level Cost Allocation:** Costs are allocated to pods based on their CPU and memory requests/usage.

**Kubecost Metrics:**
- **Total Cost per Namespace:** CPU, memory, storage, network.
- **Cost per Pod:** Granular cost breakdown per pod.
- **Idle Cost:** Cost of idle resources (unused capacity).
- **Efficiency:** Ratio of requested vs. used resources.

### 31.6 Carbon Monitoring (Sustainability)

**Purpose:** Measure, report, and optimize the environmental footprint of the platform's infrastructure and workloads.

**Carbon Footprint Measurement:**

| Tool | Purpose | Justification |
| :--- | :--- | :--- |
| **Cloud Carbon Footprint** | Calculate carbon emissions from cloud usage | Open-source, supports AWS, Azure, GCP. |
| **Kepler** | Kubernetes carbon monitoring | eBPF-based, measures carbon footprint of Kubernetes workloads. |
| **Scaphandre** | Power consumption measurement | Measures power consumption of containers. |

**Carbon Optimization:**
- **Carbon-Aware Scheduling:** Schedule workloads in low-carbon regions or during periods of low grid carbon intensity.
- **Resource Optimization:** Rightsizing reduces energy consumption.
- **Spot Instances:** Use spot instances in regions with high renewable energy contribution.

**Reporting:**
- **Carbon Reports:** Generate monthly carbon reports for compliance (GHG Protocol, CSRD).
- **Dashboards:** Integrate carbon metrics into Grafana for visibility.

---

## Chapter 32: Disaster Recovery & Multi-Region Active-Active

### 32.1 Disaster Recovery Overview

**Purpose:** Ensure business continuity in the event of a regional outage, data center failure, or major infrastructure failure.

**RPO / RTO Objectives:**

| Tier | Recovery Point Objective (RPO) | Recovery Time Objective (RTO) |
| :--- | :--- | :--- |
| **Tier 0 (Critical)** | 0 seconds (no data loss) | < 1 minute |
| **Tier 1 (Business Critical)** | < 5 seconds | < 5 minutes |
| **Tier 2 (Important)** | < 1 minute | < 1 hour |
| **Tier 3 (Batch)** | < 1 hour | < 24 hours |

**DR Strategies:**
- **Active-Active:** Services are running in multiple regions simultaneously. Traffic is load-balanced across regions. Zero RPO, near-zero RTO.
- **Active-Passive:** Services are running in one primary region. A secondary region is on standby. Data is replicated asynchronously. RPO = replication lag, RTO = failover time.

### 32.2 Backup and Restore

**Purpose:** Regularly back up stateful data (databases, volumes, object stores) and be able to restore to a point in time.

**Backup Strategy:**

| Data Type | Backup Tool | Backup Frequency | Retention |
| :--- | :--- | :--- | :--- |
| **Databases (PostgreSQL)** | AWS Backup / Azure Backup / Velero | Hourly (incremental), Daily (full) | 30 days (hot), 1 year (cold) |
| **Kubernetes Volumes (PV)** | Velero + CSI snapshots | Daily | 30 days |
| **Object Storage (S3)** | S3 Versioning + Lifecycle | Continuous (versioning) | 30 days (history) |
| **ConfigMaps / Secrets** | Velero (backup cluster state) | Daily | 30 days |

**Restore Testing:**
- **Automated Restore Testing:** Regularly restore backups to a test environment and validate data integrity.
- **Game-Day Drills:** Schedule DR drills (e.g., quarterly) to test failover procedures.

**Velero (Kubernetes Backup):**
- **Backup:** Backs up Kubernetes resources (deployments, services, config maps) and persistent volumes (via CSI snapshots).
- **Restore:** Restores the cluster state to a previous point in time.
- **Schedule:** Supports scheduled backups (daily, weekly).
- **Integrations:** Integrates with cloud storage (S3, Azure Blob, GCS).

### 32.3 Multi-Region Active-Active

**Purpose:** Serve traffic from multiple data centres simultaneously, with zero RPO and near-zero RTO.

**Implementation Requirements:**
- **Global Load Balancer:** DNS-based (Route 53, Cloudflare) with health checks and latency-based routing.
- **Multi-Region Databases:** CockroachDB, Cloud Spanner, or YugabyteDB for globally distributed SQL with strong consistency.
- **Event Streaming:** Kafka with multi-region replication (MirrorMaker) or Pulsar with geo-replication.
- **Stateless Services:** Services are stateless and can be deployed in any region.
- **Stateful Services:** Stateful services must use globally distributed databases or rely on session affinity.

**Database Options:**

| Database | Consistency | Latency | Complexity |
| :--- | :--- | :--- | :--- |
| **CockroachDB** | Strong (serializable) | Low | High |
| **Google Cloud Spanner** | Strong (external consistency) | Low | High (managed) |
| **YugabyteDB** | Strong (serializable) | Low | High |
| **PostgreSQL + BDR** | Eventual (asynchronous) | Medium | Medium |
| **Cassandra** | Eventual (tunable) | Very Low | Medium |

**Active-Active Services:**
- **API Gateway:** Deployed in all regions. Global load balancer routes to the nearest healthy instance.
- **BFF:** Deployed in all regions. Uses service discovery (Consul) to locate services in the same region (to avoid cross-region latency).
- **Engines:** Deployed in all regions. Use distributed locks (etcd/Redis) for coordination.
- **Sagas:** Use distributed Saga orchestrator (Temporal) with multi-region workers.

### 32.4 Multi-Region Active-Passive (Cost-Effective Alternative)

**Purpose:** Serve traffic from a primary region, with a secondary region on standby for disaster recovery.

**Implementation:**
- **DNS Failover:** Route 53 (or similar) monitors the health of the primary region. If unhealthy, traffic is routed to the secondary region.
- **Data Replication:** Asynchronous replication of databases (PostgreSQL streaming replication, S3 cross-region replication).
- **Infrastructure Deployment:** Infrastructure (Kubernetes, databases, message buses) is deployed in the secondary region but scaled down (e.g., minimal replicas). On failover, the secondary region is scaled up.

**RPO/RTO:** RPO = replication lag (typically < 5 seconds). RTO = startup time for services in the secondary region (typically < 5 minutes).

**Implementation:**
- **Terraform:** Terraform modules define both primary and secondary regions. The secondary region uses the same modules but with different variables.
- **ArgoCD:** ArgoCD syncs the secondary region to the latest Git state (with health checks to prevent sync when primary is healthy).

### 32.5 Chaos Engineering for DR Testing

**Purpose:** Validate the system's resilience to infrastructure failures and the effectiveness of DR procedures.

**Implementation:**
- **Chaos Mesh:** Injects failures into the Kubernetes cluster (pod kills, network latency, disk pressure).
- **Gremlin:** Chaos engineering platform with pre-built experiments (shutdown of Kubernetes nodes, CPU spike).
- **AWS Fault Injection Simulator:** AWS-native chaos engineering service.

**Scenarios:**
- **Pod Kill:** Kill a random pod and observe recovery.
- **Node Down:** Simulate a Kubernetes node failure.
- **Network Partition:** Introduce network latency between services.
- **Region Failover:** Simulate a full region outage and validate the failover procedure.

**Metrics:**
- **Recovery Time:** Time taken to recover from the failure.
- **Data Loss:** Check for data loss after failover.
- **User Impact:** Validate that users did not experience errors.

---

# PART 7: OBSERVABILITY, TESTING & RESILIENCE

---

## Chapter 33: Observability (Logs, Metrics, Traces, Profiling)

### 33.1 The Four Pillars of Observability

The platform implements comprehensive observability across four pillars:

1. **Logs:** Structured, searchable, and correlated event records.
2. **Metrics:** Dimensional time-series data for monitoring and alerting.
3. **Traces:** End-to-end request flow across services.
4. **Profiles:** Continuous performance profiling for root-cause analysis.

All observability data is correlated using a common `traceId`, `spanId`, and `correlationId` propagated across all components.

### 33.2 Structured Logging

**Purpose:** Provide centralized, structured, and searchable logs with correlation IDs.

**Implementation:**

| Environment | Adapter | Description |
| :--- | :--- | :--- |
| **Development** | `ConsoleLogger` | Logs to the console with colored output for readability. |
| **Test / Staging** | `ElasticLogger` | Logs are shipped to Elasticsearch (via Filebeat/Fluentd). |
| **Production** | `ElasticLogger` | Logs are shipped to Elasticsearch with high availability and retention policies. |

**Log Structure:**

```json
{
  "timestamp": "2026-06-17T10:30:00.123Z",
  "level": "Info",
  "traceId": "a1b2c3d4e5f6",
  "spanId": "g7h8i9j0k1l2",
  "correlationId": "order-12345",
  "service": "bpmn-engine",
  "module": "ProcessEngine.BPMN",
  "operation": "StartProcess",
  "userId": "user-123",
  "message": "Process started successfully",
  "properties": {
    "processId": "proc-456",
    "processDefinitionId": "def-789"
  }
}
```

**Log Shipping Pipeline:**
1. **Application:** Logs are written to stdout using `ILogger` (Serilog or Microsoft.Extensions.Logging).
2. **Collector:** Filebeat/Fluentd collects logs from all pods and ships them to Elasticsearch.
3. **Indexing:** Logs are indexed in Elasticsearch with indices by date (e.g., `logs-2026.06.17`).
4. **Retention:** Logs are retained for 30 days (hot), 1 year (warm), and 7 years (cold archive).

**Log Correlation:**
- **traceId:** Propagated from the API Gateway (or BFF) to all downstream services via headers (`X-Trace-Id`).
- **spanId:** Generated for each operation (Use Case, Engine execution, external call).
- **correlationId:** Business-level correlation ID (e.g., order ID, process instance ID).

**Sensitive Data Masking:**
- **PII Masking:** Logs are automatically masked for PII (credit card numbers, SSN, email) using log sanitization filters.
- **Secrets:** Secrets (passwords, tokens) are never logged.

### 33.3 Metrics and Monitoring

**Purpose:** Provide dimensional time-series data for monitoring, alerting, and capacity planning.

**Metrics Types:**
- **RED Metrics:** Rate, Errors, Duration for every service endpoint.
- **USE Metrics:** Utilization, Saturation, Errors for every resource (CPU, memory, disk, network).
- **Business Metrics:** Process completion rates, decision outcomes, SLA breaches, agent performance.

**Implementation:**

| Environment | Adapter | Description |
| :--- | :--- | :--- |
| **Development** | `ConsoleMetrics` | Metrics are logged to the console for debugging. |
| **Test / Staging** | `PrometheusMetrics` | Metrics are scraped by Prometheus. |
| **Production** | `PrometheusMetrics` | Metrics are scraped by Prometheus with high availability and long-term storage (Thanos/Cortex). |

**Metrics Exporter:**

The platform exposes metrics via the OpenTelemetry Metrics API, which is scraped by Prometheus.

```csharp
[TraceSpan]
[CircuitBreaker(PolicyName = "BpmnEngine")]
public async Task<StartProcessResult> Handle(StartProcessCommand cmd)
{
    var stopwatch = Stopwatch.StartNew();
    try
    {
        var result = await _engine.ExecuteAsync(...);
        _metrics.RecordProcessDuration(cmd.ProcessDefinitionId, stopwatch.Elapsed);
        _metrics.IncrementProcessStarted(cmd.ProcessDefinitionId);
        return result;
    }
    catch (Exception ex)
    {
        _metrics.IncrementProcessFailed(cmd.ProcessDefinitionId, ex.GetType().Name);
        throw;
    }
}
```

**Key Metrics:**

| Metric | Type | Description |
| :--- | :--- | :--- |
| `process_started_total` | Counter | Number of processes started per definition. |
| `process_completed_total` | Counter | Number of processes completed per definition. |
| `process_duration_seconds` | Histogram | Duration of process execution (p50, p95, p99). |
| `process_failed_total` | Counter | Number of process failures per definition. |
| `task_assigned_total` | Counter | Number of tasks assigned per user/group. |
| `task_completed_total` | Counter | Number of tasks completed per user/group. |
| `engine_calls_total` | Counter | Number of engine invocations per engine type. |
| `engine_duration_seconds` | Histogram | Duration of engine execution per engine type. |
| `http_requests_total` | Counter | Number of HTTP requests per endpoint, method, status. |
| `http_duration_seconds` | Histogram | HTTP request duration per endpoint. |
| `kafka_messages_total` | Counter | Number of Kafka messages produced/consumed per topic. |
| `kafka_lag` | Gauge | Consumer lag per consumer group. |
| `database_connections` | Gauge | Database connection pool usage. |
| `cache_hit_ratio` | Gauge | Cache hit ratio per cache type. |

**Alerting:**
- **Prometheus Alertmanager:** Configured with multi-window, multi-burn-rate alerts for SLOs.
- **Alert Rules:**
  - High error rate (> 1% for 5 minutes).
  - High latency (p95 > 1 second for 5 minutes).
  - Circuit breaker open.
  - Kafka consumer lag > 1000 messages.
  - Pod restarts > 5 per minute.
  - Database connection pool exhausted.
  - Certificate expiry within 7 days.

### 33.4 Distributed Tracing

**Purpose:** Provide end-to-end request flow across services, enabling root-cause analysis and performance optimization.

**Implementation:**

| Environment | Adapter | Description |
| :--- | :--- | :--- |
| **Development** | `ConsoleTracer` | Spans are logged to the console for debugging. |
| **Test / Staging** | `OpenTelemetryTracer` | Spans are exported to Jaeger/Tempo via OTLP. |
| **Production** | `OpenTelemetryTracer` | Spans are exported to Tempo/Jaeger with high availability and sampling strategies. |

**Tracing Instrumentation:**

The platform uses OpenTelemetry for instrumentation. The `ITracer` port is implemented via OpenTelemetry's `ActivitySource`.

```csharp
[TraceSpan] // AOP attribute that creates a span
public async Task<StartProcessResult> Handle(StartProcessCommand cmd)
{
    using var span = _tracer.StartSpan("StartProcess", tags: new { processId = cmd.ProcessId });
    span.SetAttribute("processDefinitionId", cmd.ProcessDefinitionId);
    
    var result = await _engine.ExecuteAsync(...);
    span.SetAttribute("result", result.Status);
    return result;
}
```

**Trace Propagation:**
- **Inbound:** The API Gateway extracts the `traceId` from the incoming request headers (`X-Trace-Id`).
- **Outbound:** The `HttpClient` or gRPC client injects the `traceId` into the outgoing request headers.
- **Kafka:** The `traceId` is propagated in Kafka message headers.

**Sampling Strategies:**
- **Development:** 100% sampling (full traces).
- **Test:** 100% sampling (full traces).
- **Staging:** 10% sampling (random).
- **Production:** 1% sampling (random) + 100% sampling for specific endpoints (e.g., error traces, high-value transactions).

**Trace Visualization:**
- **Jaeger:** Jaeger UI for trace visualization, waterfall diagrams, and trace analysis.
- **Tempo:** Grafana Tempo for querying traces by trace ID or service name.

### 33.5 Continuous Profiling

**Purpose:** Provide always-on profiling of production workloads to identify performance bottlenecks without impacting performance.

**Implementation:**

| Environment | Adapter | Description |
| :--- | :--- | :--- |
| **Development** | Disabled | Profiling is not required in development. |
| **Production** | `Pyroscope` / `Parca` | Continuous profiling with low overhead (< 1% CPU). |

**Profiling Data:**
- **CPU Profiling:** Identify CPU hotspots (methods consuming the most CPU time).
- **Memory Profiling:** Identify memory allocation hotspots and memory leaks.
- **Goroutine / Thread Profiling:** Identify blocking operations and deadlocks.

**Tools:**
- **Grafana Pyroscope:** Open-source continuous profiling, integrated with Grafana.
- **Parca:** Open-source continuous profiling for Kubernetes workloads.
- **Google Cloud Profiler:** Managed profiling for GCP workloads.
- **Datadog Continuous Profiler:** Managed profiling with Datadog.

**Profiling Workflow:**
1. The profiler runs as a sidecar (or daemonset) in the Kubernetes cluster.
2. Profiling data is collected at regular intervals (e.g., every 10 seconds).
3. Data is stored in the profiler's backend (Pyroscope/Parca).
4. Developers can query profiling data by service, time range, and metric type.
5. Profiles can be compared across versions to identify regressions.

---

## Chapter 34: Business Activity Monitoring (BAM) & Process Mining

### 34.1 Business Activity Monitoring (BAM)

**Purpose:** Provide real-time dashboards and alerts over business KPIs (process completion rates, SLA breaches, decision outcomes).

**BAM Data Sources:**
- **Domain Events:** Process started, process completed, task assigned, decision evaluated.
- **Metrics:** Process duration, task duration, decision times.
- **Audit Logs:** User actions, system actions.

**Implementation:**

| Environment | Adapter | Description |
| :--- | :--- | :--- |
| **Development** | `InMemoryBam` | In-memory BAM for development and testing. |
| **Production** | `ElasticsearchBam` | BAM data is stored in Elasticsearch (or OpenSearch) with pre-aggregated dashboards. |

**BAM Dashboards:**

| Dashboard | Purpose | Metrics |
| :--- | :--- | :--- |
| **Process Performance** | Monitor process completion times and throughput | Average process duration (p50, p95, p99), process completion rate, process SLA compliance. |
| **Task Performance** | Monitor task assignment and completion | Average task duration, task backlog, task SLA compliance. |
| **Decision Performance** | Monitor decision outcomes | Decision distribution, decision evaluation time, decision accuracy. |
| **Agent Performance** | Monitor agent actions and success rates | Agent task completion rate, agent response time, agent error rate. |
| **SLA Dashboard** | Monitor SLA breaches | Number of SLA breaches, breach severity, breach trends. |

**BAM Alerts:**
- **SLA Breach:** Alert when a process exceeds its SLA threshold.
- **Process Failure:** Alert when a process fails (e.g., due to an exception).
- **Task Backlog:** Alert when the task backlog exceeds a threshold.
- **System Health:** Alert when system metrics (CPU, memory, error rates) exceed thresholds.

**Implementation:**

```csharp
public class ProcessCompletedEventHandler : IEventHandler<ProcessCompletedEvent>
{
    private readonly IBamExporter _bam;

    public async Task HandleAsync(ProcessCompletedEvent @event, CancellationToken ct)
    {
        var duration = @event.CompletedAt - @event.StartedAt;
        var slaBreached = duration > @event.SlaThreshold;

        await _bam.RecordAsync(new ProcessCompletionMetrics
        {
            ProcessDefinitionId = @event.ProcessDefinitionId,
            ProcessInstanceId = @event.ProcessInstanceId,
            StartedAt = @event.StartedAt,
            CompletedAt = @event.CompletedAt,
            DurationMs = duration.TotalMilliseconds,
            SlaBreached = slaBreached,
            Status = @event.Status,
            UserId = @event.AssignedUserId
        });
    }
}
```

### 34.2 Process Mining

**Purpose:** Discover, analyze, and improve business processes from event logs.

**XES Event Logs:**
- **XES (eXtensible Event Stream):** The IEEE 1849 standard for event logs.
- **Export Frequency:** Daily or on-demand.
- **Export Target:** Celonis, ProM, Apromore, PM4Py.

**Process Mining Capabilities:**
- **Process Discovery:** Automatically discover the actual process model from event logs.
- **Conformance Checking:** Compare the discovered process with the intended BPMN model.
- **Variant Analysis:** Identify process variants (different paths taken through the process).
- **Bottleneck Detection:** Identify bottlenecks and performance issues.
- **Root-Cause Analysis:** Identify the root causes of process failures.

**Implementation:**

| Environment | Adapter | Description |
| :--- | :--- | :--- |
| **Development** | `InMemoryXesExporter` | Exports XES logs to memory for development and testing. |
| **Production** | `KafkaXesExporter` | Exports XES logs to Kafka for consumption by Celonis/PM4Py. |

**Process Mining Pipeline:**
1. Domain events are collected and stored in the event store (Kafka/EventStoreDB).
2. A scheduled job (daily) extracts relevant events and transforms them into XES format.
3. The XES logs are exported to the process mining tool (Celonis, ProM).
4. The process mining tool discovers the process model and identifies bottlenecks.
5. Insights are fed back into the platform (e.g., as recommendations for process improvement).

**Integration with Celonis:**
- **Data Export:** The platform exports XES logs to Celonis via the Celonis API (or via a Celonis connector).
- **Celonis UI:** Business analysts view the discovered process model and performance metrics in Celonis.
- **Actionable Insights:** Celonis identifies bottlenecks and recommends process improvements. Recommendations are captured as change requests in the Model Repository.

---

## Chapter 35: Resilience Engineering (Circuit Breakers, Bulkheads, Retries)

### 35.1 Resilience Engineering Overview

**Purpose:** Ensure the platform remains available and responsive in the face of failures (network partitions, service crashes, timeouts, high load).

**Resilience Patterns:**
1. **Circuit Breaker:** Prevent cascading failures.
2. **Bulkhead:** Isolate failure domains.
3. **Retry with Backoff:** Handle transient failures.
4. **Timeout:** Prevent hanging operations.
5. **Fallback:** Provide graceful degradation.
6. **Health Checks:** Detect and recover from failures.
7. **Chaos Engineering:** Proactively test resilience.

### 35.2 Circuit Breaker

**Purpose:** Prevent cascading failures when a downstream service is unavailable.

**State Machine:**
- **Closed:** Requests are allowed. Failures increment a failure counter.
- **Open:** Requests are blocked immediately (fail-fast). A timeout starts.
- **Half-Open:** After the timeout, a single request is allowed to test the service.

**Implementation:**
- **Polly:** .NET resilience library with circuit breaker support.
- **Istio/Envoy:** Circuit breaker at the service mesh level (outlier detection).

**Polly Circuit Breaker Example:**

```csharp
[CircuitBreaker(PolicyName = "BpmnEngine")] // AOP attribute
public async Task<StartProcessResult> Handle(StartProcessCommand cmd)
{
    // Business logic
}
```

**Configuration:**

```json
"CircuitBreakerOptions": {
    "FailureThreshold": 0.5,
    "SamplingDurationSeconds": 30,
    "MinimumThroughput": 100,
    "BreakDurationSeconds": 60
}
```

- **FailureThreshold:** 50% failure rate triggers the circuit to open.
- **SamplingDuration:** 30-second window for failure rate calculation.
- **MinimumThroughput:** Minimum 100 requests before opening the circuit.
- **BreakDuration:** Circuit remains open for 60 seconds before transitioning to half-open.

**Distributed Circuit Breaker:**
- The circuit breaker state is stored in a distributed store (Redis) so that all pods share the same circuit state.
- This prevents a single pod from opening the circuit while others continue to hammer a failing service.

### 35.3 Bulkhead

**Purpose:** Limit concurrent requests to a service to prevent thread pool exhaustion.

**Implementation:**

| Environment | Adapter | Description |
| :--- | :--- | :--- |
| **Development** | `NoOpBulkhead` | No concurrency limits. |
| **Production** | `PollyBulkhead` | Polly bulkhead policy with configurable concurrency limit. |

**Polly Bulkhead Example:**

```csharp
[Bulkhead(PolicyName = "BpmnEngine", MaxParallelization = 10)] // AOP attribute
public async Task<StartProcessResult> Handle(StartProcessCommand cmd)
{
    // Business logic
}
```

**Configuration:**
- **MaxParallelization:** Maximum number of concurrent requests.
- **QueueLimit:** Maximum number of queued requests (requests exceeding the queue limit are rejected).

### 35.4 Retry with Exponential Backoff

**Purpose:** Handle transient failures (network timeouts, database deadlocks) by retrying the operation.

**Implementation:**
- **Polly:** .NET resilience library with retry support.

**Polly Retry Example:**

```csharp
[RetryPolicy(MaxRetries = 3, BaseDelayMs = 100, ExponentialFactor = 2.0)] // AOP attribute
public async Task<StartProcessResult> Handle(StartProcessCommand cmd)
{
    // Business logic
}
```

**Configuration:**
- **MaxRetries:** Maximum number of retries (3).
- **BaseDelay:** 100 milliseconds.
- **ExponentialFactor:** 2.0 (retry delays: 100ms, 200ms, 400ms).
- **Jitter:** Random jitter (20%) to avoid the thundering herd problem.

**Retry Filters:**
- **Transient Faults:** Only retry on specific exception types (e.g., `TimeoutException`, `SqlException`, `HttpRequestException`).
- **Idempotency:** Retries are safe for idempotent operations. Non-idempotent operations may need an idempotency key.

### 35.5 Timeouts

**Purpose:** Prevent hanging operations that consume resources.

**Implementation:**
- **Polly:** Timeout policy with configurable timeout duration.
- **HttpClient:** `HttpClient.Timeout`.
- **gRPC:** `CallOptions.Deadline`.
- **Service Mesh:** Istio/Envoy timeouts.

**Polly Timeout Example:**

```csharp
[Timeout(PolicyName = "BpmnEngine", Seconds = 5)] // AOP attribute
public async Task<StartProcessResult> Handle(StartProcessCommand cmd)
{
    // Business logic
}
```

**Configuration:**
- **Default Timeout:** 5 seconds for internal calls, 30 seconds for external calls.
- **Cancelation:** The timeout exception triggers the circuit breaker.

### 35.6 Fallback

**Purpose:** Provide graceful degradation when a service is unavailable.

**Implementation:**
- **Polly:** Fallback policy provides alternative responses.

**Polly Fallback Example:**

```csharp
[Fallback(PolicyName = "BpmnEngine", FallbackResponse = "Cached response")] // AOP attribute
public async Task<string> Handle(QueryCommand cmd)
{
    // Business logic
}
```

**Use Cases:**
- **Cached Response:** If the service is unavailable, return a cached response.
- **Default Value:** Return a default value (e.g., empty list, zero count).
- **Stale Data:** Return stale data with a warning header.

### 35.7 Health Checks

**Purpose:** Detect and recover from failures.

**Implementation:**
- **Kubernetes Liveness Probe:** Checks if the pod is alive. If the probe fails, the pod is restarted.
- **Kubernetes Readiness Probe:** Checks if the pod is ready to receive traffic. If the probe fails, traffic is not routed to the pod.
- **Custom Health Checks:** The `IHealthCheck` interface exposes custom health checks for dependencies (database, Kafka, Redis, service mesh).

**Health Check Endpoint:**
- **/health/ready:** Returns `200 OK` if the service is ready.
- **/health/live:** Returns `200 OK` if the service is alive.

**Custom Health Check Example:**

```csharp
public class DatabaseHealthCheck : IHealthCheck
{
    public async Task<HealthCheckResult> CheckHealthAsync(HealthCheckContext context, CancellationToken ct)
    {
        try
        {
            await _dbContext.Database.ExecuteSqlRawAsync("SELECT 1", ct);
            return HealthCheckResult.Healthy();
        }
        catch (Exception ex)
        {
            return HealthCheckResult.Unhealthy("Database is unavailable", ex);
        }
    }
}
```

---

## Chapter 36: Testing Strategy (Unit, Integration, Contract, Chaos, Performance)

### 36.1 Testing Pyramid

The platform follows the testing pyramid approach:

1. **Unit Tests:** Fast, isolated, in-memory. (~70% of tests)
2. **Integration Tests:** Test interactions with infrastructure (database, message bus). (~20% of tests)
3. **Contract Tests:** Verify API contracts between services. (~5% of tests)
4. **Performance Tests:** Validate latency and throughput. (~5% of tests)
5. **Chaos Tests:** Validate resilience to failures.

### 36.2 Unit Tests

**Purpose:** Test individual components in isolation (Aggregates, Value Objects, Use Cases, Engines).

**Implementation:**
- **Framework:** xUnit (or NUnit).
- **Mocking:** Moq (or NSubstitute).
- **In-Memory:** All dependencies are replaced with in-memory adapters (InMemoryRepository, InMemoryBus, LocalDistributedLock).

**Unit Test Example:**

```csharp
[Fact]
public async Task StartProcess_WhenValidCommand_ShouldStartProcess()
{
    // Arrange
    var repository = new InMemoryProcessInstanceRepository();
    var engine = new BpmnEngine();
    var bus = new InMemoryBus();
    var useCase = new StartProcessUseCase(repository, engine, bus);
    var command = new StartProcessCommand("order-123", new Variables {{ "amount", 100 }});

    // Act
    var result = await useCase.Handle(command, CancellationToken.None);

    // Assert
    Assert.NotNull(result.ProcessId);
    var instance = await repository.GetAsync(result.ProcessId);
    Assert.Equal(ProcessStatus.Running, instance.Status);
}
```

### 36.3 Integration Tests

**Purpose:** Test interactions between components and infrastructure (database, message bus, cache).

**Implementation:**
- **Testcontainers:** Spin up Docker containers for PostgreSQL, Kafka, Redis, etc., during the test run.
- **WebApplicationFactory:** Create an in-memory TestServer for end-to-end integration testing.
- **In-Memory Fallback:** In CI/CD pipelines where Testcontainers are not supported, fall back to in-memory adapters.

**Integration Test Example:**

```csharp
[Fact]
public async Task StartProcess_ShouldPersistToDatabase()
{
    // Arrange
    using var container = new PostgreSqlBuilder()
        .WithImage("postgres:15")
        .Build();
    await container.StartAsync();

    var dbContext = new PlatformDbContext(container.GetConnectionString());
    await dbContext.Database.MigrateAsync();

    var repository = new EFCoreProcessInstanceRepository(dbContext);
    var engine = new BpmnEngine();
    var bus = new KafkaBus(TestKafkaOptions);
    var useCase = new StartProcessUseCase(repository, engine, bus);
    var command = new StartProcessCommand("order-123", new Variables());

    // Act
    var result = await useCase.Handle(command, CancellationToken.None);

    // Assert
    var instance = await dbContext.ProcessInstances.FindAsync(result.ProcessId);
    Assert.NotNull(instance);
    Assert.Equal(ProcessStatus.Running, instance.Status);
}
```

### 36.4 Contract Tests

**Purpose:** Verify that services honour their API contracts across provider and consumer boundaries.

**Implementation:**
- **Pact:** Consumer-driven contract testing.
- **Provider:** The service provider runs a Pact verification suite to ensure it satisfies the consumer's expectations.

**Pact Workflow:**
1. Consumer writes a Pact test (specifying expected request and response).
2. Pact test generates a contract file.
3. The contract file is shared with the provider (via Pact Broker).
4. Provider runs a Pact verification test against its implementation.

**Pact Example:**

```csharp
[Fact]
public void StartProcessPact()
{
    _pact
        .UponReceiving("a request to start a process")
        .Given("the process definition exists")
        .WithRequest(HttpMethod.Post, "/api/v1/processes")
        .WithBody(new { processDefinitionId = "order-approval" })
        .WillRespondWith(HttpStatusCode.OK)
        .WithBody(new { processId = "123" });
}
```

### 36.5 Performance Tests

**Purpose:** Validate system latency and throughput under expected and peak loads.

**Implementation:**
- **k6:** Modern load testing tool (scriptable, container-native).
- **Locust:** Python-based load testing with a web UI.
- **JMeter:** Traditional load testing (Java).

**Performance Test Workflow:**
1. Define the test scenario (e.g., start 1000 processes per second, simulate 100 concurrent users).
2. Run the test from a dedicated test environment (or from multiple regions).
3. Collect metrics (latency, throughput, error rate).
4. Validate against SLOs (e.g., p95 < 1 second, error rate < 0.1%).
5. Generate a performance test report.

**Performance Test Example (k6):**
```javascript
import http from 'k6/http';
import { check } from 'k6';

export let options = {
    stages: [
        { duration: '30s', target: 10 }, // Ramp up
        { duration: '60s', target: 10 }, // Stay at 10 users
        { duration: '30s', target: 0 }, // Ramp down
    ],
};

export default function () {
    let res = http.post('http://localhost:8080/api/v1/processes', JSON.stringify({
        processDefinitionId: 'order-approval'
    }), {
        headers: { 'Content-Type': 'application/json' }
    });
    check(res, {
        'status is 200': (r) => r.status === 200,
        'response time < 500ms': (r) => r.timings.duration < 500,
    });
}
```

### 36.6 Chaos Tests

**Purpose:** Validate the system's resilience to infrastructure failures.

**Implementation:**
- **Chaos Mesh:** Kubernetes-native chaos engineering.
- **Gremlin:** Chaos engineering platform with pre-built experiments.
- **AWS Fault Injection Simulator:** AWS-native chaos engineering service.

**Chaos Experiments:**
- **Pod Kill:** Kill a random pod and observe recovery.
- **Node Down:** Simulate a Kubernetes node failure.
- **Network Partition:** Introduce network latency between services.
- **Kafka Broker Failure:** Simulate a Kafka broker failure.
- **Database Failover:** Simulate a database primary failover.
- **Certificate Expiry:** Simulate certificate expiry and auto-renewal.

**Chaos Test Workflow:**
1. Deploy the application to a test environment (Staging).
2. Inject a failure (e.g., kill a pod).
3. Observe the system's response (recovery time, error rate, data loss).
4. Validate that the system self-heals.
5. Generate a chaos test report.

---

## Chapter 37: Capacity Planning & Autoscaling

### 37.1 Capacity Planning Overview

**Purpose:** Predict future resource requirements based on growth trends and ensure the system meets performance targets.

**Capacity Planning Process:**
1. **Monitor:** Collect historical usage data (CPU, memory, request rates, throughput).
2. **Forecast:** Predict future usage based on historical trends and business projections.
3. **Scale:** Adjust capacity to meet forecasted demand.
4. **Review:** Continuously review and refine the capacity plan.

### 37.2 Horizontal Pod Autoscaling (HPA)

**Purpose:** Automatically scale the number of pods based on metrics (CPU, memory, custom metrics).

**Implementation:**
- **Kubernetes HPA:** Built-in autoscaling based on CPU and memory.
- **KEDA:** Kubernetes-based event-driven autoscaling (scale based on Kafka lag, queue length, etc.).

**HPA Configuration:**

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: bpmn-engine-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: bpmn-engine
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

**KEDA (Event-Driven Scaling):**

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: kafka-consumer-scaler
spec:
  scaleTargetRef:
    name: bpmn-engine-consumer
  triggers:
  - type: kafka
    metadata:
      topic: ordering.process_events
      lagThreshold: "100"
      bootstrapServers: "kafka-cluster:9092"
```

### 37.3 Vertical Pod Autoscaling (VPA)

**Purpose:** Automatically adjust pod resource requests (CPU, memory) based on usage.

**Implementation:**
- **Kubernetes VPA:** Built-in vertical autoscaling (recommends resource requests).
- **StormForge:** Advanced vertical autoscaling with performance and cost optimization.

**VPA Configuration:**

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: bpmn-engine-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: bpmn-engine
  updatePolicy:
    updateMode: "Off" # "Off", "Initial", "Recreate", "Auto"
```

**Note:** VPA is used for recommendations, not for automatic updates (in production). HPA is used for automatic scaling.

### 37.4 Cluster Autoscaler

**Purpose:** Automatically scale the worker nodes in the Kubernetes cluster based on pending pods.

**Implementation:**
- **AWS Cluster Autoscaler:** AWS managed node groups with cluster autoscaler.
- **Karpenter:** Modern node autoscaler with cost-aware scheduling.

**Karpenter Features:**
- **Cost-Aware:** Karpenter chooses the cheapest instance type that satisfies the pod's resource requirements.
- **Provisioning:** Karpenter provisions new nodes automatically.
- **De-provisioning:** Karpenter de-provisions idle nodes.

**Karpenter Configuration:**

```yaml
apiVersion: karpenter.sh/v1alpha5
kind: Provisioner
metadata:
  name: default
spec:
  labels:
    type: karpenter
  requirements:
    - key: kubernetes.io/arch
      operator: In
      values: [amd64, arm64]
    - key: karpenter.sh/capacity-type
      operator: In
      values: [on-demand, spot]
  limits:
    resources:
      cpu: 1000
      memory: 4000Gi
  ttlSecondsUntilExpired: 86400
  providerRef:
    name: aws
```

### 37.5 Capacity Forecasting

**Purpose:** Predict future resource requirements based on growth trends.

**Tools:**
- **Prometheus + Grafana:** Use Prometheus for metrics collection and Grafana for visualization and forecasting.
- **Prophet:** Facebook's open-source forecasting tool.
- **Custom ML Models:** Use machine learning models to predict future usage.

**Capacity Forecasting Workflow:**
1. Collect historical metrics (CPU, memory, request rates) from Prometheus.
2. Use Prophet or a custom ML model to forecast future usage.
3. Generate capacity recommendations (e.g., "increase CPU requests by 20% in the next 3 months").
4. Adjust autoscaling configurations (HPA, VPA, Cluster Autoscaler) based on the forecast.

---

## Chapter 38: Scheduling, Cron Jobs, and Deferred Execution

### 38.1 Distributed Scheduling Overview

**Purpose:** Execute scheduled jobs (cron jobs) and deferred tasks (delayed execution) in a distributed environment with exactly-once semantics.

**Use Cases:**
- **Cron Jobs:** Daily batch jobs (e.g., process mining export, data archival, report generation).
- **Deferred Execution:** Execute a task after a specific delay (e.g., 30 minutes after order creation, send a reminder).
- **Scheduled Workflows:** Start a BPMN process on a schedule (e.g., every Monday at 9 AM).

### 38.2 Distributed Cron Jobs

**Purpose:** Run a job exactly once across a cluster on a defined schedule.

**Implementation:**

| Environment | Adapter | Description |
| :--- | :--- | :--- |
| **Development** | `InMemoryScheduler` | In-memory scheduler for development and testing. |
| **Production** | `QuartzScheduler` / `Temporal` | Distributed scheduler with high availability and failover. |

**Kubernetes CronJob (Alternative):**

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: process-mining-export
spec:
  schedule: "0 1 * * *" # Daily at 1 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: exporter
            image: platform/process-mining-exporter:latest
          restartPolicy: OnFailure
```

**Limitations of Kubernetes CronJob:**
- No distributed locking (multiple pods may start the same job).
- No retry or dead-letter queue.
- No monitoring of job execution.

**Quartz Scheduler:**

```csharp
[DisallowConcurrentExecution]
public class ProcessMiningExportJob : IJob
{
    public async Task Execute(IJobExecutionContext context)
    {
        await _exporter.ExportXesLogsAsync();
    }
}
```

**Configuration:**

```json
"QuartzOptions": {
    "Database": "quartz",
    "InstanceId": "AUTO",
    "JobStore": {
        "Type": "Quartz.Impl.AdoJobStore.JobStoreTX",
        "DriverDelegateType": "Quartz.Impl.AdoJobStore.PostgreSQLDelegate",
        "DataSource": "quartz",
        "TablePrefix": "QRTZ_"
    }
}
```

### 38.3 Deferred Execution (Delayed Jobs)

**Purpose:** Execute a task after a specific delay, not on a cron schedule.

**Use Cases:**
- **Timer Events in BPMN:** Start a timer event after a specific duration.
- **Reminders:** Send a reminder 30 minutes after an order is placed.
- **Expiry:** Expire a session after 60 minutes of inactivity.

**Implementation:**

| Environment | Adapter | Description |
| :--- | :--- | :--- |
| **Development** | `InMemoryTimerScheduler` | In-memory timer scheduler for development and testing. |
| **Production** | `Temporal` / `Quartz` | Durable timer scheduler with persistence and failover. |

**Timer Scheduler Port:**

```csharp
public interface ITimerScheduler
{
    Task<string> ScheduleAsync(string jobId, DateTimeOffset fireTime, IDictionary<string, object> payload, CancellationToken ct);
    Task CancelAsync(string jobId, CancellationToken ct);
    Task<bool> ExistsAsync(string jobId, CancellationToken ct);
}
```

**Temporal for Deferred Execution:**

```csharp
[Workflow]
public interface IDeferredWorkflow
{
    [WorkflowMethod]
    Task<string> ExecuteAsync(string jobId, string payload, TimeSpan delay);
}

[Activity]
public interface IDeferredActivity
{
    Task ExecuteAsync(string payload);
}

public class DeferredWorkflow : IDeferredWorkflow
{
    public async Task<string> ExecuteAsync(string jobId, string payload, TimeSpan delay)
    {
        await Workflow.SleepAsync(delay);
        await Workflow.ExecuteActivityAsync<IDeferredActivity>(a => a.ExecuteAsync(payload));
        return "completed";
    }
}
```

**Timer Scheduling in BPMN Engine:**
- The BPMN Engine processes a timer event and schedules a deferred task.
- The `ITimerScheduler` schedules the task to fire at the specified time.
- When the timer fires, the BPMN Engine is invoked to resume the process.

### 38.4 Exactly-Once Job Execution

**Challenge:** Ensure that a job is executed exactly once, even if the scheduler restarts or a pod fails.

**Solutions:**
- **Leader Election:** Ensure that only one pod (the leader) executes the scheduled jobs.
- **Idempotent Jobs:** Jobs are idempotent, so duplicate execution has no side effects.
- **Job State Table:** Track job execution state in a database (e.g., "pending", "running", "completed").

**Leader Election for Schedulers:**
- The scheduler component (e.g., Quartz) uses `IDistributedLock` to acquire a lease on the "leader" lock.
- Only the leader pod executes the scheduled jobs.
- If the leader pod fails, another pod acquires the lock and becomes the leader.

### 38.5 Job Monitoring and Observability

**Purpose:** Monitor job runs, view history, retry failures, and alert.

**Implementation:**
- **Job Dashboard:** A dashboard (Grafana) showing job runs (status, duration, error messages).
- **Job Logs:** Logs for each job run (structured logs with correlation IDs).
- **Job Alerts:** Alerts for job failures, job delays, or job runtime exceeding thresholds.
- **Job Metrics:** Metrics for job execution (number of runs, success rate, duration).

**Job Metrics:**

| Metric | Type | Description |
| :--- | :--- | :--- |
| `job_runs_total` | Counter | Number of job executions per job type, status. |
| `job_duration_seconds` | Histogram | Duration of job execution per job type. |
| `job_failures_total` | Counter | Number of job failures per job type. |
| `job_lag_seconds` | Gauge | Delay between scheduled and actual job execution. |

---

# PART 8: CONTENT, KNOWLEDGE & AI PIPELINES

---

## Chapter 39: Unified Document Abstraction

### 39.1 Architecture Overview

The Unified Document Abstraction layer provides a canonical representation for documents and artifacts across all formats. This abstraction enables consistent processing, transformation, and generation of content regardless of the underlying file format.

**Core Capabilities:**

- **Parse:** Extract structured data and metadata from documents.
- **Render:** Generate documents from templates and data.
- **Transform:** Convert between formats.
- **Validate:** Validate documents against schemas or business rules.
- **Chunk:** Split large documents into semantically coherent chunks.
- **Embed:** Compute vector embeddings for text chunks.

### 39.2 Unified Document Model

**Purpose:** Represent any document format as a common, structured, annotated object model.

**Canonical Document Model:**

```csharp
public class CanonicalDocument
{
    public string Id { get; set; }
    public string Title { get; set; }
    public string Author { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime ModifiedAt { get; set; }
    public string Format { get; set; } // "docx", "pdf", "html", etc.
    public IList<Section> Sections { get; set; }
    public IList<Table> Tables { get; set; }
    public IList<Image> Images { get; set; }
    public IList<Field> Fields { get; set; } // Key-value pairs for structured data
    public IDictionary<string, object> Metadata { get; set; }
}

public class Section
{
    public string Id { get; set; }
    public string Title { get; set; }
    public string Content { get; set; }
    public string ContentType { get; set; } // "text", "markdown", "html", "xml"
    public int Level { get; set; } // Heading level (1-6)
    public IList<Section> SubSections { get; set; }
}

public class Table
{
    public string Id { get; set; }
    public string Title { get; set; }
    public IList<string> Headers { get; set; }
    public IList<IList<object>> Rows { get; set; }
}

public class Image
{
    public string Id { get; set; }
    public string Name { get; set; }
    public byte[] Data { get; set; }
    public string MimeType { get; set; }
    public string Caption { get; set; }
}
```

### 39.3 Document Parsing Adapters

**Purpose:** Parse documents from various formats into the canonical document model.

**Implementation:**

| Format | Adapter | Description |
| :--- | :--- | :--- |
| **DOCX / XLSX / PPTX** | `OpenXmlParser` | Uses DocumentFormat.OpenXml (Microsoft Open XML SDK). |
| **PDF** | `PdfParser` | Uses PdfPig or iTextSharp for text extraction and structure parsing. |
| **HTML** | `HtmlParser` | Uses AngleSharp (HTML5 parser). |
| **Markdown** | `MarkdownParser` | Uses Markdig for Markdown parsing. |
| **CSV / TSV** | `CsvParser` | Uses CsvHelper or custom parser. |
| **JSON / XML** | `JsonParser` / `XmlParser` | Uses System.Text.Json and System.Xml. |
| **CAD (STEP, IGES, STL)** | `CadParser` | Uses Open Cascade or IfcOpenShell. |
| **Image (PNG, JPEG)** | `ImageParser` | Uses ImageSharp for metadata extraction and OCR (Tesseract). |
| **Audio / Video** | `MediaParser` | Uses FFmpeg for metadata extraction; Whisper for ASR. |

**Parser Interface:**

```csharp
public interface IDocumentParser
{
    Task<CanonicalDocument> ParseAsync(Stream stream, CancellationToken ct);
    bool Supports(string format);
}
```

### 39.4 Document Generation Adapters

**Purpose:** Generate documents from templates and data.

**Implementation:**

| Format | Adapter | Description |
| :--- | :--- | :--- |
| **DOCX** | `DocxGenerator` | Uses DocumentFormat.OpenXml to populate DOCX templates. |
| **PDF** | `PdfGenerator` | Uses QuestPDF or PuppeteerSharp for PDF generation. |
| **HTML** | `HtmlRenderer` | Uses Razor or Handlebars for HTML generation. |
| **Markdown** | `MarkdownGenerator` | Custom Markdown writer. |
| **Excel (XLSX)** | `ExcelGenerator` | Uses DocumentFormat.OpenXml to generate Excel spreadsheets. |
| **PPTX** | `PptxGenerator` | Uses DocumentFormat.OpenXml to generate PowerPoint presentations. |

**Generator Interface:**

```csharp
public interface IDocumentGenerator
{
    Task<Stream> GenerateAsync(CanonicalDocument document, string templateId, IDictionary<string, object> data, CancellationToken ct);
    bool Supports(string format);
}
```

### 39.5 Document Transformation

**Purpose:** Transform documents between formats.

**Implementation:**

| Transformation | Adapter | Description |
| :--- | :--- | :--- |
| **DOCX → PDF** | `DocxToPdfTransformer` | Uses LibreOffice headless or QuestPDF. |
| **HTML → DOCX** | `HtmlToDocxTransformer` | Uses HtmlToOpenXml or custom converter. |
| **Markdown → HTML** | `MarkdownToHtmlTransformer` | Uses Markdig. |
| **JSON → CSV** | `JsonToCsvTransformer` | Custom transformer. |
| **PDF → Text** | `PdfToTextTransformer` | Uses PdfPig. |

**Transformer Interface:**

```csharp
public interface IDocumentTransformer
{
    Task<Stream> TransformAsync(Stream input, string sourceFormat, string targetFormat, CancellationToken ct);
    bool Supports(string sourceFormat, string targetFormat);
}
```

### 39.6 Document Chunking

**Purpose:** Split large documents into semantically coherent chunks for RAG ingestion, embedding, and search.

**Chunking Strategies:**
- **Fixed-Size Chunking:** Split by token count or character count with overlap.
- **Paragraph Chunking:** Split by paragraph boundaries.
- **Sentence Chunking:** Split by sentence boundaries.
- **Semantic Chunking:** Use embeddings to detect semantic boundaries.
- **Document-Structure Chunking:** Split by headings, sections, or tables.

**Implementation:**

```csharp
public interface IDocumentChunker
{
    Task<IList<Chunk>> ChunkAsync(CanonicalDocument document, ChunkingOptions options, CancellationToken ct);
}

public class Chunk
{
    public string Id { get; set; }
    public string Content { get; set; }
    public int Order { get; set; }
    public string DocumentId { get; set; }
    public string SectionId { get; set; }
    public IDictionary<string, object> Metadata { get; set; }
}
```

### 39.7 Document Embedding

**Purpose:** Compute vector embeddings for text chunks for semantic search and RAG.

**Implementation:**

| Environment | Adapter | Description |
| :--- | :--- | :--- |
| **Development** | `LocalEmbeddingGenerator` | Uses ONNX Runtime with a small embedding model. |
| **Production** | `OpenAIEmbeddingGenerator` | Uses OpenAI's text-embedding-3-small or text-embedding-3-large. |

**Embedding Interface:**

```csharp
public interface IEmbeddingGenerator
{
    Task<float[]> GenerateEmbeddingAsync(string text, CancellationToken ct);
    Task<IList<float[]>> GenerateEmbeddingsAsync(IList<string> texts, CancellationToken ct);
}
```

### 39.8 Artifact Storage

**Purpose:** Store and retrieve artifacts (documents, images, CAD files, etc.) with versioning, lifecycle policies, and access control.

**Implementation:**

| Environment | Adapter | Description |
| :--- | :--- | :--- |
| **Development** | `LocalFileArtifactStorage` | Local file system storage. |
| **Test / Staging** | `MinioArtifactStorage` | MinIO container (S3-compatible). |
| **Production** | `S3ArtifactStorage` | AWS S3 or MinIO cluster with cross-region replication. |

**Artifact Storage Interface:**

```csharp
public interface IArtifactStorage
{
    Task<string> StoreAsync(Stream stream, string fileName, IDictionary<string, object> metadata, CancellationToken ct);
    Task<Stream> RetrieveAsync(string artifactId, CancellationToken ct);
    Task DeleteAsync(string artifactId, CancellationToken ct);
    Task<IList<ArtifactMetadata>> ListAsync(string prefix, CancellationToken ct);
}
```

---

## Chapter 40: Retrieval-Augmented Generation (RAG) Pipelines

### 40.1 RAG Architecture Overview

**Purpose:** Ground LLM responses in enterprise knowledge by retrieving relevant documents from a knowledge base and providing them as context to the LLM.

**RAG Pipeline Steps:**
1. **Ingestion:** Documents are ingested from various sources (file uploads, S3, databases, web).
2. **Parsing:** Documents are parsed into the canonical document model.
3. **Chunking:** Documents are split into coherent chunks.
4. **Embedding:** Chunks are converted to vector embeddings.
5. **Storage:** Chunks and embeddings are stored in a vector database.
6. **Retrieval:** On query, relevant chunks are retrieved via semantic search.
7. **Generation:** Retrieved chunks are provided as context to the LLM for answer generation.

### 40.2 Ingestion Pipeline

**Purpose:** Ingest documents from various sources into the RAG system.

**Ingestion Sources:**
- **File Uploads:** Users upload documents via the API or UI.
- **S3 / Object Storage:** Documents are automatically ingested from S3 buckets.
- **Databases:** Documents are extracted from relational databases.
- **Web:** Documents are crawled from internal or external websites.
- **Email:** Documents are extracted from email attachments.
- **Kafka:** Documents are streamed via Kafka.

**Implementation:**

| Environment | Adapter | Description |
| :--- | :--- | :--- |
| **Development** | `InMemoryIngestionPipeline` | Processes documents in-memory. |
| **Production** | `KafkaIngestionPipeline` | Ingestion tasks are processed via Kafka (async, parallel). |

**Ingestion Workflow:**

```csharp
public class IngestionOrchestrator
{
    private readonly IDocumentParser _parser;
    private readonly IDocumentChunker _chunker;
    private readonly IEmbeddingGenerator _embedder;
    private readonly IVectorStore _vectorStore;
    private readonly IArtifactStorage _storage;

    public async Task IngestAsync(Stream documentStream, string fileName, CancellationToken ct)
    {
        // 1. Parse document
        var document = await _parser.ParseAsync(documentStream, ct);
        
        // 2. Store original document
        var artifactId = await _storage.StoreAsync(documentStream, fileName, document.Metadata, ct);
        
        // 3. Chunk document
        var chunks = await _chunker.ChunkAsync(document, new ChunkingOptions { ChunkSize = 500, Overlap = 50 }, ct);
        
        // 4. Generate embeddings
        var texts = chunks.Select(c => c.Content).ToList();
        var embeddings = await _embedder.GenerateEmbeddingsAsync(texts, ct);
        
        // 5. Store chunks and embeddings in vector store
        var vectors = chunks.Zip(embeddings, (chunk, embedding) => new Vector
        {
            Id = chunk.Id,
            Embedding = embedding,
            Metadata = new Dictionary<string, object>
            {
                ["documentId"] = artifactId,
                ["sectionId"] = chunk.SectionId,
                ["order"] = chunk.Order,
                ["content"] = chunk.Content
            }
        }).ToList();
        
        await _vectorStore.UpsertAsync(vectors, ct);
    }
}
```

### 40.3 Retrieval Pipeline

**Purpose:** Retrieve the most relevant chunks from the vector store based on a user query.

**Retrieval Strategies:**
- **Dense Retrieval:** Use embeddings and cosine similarity (primary).
- **Sparse Retrieval:** Use keyword search (BM25) (hybrid search).
- **Hybrid Retrieval:** Combine dense and sparse retrieval (reciprocal rank fusion).
- **Re-ranking:** Use a cross-encoder or LLM to re-rank retrieved chunks.

**Implementation:**

```csharp
public class RetrievalPipeline
{
    private readonly IVectorStore _vectorStore;
    private readonly IEmbeddingGenerator _embedder;
    private readonly ILLMService _llm;

    public async Task<RetrievalResult> RetrieveAsync(string query, int topK, CancellationToken ct)
    {
        // 1. Generate query embedding
        var queryEmbedding = await _embedder.GenerateEmbeddingAsync(query, ct);
        
        // 2. Retrieve top K chunks
        var results = await _vectorStore.SearchAsync(queryEmbedding, topK, ct);
        
        // 3. Optionally re-rank results
        var reRanked = await _reRanker.ReRankAsync(query, results, ct);
        
        return new RetrievalResult
        {
            Query = query,
            Chunks = reRanked.Select(r => r.Chunk).ToList(),
            Sources = reRanked.Select(r => r.Metadata["documentId"].ToString()).Distinct().ToList()
        };
    }
}
```

### 40.4 Generation Pipeline

**Purpose:** Generate an answer using the retrieved chunks as context.

**Implementation:**

```csharp
public class GenerationPipeline
{
    private readonly ILLMService _llm;
    private readonly IPromptTemplate _promptTemplate;

    public async Task<GenerationResult> GenerateAsync(string query, RetrievalResult retrievalResult, CancellationToken ct)
    {
        // 1. Construct prompt with retrieved chunks
        var prompt = _promptTemplate.Render(new
        {
            query = query,
            context = string.Join("\n\n", retrievalResult.Chunks.Select(c => c.Content))
        });
        
        // 2. Generate response
        var response = await _llm.GenerateAsync(prompt, ct);
        
        return new GenerationResult
        {
            Query = query,
            Answer = response.Text,
            Sources = retrievalResult.Sources,
            TokensUsed = response.TokensUsed
        };
    }
}
```

### 40.5 Vector Store Selection

**Purpose:** Store and query vector embeddings.

**Implementation:**

| Environment | Adapter | Description |
| :--- | :--- | :--- |
| **Development** | `InMemoryVectorStore` | In-memory vector store (local Lucene index). |
| **Test / Staging** | `MilvusClient` | Milvus container with test data. |
| **Production** | `MilvusClient` | Milvus cluster with high availability. |

**Vector Store Interface:**

```csharp
public interface IVectorStore
{
    Task UpsertAsync(IList<Vector> vectors, CancellationToken ct);
    Task<IList<SearchResult>> SearchAsync(float[] queryEmbedding, int topK, CancellationToken ct);
    Task<IList<SearchResult>> HybridSearchAsync(string query, float[] queryEmbedding, int topK, CancellationToken ct);
    Task DeleteAsync(string id, CancellationToken ct);
}
```

**Alternative Vector Stores:**

| Database | Use Case | Justification |
| :--- | :--- | :--- |
| **pgvector** | PostgreSQL extension | Simple vector search integrated with relational data. Suitable for small to medium workloads. |
| **Qdrant** | High-performance vector search | Open-source, high-performance, supports filtering and hybrid search. |
| **Weaviate** | Hybrid search (keyword + vector) | Built-in RAG capabilities, GraphQL interface. |
| **Pinecone** | Managed vector database | Cloud-native, fully managed, high availability. |

---

## Chapter 41: Knowledge Graphs, Semantic Search, and Digital Twins

### 41.1 Knowledge Graph Overview

**Purpose:** Model highly connected data, semantic relationships, and knowledge representation using graph databases.

**Use Cases:**
- **Ontology Management:** Define and manage business ontologies (OWL, RDFS).
- **Entity Resolution:** Link entities across different systems.
- **Semantic Search:** Search using relationships and context.
- **Recommendation Systems:** Recommend items based on relationships.
- **Root-Cause Analysis:** Trace dependencies and impacts.
- **Digital Twins:** Model physical assets and their relationships.

### 41.2 Graph Database Abstraction

**Implementation:**

| Environment | Adapter | Description |
| :--- | :--- | :--- |
| **Development** | `InMemoryGraphStore` | In-memory graph store (Lucene-based). |
| **Test / Staging** | `Neo4jClient` | Neo4j container. |
| **Production** | `Neo4jClient` | Neo4j cluster with causal clustering. |

**Graph Store Interface:**

```csharp
public interface IGraphStore
{
    Task<Node> CreateNodeAsync(Node node, CancellationToken ct);
    Task<Relationship> CreateRelationshipAsync(string sourceId, string targetId, string type, IDictionary<string, object> properties, CancellationToken ct);
    Task<IList<Node>> QueryNodesAsync(string cypherQuery, IDictionary<string, object> parameters, CancellationToken ct);
    Task<IList<Path>> QueryPathsAsync(string cypherQuery, IDictionary<string, object> parameters, CancellationToken ct);
    Task DeleteNodeAsync(string id, CancellationToken ct);
}
```

### 41.3 Ontology Management

**Purpose:** Define and manage business ontologies (OWL, RDFS).

**Implementation:**
- **Ontology Model:** Classes, properties, relationships, and constraints.
- **Reasoning:** Inference engine for deriving new facts.
- **Validation:** Validate instances against the ontology.

**Ontology Example:**

```json
{
  "ontology": {
    "name": "CustomerOntology",
    "version": "1.0.0",
    "classes": [
      {
        "name": "Customer",
        "properties": ["customerId", "name", "email", "phone"]
      },
      {
        "name": "Order",
        "properties": ["orderId", "orderDate", "totalAmount", "status"]
      }
    ],
    "relationships": [
      {
        "source": "Customer",
        "target": "Order",
        "type": "placed",
        "cardinality": "one-to-many"
      }
    ]
  }
}
```

### 41.4 Semantic Search

**Purpose:** Search using relationships and context, not just keywords.

**Implementation:**
- **Graph Traversal:** Use Cypher/SPARQL to traverse the graph.
- **Hybrid Search:** Combine graph traversal with vector search for context.
- **Entity Linking:** Link entities in the query to nodes in the graph.

**Semantic Search Example (Cypher):**

```cypher
MATCH (c:Customer {customerId: $customerId})
MATCH (c)-[:placed]->(o:Order)
MATCH (o)-[:contains]->(i:Item)
WHERE i.category = $category
RETURN o, i
```

### 41.5 Digital Twins

**Purpose:** Mirror physical assets in software, synchronising state, and enabling simulation and what-if analysis.

**Use Cases:**
- **IoT Device Twins:** Model IoT devices and their state (sensors, actuators).
- **Asset Twins:** Model physical assets (machines, vehicles, buildings) and their lifecycle.
- **Process Twins:** Model business processes and their execution state.
- **Organisational Twins:** Model organisational structure and relationships.

**Digital Twin Model:**

```csharp
public class DigitalTwin
{
    public string Id { get; set; }
    public string Type { get; set; } // "Device", "Asset", "Process", etc.
    public string Name { get; set; }
    public string Description { get; set; }
    public IDictionary<string, object> Properties { get; set; }
    public IList<Relationship> Relationships { get; set; }
    public IList<Event> Events { get; set; }
    public DateTime LastSyncAt { get; set; }
}
```

**Digital Twin Synchronization:**
- **Push:** IoT devices push state changes to the digital twin.
- **Poll:** The system polls devices for state changes.
- **Event-Driven:** State changes are captured via event streams (Kafka).

**Implementation:**

| Environment | Adapter | Description |
| :--- | :--- | :--- |
| **Development** | `InMemoryTwinStore` | In-memory digital twin store. |
| **Production** | `GraphTwinStore` | Digital twins stored in the graph database (Neo4j). |

### 41.6 Simulation and What-If Analysis

**Purpose:** Predict system behaviour under hypothetical conditions using the digital twin.

**Implementation:**
- **Simulation Engine:** A simulation engine (AnyLogic, Simulink, or custom) executes simulation models.
- **What-If Analysis:** Users can run scenarios and observe the predicted outcomes.
- **Optimization:** The simulation engine can be used to optimize parameters.

**Integration:**
- The simulation engine is invoked as a service (via gRPC or REST).
- Simulation results are stored in the digital twin (as "what-if" versions).
- Insights are fed back into the platform (e.g., as recommendations).

---

## Chapter 42: Model Registry (MLflow) & LLM Observability (LangSmith)

### 42.1 MLOps Overview

**Purpose:** Manage the lifecycle of machine learning models, including training, versioning, deployment, and monitoring.

**Core Components:**
1. **Experiment Tracking:** Log hyperparameters, metrics, and artifacts for every training run.
2. **Model Registry:** Version, store, and stage ML models for deployment.
3. **Model Serving:** Deploy models as scalable services.
4. **Model Monitoring:** Monitor model performance in production (drift detection, accuracy).

### 42.2 Experiment Tracking

**Purpose:** Log hyperparameters, metrics, and artifacts for every training run, enabling reproducibility and comparison.

**Implementation:**

| Environment | Adapter | Description |
| :--- | :--- | :--- |
| **Development** | `FileSystemExperimentTracker` | Logs experiments to the local file system. |
| **Production** | `MlflowExperimentTracker` | MLflow Tracking server for experiment storage. |

**Experiment Tracking Example:**

```python
import mlflow

with mlflow.start_run(run_name="xgboost_training"):
    mlflow.log_param("learning_rate", 0.1)
    mlflow.log_param("max_depth", 6)
    mlflow.log_metric("accuracy", 0.95)
    mlflow.log_metric("f1_score", 0.94)
    mlflow.log_artifact("confusion_matrix.png")
    mlflow.sklearn.log_model(model, "model")
```

### 42.3 Model Registry

**Purpose:** Version, store, and stage ML models for deployment.

**Implementation:**

| Environment | Adapter | Description |
| :--- | :--- | :--- |
| **Development** | `InMemoryModelRegistry` | In-memory model registry. |
| **Production** | `MlflowModelRegistry` | MLflow Model Registry. |

**Model Registry Interface:**

```csharp
public interface IModelRegistry
{
    Task<ModelVersion> RegisterModelAsync(string modelName, string modelPath, string version, IDictionary<string, object> metadata, CancellationToken ct);
    Task<ModelVersion> GetModelAsync(string modelName, string version, CancellationToken ct);
    Task<IList<ModelVersion>> ListModelsAsync(string modelName, CancellationToken ct);
    Task<ModelVersion> PromoteModelAsync(string modelName, string version, string stage, CancellationToken ct);
}
```

### 42.4 Model Serving

**Purpose:** Deploy models as scalable services.

**Implementation:**

| Environment | Adapter | Description |
| :--- | :--- | :--- |
| **Development** | `InMemoryModelServer` | In-memory model server for testing. |
| **Production** | `SeldonCore` | Kubernetes-native model serving with canary deployments. |

**Model Serving Interface:**

```csharp
public interface IModelServer
{
    Task<TResult> PredictAsync<TInput, TResult>(string modelName, string version, TInput input, CancellationToken ct);
    Task DeployModelAsync(string modelName, string version, DeploymentConfiguration config, CancellationToken ct);
}
```

### 42.5 LLM Observability

**Purpose:** Monitor and evaluate LLM-based agents and workflows.

**Key Metrics:**
- **Latency:** Time to generate a response.
- **Tokens Used:** Number of input and output tokens.
- **Cost:** Cost per request (tokens * price).
- **Quality:** Accuracy, relevance, hallucinations.
- **Safety:** Guardrail violations.

**Implementation:**

| Environment | Adapter | Description |
| :--- | :--- | :--- |
| **Development** | `ConsoleLLMObserver` | Logs LLM interactions to the console. |
| **Production** | `LangSmithLLMObserver` | LangSmith for LLM observability. |

**LLM Observability Example:**

```csharp
[TraceSpan]
public async Task<string> GenerateAsync(string prompt)
{
    using var span = _tracer.StartSpan("LLM.Generate");
    span.SetAttribute("prompt", prompt);
    span.SetAttribute("model", "gpt-4");
    
    var response = await _llmService.GenerateAsync(prompt);
    
    span.SetAttribute("tokens_used", response.TokensUsed);
    span.SetAttribute("cost", response.Cost);
    span.SetAttribute("safety_violation", response.SafetyViolation);
    
    return response.Text;
}
```

### 42.6 Prompt Versioning

**Purpose:** Track which prompt template and model produced which outputs.

**Implementation:**

| Environment | Adapter | Description |
| :--- | :--- | :--- |
| **Development** | `FileSystemPromptRegistry` | Stores prompts in the local file system. |
| **Production** | `GitPromptRegistry` | Stores prompts in the Model Repository (Git). |

**Prompt Registry Interface:**

```csharp
public interface IPromptRegistry
{
    Task<PromptVersion> GetPromptAsync(string promptId, string version, CancellationToken ct);
    Task<PromptVersion> GetLatestPromptAsync(string promptId, CancellationToken ct);
    Task<PromptVersion> RegisterPromptAsync(string promptId, string template, IDictionary<string, object> metadata, CancellationToken ct);
}
```

---

## Chapter 43: Synthetic Data Generation & Test Data Management

### 43.1 Synthetic Data Generation Overview

**Purpose:** Create realistic but artificial data for testing, training, and privacy-preserving analytics.

**Use Cases:**
- **Testing:** Generate realistic test data for integration and performance tests.
- **Development:** Provide realistic data for local development environments.
- **Training:** Generate synthetic training data for machine learning models.
- **Privacy:** Generate data that preserves the statistical properties of production data without exposing PII.

### 43.2 Rule-Based Generation

**Purpose:** Produce data that matches defined patterns, constraints, and relationships.

**Implementation:**

| Environment | Adapter | Description |
| :--- | :--- | :--- |
| **Development** | `FakerDataGenerator` | Uses the Faker library for realistic data. |
| **Production** | `SynthDataGenerator` | Uses Synth (open-source synthetic data generator). |

**Synthetic Data Configuration:**

```json
{
  "schema": {
    "name": "Customer",
    "fields": [
      {
        "name": "customerId",
        "type": "uuid"
      },
      {
        "name": "firstName",
        "type": "firstName"
      },
      {
        "name": "lastName",
        "type": "lastName"
      },
      {
        "name": "email",
        "type": "email"
      },
      {
        "name": "phone",
        "type": "phoneNumber"
      },
      {
        "name": "address",
        "type": "address"
      },
      {
        "name": "birthDate",
        "type": "date",
        "constraints": {
          "min": "1950-01-01",
          "max": "2010-01-01"
        }
      }
    ]
  },
  "count": 1000,
  "seed": 42
}
```

### 43.3 ML-Based Generation

**Purpose:** Learn the statistical distribution of real data and generate new samples.

**Implementation:**

| Environment | Adapter | Description |
| :--- | :--- | :--- |
| **Development** | `InMemoryMLGenerator` | Simulates ML-based generation. |
| **Production** | `GretelDataGenerator` | Uses Gretel or Mostly AI for ML-based generation. |

**ML-Based Generation Workflow:**
1. **Training:** Train a generative model (GAN, VAE, or LLM) on production data.
2. **Generation:** Generate new samples from the trained model.
3. **Validation:** Validate the generated data (statistical properties, referential integrity).

### 43.4 Test Data Management

**Purpose:** Provision, refresh, and clean up test datasets on-demand for CI/CD.

**Implementation:**

| Environment | Adapter | Description |
| :--- | :--- | :--- |
| **Development** | `InMemoryTestDataManager` | In-memory test data manager. |
| **Production** | `TonicTestDataManager` | Tonic for test data management. |

**Test Data Management Workflow:**
1. **Data Provisioning:** A developer requests a test dataset via the API.
2. **Data Generation:** The system generates a synthetic dataset (or masks a production subset).
3. **Data Delivery:** The dataset is delivered as a database backup, CSV file, or API response.
4. **Data Cleanup:** The dataset is cleaned up after a TTL expires.

### 43.5 Data Anonymization for Production Replicas

**Purpose:** Replace real PII with realistic synthetic data while preserving format and relationships.

**Implementation:**

| Environment | Adapter | Description |
| :--- | :--- | :--- |
| **Development** | `InMemoryAnonymizer` | In-memory anonymization. |
| **Production** | `DelphixAnonymizer` | Delphix for data anonymization. |

**Anonymization Rules:**

| Field | Anonymization Rule | Description |
| :--- | :--- | :--- |
| **firstName** | `firstName` | Generate a realistic first name. |
| **lastName** | `lastName` | Generate a realistic last name. |
| **email** | `email` | Generate a realistic email address. |
| **phone** | `phoneNumber` | Generate a realistic phone number. |
| **address** | `address` | Generate a realistic address. |
| **creditCard** | `format-preserving-encryption` | Encrypt while preserving the format. |
| **birthDate** | `shift` | Shift the date by a random offset. |

---

## Document Conclusion

This Architecture Document defines the complete architectural standard for the Agentic, Model-Driven, Polymorphic Distributed BPMS platform. It covers 65 distinct capability domains across eight logical parts:

1. **Foundations & The Golden Thread:** The system identity, guiding principles, Polymorphic Runtime engine, and multi-stage environment strategy.
2. **Core Runtime & Domain Orchestration:** The Modular Monolith, Clean Architecture, Engine Ecosystem, declarative models, distributed transactions, and service discovery.
3. **Data Fabric & Event Streaming:** Multi-model persistence, event streaming, CDC, data governance, and archival.
4. **API Management & Agentic Mesh:** Northbound exposure, southbound integration, agentic systems (A2A, MCP), skills engines, and UI/BFF.
5. **Security, Identity, and Compliance:** Zero-trust architecture, IAM, secrets management, HSM, compliance automation, and quantum-safe cryptography.
6. **Cloud-Native Infrastructure & Operations:** Kubernetes, service mesh, IaC, multi-stage environments, FinOps, disaster recovery, and multi-cloud.
7. **Observability, Testing & Resilience:** Observability (logs, metrics, traces, profiling), BAM, process mining, resilience engineering, testing strategy, capacity planning, and scheduling.
8. **Content, Knowledge & AI Pipelines:** Document abstraction, RAG pipelines, knowledge graphs, digital twins, MLOps, and synthetic data.

The architecture is unified by a single "Golden Thread": the **Polymorphic Runtime** engine, which enables the same compiled binary to run identically across development, test, staging, and production environments, with its runtime topology defined purely by configuration. This ensures consistency, reduces complexity, and accelerates delivery while maintaining enterprise-grade security, scalability, and resilience.

All architecture decisions, patterns, and tool selections are documented in the appendices, which provide detailed configuration schemas, code samples, security checklists, and tool selection matrices.

---

## Appendices

### Appendix A: RuntimeTopology JSON Schemas

**Development Schema:**

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
  "ModelRepositoryOptions": {
    "Type": "FileSystem",
    "BasePath": "./Models"
  },
  "ArtifactStorageOptions": {
    "Type": "LocalFile",
    "BasePath": "./Artifacts"
  }
}
```

**Production Schema:**

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
    "ClientId": "platform-producer"
  },
  "EtcdOptions": {
    "Endpoints": ["etcd-1:2379", "etcd-2:2379", "etcd-3:2379"],
    "LeaseTtlSeconds": 30
  },
  "RedisOptions": {
    "ConnectionString": "redis-cluster:6379"
  },
  "ConsulOptions": {
    "Address": "consul-server:8500",
    "Datacenter": "dc1"
  },
  "DatabaseOptions": {
    "ConnectionString": "${DB_CONNECTION_STRING}",
    "Provider": "SqlServer"
  },
  "ModelRepositoryOptions": {
    "Type": "GitLabRegistry",
    "BaseUrl": "https://model-registry.internal/api/v4"
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

### Appendix B: Engine API Reference & Code Samples

**BPMN Engine API:**

```csharp
public interface IBpmnEngine
{
    Task<BpmnExecutionResult> ExecuteAsync(BpmnModel model, BpmnExecutionContext context, CancellationToken ct);
    Task<BpmnExecutionResult> ResumeAsync(string processInstanceId, BpmnExecutionEvent @event, CancellationToken ct);
}

public class BpmnExecutionResult
{
    public IList<BpmnCommand> Commands { get; set; }
    public IList<DomainEvent> Events { get; set; }
    public bool IsComplete { get; set; }
    public string Error { get; set; }
}
```

**DMN Engine API:**

```csharp
public interface IDmnEngine
{
    Task<DmnExecutionResult> EvaluateAsync(DmnModel model, DmnExecutionContext context, CancellationToken ct);
}

public class DmnExecutionResult
{
    public object Output { get; set; }
    public IList<DmnDecision> Decisions { get; set; }
    public bool IsComplete { get; set; }
    public string Error { get; set; }
}
```

### Appendix C: Security Hardening Checklist

- [ ] **Network Policies:** Default-deny ingress/egress. Allow only explicitly required traffic.
- [ ] **mTLS:** STRICT mode enabled for all service-to-service communication.
- [ ] **Authentication:** OAuth2/OIDC for end-user authentication. SPIFFE/SPIRE for workload identity.
- [ ] **Authorization:** OPA policies enforced at API Gateway and Service Mesh levels.
- [ ] **Secrets:** Vault for all secrets. Dynamic credentials with short TTLs. No secrets in environment variables.
- [ ] **TLS Certificates:** cert-manager for automatic certificate issuance and renewal.
- [ ] **Audit Logging:** All actions are logged immutably. Audit logs are shipped to SIEM.
- [ ] **Image Scanning:** Trivy or Grype for vulnerability scanning of container images.
- [ ] **SBOM:** Software Bill of Materials generated for all container images.
- [ ] **Pod Security:** Pod Security Standards (PSS) enforced at the cluster level.
- [ ] **Network Policy:** Cilium or Calico for Layer 7 network policies.
- [ ] **Data Encryption:** Encryption at rest for all databases and object storage.
- [ ] **Data Masking:** Sensitive data masked in non-production environments.
- [ ] **Quantum-Safe:** Hybrid cryptography (classical + PQC) for long-lived secrets.
- [ ] **HSM:** HSM for root CA, JWT signing, and encryption keys.
- [ ] **Compliance Automation:** Vanta/Drata for continuous compliance monitoring.

### Appendix D: Tool Selection Matrix (Domains vs. Tools)

#### Brief Table
| Domain | Primary Tool | Alternative(s) |
| :--- | :--- | :--- |
| **Orchestration** | Kubernetes (EKS/AKS/GKE) | OpenShift, Rancher |
| **Service Mesh** | Istio | Linkerd, Consul Connect |
| **Service Discovery** | Consul | etcd, Kubernetes DNS |
| **Messaging** | Apache Kafka | Apache Pulsar, RabbitMQ |
| **API Gateway** | YARP | Kong, Traefik, Envoy |
| **BPMN Engine** | Elsa Workflows | Camunda (via integration) |
| **DMN Engine** | Custom (Microsoft RulesEngine) | Drools (via integration) |
| **State Machine** | Stateless | Appccelerate State Machine |
| **Distributed Locking** | etcd | Redis (Redlock) |
| **Distributed Cache** | Redis | Hazelcast |
| **Database (Relational)** | PostgreSQL | CockroachDB |
| **Database (Document)** | MongoDB | Cosmos DB |
| **Database (Graph)** | Neo4j | Amazon Neptune |
| **Database (Vector)** | Milvus | Qdrant, pgvector |
| **Database (Time-Series)** | TimescaleDB | InfluxDB |
| **Object Storage** | MinIO / S3 | Azure Blob Storage, GCS |
| **Secrets Management** | HashiCorp Vault | AWS Secrets Manager |
| **HSM** | AWS CloudHSM | Azure Dedicated HSM |
| **IAM** | Keycloak | Okta, Auth0 |
| **Authorization** | Open Policy Agent (OPA) | Casbin, Cedar |
| **Observability (Logs)** | Elasticsearch + Fluentd | Loki + Promtail |
| **Observability (Metrics)** | Prometheus + Grafana | Datadog, New Relic |
| **Observability (Traces)** | Tempo / Jaeger | AWS X-Ray |
| **Continuous Profiling** | Pyroscope | Parca |
| **IaC** | Terraform | Crossplane, Pulumi |
| **CI/CD** | GitLab CI / GitHub Actions | Jenkins, Argo Workflows |
| **GitOps** | ArgoCD | Flux |
| **Testing (Load)** | k6 | Locust, JMeter |
| **Testing (Chaos)** | Chaos Mesh | Gremlin |
| **Testing (Contract)** | Pact | Spring Cloud Contract |
| **Document Processing** | DocumentFormat.OpenXml + QuestPDF | Aspose (commercial) |
| **RAG** | LangChain + Milvus | LlamaIndex + Qdrant |
| **MLOps** | MLflow | Weights & Biases |
| **LLM Observability** | LangSmith | Arize Phoenix |

---

### DECISION MATRIX: .NET LIBRARY SELECTION FOR THE POLYMORPHIC DISTRIBUTED BPMS PLATFORM

This document provides a comprehensive decision matrix for selecting .NET open-source libraries across all 65 architectural domains. Each section evaluates available options against selection criteria including open-source status, community adoption (GitHub stars, NuGet downloads), activity (last update), feature completeness, and architectural fit. Custom development is considered as an option where no suitable library exists.

---

## Domain 1: Aspect-Oriented Programming (AOP) & Method Interception

### Requirement
Compile-time AOP for cross-cutting concerns (tracing, circuit breakers, retries, rate limiting) using .NET 10's source generator and interceptor features.

### Candidate Libraries

| Library | Approach | Stars | Downloads | Last Update | License | Key Features |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **SkyHigh.StaticProxy** | Source Generator | Not available | Not available | Active | Not specified | Compile-time method interception, lightweight, high-performance, supports .NET 10 interceptors |
| **AspectWeaver** | Source Generator (C# 12 Interceptors) | Not available | 760 total | Oct 2025 | Not specified | High-performance source generator, C# 12 Interceptor support |
| **AspectCore-Framework** | Runtime/Dynamic Proxy | 1,719 | 3.79M | ~2 years ago | Not specified | Interceptor and dynamic proxy support for Autofac, mature but runtime-based |

### Feature Comparison

| Feature | SkyHigh.StaticProxy | AspectWeaver | AspectCore-Framework |
| :--- | :--- | :--- | :--- |
| Compile-time interception | Yes | Yes | No (runtime) |
| .NET 10 Interceptor support | Yes | Yes | No |
| Zero runtime overhead | Yes | Yes | No |
| Source generator based | Yes | Yes | No |
| Mature/Stable | Emerging | Emerging | Mature |
| Community adoption | Low | Very Low | High |

### Selection Decision

**Recommended: SkyHigh.StaticProxy** with AspectWeaver as a lighter alternative.

**Rationale:**
- SkyHigh.StaticProxy provides compile-time method interception through source generators without runtime overhead. This aligns perfectly with the architecture's requirement for zero-runtime-cost AOP.
- AspectWeaver is a high-performance source generator utilizing C# 12 Interceptors but has very low adoption (~760 total downloads).
- AspectCore-Framework is mature (3.79M downloads, 1,719 stars) but uses runtime dynamic proxies, which introduces overhead not suitable for high-performance engine execution.
- .NET 10 Interceptors are a new feature that allows replacing or modifying method behavior at compile time using source generators.

**Custom Development Consideration:** Custom source generator implementation is possible but would require significant investment. Given the availability of SkyHigh.StaticProxy, custom development is not recommended.

---

## Domain 2: Mediator & CQRS (Command/Query Separation)

### Requirement
Mediator pattern implementation for Use Case orchestration, supporting in-process command/query dispatching with minimal ceremony and high performance.

### Candidate Libraries

| Library | Stars | Downloads | Last Update | License | Key Features |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Wolverine** | ~1,140 | ~20K | Active (days ago) | MIT | Source generator-based, convention-driven, built-in outbox, in-process + distributed messaging |
| **MediatR** | ~12,000+ | 2M+ | Active | Apache-2.0 | Mature, extensive ecosystem, behavior pipeline, widely adopted |
| **MassTransit** | ~5,242 | 22M+ | Active (days ago) | Apache-2.0 | Full messaging framework, includes mediator, saga support |

### Feature Comparison

| Feature | Wolverine | MediatR | MassTransit |
| :--- | :--- | :--- | :--- |
| Mediator pattern | Yes (native) | Yes (primary) | Yes (via mediator) |
| Source generator based | Yes | No | No |
| Convention-driven | Yes | No | No |
| Built-in outbox | Yes | No | Yes |
| Distributed messaging | Yes | No (external) | Yes |
| Saga support | Limited | No | Yes |
| Boilerplate | Minimal | Significant | Moderate |
| Performance | High | Moderate | Moderate |

### Selection Decision

**Recommended: Wolverine** as primary mediator, with MassTransit for distributed messaging scenarios.

**Rationale:**
- Wolverine is a "Next Generation .NET Mediator and Message Bus" built with source generators for minimal runtime overhead. It combines mediator pattern, in-process messaging, and distributed messaging in one solution.
- MediatR is the industry standard with 12,000+ stars and 2M+ downloads. However, it requires external libraries for distributed scenarios and has significant boilerplate.
- Wolverine eliminates boilerplate through convention-driven minimalism, which aligns with the architecture's goal of reducing developer friction.
- MassTransit is a comprehensive distributed application framework but is primarily designed for message bus scenarios.

**Custom Development Consideration:** Building a custom mediator would be time-consuming and unnecessary given the quality of Wolverine and MediatR.

---

## Domain 3: Distributed Messaging & Message Bus

### Requirement
Message bus abstraction with adapters for Kafka, RabbitMQ, and in-memory transport, supporting transactional outbox, sagas, and exactly-once semantics.

### Candidate Libraries

| Library | Stars | Downloads | Last Update | License | Transport Support |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **MassTransit** | ~5,242 | 22M+ | Active (days ago) | Apache-2.0 | Kafka, RabbitMQ, Azure SB, SQS, In-Memory |
| **Wolverine** | ~1,140 | ~20K | Active (days ago) | MIT | Kafka, RabbitMQ, Azure SB, SQS, In-Memory |
| **NServiceBus** | Not open | Commercial | Active | Commercial | Multiple transports, enterprise-grade |

### Feature Comparison

| Feature | MassTransit | Wolverine | NServiceBus |
| :--- | :--- | :--- | :--- |
| Open-source | Yes | Yes | No (commercial) |
| Multiple transports | Yes | Yes | Yes |
| Transactional outbox | Yes | Yes | Yes |
| Saga orchestration | Yes | Limited | Yes |
| Source generator based | No | Yes | No |
| Community adoption | Very High | Growing | Enterprise |
| Cost | Free | Free | Commercial |

### Selection Decision

**Recommended: MassTransit** as the primary message bus abstraction, with Wolverine as an alternative for simpler scenarios.

**Rationale:**
- MassTransit provides a developer-focused, modern platform for creating distributed applications with support for multiple transports through a unified API.
- A comparative study shows Wolverine provides the lowest publication latency, while MassTransit demonstrates the fastest consumption throughput with high stability.
- MassTransit includes transactional outbox support and saga orchestration, making it ideal for the architecture's distributed transaction requirements.
- MassTransit is open-source with very high community adoption.
- Wolverine is a compelling alternative that combines mediator and messaging in one solution, but MassTransit has a larger ecosystem.

**Custom Development Consideration:** Custom messaging infrastructure would be extremely complex and is not recommended given the maturity of MassTransit.

---

## Domain 4: Distributed Locking & Leader Election

### Requirement
Distributed lock abstraction with adapters for Redis, etcd, and in-memory implementations, supporting lease-based locks and fencing tokens.

### Candidate Libraries

| Library | Stars | Downloads | Last Update | License | Backend Support |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **DistributedLock** | Not available | Not available | Oct 2025 | Not specified | Redis, SQL Server, PostgreSQL, MySQL, ZooKeeper, File |
| **RedLock.net** | Not available | Not available | Active | Not specified | Redis (Redlock algorithm) |
| **Taurus.DistributedLock** | Not available | 5,168 | Mar 2025 | Not specified | Redis, MemCache, Database, Local, File |

### Feature Comparison

| Feature | DistributedLock | RedLock.net | Taurus.DistributedLock |
| :--- | :--- | :--- | :--- |
| Redis support | Yes | Yes (Redlock) | Yes |
| etcd support | Yes | No | No |
| SQL Server support | Yes | No | Yes |
| ZooKeeper support | Yes | No | No |
| Multiple backends | Yes | No | Yes |
| Reader-writer locks | Yes | No | No |
| Semaphore support | Yes | No | No |

### Selection Decision

**Recommended: DistributedLock** suite (including `DistributedLock.Redis` and `DistributedLock.Etcd`) as the primary locking abstraction.

**Rationale:**
- DistributedLock provides robust and easy-to-use distributed mutexes, reader-writer locks, and semaphores based on a variety of underlying technologies.
- It supports Redis, SQL Server, PostgreSQL, MySQL, ZooKeeper, and file-based locking, providing the polymorphic runtime flexibility required.
- RedLock.net is a C# implementation of the Redlock distributed lock algorithm but only supports Redis.
- DistributedLock.Redis version 1.1.0 was released in August 2025, indicating active maintenance.

**Custom Development Consideration:** Custom distributed lock implementation would require consensus protocol expertise (Raft/Paxos) and is not recommended.

---

## Domain 5: Resilience Engineering (Circuit Breakers, Retries, Bulkheads)

### Requirement
Resilience pipeline with circuit breakers, retry policies, bulkheads, timeouts, and fallbacks, integrated with AOP interceptors.

### Candidate Libraries

| Library | Stars | Downloads | Last Update | License | Key Features |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Polly** | Not available | Very High | Active | BSD-3-Clause | Retry, circuit breaker, timeout, bulkhead, rate limit, fallback, hedging |
| **Microsoft.Extensions.Http.Resilience** | N/A | High | Active | MIT | Built on Polly V8, resilience pipeline |

### Feature Comparison

| Feature | Polly | Microsoft.Extensions.Http.Resilience |
| :--- | :--- | :--- | :--- |
| Retry | Yes | Yes |
| Circuit breaker | Yes | Yes |
| Timeout | Yes | Yes |
| Bulkhead | Yes | Yes |
| Rate limiting | Yes | Yes |
| Fallback | Yes | Yes |
| Hedging | Yes | Yes |
| HTTP-specific | No | Yes |
| Performance | Baseline | ~2.8% slower than Polly V8 |

### Selection Decision

**Recommended: Polly** as the primary resilience library.

**Rationale:**
- Polly is the .NET resilience and transient fault-handling library that allows developers to express strategies such as retry, circuit breaker, timeout, bulkhead, rate limiting, fallback, and hedging.
- Microsoft.Extensions.Http.Resilience is built on Polly V8 and provides a resilience pipeline. Performance is nearly identical to Polly V8 (only 2.8% difference).
- Polly integrates seamlessly with AOP interceptors, enabling declarative resilience policies via attributes.
- Polly is thread-safe and fluent, making it ideal for the architecture's resilience requirements.

**Custom Development Consideration:** Building a custom resilience library would be extremely complex and is not recommended.

---

## Domain 6: Observability (Logging, Metrics, Tracing)

### Requirement
Comprehensive observability with structured logging, dimensional metrics, distributed tracing, and continuous profiling.

### Sub-domain 6.1: Logging

| Library | Stars | Downloads | Last Update | License | Key Features |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Serilog** | Not available | Very High | Active | MIT | Structured logging, sinks for many destinations, destructuring |
| **NLog** | Not available | Very High | Active | BSD-3-Clause | Async logging, XML configuration, extensive targets |
| **Microsoft.Extensions.Logging** | N/A | N/A | Active | MIT | Built-in, ILogger abstraction, provider model |

**Recommended: Serilog** with ILogger abstraction.

**Rationale:** Serilog provides strongly-typed structured logging and integrates with ILogger. Research indicates Serilog has ~15% higher CPU usage than NLog, but its structured format simplifies log analysis. The architecture's ILogger abstraction allows swapping implementations.

### Sub-domain 6.2: Metrics

| Library | Stars | Downloads | Last Update | License | Key Features |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Prometheus.Net** | Not available | High | Active | MIT | Counters, gauges, histograms, summaries, HTTP exporter |
| **OpenTelemetry Metrics** | N/A | Growing | Active | Apache-2.0 | Vendor-neutral, integrates with Prometheus |

**Recommended: OpenTelemetry Metrics** with Prometheus exporter.

**Rationale:** OpenTelemetry provides vendor-neutral metrics collection and is becoming the standard. Microsoft recommends OpenTelemetry over Application Insights SDK. Prometheus integration is well-supported.

### Sub-domain 6.3: Distributed Tracing

| Library | Stars | Downloads | Last Update | License | Key Features |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **OpenTelemetry .NET** | N/A | Growing | Active | Apache-2.0 | Vendor-neutral, OTLP export, context propagation |
| **Application Insights SDK** | N/A | High | Deprecating | Commercial | Azure-native, deep integration |

**Recommended: OpenTelemetry .NET** with OTLP exporter.

**Rationale:** OpenTelemetry is the standardized format for logging, tracing, and metrics. The Azure Monitor OpenTelemetry SDK is the future replacement for Application Insights SDK. OTLP with a collector is the easiest, most production-ready approach.

---

## Domain 7: Workflow Engines (BPMN, CMMN)

### Requirement
BPMN 2.0 and CMMN 1.1 engine support with model-driven execution and persistence.

### Candidate Libraries

| Library | Stars | Downloads | Last Update | License | BPMN Support |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Elsa Workflows** | ~7,033 | ~332K | ~15 days ago | MIT | BPMN 2.0 import/export |
| **DWKit** | Not available | Not available | Not available | Not specified | Full BPMN 2.0 conformance |
| **Meridian.Workflow** | Not available | Not available | Not available | Not specified | Fluent DSL (not BPMN) |

### Feature Comparison

| Feature | Elsa Workflows | DWKit | Meridian.Workflow |
| :--- | :--- | :--- | :--- |
| BPMN 2.0 support | Yes (import/export) | Yes (full conformance) | No (DSL only) |
| CMMN support | Limited | No | No |
| Visual designer | Yes | Yes | No |
| Persistence | Yes | Yes | Yes |
| Community adoption | Very High | Low | Low |
| Extensibility | High | Moderate | High |

### Selection Decision

**Recommended: Elsa Workflows** as the primary workflow engine foundation.

**Rationale:**
- Elsa Workflows is the most mature open-source .NET workflow engine with ~7,033 stars.
- Elsa v4 is highly extensible, supports BPMN 2.0 import/export, and features a modern designer UI.
- Elsa supports workflow definition in code, JSON, YAML, or XML.
- Elsa is MIT licensed.
- DWKit offers full BPMN 2.0 conformance but has lower community adoption.

**Custom Development Consideration:** Building a BPMN engine from scratch would be extremely complex (years of effort). Not recommended.

---

## Domain 8: API Gateway

### Requirement
API gateway with routing, rate limiting, authentication, service discovery integration, and high performance.

### Candidate Libraries

| Library | Stars | Downloads | Last Update | License | Key Features |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **YARP** | Not available | Very High | Active | MIT | High-performance, flexible routing, Microsoft-maintained |
| **Ocelot** | Not available | High | Active | Not specified | JSON config, JWT auth, rate limiting, load balancing |
| **Kong** | Not .NET | N/A | Active | Apache-2.0 | Full API lifecycle, plugin ecosystem |

### Feature Comparison

| Feature | YARP | Ocelot | Kong |
| :--- | :--- | :--- | :--- |
| .NET native | Yes | Yes | No (Go/nginx) |
| High performance | Yes | Moderate | Very High |
| Service discovery | Yes | Yes (Consul) | Yes |
| Rate limiting | Yes | Yes | Yes |
| Authentication | Yes | Yes | Yes |
| Configuration | Code/JSON | JSON | YAML/Admin API |
| Microsoft-maintained | Yes | No | No |

### Selection Decision

**Recommended: YARP** as the primary API gateway.

**Rationale:**
- YARP (Yet Another Reverse Proxy) is a high-performance reverse proxy library from Microsoft.
- YARP is considered a better alternative than Ocelot.
- YARP integrates well with service discovery (Consul, Kubernetes).
- Ocelot is lightweight with simple JSON-based configuration but has lower performance.

**Custom Development Consideration:** Building a custom API gateway is not recommended given the quality of YARP.

---

## Domain 9: Service Discovery

### Requirement
Service discovery abstraction with adapters for Consul, Kubernetes, and localhost.

### Candidate Libraries

| Library | Stars | Downloads | Last Update | License | Key Features |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Steeltoe Discovery** | Not available | ~2.78M | Sep 2025 | Apache-2.0 | Consul, Eureka support |
| **Consul API Client** | N/A | High | Active | Not specified | Direct Consul integration |
| **Microsoft.Extensions.ServiceDiscovery** | N/A | Not available | Active | MIT | .NET Aspire service discovery |

### Feature Comparison

| Feature | Steeltoe Discovery | Consul API Client | Microsoft.Extensions.ServiceDiscovery |
| :--- | :--- | :--- | :--- |
| Consul support | Yes | Yes | No |
| Eureka support | Yes | No | No |
| HTTP client integration | Yes | No | Yes |
| Kubernetes support | Limited | No | Yes |
| Caching load balancer | Yes | No | No |

### Selection Decision

**Recommended: Steeltoe Discovery** for Consul integration.

**Rationale:**
- Steeltoe simplifies integrating service discovery into .NET-based microservices by providing out-of-the-box support for Consul.
- The Steeltoe caching load balancer works well with Consul service discovery.
- Steeltoe is under active development with ~2.78M downloads.

---

## Domain 10: Distributed Cache

### Requirement
Distributed cache abstraction with adapters for Redis, local memory, and other providers.

### Candidate Libraries

| Library | Stars | Downloads | Last Update | License | Key Features |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **StackExchange.Redis** | Not available | Very High | Active | MIT | Official Redis client, IDistributedCache implementation |
| **Garnet** | Not available | Not available | Active | MIT | Microsoft Research, Redis-compatible, higher performance |
| **CacheManager** | Not available | Not available | Not available | Not specified | Multi-provider abstraction |

### Feature Comparison

| Feature | StackExchange.Redis | Garnet | CacheManager |
| :--- | :--- | :--- | :--- |
| Redis protocol | Yes | Yes (compatible) | Yes |
| IDistributedCache | Yes | Yes (with caveats) | Yes |
| Performance | Good | Excellent | Good |
| Lua script support | Yes | Limited | Depends |
| Microsoft-backed | No | Yes | No |
| Maturity | High | Emerging | Moderate |

### Selection Decision

**Recommended: StackExchange.Redis** for production, with Garnet evaluation for future.

**Rationale:**
- StackExchange.Redis is the standard Redis client for .NET with the official IDistributedCache implementation.
- Garnet is a high-performance remote cache-store from Microsoft Research offering strong performance, scalability, and Redis compatibility. Garnet delivered the highest performance across all metrics in a comparative study.
- However, Garnet has limited Lua scripting support (EVAL/EVALSHA), which .NET's IDistributedCache relies on for atomic operations.
- Garnet may be suitable for future adoption once Lua support is complete.

---

## Domain 11: Outbox Pattern & CDC

### Requirement
Outbox pattern implementation with Debezium CDC integration for reliable event publishing.

### Candidate Libraries

| Library | Stars | Downloads | Last Update | License | Key Features |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **MassTransit Outbox** | ~5,242 | 22M+ | Active | Apache-2.0 | Built-in outbox, multiple database support |
| **Wolverine Outbox** | ~1,140 | ~20K | Active | MIT | Database-backed outbox, inbox pattern, deduplication |
| **Transactional Outbox for .NET** | Not available | Not available | ~5 months ago | Not specified | SQL Server, Azure Service Bus |

### Feature Comparison

| Feature | MassTransit Outbox | Wolverine Outbox | Transactional Outbox for .NET |
| :--- | :--- | :--- | :--- |
| Database-backed | Yes | Yes | Yes |
| FIFO ordering | Yes | Yes | Yes |
| Inbox pattern | Yes | Yes | No |
| Deduplication | Yes | Yes | No |
| Debezium/CDC integration | Yes | Yes | No |
| Community adoption | Very High | Growing | Low |

### Selection Decision

**Recommended: Wolverine Outbox** or **MassTransit Outbox** with Debezium CDC.

**Rationale:**
- Wolverine provides a true database-backed outbox, inbox pattern implementation, and deduplication.
- MassTransit also includes built-in outbox support and is more widely adopted.
- Debezium (CDC) monitors database logs and streams changes to Kafka.
- A custom implementation would require significant effort and is not recommended.

---

## Domain 12: Testing Frameworks

### Requirement
Unit testing, integration testing, contract testing, and performance testing frameworks.

### Sub-domain 12.1: Unit Testing

| Library | Stars | Downloads | Last Update | License | Key Features |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **xUnit.net** | Not available | Very High | Active | Apache-2.0 | Modern, [Fact]/[Theory], isolated tests |
| **NUnit** | Not available | Very High | Active | MIT | Mature, [Test]/[TestCase], rich assertions |
| **MSTest** | N/A | High | Active | MIT | Microsoft default, Visual Studio integration |

**Recommended: xUnit.net.**

**Rationale:** xUnit is the modern standard for .NET Core and ASP.NET Core. It emphasizes isolated tests with less shared state and uses constructors for setup. All three are open-source with active communities.

### Sub-domain 12.2: Contract Testing

**Recommended: Pact.**

**Rationale:** Pact is the industry standard for consumer-driven contract testing in .NET.

### Sub-domain 12.3: Performance Testing

**Recommended: k6.**

**Rationale:** k6 is modern, scriptable, and container-native, making it ideal for CI/CD integration.

---

## Domain 13: GraphQL

### Requirement
GraphQL server implementation for flexible querying.

### Candidate Libraries

| Library | Stars | Downloads | Last Update | License | Key Features |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Hot Chocolate** | Not available | High | Active | MIT | Full-featured, ASP.NET Core integration, EF Core support |
| **GraphQL.NET** | Not available | High | Active | MIT | Spec-compliant, one-to-one mapping |

### Feature Comparison

| Feature | Hot Chocolate | GraphQL.NET |
| :--- | :--- | :--- | :--- |
| Full-featured framework | Yes | No (library) |
| ASP.NET Core integration | Yes | Yes |
| EF Core integration | Yes | Limited |
| Schema generation | Automatic | Manual |
| Federation support | Yes | Limited |
| .NET-native feel | Yes | No |

### Selection Decision

**Recommended: Hot Chocolate.**

**Rationale:** Hot Chocolate is a full-featured GraphQL framework that takes the complexity away from building a GraphQL server. It integrates with ASP.NET Core and Entity Framework Core, offering convenient attributes and automatic schema generation. GraphQL.NET implements the specification in a one-to-one manner without asking how it could feel more .NET-like.

---

## Domain 14: gRPC

### Requirement
gRPC client and server implementation.

### Candidate Libraries

| Library | Approach | License | Key Features |
| :--- | :--- | :--- | :--- |
| **Grpc.Net.Client** | .NET-native | MIT | Official Microsoft-supported, uses HTTP/2 and TLS |
| **Grpc.Core** | C++ wrapper | Apache-2.0 | Legacy, wraps gRPC C-core |

### Selection Decision

**Recommended: Grpc.Net.Client** for clients, **Grpc.AspNetCore** for servers.

**Rationale:**
- Grpc.Net.Client is the Microsoft-supported gRPC client for .NET Core 3.1 and .NET 5+.
- Grpc.Core is deprecated and should be migrated from.
- Grpc.Net.Client has limited .NET Framework support via WinHttpHandler.

---

## Domain 15: Document Processing

### Requirement
Parsing, rendering, and transforming DOCX, PDF, XLSX, PPTX, HTML, Markdown, and CAD formats.

### Candidate Libraries

| Format | Library | License | Key Features |
| :--- | :--- | :--- | :--- |
| **DOCX/XLSX/PPTX** | DocumentFormat.OpenXml | MIT | Microsoft Open XML SDK |
| **DOCX/XLSX** | ClosedXML | MIT | Intuitive OpenXML API |
| **PDF** | QuestPDF | Apache-2.0 | Modern PDF generation |
| **PDF** | PdfPig | Apache-2.0 | PDF parsing (no Adobe dependencies) |
| **HTML** | AngleSharp | MIT | HTML5 parser |
| **Markdown** | Markdig | MIT | Markdown parsing |
| **CAD** | Custom | N/A | No mature open-source .NET CAD library |

### Selection Decision

**Recommended:**
- **DocumentFormat.OpenXml** for DOCX, XLSX, PPTX (Microsoft's official SDK).
- **ClosedXML** for Excel as a more intuitive wrapper.
- **QuestPDF** for PDF generation (modern, fluent API).
- **PdfPig** for PDF parsing.
- **AngleSharp** for HTML5 parsing.
- **Markdig** for Markdown.

**Custom Development for CAD:** No mature open-source .NET CAD library exists. Custom CAD parsing or integration with C++ libraries (Open Cascade, IfcOpenShell) via interop is required.

---

## Domain 16: RAG & AI Orchestration

### Requirement
Retrieval-Augmented Generation pipelines, agent orchestration, and LLM integration.

### Candidate Libraries

| Library | Stars | License | Key Features |
| :--- | :--- | :--- | :--- |
| **Semantic Kernel** | Not available | MIT | Microsoft's orchestration framework, .NET-first, agents, RAG, planning |
| **LangChain (Python)** | ~90,000+ | MIT | Largest ecosystem, Python-first, extensive integrations |

### Selection Decision

**Recommended: Semantic Kernel** for .NET-native AI orchestration.

**Rationale:**
- Semantic Kernel is Microsoft's orchestration framework with tight .NET integration.
- It supports agents, RAG, and planning with Microsoft.Extensions.AI.
- LangChain has a larger ecosystem but is Python-first.
- Semantic Kernel is the natural choice for a .NET platform.

---

## Domain 17: Vector Databases

### Requirement
Store and search high-dimensional embeddings for RAG and AI memory.

### Candidate Libraries

| Library | License | Key Features |
| :--- | :--- | :--- |
| **Milvus** | Apache-2.0 | High-scale, cloud-native, C# SDK available |
| **Qdrant** | Apache-2.0 | Rust-based, fast, filtering, hybrid search |
| **pgvector** | PostgreSQL | Simple, integrated with PostgreSQL |
| **Pinecone** | Commercial | Managed, high availability |

### Selection Decision

**Recommended: Milvus** for production, **pgvector** for smaller workloads.

**Rationale:**
- Milvus is built for high-dimensional search at production scale with a C# SDK.
- Qdrant is developer-friendly and open-source.
- pgvector is suitable for mid-scale workloads.
- Enterprise teams often choose Pinecone or cloud-native services.

---

## Domain 18: Identity & Access Management (IAM)

### Requirement
OAuth2/OIDC server for authentication and authorization.

### Candidate Libraries

| Library | License | Key Features |
| :--- | :--- | :--- |
| **Keycloak** | Apache-2.0 | Open-source IdP, OIDC, SAML, SSO, UI, role management |
| **Duende IdentityServer** | Commercial | .NET-native, OIDC-certified |
| **Ory Hydra/Kratos** | Apache-2.0 | OIDC-certified, zero-trust |

### Selection Decision

**Recommended: Keycloak.**

**Rationale:**
- Keycloak is open-source with OIDC, OAuth2, and SAML support.
- Keycloak is ready-to-use with UI, SSO, and role management.
- IdentityServer requires more custom coding.
- Keycloak integrates well with ASP.NET Core.

---

## Domain 19: Secrets Management

### Requirement
Secure storage, management, and rotation of secrets.

### Candidate Libraries

| Library | License | Key Features |
| :--- | :--- | :--- |
| **HashiCorp Vault** | MPL-2.0 | Dynamic secrets, encryption as a service, audit logging |
| **Azure Key Vault** | Commercial | Cloud-native, managed, .NET SDK |
| **AWS Secrets Manager** | Commercial | Cloud-native, managed |

### Selection Decision

**Recommended: HashiCorp Vault** with **VaultSharp** client.

**Rationale:**
- VaultSharp is a comprehensive cross-platform .NET library for HashiCorp's Vault.
- Vault provides dynamic secrets, certificate management, and audit logging.
- Cloud-native options (Azure Key Vault, AWS Secrets Manager) are also viable.

---

## Domain 20: OpenTelemetry Collector

### Requirement
Telemetry collection, processing, and export.

### Recommendation

**Recommended: OpenTelemetry Collector** with OTLP export.

**Rationale:**
- The OpenTelemetry Collector is a separate process that receives telemetry via OTLP.
- Using OTLP with a collector is the easiest, most production-ready approach.
- Elastic Distributions of OpenTelemetry (EDOT) provides a production-tested OTel ecosystem.

---

## Summary Recommendation Table

| Domain | Primary Recommendation | Alternative | Custom Development |
| :--- | :--- | :--- | :--- |
| AOP | SkyHigh.StaticProxy | AspectWeaver | Not recommended |
| Mediator/CQRS | Wolverine | MediatR | Not recommended |
| Messaging | MassTransit | Wolverine | Not recommended |
| Distributed Locking | DistributedLock | RedLock.net | Not recommended |
| Resilience | Polly | Microsoft.Extensions.Http.Resilience | Not recommended |
| Logging | Serilog + ILogger | NLog | Not recommended |
| Metrics | OpenTelemetry Metrics | Prometheus.Net | Not recommended |
| Tracing | OpenTelemetry .NET | Application Insights | Not recommended |
| Workflow (BPMN) | Elsa Workflows | DWKit | Not recommended |
| API Gateway | YARP | Ocelot | Not recommended |
| Service Discovery | Steeltoe Discovery | Consul API | Not recommended |
| Distributed Cache | StackExchange.Redis | Garnet (future) | Not recommended |
| Outbox/CDC | Wolverine/MassTransit Outbox + Debezium | Custom | Not recommended |
| Unit Testing | xUnit.net | NUnit | Not recommended |
| Contract Testing | Pact | Spring Cloud Contract | Not recommended |
| Performance Testing | k6 | Locust | Not recommended |
| GraphQL | Hot Chocolate | GraphQL.NET | Not recommended |
| gRPC | Grpc.Net.Client | Grpc.Core (deprecated) | Not recommended |
| Document Processing | OpenXml + QuestPDF + PdfPig | Aspose (commercial) | CAD only |
| RAG/AI | Semantic Kernel | LangChain (Python) | Not recommended |
| Vector Database | Milvus | pgvector | Not recommended |
| IAM | Keycloak | Duende IdentityServer | Not recommended |
| Secrets Management | HashiCorp Vault | Azure Key Vault | Not recommended |
| OpenTelemetry Collector | OTel Collector | EDOT | Not recommended |

---

### Appendix E: Model Repository Sample Structure

This appendix provides a concrete example of the Model Repository structure as defined in the architecture document.

#### E.1 Repository Root Structure

```
ModelRepository/
├── README.md
├── .gitignore
├── .model-version
├── BoundedContexts/
│   ├── ContractLifecycle/
│   │   ├── README.md
│   │   ├── BPMN/
│   │   │   ├── ApprovalWorkflow.bpmn
│   │   │   └── ContractAmendmentProcess.bpmn
│   │   ├── DMN/
│   │   │   ├── RiskScoring.dmn
│   │   │   └── ApprovalRules.dmn
│   │   ├── CMMN/
│   │   │   └── DisputeCase.cmmn
│   │   ├── StateMachines/
│   │   │   └── ContractLifecycle.scxml
│   │   ├── CEP/
│   │   │   └── CompliancePatterns.json
│   │   ├── Forms/
│   │   │   ├── ContractRequest.uiform
│   │   │   └── ApprovalForm.uiform
│   │   ├── Artifacts/
│   │   │   ├── ContractTemplate.docx
│   │   │   └── InvoiceTemplate.xlsx
│   │   ├── API/
│   │   │   ├── ContractApi.openapi.yaml
│   │   │   └── ContractService.proto
│   │   └── meta.yaml
│   ├── CustomerOnboarding/
│   │   ├── README.md
│   │   ├── BPMN/
│   │   │   └── OnboardingProcess.bpmn
│   │   ├── DMN/
│   │   │   └── EligibilityCheck.dmn
│   │   ├── Forms/
│   │   │   └── CustomerRegistration.uiform
│   │   └── meta.yaml
│   └── OrderFulfillment/
│       ├── README.md
│       ├── BPMN/
│       │   ├── OrderProcessing.bpmn
│       │   └── ReturnProcess.bpmn
│       ├── DMN/
│       │   └── ShippingRules.dmn
│       ├── StateMachines/
│       │   └── OrderState.scxml
│       ├── CEP/
│       │   └── FraudDetection.json
│       ├── Artifacts/
│       │   ├── OrderConfirmation.docx
│       │   └── PackingSlip.docx
│       └── meta.yaml
├── Shared/
│   ├── Schemas/
│   │   ├── Customer.avro
│   │   ├── Order.avro
│   │   └── Payment.avro
│   ├── APIs/
│   │   ├── common-api.yaml
│   │   └── authentication.proto
│   └── UI/
│       └── theme.json
├── Skills/
│   ├── CustomerSupport/
│   │   ├── skill.json
│   │   ├── prompt.txt
│   │   └── examples/
│   │       └── sample-query.json
│   └── DataAnalytics/
│       ├── skill.json
│       └── prompt.txt
└── Agents/
    ├── SupportAgent/
    │   ├── agent.json
    │   └── behaviors/
    │       └── escalation-policy.json
    └── DataAnalyst/
        ├── agent.json
        └── behaviors/
            └── query-generation.json
```

#### E.2 Bounded Context Meta File (`meta.yaml`)

Each Bounded Context contains a `meta.yaml` file defining ownership, versioning, and dependencies.

```yaml
# ContractLifecycle/meta.yaml
context: ContractLifecycle
owner:
  team: "Contracts Team"
  contact: "contracts-engineering@platform.internal"
description: "Manages contract creation, approval, amendment, and lifecycle"
version: "1.2.0"

dependencies:
  - context: "CustomerOnboarding"
    version: ">=1.0.0"
  - context: "OrderFulfillment"
    version: ">=1.1.0"

models:
  - type: "BPMN"
    files:
      - "ApprovalWorkflow.bpmn"
      - "ContractAmendmentProcess.bpmn"
  - type: "DMN"
    files:
      - "RiskScoring.dmn"
      - "ApprovalRules.dmn"
  - type: "CMMN"
    files:
      - "DisputeCase.cmmn"
  - type: "Form"
    files:
      - "ContractRequest.uiform"
      - "ApprovalForm.uiform"

events:
  - "ContractCreated"
  - "ContractApproved"
  - "ContractAmended"
  - "ContractExpired"
  - "ContractDisputed"

configuration:
  env:
    default:
      retentionPeriod: "7 years"
      autoArchiveDays: 90
    production:
      retentionPeriod: "10 years"
      autoArchiveDays: 365
```

#### E.3 Model File Examples

##### BPMN Model Example (`ApprovalWorkflow.bpmn`)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL"
             xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
             targetNamespace="http://bpmn.io/schema/bpmn">
  <process id="ApprovalWorkflow" isExecutable="true">
    <startEvent id="StartEvent" name="Contract Requested"/>
    <userTask id="LegalReview" name="Legal Review">
      <potentialOwner>
        <resourceAssignmentExpression>
          <formalExpression>legal-team</formalExpression>
        </resourceAssignmentExpression>
      </potentialOwner>
    </userTask>
    <businessRuleTask id="RiskAssessment" name="Risk Assessment">
      <implementationRef>
        <formalExpression>RiskScoring.dmn</formalExpression>
      </implementationRef>
    </businessRuleTask>
    <exclusiveGateway id="RiskDecision" name="Risk Decision">
      <conditionSequenceFlow>
        <conditionExpression>riskScore &lt; 50</conditionExpression>
      </conditionSequenceFlow>
    </exclusiveGateway>
    <userTask id="ManagerApproval" name="Manager Approval">
      <potentialOwner>
        <resourceAssignmentExpression>
          <formalExpression>managers</formalExpression>
        </resourceAssignmentExpression>
      </potentialOwner>
    </userTask>
    <endEvent id="EndEvent" name="Contract Approved"/>
    <endEvent id="RejectEvent" name="Contract Rejected"/>
  </process>
</definitions>
```

##### DMN Model Example (`RiskScoring.dmn`)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="https://www.omg.org/spec/DMN/20191111/MODEL/"
             id="RiskScoring">
  <decision id="RiskScore" name="Risk Score">
    <informationRequirement>
      <requiredDecision href="#RiskFactors"/>
    </informationRequirement>
    <decisionTable id="RiskScoreTable" hitPolicy="COLLECT" preferredOrientation="Rule-as-Row">
      <input id="input1" label="Risk Factor">
        <inputExpression typeRef="string">
          <text>riskFactor</text>
        </inputExpression>
      </input>
      <input id="input2" label="Value">
        <inputExpression typeRef="number">
          <text>value</text>
        </inputExpression>
      </input>
      <output id="output1" label="Score">
        <outputExpression typeRef="number">
          <text>score</text>
        </outputExpression>
      </output>
      <rule id="rule1">
        <inputEntry id="entry1"><text>"VALUE"</text></inputEntry>
        <inputEntry id="entry2"><text>> 1000000</text></inputEntry>
        <outputEntry id="output1"><text>10</text></outputEntry>
      </rule>
      <rule id="rule2">
        <inputEntry id="entry3"><text>"VALUE"</text></inputEntry>
        <inputEntry id="entry4"><text>between 500000 and 1000000</text></inputEntry>
        <outputEntry id="output2"><text>5</text></outputEntry>
      </rule>
    </decisionTable>
  </decision>
</definitions>
```

##### Form Model Example (`ContractRequest.uiform`)

```json
{
  "$schema": "https://platform.internal/schemas/ui-form/v1",
  "id": "ContractRequest",
  "title": "Contract Request Form",
  "description": "Form for requesting a new contract",
  "fields": [
    {
      "id": "contractType",
      "type": "dropdown",
      "label": "Contract Type",
      "required": true,
      "options": [
        {"value": "NDA", "label": "Non-Disclosure Agreement"},
        {"value": "ServiceAgreement", "label": "Service Agreement"},
        {"value": "Partnership", "label": "Partnership Agreement"},
        {"value": "Other", "label": "Other"}
      ]
    },
    {
      "id": "counterpartyName",
      "type": "text",
      "label": "Counterparty Name",
      "required": true,
      "maxLength": 100
    },
    {
      "id": "counterpartyEmail",
      "type": "email",
      "label": "Counterparty Email",
      "required": true,
      "validation": {
        "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
      }
    },
    {
      "id": "contractValue",
      "type": "currency",
      "label": "Contract Value",
      "required": true,
      "currency": "USD",
      "minValue": 0
    },
    {
      "id": "description",
      "type": "textarea",
      "label": "Contract Description",
      "required": true,
      "rows": 5
    },
    {
      "id": "attachments",
      "type": "file",
      "label": "Supporting Documents",
      "multiple": true,
      "acceptedTypes": ["application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    }
  ],
  "actions": [
    {
      "id": "submit",
      "label": "Submit",
      "type": "primary",
      "action": "submit"
    },
    {
      "id": "draft",
      "label": "Save Draft",
      "type": "secondary",
      "action": "save"
    }
  ]
}
```

#### E.4 Agent Definition Example (`agent.json`)

```json
{
  "$schema": "https://platform.internal/schemas/agent/v1",
  "agentId": "support-agent-v1",
  "agentType": "CustomerSupportAgent",
  "version": "1.2.0",
  "description": "Handles customer support inquiries and ticket resolution",
  "capabilities": [
    {
      "name": "resolveIssue",
      "description": "Resolves customer support issues",
      "inputSchema": {
        "type": "object",
        "properties": {
          "issueId": {"type": "string"},
          "description": {"type": "string"},
          "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"]}
        },
        "required": ["issueId", "description"]
      },
      "outputSchema": {
        "type": "object",
        "properties": {
          "resolution": {"type": "string"},
          "status": {"type": "string", "enum": ["resolved", "escalated", "pending"]}
        }
      }
    },
    {
      "name": "escalateIssue",
      "description": "Escalates an issue to a human agent",
      "inputSchema": {
        "type": "object",
        "properties": {
          "issueId": {"type": "string"},
          "reason": {"type": "string"}
        }
      }
    }
  ],
  "skills": [
    {
      "skillId": "customer-support-skill",
      "version": "1.0.0"
    },
    {
      "skillId": "knowledge-retrieval",
      "version": "1.1.0"
    }
  ],
  "memory": {
    "type": "conversation",
    "ttl": 3600,
    "maxTokens": 4000
  },
  "trustLevel": "high",
  "permissions": [
    "read:customer-data",
    "read:ticket-data",
    "write:ticket-data",
    "send:email"
  ]
}
```

#### E.5 Versioning Strategy

The Model Repository uses semantic versioning for all models. The `.model-version` file tracks the current version of the repository.

```
# .model-version
RepositoryVersion: 2.1.0
LastUpdate: 2026-06-17T10:30:00Z
```

Each model file can be versioned independently, but the repository as a whole has a version number for change management purposes.

---

### Appendix F: Deployment Pipeline Reference Architecture

This appendix provides a detailed reference architecture for the CI/CD and deployment pipeline as defined in the architecture document.

#### F.1 Pipeline Overview

The pipeline follows the "Build Once, Deploy Anywhere" principle with promotion through environments.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Development   │────▶│      Test       │────▶│    Staging      │────▶│   Production    │
│   (Dev/PR)      │     │   (Automated)   │     │  (Manual Gate)  │     │  (Manual Gate)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │                       │
        ▼                       ▼                       ▼                       ▼
  ┌─────────────┐       ┌─────────────┐       ┌─────────────┐       ┌─────────────┐
  │ Smoke Tests │       │ Integration │       │ Performance │       │   Canary    │
  │   (Local)   │       │  + Contract │       │    Tests    │       │   Analysis  │
  └─────────────┘       └─────────────┘       └─────────────┘       └─────────────┘
```

#### F.2 CI Pipeline Stages

##### Stage 1: Code & Model Validation

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                               CI Pipeline (GitLab CI / GitHub Actions)             │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐   │
│  │  Source Code Build  │     │  Model Validation   │     │  Unit Tests (xUnit) │   │
│  │  - Compile .NET 10  │     │  - Syntax (BPMN,    │     │  - In-memory mode   │   │
│  │  - Roslyn Analyzers │     │    DMN, JSON Schema)│     │  - Coverage Report  │   │
│  │  - Create Container │     │  - Semantic         │     │  - Integrate with   │   │
│  │    Image           │     │  - Sandbox Execution│     │    SonarQube        │   │
│  └─────────────────────┘     └─────────────────────┘     └─────────────────────┘   │
│                                                                                     │
│  ┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐   │
│  │  Container Build    │     │  Vulnerability Scan │     │  Push to Registry   │   │
│  │  - Dockerfile       │     │  - Trivy / Grype    │     │  - ECR / ACR / GCR  │   │
│  │  - Multi-stage      │     │  - SBOM Generation  │     │  - Image Signing    │   │
│  │    Build            │     │  - Sign (cosign)    │     │  - Tag: Commit SHA  │   │
│  └─────────────────────┘     └─────────────────────┘     └─────────────────────┘   │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

##### Stage 2: Integration & Contract Testing

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           Test Environment Deployment                              │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐   │
│  │  Deploy to Test     │     │  Integration Tests  │     │  Contract Tests     │   │
│  │  - Helm Upgrade     │     │  - Testcontainers   │     │  - Pact (Consumer)  │   │
│  │  - ConfigMap Update │     │  - Database, Kafka  │     │  - Pact Broker      │   │
│  │  - RuntimeTopology  │     │    Redis, Neo4j     │     │  - Provider        │   │
│  │    (Test profile)   │     │  - E2E scenarios    │     │    Verification     │   │
│  └─────────────────────┘     └─────────────────────┘     └─────────────────────┘   │
│                                                                                     │
│  ┌─────────────────────┐     ┌─────────────────────┐                               │
│  │  Load Tests (k6)    │     │  Chaos Tests        │                               │
│  │  - Baseline metrics │     │  - Pod Kill         │                               │
│  │  - Stress scenarios │     │  - Network latency  │                               │
│  │  - Validate SLOs    │     │  - Node failure     │                               │
│  └─────────────────────┘     └─────────────────────┘                               │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

##### Stage 3: Staging Deployment (Manual Approval Gate)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         Staging Environment Deployment                             │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                                                                             │   │
│  │  ┌─────────────────────┐     ┌─────────────────────┐                       │   │
│  │  │  Manual Approval    │     │  Deploy to Staging  │                       │   │
│  │  │  - Release Manager  │     │  - Helm Upgrade     │                       │   │
│  │  │  - Review Changes   │     │  - ConfigMap Update │                       │   │
│  │  │  - Approve         │     │  - RuntimeTopology  │                       │   │
│  │  │                     │     │    (Staging profile)│                       │   │
│  │  └─────────────────────┘     └─────────────────────┘                       │   │
│  │                                                                             │   │
│  │  ┌─────────────────────┐     ┌─────────────────────┐                       │   │
│  │  │  Smoke Tests        │     │  UAT (User          │                       │   │
│  │  │  - Health checks    │     │    Acceptance       │                       │   │
│  │  │  - Critical flows   │     │    Testing)         │                       │   │
│  │  └─────────────────────┘     └─────────────────────┘                       │   │
│  │                                                                             │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

##### Stage 4: Production Deployment (Canary)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        Production Environment Deployment                           │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                                                                             │   │
│  │  ┌─────────────────────┐     ┌─────────────────────┐                       │   │
│  │  │  Canary Deployment  │     │  Traffic Splitting  │                       │   │
│  │  │  - Deploy v2 (10%)  │     │  - Istio VirtualSvc │                       │   │
│  │  │  - Maintain v1 (90%)│     │  - 10% → v2        │                       │   │
│  │  └─────────────────────┘     └─────────────────────┘                       │   │
│  │                                                                             │   │
│  │  ┌─────────────────────┐     ┌─────────────────────┐                       │   │
│  │  │  Canary Analysis    │     │  Gradual Rollout    │                       │   │
│  │  │  - Error rate       │     │  - Increase to 50%  │                       │   │
│  │  │  - Latency (p95)    │     │  - Increase to 100% │                       │   │
│  │  │  - Business metrics │     │  - Rollback on      │                       │   │
│  │  │  - Prometheus       │     │    failure          │                       │   │
│  │  └─────────────────────┘     └─────────────────────┘                       │   │
│  │                                                                             │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

#### F.3 ArgoCD Application Configuration

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: platform
  namespace: argocd
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: default
  source:
    repoURL: https://gitlab.platform.internal/platform/helm-charts
    targetRevision: HEAD
    path: platform
    helm:
      valueFiles:
        - values-common.yaml
        - $env-values/values-${ENVIRONMENT}.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: platform-${ENVIRONMENT}
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
      - ApplyOutOfSyncOnly=true
```

#### F.4 Environment Values Files

##### values-dev.yaml

```yaml
environment: dev
replicaCount: 1

runtimeTopology:
  communicationMode: InMemory
  lockStrategy: Local
  persistenceMode: InMemory
  cachingMode: Local
  serviceDiscoveryMode: Localhost
  securityMode: Passthrough
  observabilityMode: Console
  resilienceMode: None

resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 200m
    memory: 256Mi

ingress:
  enabled: false
```

##### values-staging.yaml

```yaml
environment: staging
replicaCount: 2

runtimeTopology:
  communicationMode: Kafka_gRPC
  lockStrategy: Redis
  persistenceMode: EFCore_PostgreSQL
  cachingMode: Redis
  serviceDiscoveryMode: Consul_K8s
  securityMode: Spiffe_mTLS
  observabilityMode: OpenTelemetry
  resilienceMode: Production

resources:
  limits:
    cpu: 1000m
    memory: 1Gi
  requests:
    cpu: 500m
    memory: 512Mi

ingress:
  enabled: true
  host: staging.platform.internal
  tls: true
```

##### values-prod.yaml

```yaml
environment: prod
replicaCount: 3

runtimeTopology:
  communicationMode: Kafka_gRPC
  lockStrategy: Etcd
  persistenceMode: EFCore_PostgreSQL
  cachingMode: Redis
  serviceDiscoveryMode: Consul_K8s
  securityMode: Spiffe_mTLS
  observabilityMode: OpenTelemetry
  resilienceMode: Production
  kafkaOptions:
    bootstrapServers: kafka-cluster:9092
    schemaRegistryUrl: http://schema-registry:8081
  etcdOptions:
    endpoints: ["etcd-1:2379", "etcd-2:2379", "etcd-3:2379"]
    leaseTtlSeconds: 30

resources:
  limits:
    cpu: 2000m
    memory: 2Gi
  requests:
    cpu: 1000m
    memory: 1Gi

ingress:
  enabled: true
  host: platform.internal
  tls: true
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80
```

#### F.5 Pipeline Tools Summary

| Stage | Tool | Purpose |
| :--- | :--- | :--- |
| **CI** | GitLab CI / GitHub Actions | Pipeline orchestration |
| **Build** | dotnet build/publish | .NET 10 compilation |
| **Container** | Docker / BuildKit | Container image build |
| **Vulnerability** | Trivy / Grype | Image vulnerability scanning |
| **Registry** | ECR / ACR / GCR / Harbor | Container registry |
| **Signing** | cosign (Sigstore) | Image signing |
| **Orchestration** | Helm | Kubernetes packaging |
| **GitOps** | ArgoCD | Declarative deployment |
| **Service Mesh** | Istio | Traffic management, canary |
| **Observability** | Prometheus + Grafana | Metrics and dashboards |
| **Testing** | k6 / Locust | Performance testing |
| **Chaos** | Chaos Mesh / Gremlin | Chaos engineering |
| **Contract** | Pact | Contract testing |
| **Cost** | Kubecost / OpenCost | Cost monitoring |

---
