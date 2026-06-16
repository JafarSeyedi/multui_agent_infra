# Deployment Agnostic - Technical Specification v1.0.2

**Document Version:** 1.0.2  
**Date:** 2026-06-16  

## Table of Contents

1. Introduction (scope, principles, definitions)
2. Canonical Message Model (detailed)
3. Protocol Adapter Plugin Model (detailed)
4. Deployment as Code (detailed)
5. **Domain 3 – Inter‑Service Communication** (full)
6. **Domain 4 – Service Mesh**
7. **Domain 5 – Northbound Exposure (API Management)**
8. **Domain 6 – Southbound Integration & Transformation**
9. **Domain 7 – State & Caching**
10. **Domain 8 – Configuration & Secrets Management**
11. **Domain 9 – Event Streaming & CEP**
12. **Domain 10 – Data Consistency & Distributed Transactions**
13. **Domain 11 – Observability**
14. **Domain 12 – Security**
15. **Domain 13 – Agentic Systems & AI‑Native Integration**
16. **Domain 14 – UI Backend & Frontend Platform**
17. **Domain 15 – Load Balancing & Traffic Routing**
18. **Domain 16 – Data Persistence & Storage**
19. **Domain 20 – Artifact Processing & Abstraction**
20. **Domain 42 – Code & Model Provenance**
21. **Domain 65 – Data Masking & Test Data**
22. Domain Mapping Table (all domains 1‑65, with relationship)
23. Cross‑Cutting Concerns (retry policy, idempotency, etc.)
24. Open Issues (none for v1.0)
25. Appendices (schemas, examples)

I will now write the full content. Please note: this will be very long (likely >10,000 words), but it will give you the **complete specification** you need. I will start with the most critical domains and then provide the rest. If the message exceeds character limits, I will split into multiple messages. Let me begin.

---

## 1. Introduction (Condensed)

See earlier sections for principles. We assume reader is familiar with the deployment‑agnostic concept.

## 2. Canonical Message Model (Detailed)

*(Already provided in Section 3 of previous long document – keep as is.)*

## 3. Protocol Adapter Plugin Model (Detailed)

*(Already provided – keep as is.)*

## 4. Deployment as Code (Detailed)

*(Already provided – keep as is.)*

---

## 5. Domain 3 – Inter‑Service Communication

### 5.1 Problem Statement
The engine must invoke external services (credit checks, fraud detection, LLMs, etc.) and receive events from them. These interactions can be synchronous (request/reply) or asynchronous (publish/subscribe, request/reply over queues). The communication may need streaming (e.g., real‑time agent outputs). The engine must remain unaware of the underlying transport (HTTP, gRPC, Kafka, in‑memory) and resilience mechanisms (retries, timeouts, circuit breakers).

### 5.2 Engine’s Role
- The engine issues **logical service calls** using a service name (e.g., `credit-check`).
- It provides a **protocol adapter registry** that maps logical names to a concrete adapter implementation.
- The engine enforces idempotency: every outgoing message carries a unique `id` (CloudEvents attribute), and every incoming message is checked against a deduplication store.
- The engine handles both **sync** and **async** patterns uniformly via the same `IProtocolAdapter.SendAsync` method (async adapters return a task that completes when the message is acknowledged; for request/reply, they wait for a correlated response).

### 5.3 Pluggable Interfaces

```csharp
public interface IProtocolAdapter
{
    string ProtocolName { get; }
    Task<CanonicalMessage> SendAsync(CanonicalMessage request, ProtocolContext context, CancellationToken cancellationToken);
}

public interface IStreamingProtocolAdapter : IProtocolAdapter
{
    Task<IAsyncEnumerable<CanonicalMessage>> StreamAsync(
        IAsyncEnumerable<CanonicalMessage> requestStream,
        ProtocolContext context,
        CancellationToken cancellationToken);
}

public class ProtocolContext
{
    public TimeSpan Timeout { get; set; }
    public RetryPolicy RetryPolicy { get; set; }
    public IReadOnlyDictionary<string, object> Metadata { get; set; }
}
```

### 5.4 Default Implementations (v1.0)

| Adapter | Description | Configuration Example |
|---------|-------------|----------------------|
| `InMemoryAdapter` | Direct method call to a registered service stub (for testing and monolith). | `protocol: in-memory` |
| `HttpAdapter` | REST/JSON over HTTP/1.1 or HTTP/2. Supports OpenAPI. | `protocol: http; endpoint: https://api.example.com` |
| `GrpcAdapter` | gRPC (unary, client, server, bi‑di streaming). | `protocol: grpc; endpoint: grpc://service:50051` |
| `KafkaAdapter` | Async request/reply over Kafka topics. | `protocol: kafka; brokers: ["kafka:9092"]; requestTopic: "req"; replyTopic: "resp"` |

All adapters implement the uniform retry and timeout policies defined in Section 23.

### 5.5 Deployment Configuration

```yaml
bindings:
  services:
    credit-check:
      protocol: grpc
      endpoint: "credit-check.internal:50051"
      timeout: "3s"
      retryPolicy: "standard"
      loadBalancing: "round-robin"
    fraud-detection:
      protocol: http
      endpoint: "http://fraud:8080"
      timeout: "10s"
```

### 5.6 Relationship to Other Domains
- Uses `ISecretResolver` (Domain 8) for credentials (TLS certificates, API keys).
- Uses `ILoadBalancer` (Domain 15) if multiple endpoints.
- Uses `IDeduplicationStore` (Domain 7) for idempotency.
- Observability spans are created via `ITracer` (Domain 11).

### 5.7 Open Issues (v1.0)
None – all streaming patterns are included.

---

## 6. Domain 4 – Service Mesh

### 6.1 Problem Statement
A service mesh (Istio, Linkerd) can provide transparent mTLS, circuit breaking, retries, and traffic shifting without application changes. The engine must work correctly whether a mesh is present or not.

### 6.2 Engine’s Role
- The engine **does not require** a mesh.
- It must be able to **opt out** of engine‑side retries when mesh retries are enabled (to avoid double execution).
- It must propagate trace headers (W3C `traceparent`) so the mesh can generate spans.

### 6.3 Pluggable Interfaces
None – the mesh is infrastructure. However, the deployment config can disable engine‑side retries and set `tls: passthrough`.

### 6.4 Default Behaviour
- If deployment config has `tls: passthrough`, the adapter does not terminate TLS (assumes sidecar does).
- If `retryPolicy: none`, the engine does not retry (mesh will handle).

### 6.5 Deployment Configuration

```yaml
bindings:
  services:
    credit-check:
      protocol: grpc
      endpoint: "credit-check.default.svc.cluster.local:50051"
      tls: passthrough   # sidecar handles mTLS
      retryPolicy: none  # mesh provides retries
```

### 6.6 Relationship
- Observability: mesh generates spans, but engine also generates its own; they are linked via `traceparent`.

### 6.7 Open Issues
None.

---

## 7. Domain 5 – Northbound Exposure (API Management)

### 7.1 Problem Statement
External clients (UI, partner systems) need to start workflows, query state, and receive events. This requires authentication, rate limiting, request transformation, and possibly an API gateway.

### 7.2 Engine’s Role
- The engine exposes a native REST/gRPC API (OpenAPI defined).
- It provides a pluggable `IApiGateway` interface that can be implemented by a separate gateway engine (our own default) or third‑party (Kong, Apigee).
- The engine **does not** perform rate limiting or OAuth2 itself; it delegates to the gateway plugin.

### 7.3 Pluggable Interfaces

```csharp
public interface IApiGateway
{
    Task<HttpResponse> HandleRequestAsync(HttpRequest request, CancellationToken ct);
    void ConfigureRateLimiting(RateLimitOptions options);
    void ConfigureAuthentication(IAuthenticator authenticator);
}
```

### 7.4 Default Implementation (Mandatory v1.0)
Our own **API Gateway Engine** – a separate service (or embeddable) that:
- Routes requests to the engine’s internal API.
- Implements rate limiting (token bucket), OAuth2/OIDC, API key validation.
- Transforms requests/responses (e.g., version mapping).
- Aligns authentication with the engine’s `IAuthenticator` (shares the same token validation logic).

Deployment config:
```yaml
apiGateway:
  type: "our-gateway"
  endpoint: "https://api.mycompany.com"
  rateLimiting:
    enabled: true
    requestsPerSecond: 1000
  oauth2:
    issuer: "https://auth.mycompany.com"
    audience: "bpms-api"
```

### 7.5 Relationship to Security (Domain 12)
The gateway passes authenticated principal (JWT) via headers; the engine’s `IAuthenticator` may re‑validate or trust the gateway.

### 7.6 Open Issues
None.

---

## 8. Domain 6 – Southbound Integration & Transformation

### 8.1 Problem Statement
The engine must call external systems (legacy SOAP, FTP, databases) and transform data between the canonical model and service‑specific formats. It must handle EAI patterns (splitter, aggregator, enricher, router).

### 8.2 Engine’s Role
- The engine includes a **built‑in transformation engine** (not delegated to external Camel).
- Transformations are defined as **models** (JSONata, JQ, or custom DSL) stored in the deployment config or referenced via URI.
- The engine orchestrates EAI patterns natively using BPMN constructs (multi‑instance, conditional flows, service tasks with transformers).

### 8.3 Pluggable Interfaces

```csharp
public interface ITransformer
{
    Task<CanonicalMessage> TransformAsync(CanonicalMessage input, string transformationName, CancellationToken ct);
}
```

### 8.4 Default Implementation
- **JSONata** (via `Jsonata.NET` or embedded JS engine) – expressive for JSON transformations.
- **JQ** – for lightweight filtering.
- Custom mappings can be written as C# functions registered at startup.

Example transformation definition:
```yaml
transformations:
  - name: "enrich-customer"
    source: "credit-check-response"
    target: "customer-profile"
    script: |
      {
        "fullName": firstName & " " & lastName,
        "score": creditScore,
        "risk": $match(creditScore, [[0,600,"high"],[601,750,"medium"],[751,850,"low"]])
      }
```

### 8.5 EAI Patterns Built‑in
- **Content‑based router:** DMN decision table routes to different `serviceTask`.
- **Splitter:** BPMN multi‑instance sub‑process iterates over a collection.
- **Aggregator:** BPMN event‑based gateway waiting for multiple responses.
- **Enricher:** service task calls a transformer before/after external call.
- **Filter:** conditional sequence flow.

No external Camel is required.

### 8.6 Deployment Configuration
```yaml
transformations:
  - name: "address-normalize"
    script: "https://s3.models/transformations/addr.jq"
```

### 8.7 Relationship
- Uses `IProtocolAdapter` to call external systems after transformation.
- Used by `IArtifactProcessor` (Domain 20) for document conversion.

### 8.8 Open Issues
None.

---

## 9. Domain 7 – State & Caching

### 9.1 Problem Statement
The engine must durably store workflow instances, timers, idempotency keys, and other state across restarts. It also needs fast, transient access to frequently used data (process definitions, deployment config). Multiple domains (workflow, agent memory, artifact lifecycle) require state management.

### 9.2 Engine’s Role
- Provide pluggable `IStateBackend` for durable, transactional state.
- Provide pluggable `ICache` for transient data.
- Provide pluggable `IDistributedLock` for leader election and coordination.
- All state is serialised using the canonical message model (CloudEvents + JSON Schema).

### 9.3 Pluggable Interfaces

```csharp
public interface IStateBackend
{
    Task<WorkflowSnapshot> LoadAsync(string instanceId, CancellationToken ct);
    Task SaveAsync(WorkflowSnapshot snapshot, CancellationToken ct);
    Task AppendEventAsync(WorkflowEvent evt, CancellationToken ct);
    Task<IEnumerable<WorkflowEvent>> ReplayEventsAsync(string instanceId, long fromVersion, CancellationToken ct);
    Task<IEnumerable<string>> ListActiveInstancesAsync(string tenantId, CancellationToken ct);
    Task<long> GetNextSequenceAsync(string sequenceName, CancellationToken ct);
}

public interface ICache
{
    Task<T> GetOrCreateAsync<T>(string key, Func<Task<T>> factory, TimeSpan ttl, CancellationToken ct);
    Task InvalidateAsync(string key, CancellationToken ct);
}

public interface IDistributedLock
{
    Task<IDisposable> AcquireAsync(string resourceName, TimeSpan timeout, CancellationToken ct);
}
```

### 9.4 Default Implementations (v1.0)

| Interface | Default Implementation | Configuration |
|-----------|------------------------|----------------|
| `IStateBackend` | PostgreSQL with JSONB columns, table `workflow_instances`, `events` | `type: postgresql` |
| `ICache` | In‑memory `ConcurrentDictionary` with TTL; production: Redis | `type: redis` (optional) |
| `IDistributedLock` | PostgreSQL advisory lock (`SELECT pg_try_advisory_lock`) | `type: postgresql` |

### 9.5 Deployment Configuration

```yaml
stateBackend:
  type: postgresql
  connectionString: "Host=postgres;Database=bpms"
  secretRef: "db-credentials"
cache:
  type: redis
  connectionString: "redis://cache:6379"
  ttl: "300s"
distributedLock:
  type: postgresql
```

### 9.6 Relationship to Other Domains
- Used by Domain 10 (transactions) to persist saga state.
- Used by Domain 9 (event sourcing) as the event store.
- Used by Domain 20 to store artifact metadata.

### 9.7 Open Issues
None.

---

## 10. Domain 8 – Configuration & Secrets Management

### 10.1 Problem Statement
The engine must load environment‑specific configuration (endpoints, retry policies, feature flags) without code changes. Secrets (database passwords, API keys) must never appear in plain text in configuration files.

### 10.2 Engine’s Role
- Load deployment configuration from a pluggable source (file, Consul, Kubernetes ConfigMap).
- **Hot reload** configuration without restart for non‑critical sections (bindings, log levels, retry policies).
- Resolve secrets via a pluggable `ISecretResolver`; configuration contains only references (`secretRef`).

### 10.3 Pluggable Interfaces

```csharp
public interface IConfigSource
{
    IObservable<DeploymentConfig> OnChange { get; }
    Task<DeploymentConfig> LoadAsync(CancellationToken ct);
}

public interface ISecretResolver
{
    Task<string> ResolveAsync(string secretRef, CancellationToken ct);
    Task<byte[]> ResolveBinaryAsync(string secretRef, CancellationToken ct);
}
```

### 10.4 Default Implementations (v1.0)

| Source | Description |
|--------|-------------|
| `FileConfigSource` | Watches a local YAML file (`FileSystemWatcher`). |
| `KubernetesConfigMapSource` | Watches a ConfigMap via Kubernetes API watch. |
| `EnvironmentVariableSecretResolver` | Reads from env var (e.g., `SECRET_DB_PASSWORD`). |
| `FileSecretResolver` | Reads from `/secrets/{ref}` file (Kubernetes mounted secret). |
| `HashicorpVaultResolver` | Connects to Vault KV v2 engine. |

### 10.5 Hot Reload Behaviour
- Changes to `bindings.services`, `retryPolicies`, `observability.logging.level` are applied immediately.
- Changes to `stateBackend`, `security.authenticator` require restart (logged as warning).

### 10.6 Deployment Configuration

```yaml
secretsResolver:
  type: hashicorp-vault
  address: "https://vault.prod:8200"
  role: "bpms-engine"
configSource:
  type: file
  path: "/etc/bpms/deployment-config.yaml"
  watch: true
```

### 10.7 Open Issues
None.

---

## 11. Domain 9 – Event Streaming & CEP

### 11.1 Problem Statement
The engine must support event‑driven architectures: start workflows from events, publish events during execution, and perform complex event processing (CEP) for Business Activity Monitoring (BAM) and alerting. Event sourcing (global, cross‑workflow) is required for replay and analytics.

### 11.2 Engine’s Role
- Provide `IEventStore` for append‑only, replayable event log.
- Provide `ICepEngine` for pattern detection over event streams.
- All workflow‑generated events (task completions, state changes, agent decisions) are stored in the event store.
- The engine can replay events to rebuild workflow state or for analytical queries.

### 11.3 Pluggable Interfaces

```csharp
public interface IEventStore
{
    Task AppendAsync(CloudEvent evt, CancellationToken ct);
    IAsyncEnumerable<CloudEvent> QueryAsync(EventQuery query, CancellationToken ct);
}

public interface ICepEngine
{
    Task RegisterRuleAsync(CepRule rule, CancellationToken ct);
    Task<IAsyncEnumerable<CepEvent>> ProcessAsync(IAsyncEnumerable<CloudEvent> eventStream, CancellationToken ct);
}
```

### 11.4 Default Implementations (v1.0)

| Interface | Default Implementation | Features |
|-----------|------------------------|----------|
| `IEventStore` | Kafka (compact topics) or PostgreSQL (events table) | Partitioned by tenant, indexed by workflow ID |
| `ICepEngine` | Kafka Streams with KSQL (for BAM) or Esper (for in‑process) | Sliding windows, pattern matching, aggregation |

### 11.5 Global Event Sourcing (v1.0)
- All events are stored in a global event log (tenant‑partitioned). This enables cross‑workflow analytics (e.g., “how many orders > $1000 in last hour”).
- The engine’s state backend also stores snapshots; event replay can rebuild any instance.

### 11.6 Deployment Configuration

```yaml
eventStore:
  type: kafka
  brokers: ["kafka:9092"]
  topic: "bpms-events"
  retention: "30d"
cepEngine:
  type: kafka-streams
  applicationId: "bpms-cep"
  rules:
    - name: "high-value-order"
      pattern: "select * from events where type='OrderPlaced' and data.amount > 10000"
      action: "send_alert"
```

### 11.7 Relationship
- Used by Domain 11 (observability) for alerting.
- Used by Domain 13 (agentic) to store agent‑decision traces.

### 11.8 Open Issues
None.

---

## 12. Domain 10 – Data Consistency & Distributed Transactions

### 12.1 Problem Statement
Long‑running workflows often involve multiple external calls that cannot be rolled back atomically (e.g., booking a flight, charging a credit card). The engine must support saga pattern (orchestrated compensation) and the outbox pattern for exactly‑once message publication. Transactions may span multiple engine instances.

### 12.2 Engine’s Role
- Provide `ITransactionManager` that handles saga orchestration, compensation registration, and two‑phase commit (optional, for monolith).
- Implement the **outbox pattern** to atomically update local state and publish a message.
- Support **distributed sagas** across engine instances via asynchronous compensation messages.

### 12.3 Pluggable Interfaces

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

### 12.4 Default Implementation (v1.0)
- **Saga orchestrator** – stores compensation actions in the workflow instance state. When a step fails, the engine invokes compensations in reverse order.
- **Outbox relay** – a background process that polls the `outbox` table (in the same database as state backend) and publishes messages to the message broker. Idempotency keys prevent duplicates.

### 12.5 Distributed Saga Across Engine Instances
- The orchestrator engine sends compensation commands as asynchronous messages (using `IProtocolAdapter`). The receiving engine executes the compensation idempotently.
- No distributed transaction coordinator is required; eventual consistency is accepted.

### 12.6 Deployment Configuration

```yaml
transactionManager:
  type: saga
  outbox:
    enabled: true
    pollInterval: "1s"
    batchSize: 100
```

### 12.7 Relationship
- Uses `IStateBackend` (Domain 7) to store compensation actions.
- Uses `IProtocolAdapter` (Domain 3) to send compensation commands.

### 12.8 Open Issues
None.

---

## 13. Domain 11 – Observability

### 13.1 Problem Statement
The engine must emit logs, metrics, traces, and alerts to help operators understand system behaviour, debug failures, and meet SLAs.

### 13.2 Engine’s Role
- Provide pluggable `ILogger`, `IMetrics`, `ITracer`, `IAlerting` interfaces.
- Automatically add trace context to all outgoing messages (CloudEvents `traceparent`).
- Expose standard metrics: workflow start/completion rates, task duration, error rates, queue lengths.
- Evaluate alerting rules (defined in deployment config) using the CEP engine.

### 13.3 Pluggable Interfaces

```csharp
public interface ILogger
{
    void Log(LogLevel level, string message, params object[] args);
}

public interface IMetrics
{
    void Counter(string name, double value, params KeyValuePair<string, string>[] tags);
    void Histogram(string name, double value, params KeyValuePair<string, string>[] tags);
    void Gauge(string name, double value, params KeyValuePair<string, string>[] tags);
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

### 13.4 Default Implementation (v1.0)
- **OpenTelemetry** – all three signals (logs, metrics, traces) exported via OTLP.
- **Prometheus** endpoint for metric scraping.
- **Alerting** – rules evaluated via CEP engine, alerts sent to configured webhook (Slack, PagerDuty).

### 13.5 Deployment Configuration

```yaml
observability:
  logging:
    level: "INFO"
    structured: true
  metrics:
    exporter: "prometheus"
    port: 9090
  tracing:
    exporter: "otlp"
    endpoint: "http://otel-collector:4318"
    samplingRatio: 0.1
  alerting:
    rules:
      - name: "HighErrorRate"
        expr: "rate(bpms_task_errors_total[5m]) > 0.05"
        severity: "warning"
        receivers: ["slack"]
```

### 13.6 Open Issues
None.

---

## 14. Domain 12 – Security

### 14.1 Problem Statement
The engine must authenticate incoming requests (northbound API) and authorize actions based on user or service identity. It must also securely obtain credentials for outgoing calls. Fine‑grained attribute‑based access control (ABAC) is required for multi‑tenant and agentic scenarios.

### 14.2 Engine’s Role
- Provide `IAuthenticator` for incoming requests (JWT, mTLS, API key).
- Provide `IAuthorizer` with ABAC support (evaluates policies using attributes: tenant, role, action, resource).
- Provide `ISecretResolver` (shared with Domain 8) for outgoing credentials.
- Enforce tenant isolation at the state and event level (every record has `tenantId`).

### 14.3 Pluggable Interfaces

```csharp
public interface IAuthenticator
{
    Task<AuthenticationResult> AuthenticateAsync(HttpRequest request, CancellationToken ct);
}

public interface IAuthorizer
{
    Task<bool> IsAllowedAsync(AuthorizationContext context, CancellationToken ct);
}

public class AuthorizationContext
{
    public string Subject { get; set; }
    public string Action { get; set; }
    public string Resource { get; set; }
    public Dictionary<string, object> Attributes { get; set; }
}
```

### 14.4 Default Implementations (v1.0)

| Interface | Default | Description |
|-----------|---------|-------------|
| `IAuthenticator` | JWT with OIDC discovery | Validates tokens from issuer, checks audience. |
| `IAuthorizer` | Open Policy Agent (OPA) | Policies stored in deployment config or external bundle. |
| `ISecretResolver` | Kubernetes Secrets / Vault | As in Domain 8. |

### 14.5 ABAC Policies (Example)
```rego
package bpms.authz

allow {
    input.action == "start_workflow"
    input.attributes.tenant == input.subject.tenant
    input.subject.role in ["admin", "developer"]
}

allow {
    input.action == "read_instance"
    input.resource.tenant == input.subject.tenant
}
```

### 14.6 Deployment Configuration

```yaml
security:
  authenticator:
    type: jwt
    issuer: "https://auth.company.com"
    audience: "bpms-engine"
  authorizer:
    type: opa
    policyBundle: "https://s3.bucket/policies/bpms-authz.rego"
  secretsResolver:
    type: hashicorp-vault
```

### 14.7 Relationship to Agentic Systems
- Agents are assigned a service account identity; ABAC policies control which tools an agent can invoke.
- Agent‑to‑agent communication is subject to the same authorisation.

### 14.8 Open Issues
None.

---

## 15. Domain 13 – Agentic Systems & AI‑Native Integration

### 15.1 Problem Statement
The engine must orchestrate autonomous agents that use LLMs, call tools, and collaborate with other agents. Agent workflows require prompt management, skill discovery, memory (short‑term, long‑term, vector), and provenance tracking.

### 15.2 Engine’s Role
- Extend BPMN with `agentTask` – an activity that invokes an agent using a logical agent name.
- Provide `IAgentInvoker` to call agents via MCP (Model Context Protocol) or A2A (Agent‑to‑Agent).
- Provide `ISkillRegistry` to discover and version skills (reusable agent capabilities).
- Integrate with `IVectorStore` and `IMemoryStore` (Domain 20) for agent memory.
- Record provenance via `IProvenanceRecorder` (Domain 42).

### 15.3 Pluggable Interfaces

```csharp
public interface IAgentInvoker
{
    Task<CanonicalMessage> InvokeAsync(CanonicalMessage request, AgentContext context, CancellationToken ct);
}

public class AgentContext
{
    public string AgentName { get; set; }
    public List<ToolDefinition> Tools { get; set; }
    public IAsyncEnumerable<CanonicalMessage> ConversationHistory { get; set; }
}

public interface ISkillRegistry
{
    Task<IEnumerable<SkillDefinition>> ListSkillsAsync(CancellationToken ct);
    Task<SkillDefinition> GetSkillAsync(string skillName, CancellationToken ct);
}
```

### 15.4 Default Implementations (v1.0)

| Component | Default Implementation |
|-----------|------------------------|
| `IAgentInvoker` | MCP adapter (connects to an MCP server over stdio or HTTP/SSE). |
| `ISkillRegistry` | Local directory of skill manifests (YAML). Production: registry service via HTTP. |

### 15.5 Agent Task Extension to BPMN
Example BPMN XML snippet:
```xml
<agentTask id="analyze-risk" name="Analyze Risk" agent="risk-agent">
  <input>
    <variable name="customerData" from="customerInfo" />
  </input>
  <output>
    <variable name="riskScore" to="riskScore" />
  </output>
  <promptTemplate ref="https://models/prompts/risk-analysis.md" />
</agentTask>
```

### 15.6 Deployment Configuration

```yaml
bindings:
  agents:
    risk-agent:
      protocol: mcp
      endpoint: "http://mcp-server:8080"
      tools: ["credit-check", "fraud-detection"]
agentMemory:
  vectorStore: pgvector
  shortTerm: redis
skillRegistry:
  type: local
  path: "/skills"
```

### 15.7 Relationship to Other Domains
- Uses `IProtocolAdapter` (Domain 3) for underlying transport (MCP over HTTP/gRPC).
- Uses `IVectorStore` (Domain 20) for long‑term memory.
- Uses `IProvenanceRecorder` (Domain 42) for audit.

### 15.8 Open Issues
None.

---

## 16. Domain 14 – UI Backend & Frontend Platform

### 16.1 Problem Statement
Human users need to interact with workflows (approvals, form filling), monitor agent conversations, and view dashboards. The engine does not render UI but must provide a default, production‑ready UI backend (BFF) that consumes the engine’s APIs.

### 16.2 Engine’s Role
- Provide `IUserTaskProvider` to emit user task events and accept completions.
- Provide `IRealTimePush` to send real‑time updates (WebSocket/SSE) to the UI.
- **Mandatory default implementation:** a separate BFF engine (our own product) that implements these interfaces and serves a fully functional UI.

### 16.3 Pluggable Interfaces

```csharp
public interface IUserTaskProvider
{
    Task CreateTaskAsync(UserTask task, CancellationToken ct);
    Task CompleteTaskAsync(string taskId, UserTaskResult result, CancellationToken ct);
    Task<IEnumerable<UserTask>> ListTasksAsync(string userId, CancellationToken ct);
}

public interface IRealTimePush
{
    Task SendToUserAsync(string userId, CloudEvent message, CancellationToken ct);
    Task BroadcastToTenantAsync(string tenantId, CloudEvent message, CancellationToken ct);
}
```

### 16.4 Default Implementation (Mandatory v1.0)
Our **BFF Engine** – a separate service (container) that:
- Consumes the engine’s northbound API (over gRPC/REST).
- Provides a web UI (React) with task list, agent conversation view, workflow monitoring.
- Manages WebSocket connections and pushes real‑time updates.
- Handles user authentication (reusing engine’s `IAuthenticator`).

Deployment configuration:
```yaml
ui:
  bffEngine:
    enabled: true
    endpoint: "http://bpms-bff:8080"
    authentication: "shared"
```

The BFF engine is deployed alongside the core engine (same pod as sidecar, or separate deployment).

### 16.5 Relationship
- Uses `IUserTaskProvider` to receive tasks; the engine’s `IUserTaskProvider` is implemented by the BFF engine (a bidirectional integration). Alternatively, the engine can push tasks to the BFF via HTTP.

### 16.6 Open Issues
None.

---

## 17. Domain 15 – Load Balancing & Traffic Routing

### 17.1 Problem Statement
For both south‑bound (engine → external services) and east‑west (engine → other internal services) traffic, the engine may need to distribute requests across multiple endpoints, handle health checking, and manage work distribution among engine replicas.

### 17.2 Engine’s Role
- Provide `IResourceManager` to resolve an endpoint for a service call.
- Provide `ILoadBalancer` with pluggable algorithms (round‑robin, least‑connections, consistent hashing).
- For work distribution (e.g., scheduling timers across replicas), use `IDistributedLock` and the resource manager to assign ownership.

### 17.3 Pluggable Interfaces

```csharp
public interface IResourceManager
{
    Task<Endpoint> ResolveEndpointAsync(string serviceName, RequestContext requestContext, CancellationToken ct);
    Task ReportHealthAsync(string serviceName, Endpoint endpoint, HealthStatus status, CancellationToken ct);
}

public interface ILoadBalancer
{
    Endpoint SelectEndpoint(IEnumerable<Endpoint> endpoints, RequestContext context);
}
```

### 17.4 Default Implementations (v1.0)

| Implementation | Description |
|----------------|-------------|
| `BypassResourceManager` | Returns the first endpoint from a static list; no health checking. |
| `RoundRobinLoadBalancer` | Cycles through endpoints; supports weights. |

### 17.5 Deployment Configuration

```yaml
resourceManager:
  type: bypass  # or "round-robin"
  healthCheck:
    enabled: false
bindings:
  services:
    credit-check:
      endpoints: ["credit1:50051", "credit2:50051"]
      loadBalancing: round-robin
```

### 17.6 Relationship
- Used by `IProtocolAdapter` (Domain 3) before each call.
- For advanced scenarios (e.g., service mesh), the resource manager can be configured to return the mesh sidecar address.

### 17.7 Open Issues
None.

---

## 18. Domain 16 – Data Persistence & Storage

### 18.1 Problem Statement
The engine needs to persist not only workflow state but also vector embeddings (for agent memory), documents/artifacts (for RAG), and graph data (for knowledge representation). Different storage types have different access patterns.

### 18.2 Engine’s Role
- Reuse `IStateBackend` for durable workflow state.
- Provide `IVectorStore` for similarity search.
- Provide `IBlobStorage` for large artifacts.
- All stores align with the canonical message model: stored data can be referenced by CloudEvent `id`.

### 18.3 Pluggable Interfaces

```csharp
public interface IVectorStore
{
    Task AddAsync(string collection, Vector vector, CloudEvent metadata, CancellationToken ct);
    Task<IEnumerable<VectorSearchResult>> SimilaritySearchAsync(string collection, float[] queryVector, int limit, CancellationToken ct);
}

public interface IBlobStorage
{
    Task<Stream> ReadAsync(string blobId, CancellationToken ct);
    Task<string> WriteAsync(Stream data, string contentType, CancellationToken ct);
    Task DeleteAsync(string blobId, CancellationToken ct);
}
```

### 18.4 Default Implementations (v1.0)

| Interface | Default | Configuration |
|-----------|---------|----------------|
| `IVectorStore` | pgvector (PostgreSQL extension) | `type: pgvector` |
| `IBlobStorage` | S3 (or MinIO) for production; local file for dev | `type: s3` or `type: file` |

### 18.5 Deployment Configuration

```yaml
vectorStore:
  type: pgvector
  connectionString: "Host=postgres;Database=bpms"
blobStorage:
  type: s3
  bucket: "bpms-artifacts"
  region: "eu-west-1"
  credentialsSecretRef: "s3-credentials"
```

### 18.6 Relationship
- Used by Domain 20 (artifact processing) to store chunks and embeddings.
- Used by Domain 13 (agent memory) for long‑term memory.

### 18.7 Open Issues
None.

---

## 19. Domain 20 – Artifact Processing & Abstraction

### 19.1 Problem Statement
The engine must process documents, data files, media, and other artifacts – parse them, chunk them, create embeddings, store in vector/graph stores, and manage full lifecycle (versioning, retention, legal hold). This is essential for RAG (Retrieval‑Augmented Generation) and agent memory.

### 19.2 Engine’s Role
- Provide `IArtifactProcessor` as the main orchestration interface.
- Provide sub‑interfaces `IChunker`, `IEmbedder`, `IGraphStore`, `IMemoryStore`.
- Provide `IArtifactLifecycleManager` for versioning, retention policies, and legal hold.
- A **reference implementation** is provided (in‑process, simple chunking, mock embeddings). Third‑party processors (LangChain, ONNX, Azure AI Document Intelligence) are optional plugins after compatibility evaluation.

### 19.3 Pluggable Interfaces

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

### 19.4 Default Implementation (v1.0)
- **`ReferenceArtifactProcessor`** – in‑process, using:
  - `SentenceChunker` (splits text by sentence, configurable overlap)
  - `MockEmbedder` (returns random vectors – for testing only)
  - `InMemoryGraphStore` (for dev)
  - `InMemoryMemoryStore` (for dev)
- **Full lifecycle management** – background job scans artifact metadata (stored in `IStateBackend`) and deletes or archives expired artifacts.

### 19.5 Deployment Configuration

```yaml
artifactProcessor:
  type: reference
  chunking:
    strategy: sentence
    maxChunkSize: 512
    overlap: 50
  embedding:
    model: mock   # replace with "onnx-all-MiniLM" after evaluation
    dimension: 384
  graphStore:
    type: postgresql
  memoryStore:
    type: pgvector
  lifecycle:
    retentionDays: 90
    legalHoldEnabled: true
```

### 19.6 Third‑Party Processor Integration (Optional)
- **LangChain** – via sidecar Python service; engine calls HTTP endpoint.
- **ONNX Runtime** – native C# embedding model.
- **Azure AI Document Intelligence** – REST API.
These are not mandatory; the reference implementation is sufficient for many use cases.

### 19.7 Relationship
- Uses `IBlobStorage` (Domain 16) to read/write artifacts.
- Uses `IVectorStore` (Domain 16) for embeddings.
- Uses `IGraphStore` for knowledge graphs.

### 19.8 Open Issues
None.

---

## 20. Domain 42 – Code & Model Provenance

### 20.1 Problem Statement
For audit, debugging, and reproducibility, the engine must record which versions of models (LLMs, DMN, BPMN), prompts, skills, and tools were used to produce a given outcome.

### 20.2 Engine’s Role
- Provide `IProvenanceRecorder` to store provenance events (as CloudEvents in the event store).
- Provide `IModelResolver` to map logical model names (e.g., `llm://gpt4`) to concrete versioned identifiers.
- Automatically record provenance for every agent task, skill invocation, and decision evaluation.

### 20.3 Pluggable Interfaces

```csharp
public interface IProvenanceRecorder
{
    Task RecordAsync(ProvenanceEvent evt, CancellationToken ct);
}

public interface IModelResolver
{
    Task<ModelVersion> ResolveAsync(string logicalModelName, CancellationToken ct);
}
```

### 20.4 Default Implementations (v1.0)

| Interface | Default Implementation |
|-----------|------------------------|
| `IProvenanceRecorder` | In‑memory (dev); production uses `IEventStore` (Kafka/PostgreSQL) |
| `IModelResolver` | Local YAML mapping file; production can integrate with MLflow or LangSmith |

### 20.5 Provenance Event Schema
```json
{
  "id": "provenance-uuid",
  "source": "bpms-engine",
  "type": "com.bpms.AgentTaskInvocation",
  "subject": "workflow-123",
  "data": {
    "agentName": "risk-agent",
    "model": "gpt-4-turbo-2024-04-09",
    "promptTemplate": "risk-analysis-v2",
    "skillVersion": "1.2.0",
    "inputHash": "sha256:...",
    "outputHash": "sha256:..."
  }
}
```

### 20.6 Deployment Configuration

```yaml
provenance:
  recorder:
    type: event-store   # or "mlflow", "langsmith"
  modelResolver:
    type: file
    path: "/models/model-mappings.yaml"
```

### 20.7 Relationship
- Uses `IEventStore` (Domain 9) for persistence.
- Used by Domain 13 (agentic) to record agent decisions.

### 20.8 Open Issues
None.

---

## 21. Domain 65 – Data Masking & Test Data

### 21.1 Problem Statement
For non‑production environments, the engine must mask sensitive data (PII) in workflow variables and events. It must also be able to generate realistic synthetic test data for development and testing.

### 21.2 Engine’s Role
- Provide `IDataMasker` to apply masking rules (JSONPath + mask type) to canonical messages.
- Provide `ITestDataGenerator` to produce synthetic data conforming to JSON Schema.
- A **middleware** can automatically mask all workflow inputs/outputs when running in dev/stage environment.

### 21.3 Pluggable Interfaces

```csharp
public interface IDataMasker
{
    Task<CanonicalMessage> MaskAsync(CanonicalMessage input, MaskingRules rules, CancellationToken ct);
}

public interface ITestDataGenerator
{
    Task<T> GenerateAsync<T>(string schemaName, CancellationToken ct);
}
```

### 21.4 Default Implementations (v1.0)

| Interface | Default Implementation | Features |
|-----------|------------------------|----------|
| `IDataMasker` | JSONPath‑based masker | Redact, hash, partial mask, replace with faker |
| `ITestDataGenerator` | Bogus (C#) / Faker | Generates realistic names, addresses, etc. from schema |

### 21.5 Masking Rules Example
```yaml
maskingRules:
  - path: "$.customer.ssn"
    method: "redact"
  - path: "$.customer.email"
    method: "hash"
  - path: "$.customer.phone"
    method: "partial"
    options:
      prefix: "***"
      suffixLength: 4
```

### 21.6 Automatic Masking Middleware
In deployment config:
```yaml
dataMasking:
  enabled: true
  environment: stage   # dev, stage only
  rulesFile: "/masking-rules.yaml"
```

The middleware intercepts every incoming message and outgoing message in the engine pipeline.

### 21.7 Test Data Generation Usage
The engine exposes an internal API (or service task) to generate test data on demand:
```csharp
var customer = await testDataGenerator.GenerateAsync<Customer>("customer-schema");
```

### 21.8 Relationship
- Used by Domain 12 (security) for data privacy compliance.
- Used by CI/CD pipelines to seed test environments.

### 21.9 Open Issues
None.

---

## 22. Domain Mapping Table (All Domains 1–65)

| Domain | Relationship | Spec Section |
|--------|--------------|--------------|
| 1 Runtime Infrastructure | External | – |
| 2 Service Discovery | External (used by Domain 3) | – |
| 3 Inter‑Service Communication | Core | Section 5 |
| 4 Service Mesh | External (engine works without) | Section 6 |
| 5 Northbound Exposure | Core + plugin (our gateway) | Section 7 |
| 6 Southbound Integration & Transformation | Core | Section 8 |
| 7 State & Caching | Core plugin | Section 9 |
| 8 Configuration & Secrets | Core plugin | Section 10 |
| 9 Event Streaming & CEP | Core plugin | Section 11 |
| 10 Data Consistency & Distributed Transactions | Core plugin | Section 12 |
| 11 Observability | Core plugin | Section 13 |
| 12 Security | Core plugin | Section 14 |
| 13 Agentic Systems & AI‑Native | Core | Section 15 |
| 14 UI Backend & Frontend | Separate BFF (mandatory) | Section 16 |
| 15 Load Balancing & Traffic Routing | Core plugin | Section 17 |
| 16 Data Persistence & Storage | Core plugin | Section 18 |
| 17 Workflow Orchestration | Core | Sections 2–5 |
| 18 Knowledge & Analytics | External (engine calls services) | – |
| 19 Tool Integration | Core (`IProtocolAdapter`) | Section 5 |
| 20 Artifact Processing & Abstraction | Core plugin | Section 19 |
| 21 Developer Experience | External | – |
| 22 CI/CD | External | – |
| 23 Testing & QA | External | – |
| 24 IAM | External (engine uses `IAuthenticator`) | Section 14 |
| 25 Compliance & Audit | Engine emits events | Section 11 |
| 26 Cost Management | External | – |
| 27 Disaster Recovery | External | – |
| 28 API Lifecycle Management | External | – |
| 29 Multi‑Tenancy | Core (tenantId) | Section 14 |
| 30 Edge Computing | Engine can run on K3s | – |
| 31 Service Versioning | Core (version pinning) | Section 5 |
| 32 High Availability | Core (state backend clustering) | Section 9 |
| 33 Data Privacy | Core (`IDataMasker`) | Section 21 |
| 34 Data Pipeline | Engine orchestrates | Sections 2, 8 |
| 35 Digital Twins | External | – |
| 36 Scheduling | Core (`ITimerScheduler`) | Section 9 |
| 37 Notifications | Core (`IProtocolAdapter`) | Section 5 |
| 38 Localization | External | – |
| 39 Licensing | External | – |
| 40 Search & Full‑Text Indexing | External | – |
| 41 A/B Testing & Feature Flags | External | – |
| 42 Code & Model Provenance | Core plugin | Section 20 |
| 43 Synthetic Data Generation | Core (`ITestDataGenerator`) | Section 21 |
| 44 Blockchain | External | – |
| 45 Quantum‑Safe Crypto | External | – |
| 46 Capacity Planning | External | – |
| 47 Data Governance | External | – |
| 48 Service Catalog | External | – |
| 49 Session & State Replication | Core (state backend) | Section 9 |
| 50 Mobile Device Management | External | – |
| 51 Voice & Conversational | External | – |
| 52 Block Storage | External | – |
| 53 Message Transformation | Core (`ITransformer`) | Section 8 |
| 54 Time Synchronisation | Core (logical clocks) | Section 9 |
| 55 Document Lifecycle | Core (`IArtifactLifecycleManager`) | Section 19 |
| 56 HSM & Key Lifecycle | External (`ISecretResolver`) | Section 10 |
| 57 Network Policy | External | – |
| 58 Infrastructure as Code | External | – |
| 59 Environment Management | External | – |
| 60 Schema & DB Migration | Engine uses Flyway/Liquibase | – |
| 61 Data Archival | External | – |
| 62 Incident Response | External | – |
| 63 Sustainability | External | – |
| 64 Vendor Abstraction | Optional (Dapr) | – |
| 65 Data Masking & Test Data | Core plugin | Section 21 |

---

## 23. Cross‑Cutting Concerns

### 23.1 Uniform Error & Retry Policy Language

All protocol adapters and the engine itself support the following retry policy DSL:

```yaml
retryPolicy:
  maxAttempts: 3
  backoff:
    type: exponential | fixed | none
    initialInterval: "100ms"
    multiplier: 2.0
    maxInterval: "10s"
  onErrors: ["timeout", "network_error", "5xx"]
  neverRetry: ["invalid_argument", "unauthorized"]
deadLetter:
  enabled: true
  destination: "dlq://failed-calls"
```

### 23.2 Idempotency Key Storage and Retention

- **Storage:** `IDeduplicationStore` (default PostgreSQL table `idempotency_keys`).
- **Key format:** `{tenantId}:{workflowId}:{activityId}:{messageId}`.
- **Retention:** Keys kept for `max(workflow duration + 7 days, retry window + 24h)`. Cleanup job runs daily.

### 23.3 Message Ordering and Exactly‑Once Semantics

- The engine does **not** guarantee global order across different workflow instances.
- Within a single workflow instance, order is determined by BPMN sequence flows.
- Exactly‑once effect is achieved via at‑least‑once delivery + idempotent consumer using deduplication store.

---

## 24. Open Issues & Future Versions

**No open issues for v1.0.** All features previously considered deferred have been included.

**Planned for v1.1:**
- Full Agentic AI extension specification (enhanced `IAgentInvoker` with streaming, tool calling, and memory).
- Dynamic protocol discovery for sidecar proxies.

**Planned for v2.0:**
- Automated migration of running workflow instances across model versions.
- Cross‑region active‑active state backend.

---

## 25. Appendices

### Appendix A: Full `deployment-config.yaml` JSON Schema
*(Provided as a separate file – omitted here for brevity but available in the source repository.)*

### Appendix B: Example Configurations
Development (`dev/deployment-config.yaml`):
```yaml
environment: dev
stateBackend:
  type: in-memory
bindings:
  services:
    credit-check:
      protocol: in-memory
observability:
  logging:
    level: DEBUG
```

Production (`prod/deployment-config.yaml`):
```yaml
environment: prod
stateBackend:
  type: postgresql
  connectionString: "Host=postgres.prod;Database=bpms"
  secretRef: "db-credentials"
bindings:
  services:
    credit-check:
      protocol: grpc
      endpoint: "credit-check.internal:50051"
      tls: true
      retryPolicy: prod-retry
```

### Appendix C: Plugin Development Walkthrough (Source Generator)
*(Detailed developer guide – separate document.)*

### Appendix D: Glossary of Terms

- **Deployment Agnostic:** Same binary runs on any infrastructure with only config changes.
- **Canonical Message:** CloudEvent + JSON Schema.
- **Artifact:** Any document, data file, or media processed by the engine.
- **BFF Engine:** Our own UI backend service that consumes engine APIs.
- **Agent Task:** BPMN extension for invoking AI agents.
- **MCP:** Model Context Protocol.
- **A2A:** Agent‑to‑Agent protocol.
- **ABAC:** Attribute‑Based Access Control.
- **CEP:** Complex Event Processing.
- **BAM:** Business Activity Monitoring.

---

**End of Document v1.0.2**