# Deployment Agnostic - Technical Specification v1.0.1

**Document Version:** 1.0.1
**Status:** Approved for implementation  
**Date:** 2026-06-15  
**Authors:** Agentic BPMS Architecture Team  

---

## Table of Contents

1. Introduction and Scope  
   1.1 Purpose  
   1.2 Guiding Principles  
   1.3 Definition of "Deployment Agnostic"  
   1.4 Document Conventions  

2. Architecture Overview  
   2.1 Logical Components  
   2.2 Deployment Layers  
   2.3 Model‑Driven Approach  

3. Canonical Message Model  
   3.1 CloudEvents Envelope  
   3.2 Payload Schema (JSON Schema & Protobuf)  
   3.3 Mandatory Attributes for Engine  
   3.4 Model Cross‑Reference (URI Resolution)  

4. Protocol Adapter Plugin Model (ASP.NET Core AOT)  
   4.1 Design Constraints for Native AOT  
   4.2 `IProtocolAdapter` Interface Definition  
   4.3 Source‑Generated Registry  
   4.4 Supported Protocols (v1.0)  
   4.5 Streaming Support (gRPC, WebSocket, etc.)  

5. Deployment as Code  
   5.1 Configuration File Format (`deployment-config.yaml`)  
   5.2 Environment Overlays (dev, stage, prod)  
   5.3 Configuration Schema (full YAML specification)  
   5.4 Validation & Dry‑Run CLI  
   5.5 Dynamic Hot Reload (Watcher Implementation)  

6. Domains 3–13: Core Engine Capabilities (Detailed)  
   6.1 Domain 3 – Inter‑Service Communication  
       6.1.1 Synchronous Request/Reply  
       6.1.2 Asynchronous Messaging & Events  
       6.1.3 Full gRPC Streaming (Client & Server)  
       6.1.4 Idempotency & Deduplication Integration  
   6.2 Domain 4 – Service Mesh  
       6.2.1 Optional Transparency  
       6.2.2 Configuration When Mesh Present  
   6.3 Domain 5 – Northbound Exposure (API Management)  
       6.3.1 `IApiGateway` Plugin Interface  
       6.3.2 Default Implementation: Our API Gateway Engine  
       6.3.3 Authentication/Authorization Alignment  
   6.4 Domain 6 – Southbound Integration & Transformation  
       6.4.1 Model‑Driven Transformation Layer  
       6.4.2 `ITransformer` Interface and Built‑in Engine  
       6.4.3 EAI Patterns Inside Engine (No External Camel Required)  
   6.5 Domain 7 – State & Caching  
       6.5.1 `IStateBackend` Interface (Methods, Serialization)  
       6.5.2 `ICache` Interface (Transient, In‑Memory / Redis)  
       6.5.3 `IDistributedLock` Interface  
       6.5.4 Default Implementations: PostgreSQL, Redis, Advisory Locks  
   6.6 Domain 8 – Configuration & Secrets Management  
       6.6.1 `IConfigSource` with Hot Reload  
       6.6.2 `ISecretResolver` Interface  
       6.6.3 Default Resolvers: File, Environment, Kubernetes Secrets  
   6.7 Domain 9 – Event Streaming & CEP  
       6.7.1 `IEventStore` for Event Sourcing (Global, Cross‑Workflow)  
       6.7.2 `ICepEngine` for BAM and Observability Processing  
       6.7.3 Default: Kafka + Kafka Streams, Flink as optional  
   6.8 Domain 10 – Data Consistency & Distributed Transactions  
       6.8.1 `ITransactionManager` Interface (Sagas, 2PC)  
       6.8.2 Outbox Pattern Implementation  
       6.8.3 Distributed Saga Across Engine Instances (v1.0)  
   6.9 Domain 11 – Observability  
       6.9.1 `ILogger`, `IMetrics`, `ITracer`, `IAlerting` Interfaces  
       6.9.2 OpenTelemetry Integration  
       6.9.3 Alerting Rules Defined in Deployment Config  
   6.10 Domain 12 – Security  
        6.10.1 `IAuthenticator` (JWT, mTLS, API Key)  
        6.10.2 `IAuthorizer` with ABAC (Attribute‑Based Access Control)  
        6.10.3 `ISecretResolver` (reused from Domain 8)  
        6.10.4 Default: JWT + OPA (ABAC policies)  
   6.11 Domain 13 – Agentic Systems & AI‑Native Integration  
        6.11.1 Agent Task Extension to BPMN  
        6.11.2 `IAgentInvoker` Interface (MCP, A2A)  
        6.11.3 `ISkillRegistry` for Skill Discovery  
        6.11.4 Default Implementations: MCP Adapter, A2A over CloudEvents  

7. Extended Domains (14,15,16,20,42,65) – Detailed  
   7.1 Domain 14 – UI Backend & Frontend Platform  
       7.1.1 `IUserTaskProvider` Interface  
       7.1.2 `IRealTimePush` Interface (WebSocket/SSE)  
       7.1.3 Mandatory Default: Separate BFF Engine (Our Own)  
       7.1.4 BFF Engine API Contract  
   7.2 Domain 15 – Load Balancing & Traffic Routing  
       7.2.1 `IResourceManager` Interface  
       7.2.2 `ILoadBalancer` Interface (Algorithms)  
       7.2.3 Default Implementations: Bypass, Simple Round‑Robin  
       7.2.4 Work Distribution and Service/Messaging State Management  
   7.3 Domain 16 – Data Persistence & Storage  
       7.3.1 Reuse of `IStateBackend`, `IVectorStore`, `IBlobStorage`  
       7.3.2 Alignment with Canonical Message Model  
       7.3.3 Default Implementations: PostgreSQL, pgvector, S3/Local  
   7.4 Domain 20 – Artifact Processing & Abstraction  
       7.4.1 Renamed from "Content Processing"  
       7.4.2 `IArtifactProcessor`, `IChunker`, `IEmbedder`, `IGraphStore`, `IMemoryStore`  
       7.4.3 `IArtifactLifecycleManager` (Versioning, Retention, Legal Hold)  
       7.4.4 Default Implementation: Reference in‑process (simple chunking, local embeddings, pgvector)  
       7.4.5 Optional Plugins: LangChain, ONNX, Azure AI Document Intelligence (compatibility evaluation ongoing)  
       7.4.6 Full Lifecycle Management in v1.0  
   7.5 Domain 42 – Code & Model Provenance  
       7.5.1 `IProvenanceRecorder` Interface  
       7.5.2 `IModelResolver` Interface  
       7.5.3 Default: In‑Memory (dev) + MLflow/LangSmith adapter optional  
       7.5.4 Skill and Prompt Versioning  
   7.6 Domain 65 – Data Masking & Test Data  
       7.6.1 `IDataMasker` Interface (JSONPath‑based)  
       7.6.2 `ITestDataGenerator` Interface (Bogus/Faker)  
       7.6.3 Automatic Masking Middleware for Non‑Prod Environments  

8. Cross‑Cutting Concerns  
   8.1 Error & Retry Policy Language (JSON/YAML DSL)  
   8.2 Pluggable Backends Summary Table  
   8.3 Idempotency Key Storage and Retention  
   8.4 Message Ordering and Exactly‑Once Semantics  

9. Domain Mapping Table (All Domains 1–65)  
   (Comprehensive table with Relationship and Spec Section)  

10. Open Issues & Future Versions  
    - No deferred items for v1.0  
    - Planned for v1.1: Full agentic AI extension spec, dynamic protocol discovery  
    - Planned for v2.0: Automated workflow instance migration  

11. Appendices  
    A. Full `deployment-config.yaml` Schema (JSON Schema)  
    B. Example Configurations (dev, stage, prod)  
    C. Plugin Development Walkthrough (Source Generator)  
    D. Glossary of Terms  

---

## 1. Introduction and Scope

### 1.1 Purpose
This document provides the complete technical specification for an **Agentic BPMS (Business Process Management System)** that is **deployment agnostic**. The system uses standard process modelling languages (BPMN, DMN, CMMN, UML state machines, CEP rules) and can be deployed on any infrastructure – from a single process to a multi‑cluster Kubernetes environment – without changing the models or application code. All environment‑specific details are externalised into **deployment configuration** files.

### 1.2 Guiding Principles
- **Logical vs. Physical Separation:** Process models contain logical names (e.g., `credit-check-service`). Physical endpoints, protocols, timeouts, retries, and security are defined in deployment configuration.
- **Pluggable Everything:** Every infrastructure dependency (state storage, messaging, transaction coordination, observability, security, resource management, artifact processing, etc.) is behind a plugin interface.
- **Model‑Driven:** Communication contracts (OpenAPI, AsyncAPI, gRPC protobuf) are treated as first‑class models, referenced from BPMN and other orchestrations.
- **Deployment as Code:** Environment configurations are versioned in Git, validated, and applied declaratively.
- **Idempotency First:** All external interactions carry an idempotency key. The engine guarantees at‑least‑once delivery and uses deduplication to achieve exactly‑once effects.

### 1.3 Definition of "Deployment Agnostic"
A system is deployment agnostic if the same compiled binaries and process models can run in:
- A single process (monolith) with in‑memory communication.
- A set of operating system processes (bare‑metal) with direct TCP or named pipes.
- A Docker Compose environment with container‑to‑container networking.
- A Kubernetes cluster with or without a service mesh (Istio, Linkerd).
- A serverless environment (e.g., Knative) with auto‑scaling.

Only the **deployment configuration** and the **plugin selections** change.

### 1.4 Document Conventions
- **`Monospace`** denotes code, interface names, configuration keys, and file paths.
- *Italics* emphasise important concepts.
- **Bold** indicates mandatory requirements.
- `IInterfaceName` refers to a pluggable interface that must be implemented by the deployment.
- Default implementations are provided for all interfaces.

---

## 2. Architecture Overview

### 2.1 Logical Components

The engine consists of:

- **Core Workflow State Machine:** Executes BPMN, DMN, CMMN, state machines, and CEP rules. Maintains instance state via `IStateBackend`.
- **Protocol Adapter Registry:** Routes logical service calls to physical protocols using `IProtocolAdapter`.
- **Plugin Host:** Loads all pluggable components (state backend, transaction manager, observability, security, resource manager, artifact processor, etc.).
- **API Layer:** Exposes northbound REST/gRPC API (with OpenAPI definition) and WebSocket/SSE for real‑time updates.
- **Agentic Extensions:** Supports agent tasks (`IAgentInvoker`), skill registry, artifact processing, and provenance recording.

### 2.2 Deployment Layers

| Layer | Artifacts | Versioned | Environment‑Specific |
|-------|-----------|-----------|----------------------|
| Logical Models | BPMN, DMN, OpenAPI, Canonical schemas | Yes (Git) | No |
| Deployment Config | `deployment-config.yaml`, secret refs, policy files | Yes (Git) | Yes (overlay per env) |
| Infrastructure | Kubernetes manifests, docker‑compose, IaC scripts | Yes | Yes |

### 2.3 Model‑Driven Approach
All communication contracts are defined in standard formats:
- **OpenAPI v3** for synchronous HTTP/REST.
- **AsyncAPI** for asynchronous message channels.
- **Protobuf/Connect** for gRPC.
- **CloudEvents + JSON Schema** for canonical internal messages.

BPMN models reference these contracts via URIs (see Section 3.4).

---

## 3. Canonical Message Model

### 3.1 CloudEvents Envelope
All messages exchanged between engine components and external systems (via adapters) use the [CloudEvents v1.0](https://cloudevents.io/) specification in **JSON mode** (binary mode optional for performance).

**Example:**
```json
{
  "specversion": "1.0",
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "source": "orchestration-engine/workflow-123",
  "type": "com.example.CreditCheckResponse",
  "subject": "workflow-instance-456",
  "time": "2026-06-15T10:00:00Z",
  "traceparent": "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01",
  "datacontenttype": "application/json",
  "data": {
    "creditScore": 720,
    "approved": true
  }
}
```

### 3.2 Payload Schema
- **JSON Schema (draft 2020‑12)** is the default schema language for the `data` field.
- **Protobuf** is allowed by setting `datacontenttype: "application/protobuf"` and referencing a schema ID.
- A **schema registry** (pluggable) stores and validates schemas. Default implementation uses a PostgreSQL table.

### 3.3 Mandatory Attributes for Engine
The engine requires the following CloudEvents attributes for routing, idempotency, and correlation:

| Attribute | Description | Required |
|-----------|-------------|----------|
| `id` | Globally unique idempotency key (UUID or similar) | Yes |
| `source` | URI of the component that emitted the event | Yes |
| `type` | Domain event type, e.g., `com.example.OrderPlaced` | Yes |
| `subject` | Workflow instance ID or tenant‑unique identifier | Yes |
| `time` | Timestamp (RFC3339) | Yes |
| `traceparent` | W3C trace context for distributed tracing | Yes |

### 3.4 Model Cross‑Reference (URI Resolution)
- **Build‑time:** BPMN models contain logical names (e.g., `credit-check`). A separate model catalogue (YAML) maps logical names to URIs.
- **Compiled process definition:** URIs like `model://credit-control#operation/check` are embedded.
- **Runtime URI resolution:** The engine uses a pluggable `IUriResolver` with schemes: `model://`, `file://`, `http://`, `s3://`, `k8s://configmap/...`.
- **Fallback:** In‑memory registry for monolith deployments.

**Interface:**
```csharp
public interface IUriResolver
{
    Task<ResolvedResource> ResolveAsync(Uri uri, CancellationToken ct);
}
```

---

## 4. Protocol Adapter Plugin Model (ASP.NET Core AOT)

### 4.1 Design Constraints for Native AOT
ASP.NET Core 8 Native AOT does not support dynamic assembly loading (`Assembly.Load`). Therefore:
- **All plugins must be known at compile time.**
- **Discovery is done via source generators** that produce a static registry.
- **No runtime plugin installation** (sidecar processes can be used if absolutely necessary).

### 4.2 `IProtocolAdapter` Interface Definition

```csharp
public interface IProtocolAdapter
{
    string ProtocolName { get; }
    
    Task<CanonicalMessage> SendAsync(
        CanonicalMessage request,
        ProtocolContext context,
        CancellationToken cancellationToken
    );
}

public class ProtocolContext
{
    public TimeSpan Timeout { get; set; }
    public RetryPolicy RetryPolicy { get; set; }
    public IReadOnlyDictionary<string, object> Metadata { get; set; }
}
```

**Semantics:**
- For **sync** protocols (HTTP, gRPC unary), the `Task` completes when the response is received or timeout/error occurs.
- For **async** protocols (Kafka, AMQP), the `Task` completes when the message is **acknowledged** by the broker. For request‑reply over async, the adapter manages a correlation ID and a temporary reply destination.
- For **streaming** (gRPC bi‑di, WebSocket), the `SendAsync` may return a special `StreamingContext` object (details in section 4.5).

### 4.3 Source‑Generated Registry

**Attribute:**
```csharp
[AttributeUsage(AttributeTargets.Class)]
public class ProtocolAdapterAttribute : Attribute
{
    public string ProtocolName { get; }
    public ProtocolAdapterAttribute(string protocolName) => ProtocolName = protocolName;
}
```

**Usage:**
```csharp
[ProtocolAdapter("grpc")]
public class GrpcAdapter : IProtocolAdapter { ... }
```

**Generated code (partial):**
```csharp
public static class ProtocolAdapterRegistry
{
    public static IServiceCollection AddAllAdapters(this IServiceCollection services)
    {
        services.AddKeyedSingleton<IProtocolAdapter, GrpcAdapter>("grpc");
        services.AddKeyedSingleton<IProtocolAdapter, HttpAdapter>("http");
        services.AddKeyedSingleton<IProtocolAdapter, KafkaAdapter>("kafka");
        services.AddKeyedSingleton<IProtocolAdapter, InMemoryAdapter>("in-memory");
        // ... all adapters known at compile time
        return services;
    }
}
```

The engine resolves the adapter at runtime based on `deployment-config.yaml`:

```yaml
bindings:
  services:
    credit-check:
      protocol: grpc
```

### 4.4 Supported Protocols (v1.0)

| Protocol | Description | Features |
|----------|-------------|----------|
| `in-memory` | Direct method call within same process | Zero latency, no serialisation |
| `http` | REST/JSON over HTTP/1.1 or HTTP/2 | OpenAPI compatibility, retries, timeouts |
| `grpc` | gRPC over HTTP/2 | Full streaming (unary, server, client, bi‑di), protobuf, load balancing |
| `kafka` | Apache Kafka with request‑reply pattern | Exactly‑once with idempotent producer, consumer groups, correlation IDs |
| `amqp` (optional) | RabbitMQ, AMQP 0.9.1/1.0 | Queue‑based async, competing consumers |

### 4.5 Streaming Support (gRPC, WebSocket, etc.)

**gRPC streaming (all four patterns) is included in v1.0.**

The `IProtocolAdapter` can optionally implement `IStreamingProtocolAdapter`:

```csharp
public interface IStreamingProtocolAdapter : IProtocolAdapter
{
    Task<IAsyncEnumerable<CanonicalMessage>> StreamAsync(
        IAsyncEnumerable<CanonicalMessage> requestStream,
        ProtocolContext context,
        CancellationToken cancellationToken
    );
}
```

The engine uses this interface when the BPMN model indicates a streaming interaction (e.g., `streaming="true"` on a service task). The underlying gRPC client/server will manage the duplex stream.

---

## 5. Deployment as Code

### 5.1 Configuration File Format (`deployment-config.yaml`)

A complete example for a production environment:

```yaml
apiVersion: bpms/v1
kind: DeploymentConfig
environment: prod
logicalModels:
  bpmn: "s3://bpms-models/production/processes-v2.bpmn"
  dmn: "s3://bpms-models/production/decisions-v2.dmn"
  openapi: "s3://bpms-models/apis/"
canonicalFormat: "cloudevents+jsonschema"

stateBackend:
  type: "postgresql"
  connectionString: "Host=postgres.prod;Database=bpms;Username=..."
  secretRef: "prod/db-credentials"

vectorStore:
  type: "pgvector"
  connectionString: same as stateBackend

blobStorage:
  type: "s3"
  bucket: "bpms-artifacts-prod"
  region: "eu-west-1"
  credentialsSecretRef: "prod/s3-credentials"

bindings:
  services:
    credit-check:
      protocol: grpc
      endpoint: "credit-check.internal:50051"
      tls: true
      timeout: "3s"
      retryPolicy: "prod-retry"
      loadBalancing: "round-robin"
    fraud-detection:
      protocol: http
      endpoint: "http://fraud-simulator.prod:8080"
      timeout: "10s"
  messageChannels:
    order-events:
      protocol: kafka
      brokers: ["kafka1.prod:9092", "kafka2.prod:9092"]
      topic: "order-events"
      consumerGroup: "bpms-engine-prod"
      fromBeginning: false

retryPolicies:
  prod-retry:
    maxAttempts: 3
    backoff:
      type: exponential
      initialInterval: "100ms"
      multiplier: 2.0
      maxInterval: "10s"
    onErrors: ["timeout", "network_error", "5xx"]
    neverRetry: ["invalid_argument"]
  deadLetter:
    enabled: true
    destination: "dlq://failed-calls"

secretsResolver:
  type: "hashicorp-vault"
  address: "https://vault.prod:8200"
  role: "bpms-engine"

apiGateway:
  type: "our-gateway"  # default implementation
  endpoint: "https://api.prod.company.com"
  rateLimiting:
    enabled: true
    requestsPerSecond: 1000
  oauth2:
    issuer: "https://auth.prod.company.com"
    audience: "bpms-api"

resourceManager:
  type: "round-robin"   # simple implementation; "bypass" also available

artifactProcessor:
  type: "reference"     # in‑process reference implementation
  chunking:
    strategy: "sentence"
    maxChunkSize: 1024
  embedding:
    model: "local-mock"   # or "onnx-all-MiniLM"
    dimension: 384
  lifecycle:
    retentionDays: 90
    legalHoldEnabled: true

observability:
  tracing:
    exporter: "otlp"
    endpoint: "http://otel-collector.prod:4318"
  metrics:
    exporter: "prometheus"
    port: 9090
  logging:
    level: "INFO"
    structured: true
  alerting:
    rules:
      - name: "HighErrorRate"
        expr: "rate(bpms_task_errors_total[5m]) > 0.05"
        severity: "warning"
```

### 5.2 Environment Overlays
- Base configuration in `deployment/base.yaml`.
- Environment‑specific overrides in `deployment/prod/overlay.yaml`.
- Merged using **Kustomize** or **ytt** (engine supports JSON Merge Patch).

### 5.3 Configuration Schema (Full Specification)
See Appendix A for the JSON Schema describing all valid fields.

### 5.4 Validation & Dry‑Run CLI

**Command:**
```bash
bpms-validate --env prod --config deployment/prod/deployment-config.yaml --models s3://models/
```

**Checks performed:**
1. YAML syntax and schema conformance.
2. All logical services referenced in BPMN have a `bindings.services` entry.
3. Each bound protocol has a registered adapter (in the compiled engine).
4. Retry policies reference existing definitions.
5. Secret references are resolvable (without exposing values).
6. Transformation mappings (if used) are syntactically correct.
7. Artifact processor configuration is consistent with selected type.

**Dry‑run output:** Effective configuration merged with base, with a summary of resolved endpoints and secret references.

### 5.5 Dynamic Hot Reload (Watcher Implementation)

- The engine watches the configuration source (file system, Kubernetes ConfigMap, Consul KV) for changes.
- On change, it:
  - Validates the new configuration.
  - Applies changes **without restart** to: bindings, retry policies, logging levels, metric exporters.
  - Does **not** change state backend or security plugins (requires restart for those).
- Use `IConfigSource` interface:
```csharp
public interface IConfigSource
{
    IObservable<DeploymentConfig> OnChange { get; }
    Task<DeploymentConfig> LoadAsync();
}
```
- Default implementations: `FileConfigSource` (with `FileSystemWatcher`), `KubernetesConfigMapSource` (with watch API).

---

## 6. Domains 3–13: Core Engine Capabilities (Detailed)

### 6.1 Domain 3 – Inter‑Service Communication

#### 6.1.1 Synchronous Request/Reply
The engine uses `IProtocolAdapter` for synchronous calls. The deployment config specifies:
- `timeout` – maximum wait time.
- `retryPolicy` – which policy to apply.
- `loadBalancing` – algorithm (if more than one endpoint).

All adapters must implement the **uniform error handling** defined in Section 8.1.

#### 6.1.2 Asynchronous Messaging & Events
For one‑way send (publish) or request‑reply over async transport, the adapter:
- Returns `Task` that completes when the message is **persisted** (broker ack).
- For request‑reply, creates a correlation ID and waits for a reply message (with timeout). The reply is delivered via a temporary queue or callback.

#### 6.1.3 Full gRPC Streaming (Client & Server)
- **Client streaming:** Engine sends a stream of messages, receives a single response.
- **Server streaming:** Engine sends one request, receives a stream of responses (e.g., real‑time updates).
- **Bi‑di streaming:** Both sides exchange streams concurrently.
- The engine supports streaming in service tasks and message events. The BPMN model indicates `streaming="true"` and the adapter implements `IStreamingProtocolAdapter`.

#### 6.1.4 Idempotency & Deduplication Integration
- All outgoing messages include the `id` field (idempotency key) from the CloudEvent envelope.
- Incoming messages are deduplicated by the engine using a pluggable `IDeduplicationStore` (default: PostgreSQL table with unique constraint).
- Key format: `{tenantId}:{workflowId}:{activityId}:{messageId}`.
- Retention: keys kept for `max(workflow duration + 7 days, retry window + 24h)`.

### 6.2 Domain 4 – Service Mesh

The engine **does not require** a service mesh. However, when a mesh (Istio, Linkerd, Consul) is present:
- **Traffic routing** (canary, fault injection) is transparent – no engine changes.
- **mTLS** can be handled by the mesh; set `tls: passthrough` in deployment config.
- **Retries and circuit breakers** should be disabled at the engine level if the mesh provides them, to avoid double handling.

### 6.3 Domain 5 – Northbound Exposure (API Management)

#### 6.3.1 `IApiGateway` Plugin Interface
```csharp
public interface IApiGateway
{
    Task<HttpResponse> HandleRequestAsync(HttpRequest request, CancellationToken ct);
    void ConfigureRateLimiting(RateLimitOptions options);
    void ConfigureAuthentication(IAuthenticator authenticator);
}
```

#### 6.3.2 Default Implementation: Our API Gateway Engine
- A separate engine (same codebase) that can be deployed as a sidecar or standalone.
- Provides: OpenAPI validation, rate limiting, OAuth2/OIDC, request/response transformation, caching.
- Integrated with the engine’s `IAuthenticator` and `IAuthorizer`.

#### 6.3.3 Authentication/Authorization Alignment
- The API gateway forwards authenticated principal (JWT) to the engine via `Grpc-Metadata` or HTTP headers.
- The engine’s `IAuthenticator` re‑validates the token (or trusts the gateway if in a trusted network).

### 6.4 Domain 6 – Southbound Integration & Transformation

#### 6.4.1 Model‑Driven Transformation Layer
The engine includes a **built‑in transformation engine** (not delegated to external Camel). Transformations are defined in the deployment config or referenced as models.

**Example transformation (JSONata):**
```yaml
transformations:
  - name: "enrich-customer"
    source: "credit-check-response"
    target: "customer-profile"
    script: |
      {
        "fullName": $join([firstName, lastName], " "),
        "score": creditScore,
        "riskLevel": $match(creditScore, [[0, 600, "high"], [601, 750, "medium"], [751, 850, "low"]])
      }
```

#### 6.4.2 `ITransformer` Interface
```csharp
public interface ITransformer
{
    Task<CanonicalMessage> TransformAsync(CanonicalMessage input, string transformationName, CancellationToken ct);
}
```
- Default implementation: JSONata (via `Jsonata.NET` or embedding the JS engine) and JQ.
- Transformations can be chained (splitters, aggregators) – the engine orchestrates them as part of a service task.

#### 6.4.3 EAI Patterns Inside Engine
The engine supports common enterprise integration patterns **natively**:
- **Content‑based router:** DMN decision table routes message to different services.
- **Splitter/aggregator:** BPMN multi‑instance sub‑processes with correlation.
- **Enricher:** Service task calls an external API and merges results.
- **Message filter:** Conditional sequence flow.

No external integration framework is required; the engine’s workflow capabilities are sufficient.

### 6.5 Domain 7 – State & Caching

#### 6.5.1 `IStateBackend` Interface
```csharp
public interface IStateBackend
{
    Task<WorkflowSnapshot> LoadAsync(string instanceId, CancellationToken ct);
    Task SaveAsync(WorkflowSnapshot snapshot, CancellationToken ct);
    Task AppendEventAsync(WorkflowEvent evt, CancellationToken ct);
    Task<IEnumerable<WorkflowEvent>> ReplayEventsAsync(string instanceId, long fromVersion, CancellationToken ct);
    Task<IEnumerable<string>> ListActiveInstancesAsync(string tenantId, CancellationToken ct);
}
```
- Snapshots are serialized using the canonical message format (CloudEvents + JSON Schema).
- The default implementation uses PostgreSQL with JSONB columns.

#### 6.5.2 `ICache` Interface
```csharp
public interface ICache
{
    Task<T> GetOrCreateAsync<T>(string key, Func<Task<T>> factory, TimeSpan ttl, CancellationToken ct);
    Task InvalidateAsync(string key);
}
```
- Used for process definitions, deployment config, and session data.
- Default: in‑memory `ConcurrentDictionary` with TTL. Production: Redis.

#### 6.5.3 `IDistributedLock` Interface
```csharp
public interface IDistributedLock
{
    Task<IDisposable> AcquireAsync(string resourceName, TimeSpan timeout, CancellationToken ct);
}
```
- Used for leader election (timers, outbox relay).
- Default: PostgreSQL advisory lock (`SELECT pg_try_advisory_lock`). Alternative: Redlock over Redis.

### 6.6 Domain 8 – Configuration & Secrets Management

#### 6.6.1 `IConfigSource` with Hot Reload
Already defined in Section 5.5. The engine watches for changes and reapplies configuration dynamically for non‑critical sections.

#### 6.6.2 `ISecretResolver` Interface
```csharp
public interface ISecretResolver
{
    Task<string> ResolveAsync(string secretRef, CancellationToken ct);
    Task<byte[]> ResolveBinaryAsync(string secretRef, CancellationToken ct);
}
```
- Secret references in deployment config look like: `secretRef: "prod/db-password"`.
- The resolver maps that to a concrete secret (Vault path, Kubernetes secret, environment variable).

#### 6.6.3 Default Resolvers
- `FileSecretResolver`: reads from `/secrets/{ref}` file.
- `EnvironmentVariableSecretResolver`: reads from env var.
- `KubernetesSecretResolver`: calls Kubernetes API.
- `HashicorpVaultResolver`: uses Vault’s KV v2 engine.

### 6.7 Domain 9 – Event Streaming & CEP

#### 6.7.1 `IEventStore` for Event Sourcing (Global, Cross‑Workflow)
```csharp
public interface IEventStore
{
    Task AppendAsync(CloudEvent evt, CancellationToken ct);
    IAsyncEnumerable<CloudEvent> QueryAsync(EventQuery query, CancellationToken ct);
}
```
- All workflow‑generated events (task completion, state changes, agent decisions) are stored.
- **Global event sourcing** allows cross‑workflow analytics, replay, and debugging.
- Default implementation: Kafka (compact topics) or PostgreSQL with event table.

#### 6.7.2 `ICepEngine` for BAM and Observability Processing
```csharp
public interface ICepEngine
{
    Task RegisterRuleAsync(CepRule rule, CancellationToken ct);
    Task<IAsyncEnumerable<CepEvent>> ProcessAsync(IAsyncEnumerable<CloudEvent> eventStream, CancellationToken ct);
}
```
- Used for **Business Activity Monitoring (BAM)** – detect SLA breaches, unusual patterns.
- Also used to process observability events (metrics, logs) for alerting.
- Default implementation: Esper (Java/NET) or Kafka Streams with KSQL.

#### 6.7.3 Default: Kafka + Kafka Streams, Flink as optional
- The engine can be configured to use Kafka as both `IEventStore` and stream processor (Kafka Streams).
- For advanced CEP, Apache Flink can be plugged via a separate adapter.

### 6.8 Domain 10 – Data Consistency & Distributed Transactions

#### 6.8.1 `ITransactionManager` Interface
```csharp
public interface ITransactionManager
{
    Task<ITransaction> BeginTransactionAsync(CancellationToken ct);
}

public interface ITransaction : IAsyncDisposable
{
    Task CommitAsync(CancellationToken ct);
    Task RollbackAsync(CancellationToken ct);
    Task RegisterCompensationAsync(Func<CancellationToken, Task> compensation, string compensationId);
}
```
- The engine uses this for BPMN transactions (`<transaction>` subprocess) and for sagas.
- Default implementation: **Saga orchestrator** – stores compensation actions in the workflow state. For distributed sagas across multiple engine instances, the outbox pattern + idempotent steps is used.

#### 6.8.2 Outbox Pattern Implementation
When a service task must send a message and atomically update state, the engine:
1. Writes the outgoing message to an `outbox` table in the same database as the workflow state (same transaction).
2. A separate `OutboxRelay` (can be embedded or separate service) reads the outbox and publishes to the message broker.
3. Idempotency keys prevent duplicate publishing.

#### 6.8.3 Distributed Saga Across Engine Instances (v1.0)
- Sagas are orchestrated by the engine that started the workflow. The engine’s state backend may be distributed (PostgreSQL cluster). Compensation actions are idempotent.
- For multi‑engine coordination (e.g., workflow A calls workflow B across two engine replicas), the engine uses asynchronous messaging with correlation – no distributed lock is required; the saga state is stored in the initiating engine.

### 6.9 Domain 11 – Observability

#### 6.9.1 `ILogger`, `IMetrics`, `ITracer`, `IAlerting` Interfaces
```csharp
public interface ILogger
{
    void Log(LogLevel level, string message, params object[] args);
}

public interface IMetrics
{
    void Counter(string name, double value, params KeyValuePair<string, string>[] tags);
    void Histogram(string name, double value, params KeyValuePair<string, string>[] tags);
}

public interface ITracer
{
    IDisposable StartSpan(string name, SpanKind kind, params KeyValuePair<string, string>[] attributes);
}

public interface IAlerting
{
    Task SendAsync(Alert alert, CancellationToken ct);
}
```

#### 6.9.2 OpenTelemetry Integration
- Default implementation wraps OpenTelemetry SDK (OTLP exporter).
- All engine spans include: `workflow.id`, `activity.id`, `tenant.id`, `service.name`.
- Trace context is propagated via CloudEvents `traceparent`.

#### 6.9.3 Alerting Rules Defined in Deployment Config
Rules are expressed in the same format as the example in Section 5.1. The engine evaluates them against metrics and logs (via CEP engine) and sends alerts to configured receivers (webhook, Slack, PagerDuty).

### 6.10 Domain 12 – Security

#### 6.10.1 `IAuthenticator` (JWT, mTLS, API Key)
```csharp
public interface IAuthenticator
{
    Task<AuthenticationResult> AuthenticateAsync(HttpRequest request, CancellationToken ct);
}
```
- Default: JWT bearer token validation using OIDC discovery.

#### 6.10.2 `IAuthorizer` with ABAC (Attribute‑Based Access Control)
```csharp
public interface IAuthorizer
{
    Task<bool> IsAllowedAsync(AuthorizationContext context, CancellationToken ct);
}

public class AuthorizationContext
{
    public string Subject { get; set; }  // user or service account
    public string Action { get; set; }   // e.g., "start_workflow", "read_instance"
    public string Resource { get; set; } // e.g., "workflow:order-processing"
    public Dictionary<string, object> Attributes { get; set; } // tenantId, region, etc.
}
```
- Default implementation: **Open Policy Agent (OPA)**. Policies are stored in the deployment config or external bundle server.
- ABAC includes tenant isolation, role‑based permissions, and fine‑grained control over agent actions (e.g., which tools a specific agent can use).

#### 6.10.3 `ISecretResolver` (reused)
Already defined in Section 6.6.2.

### 6.11 Domain 13 – Agentic Systems & AI‑Native Integration

#### 6.11.1 Agent Task Extension to BPMN
A new BPMN task type: `agentTask`. Attributes:
- `agent`: logical name of the agent (bound via deployment config).
- `prompt`: reference to a prompt template (URI).
- `inputVariables`: mapping of workflow variables to agent input.
- `outputVariables`: mapping of agent response to workflow variables.

#### 6.11.2 `IAgentInvoker` Interface (MCP, A2A)
```csharp
public interface IAgentInvoker
{
    Task<CanonicalMessage> InvokeAsync(CanonicalMessage request, AgentContext context, CancellationToken ct);
}

public class AgentContext
{
    public string AgentName { get; set; }
    public Dictionary<string, object> ToolDefinitions { get; set; }
    public IAsyncEnumerable<CanonicalMessage> MemoryStream { get; set; }
}
```
- Supports **Model Context Protocol (MCP)** – the adapter calls an MCP server.
- Supports **Agent‑to‑Agent (A2A)** – the adapter sends CloudEvents to another agent’s endpoint.

#### 6.11.3 `ISkillRegistry` for Skill Discovery
```csharp
public interface ISkillRegistry
{
    Task<IEnumerable<SkillDefinition>> ListSkillsAsync(CancellationToken ct);
    Task<SkillDefinition> GetSkillAsync(string skillName, CancellationToken ct);
}
```
- Skills are versioned (semver) and described by JSON Schema.
- Default implementation: reads from a local directory of skill manifests. Production: registry service via `http` adapter.

#### 6.11.4 Default Implementations
- `MCPAdapter`: connects to an MCP server (over stdio or HTTP/SSE).
- `A2AAdapter`: sends CloudEvents over HTTP or Kafka to another agent.
- `InMemoryAgentInvoker`: for testing (mock agent).

---

## 7. Extended Domains (14,15,16,20,42,65) – Detailed

### 7.1 Domain 14 – UI Backend & Frontend Platform

#### 7.1.1 `IUserTaskProvider` Interface
```csharp
public interface IUserTaskProvider
{
    Task CreateTaskAsync(UserTask task, CancellationToken ct);
    Task CompleteTaskAsync(string taskId, UserTaskResult result, CancellationToken ct);
    Task<IEnumerable<UserTask>> ListTasksAsync(string userId, CancellationToken ct);
}
```
- The engine emits user task events (via this interface) to the task provider.
- The default provider is our **BFF engine**.

#### 7.1.2 `IRealTimePush` Interface (WebSocket/SSE)
```csharp
public interface IRealTimePush
{
    Task SendToUserAsync(string userId, CloudEvent message, CancellationToken ct);
    Task BroadcastToTenantAsync(string tenantId, CloudEvent message, CancellationToken ct);
}
```
- Default: built‑in ASP.NET Core WebSockets (if the BFF engine is embedded). For production, the BFF engine handles push.

#### 7.1.3 Mandatory Default: Separate BFF Engine (Our Own)
- The **BFF engine** is a separate service (container) that:
  - Provides a REST API for frontend (React, React Native, etc.).
  - Consumes the engine’s northbound API (via `IApiGateway`).
  - Manages user sessions, authentication, and WebSocket connections.
  - Implements the UI for human task list, agent conversation, and workflow monitoring.
- Deployment: can be sidecar (same pod) or separate deployment. Configuration:
```yaml
ui:
  bffEngine:
    enabled: true
    endpoint: "http://bpms-bff:8080"
    authentication: "shared"   # reuse engine's authenticator
```

#### 7.1.4 BFF Engine API Contract
- OpenAPI definition available in the engine’s documentation.
- Key endpoints: `GET /tasks`, `POST /tasks/{id}/complete`, `GET /workflows/{id}`, `GET /agent/conversations/{id}`.

### 7.2 Domain 15 – Load Balancing & Traffic Routing

#### 7.2.1 `IResourceManager` Interface
```csharp
public interface IResourceManager
{
    Task<Endpoint> ResolveEndpointAsync(string serviceName, RequestContext requestContext, CancellationToken ct);
    Task ReportHealthAsync(string serviceName, Endpoint endpoint, HealthStatus status, CancellationToken ct);
}
```
- The engine uses this before each call to obtain the target endpoint.
- The resource manager can also manage messaging state (e.g., Kafka partition assignment) – optional.

#### 7.2.2 `ILoadBalancer` Interface (Algorithms)
```csharp
public interface ILoadBalancer
{
    Endpoint SelectEndpoint(IEnumerable<Endpoint> endpoints, RequestContext context);
}
```
- Algorithms provided: `round-robin`, `least-connections`, `consistent-hashing`, `random`, `weighted`.

#### 7.2.3 Default Implementations: Bypass, Simple Round‑Robin
- `BypassResourceManager`: returns the first endpoint from a static list (or the only one).
- `RoundRobinLoadBalancer`: cycles through endpoints; supports weight.

#### 7.2.4 Work Distribution and Service/Messaging State Management
- For **work distribution** among workers (e.g., multiple engine replicas), the engine uses the resource manager to assign work items (e.g., timer callbacks) – this is integrated with the `IDistributedLock`.
- For **messaging state** (e.g., Kafka consumer group partitions), the engine delegates to the protocol adapter. The resource manager can provide partition assignment hints, but the adapter ultimately manages it.

### 7.3 Domain 16 – Data Persistence & Storage

#### 7.3.1 Reuse of `IStateBackend`, `IVectorStore`, `IBlobStorage`
- `IStateBackend`: as defined in 6.5.
- `IVectorStore`:
```csharp
public interface IVectorStore
{
    Task AddAsync(string collection, Vector vector, CloudEvent metadata, CancellationToken ct);
    Task<IEnumerable<VectorSearchResult>> SimilaritySearchAsync(string collection, float[] queryVector, int limit, CancellationToken ct);
}
```
- `IBlobStorage`:
```csharp
public interface IBlobStorage
{
    Task<Stream> ReadAsync(string blobId, CancellationToken ct);
    Task<string> WriteAsync(Stream data, string contentType, CancellationToken ct);
    Task DeleteAsync(string blobId, CancellationToken ct);
}
```

#### 7.3.2 Alignment with Canonical Message Model
- All stored data must be convertible to/from CloudEvents + JSON Schema. The engine stores state as JSON‑encoded CloudEvents envelopes.
- For vector embeddings, the `metadata` field contains the `id` of the canonical message.

#### 7.3.3 Default Implementations
- `PostgreSqlStateBackend`: uses Npgsql + JSONB.
- `PgVectorStore`: uses `pgvector` extension.
- `S3BlobStorage`: AWS S3 or MinIO; local file system for development.

### 7.4 Domain 20 – Artifact Processing & Abstraction

#### 7.4.1 Renamed from "Content Processing"
The domain now covers **any artifact** (documents, data files, media, CAD, etc.).

#### 7.4.2 Interfaces

```csharp
public interface IArtifactProcessor
{
    Task<ProcessedArtifact> ProcessAsync(Artifact artifact, ProcessingOptions options, CancellationToken ct);
}

public interface IChunker
{
    IAsyncEnumerable<Chunk> ChunkAsync(Stream content, ChunkingOptions options, CancellationToken ct);
}

public interface IEmbedder
{
    Task<float[]> EmbedAsync(string text, CancellationToken ct);
    Task<IEnumerable<float[]>> EmbedBatchAsync(IEnumerable<string> texts, CancellationToken ct);
}

public interface IGraphStore
{
    Task AddNodeAsync(string nodeId, Dictionary<string, object> properties, CancellationToken ct);
    Task AddEdgeAsync(string fromNode, string toNode, string relation, CancellationToken ct);
}

public interface IMemoryStore
{
    Task AddMemoryAsync(string ownerId, Memory memory, CancellationToken ct);
    Task<IEnumerable<Memory>> RecallAsync(string ownerId, string query, int limit, CancellationToken ct);
}

public interface IArtifactLifecycleManager
{
    Task RegisterArtifactAsync(ArtifactMetadata metadata, CancellationToken ct);
    Task EnforceRetentionPoliciesAsync(CancellationToken ct);
    Task SetLegalHoldAsync(string artifactId, bool hold, CancellationToken ct);
}
```

#### 7.4.3 Full Lifecycle Management (v1.0)
- Artifacts are stored in `IBlobStorage`. Metadata (version, retention date, legal hold) in `IStateBackend`.
- A background job runs periodically to delete or archive expired artifacts based on policy.

#### 7.4.4 Default Implementation: Reference In‑Process
- **Chunker:** sentence splitter, fixed‑size overlap.
- **Embedder:** local mock (returns random vector) – enough for testing.
- **GraphStore:** in‑memory (development) or PostgreSQL with pgcrypto (production).
- **MemoryStore:** uses `IVectorStore` under the hood.

#### 7.4.5 Optional Plugins (Compatibility Evaluation Ongoing)
- **LangChain** (Python sidecar) – communicates via HTTP/gRPC.
- **ONNX Runtime** (embedding models) – native C# binding.
- **Azure AI Document Intelligence** – REST API adapter.
These are not mandatory; the reference implementation suffices for most use cases.

### 7.5 Domain 42 – Code & Model Provenance

#### 7.5.1 `IProvenanceRecorder` Interface
```csharp
public interface IProvenanceRecorder
{
    Task RecordAsync(ProvenanceEvent evt, CancellationToken ct);
}
```

#### 7.5.2 `IModelResolver` Interface
```csharp
public interface IModelResolver
{
    Task<ModelVersion> ResolveAsync(string logicalModelName, CancellationToken ct);
}
```
- Used to map `llm://gpt4` → `gpt-4-turbo-2024-04-09`.

#### 7.5.3 Default: In‑Memory (dev) + MLflow/LangSmith adapter optional
- The engine records provenance events as CloudEvents in the event store.
- For production, the recorder can be configured to push to MLflow or LangSmith.

#### 7.5.4 Skill and Prompt Versioning
- Skills are versioned using semver. The provenance event includes `skillName`, `skillVersion`, `promptTemplateId`.

### 7.6 Domain 65 – Data Masking & Test Data

#### 7.6.1 `IDataMasker` Interface (JSONPath‑based)
```csharp
public interface IDataMasker
{
    Task<CanonicalMessage> MaskAsync(CanonicalMessage input, MaskingRules rules, CancellationToken ct);
}
```
- Rules: JSONPath expression + mask type (redact, hash, replace, partial).

#### 7.6.2 `ITestDataGenerator` Interface (Bogus/Faker)
```csharp
public interface ITestDataGenerator
{
    Task<T> GenerateAsync<T>(string schemaName, CancellationToken ct);
}
```
- Uses a schema registry to generate realistic data.

#### 7.6.3 Automatic Masking Middleware for Non‑Prod Environments
- The engine can be configured with a `MaskingMiddleware` that intercepts all workflow inputs and outputs in non‑production environments and applies a default mask configuration.

---

## 8. Cross‑Cutting Concerns

### 8.1 Error & Retry Policy Language (JSON/YAML DSL)

Full specification:

```yaml
retryPolicy:
  maxAttempts: 3                     # integer, >0
  backoff:
    type: exponential | fixed | none
    initialInterval: "100ms"         # duration string
    multiplier: 2.0                  # for exponential
    maxInterval: "10s"               # for exponential
  onErrors: ["timeout", "network_error", "5xx"]  # list of error categories
  neverRetry: ["invalid_argument", "unauthorized"] # fail immediately
deadLetter:
  enabled: true
  destination: "dlq://failed-calls"  # logical DLQ address
```

The engine evaluates this policy for each invocation. The protocol adapter implements the backoff and retry loop.

### 8.2 Pluggable Backends Summary Table

| Concern | Interface | Default v1.0 |
|---------|-----------|---------------|
| State storage | `IStateBackend` | PostgreSQL |
| Vector store | `IVectorStore` | pgvector |
| Blob storage | `IBlobStorage` | S3 / local file |
| Transaction | `ITransactionManager` | Saga orchestrator |
| Observability | `IObservability` | OpenTelemetry |
| Security (incoming) | `IAuthenticator` | JWT |
| Security (outgoing) | `ISecretResolver` | Kubernetes / file |
| Timer | `ITimerScheduler` | In‑memory / PostgreSQL polling |
| Deduplication | `IDeduplicationStore` | PostgreSQL |
| Resource management | `IResourceManager` | Bypass + round‑robin |
| Artifact processing | `IArtifactProcessor` | Reference implementation |
| Provenance | `IProvenanceRecorder` | In‑memory |
| Configuration source | `IConfigSource` | File (watcher) |
| API Gateway | `IApiGateway` | Our API Gateway engine |
| UI Task Provider | `IUserTaskProvider` | BFF engine |

### 8.3 Idempotency Key Storage and Retention
- **Storage:** `IDeduplicationStore` (default PostgreSQL table with unique constraint on `(key)`).
- **Key format:** `{tenantId}:{workflowId}:{activityId}:{messageId}`.
- **Retention:** Keys are retained for `max(workflow duration + 7 days, retry window + 24h)`. A background job cleans up expired keys.

### 8.4 Message Ordering and Exactly‑Once Semantics
- The engine does **not** guarantee global message ordering across different workflow instances. Within a single instance, order is determined by the BPMN sequence flow.
- For exactly‑once processing: at‑least‑once delivery + idempotent handler (using deduplication store).

---

## 9. Domain Mapping Table (All Domains 1–65)

| Domain | Relationship | Spec Section |
|--------|--------------|--------------|
| 1 Runtime Infrastructure | External (Kubernetes, Nomad) | Appendix |
| 2 Service Discovery | External (K8s DNS, Consul) | 6.1 |
| 3 East‑West Comm | Core | 6.1 |
| 4 Service Mesh | Optional | 6.2 |
| 5 Northbound Exposure | Core + plugin | 6.3 |
| 6 Southbound Integration | Core | 6.4 |
| 7 State & Caching | Core plugin | 6.5 |
| 8 Config & Secrets | Core plugin | 6.6 |
| 9 Event Streaming & CEP | Core plugin | 6.7 |
| 10 Data Consistency | Core plugin | 6.8 |
| 11 Observability | Core plugin | 6.9 |
| 12 Security | Core plugin | 6.10 |
| 13 Agentic AI | Core feature | 6.11 |
| 14 UI Backend & Frontend | Separate BFF (mandatory) | 7.1 |
| 15 Load Balancing & Traffic Routing | Optional plugin | 7.2 |
| 16 Data Persistence & Storage | Core plugin | 7.3 |
| 17 Workflow Orchestration | Core | 2 |
| 18 Knowledge & Analytics | External (engine calls) | – |
| 19 Tool Integration | Core (IProtocolAdapter) | 4 |
| 20 Artifact Processing | Core plugin | 7.4 |
| 21 Developer Experience | External | – |
| 22 CI/CD | External | – |
| 23 Testing & QA | External | – |
| 24 IAM | External (engine uses IAuthenticator) | 6.10 |
| 25 Compliance & Audit | Engine emits events | 6.7 |
| 26 Cost Management | External | – |
| 27 Disaster Recovery | External (state backend must support backups) | – |
| 28 API Lifecycle Management | External | – |
| 29 Multi‑Tenancy | Core (tenantId) | 6.10 |
| 30 Edge Computing | Engine can run on K3s | – |
| 31 Service Versioning | Core (version pinning) | 5 |
| 32 High Availability | Core (state backend clustering) | 6.5 |
| 33 Data Privacy | External (engine calls IDataMasker) | 7.6 |
| 34 Data Pipeline | Engine orchestrates | 2 |
| 35 Digital Twins | External | – |
| 36 Scheduling | Core (ITimerScheduler) | 6.5 |
| 37 Notifications | Engine via IProtocolAdapter | 6.1 |
| 38 Localization | External | – |
| 39 Licensing | External | – |
| 40 Search & Full‑Text Indexing | External | – |
| 41 A/B Testing & Feature Flags | External | – |
| 42 Code & Model Provenance | Core plugin | 7.5 |
| 43 Synthetic Data Generation | External (engine calls ITestDataGenerator) | 7.6 |
| 44 Blockchain | External | – |
| 45 Quantum‑Safe Crypto | External | – |
| 46 Capacity Planning | External | – |
| 47 Data Governance | External | – |
| 48 Service Catalog | External | – |
| 49 Session & State Replication | Core (state backend) | 6.5 |
| 50 Mobile Device Management | External | – |
| 51 Voice & Conversational | External | – |
| 52 Block Storage | External (engine uses CSI) | – |
| 53 Message Transformation | Core (ITransformer) | 6.4 |
| 54 Time Synchronisation | Engine relies on host clock + logical clocks | 6.5 |
| 55 Document Lifecycle | Core (via IArtifactLifecycleManager) | 7.4 |
| 56 HSM & Key Lifecycle | External (secret resolver) | 6.6 |
| 57 Network Policy | External | – |
| 58 Infrastructure as Code | External | – |
| 59 Environment Management | External | – |
| 60 Schema & DB Migration | Engine uses Flyway/Liquibase | – |
| 61 Data Archival | External | – |
| 62 Incident Response | External (engine logs feed SIEM) | – |
| 63 Sustainability | External | – |
| 64 Vendor Abstraction | Optional (Dapr) | – |
| 65 Data Masking & Test Data | Core plugin | 7.6 |

---

## 10. Open Issues & Future Versions

**No open issues for v1.0.** All features previously considered deferred have been included per architectural decisions.

**Planned for v1.1:**
- Full Agentic AI extension specification (enhanced `IAgentInvoker` with streaming, tool calling, and memory).
- Dynamic protocol discovery for sidecar proxies.

**Planned for v2.0:**
- Automated migration of running workflow instances across model versions.
- Cross‑region active‑active state backend.

---

## 11. Appendices

### Appendix A: Full `deployment-config.yaml` Schema (JSON Schema)

*(Provided as a separate JSON Schema file – omitted here for brevity but available in the source repository.)*

### Appendix B: Example Configurations (dev, stage, prod)

**Development (`dev/deployment-config.yaml`):**
```yaml
environment: dev
stateBackend:
  type: "in-memory"
bindings:
  services:
    credit-check:
      protocol: in-memory
artifactProcessor:
  type: "reference"
  embedding:
    model: "mock"
observability:
  logging:
    level: "DEBUG"
```

**Production (`prod/deployment-config.yaml`):** as shown in Section 5.1.

### Appendix C: Plugin Development Walkthrough (Source Generator)

*Step‑by‑step guide for creating a custom `IProtocolAdapter` using ASP.NET Core AOT source generators. (Detailed in a separate developer guide.)*

### Appendix D: Glossary of Terms

- **Deployment Agnostic:** Ability to run the same model binaries on any infrastructure without changes.
- **Canonical Message:** CloudEvent + JSON Schema.
- **Idempotency Key:** Unique identifier for deduplication.
- **Artifact:** Any document, data file, or media processed by the engine.
- **BFF Engine:** Separate UI backend service (our own) that consumes engine APIs.
- **Agent Task:** BPMN extension for invoking AI agents.
- **MCP:** Model Context Protocol.
- **A2A:** Agent‑to‑Agent protocol.
- **ABAC:** Attribute‑Based Access Control.
- **CEP:** Complex Event Processing.
- **BAM:** Business Activity Monitoring.

---

**End of Document v1.0.1**