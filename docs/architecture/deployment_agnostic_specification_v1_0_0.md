# Deployment Agnostic - Technical Specification v1.0.0

**Document Version:** 1.0.0 
**Status:** Approved for internal review  
**Date:** 2026-06-15  
**Authors:** Agentic BPMS Architecture Team  

---

## 1. Introduction

### 1.1 Purpose
This document specifies the architecture of an **Agentic BPMS (Business Process Management System)** that is **deployment agnostic** – the same logical process models (BPMN, DMN, CMMN, UML state machines, CEP rules) can be executed on vastly different infrastructure stacks (monolith, bare-metal processes, Docker, Kubernetes with service mesh, serverless) **without any code or model changes**. Only the **deployment configuration** (binding logical names to physical endpoints, protocols, QoS parameters) varies per environment.

### 1.2 Guiding Principles
- **Logical vs. Physical Separation** – Models define *what*; deployment config defines *how*.
- **Pluggable Everything** – State backends, protocol adapters, transaction coordinators, observability, security, timers, deduplication stores are all pluggable via a uniform plugin model.
- **Model-Driven** – BPMN, DMN, CMMN, UML state machines, OpenAPI, AsyncAPI, and Canonical Message Model (CloudEvents + JSON Schema) are first-class citizens.
- **Deployment as Code** – Environment-specific configurations (dev, stage, prod) are versioned, validated, and applied declaratively.
- **Idempotency First** – Every external interaction carries an idempotency key; the engine guarantees at-least-once delivery with idempotent handling to achieve exactly-once effect.

### 1.3 Scope (v1.0)
This version covers the core engine architecture, plugin system, deployment configuration, and high-level domains. Some advanced features are deferred to later versions (explicitly listed in Section 8).

---

## 2. Architecture Overview

### 2.1 Logical Components

```
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway (optional)                   │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                    Orchestration Engine                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ BPMN Engine │  │ DMN Engine  │  │ CMMN Engine │ ...     │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                │
│         └────────────────┼────────────────┘                │
│                          ▼                                 │
│              ┌───────────────────────┐                     │
│              │ Workflow State Machine │                     │
│              └───────────┬───────────┘                     │
│                          │                                 │
│         ┌────────────────┼────────────────┐               │
│         ▼                ▼                ▼               │
│ ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│ │  Protocol   │  │   State     │  │ Transaction │         │
│ │  Adapter    │  │  Backend    │  │   Manager   │         │
│ │  Registry   │  │  Plugin     │  │   Plugin    │         │
│ └─────────────┘  └─────────────┘  └─────────────┘         │
│         │                │                │               │
│ ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│ │  Timer      │  │ Observability│  │  Security   │         │
│ │  Plugin     │  │  Plugin     │  │   Plugin    │         │
│ └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Deployment Layers

| Layer | Artifacts | Versioned | Environment-Specific |
|-------|-----------|-----------|----------------------|
| Logical Models | BPMN, DMN, OpenAPI, Canonical schemas | Yes (Git) | No |
| Deployment Config | `deployment-config.yaml`, secret references | Yes (Git) | Yes (overlay per env) |
| Infrastructure | Kubernetes manifests, docker-compose, bare-metal scripts | Yes | Yes |

---

## 3. Canonical Message Model

### 3.1 Format
- **Envelope:** [CloudEvents v1.0](https://cloudevents.io/) (JSON format for interoperability, binary for performance when needed).
- **Data Schema:** JSON Schema (draft 2020-12) for validation and evolution. Protobuf serialization allowed via `datacontenttype="application/protobuf"`.
- **Mandatory attributes for engine:**
  - `id` (globally unique, used as idempotency key)
  - `source` (URI of emitting component)
  - `type` (e.g., `com.example.CreditCheckResponse`)
  - `subject` (workflow instance ID, correlation key)
  - `time` (timestamp)
  - `traceparent` (W3C trace context for observability)

### 3.2 Model Cross-Reference
- Logical references in BPMN (e.g., `message="CreditCheckResponse"`) are resolved at build time to **URIs** (e.g., `model://credit-control#message/CreditCheckResponse`).
- The engine uses a **pluggable URI resolver** that can resolve `model://`, `file://`, `http://`, `s3://`, etc., based on deployment configuration.
- Fallback: local name resolution using an in-memory registry for monolith deployments.

### 3.3 Open Issue
- **Schema registry integration** for automatic schema evolution and validation. (Deferred to v1.1)

---

## 4. Protocol Adapter Plugin Model (ASP.NET Core AOT)

### 4.1 Design Constraints
- **Native AOT** (ahead-of-time compilation) does not allow dynamic assembly loading.
- Therefore, plugins are **compile-time registered** via **source generators**.

### 4.2 Plugin Interface
```csharp
public interface IProtocolAdapter
{
    string ProtocolName { get; }
    Task<CanonicalMessage> SendAsync(
        CanonicalMessage request,
        ProtocolContext context,  // contains timeout, retry policy, etc.
        CancellationToken cancellationToken
    );
}
```

### 4.3 Registration (Source-Generated)
- Each adapter implementation is decorated with `[ProtocolAdapter]` attribute.
- A source generator produces a static registry:
```csharp
public static class ProtocolAdapterRegistry
{
    public static IServiceCollection AddAllAdapters(this IServiceCollection services)
    {
        services.AddKeyedSingleton<IProtocolAdapter, GrpcAdapter>("grpc");
        services.AddKeyedSingleton<IProtocolAdapter, KafkaAdapter>("kafka");
        services.AddKeyedSingleton<IProtocolAdapter, HttpAdapter>("http");
        // ... all adapters known at compile time
        return services;
    }
}
```
- The engine selects the adapter based on deployment config's `protocol` field.

### 4.4 Supported Protocols (v1.0)
- `in-memory` (for testing and monolith)
- `http/1.1` (REST/OpenAPI)
- `grpc` (unary only; streaming deferred)
- `kafka` (request-reply over topics with correlation)

### 4.5 Open Issues
- Streaming gRPC and WebSocket support (v1.2)
- Dynamic protocol discovery for sidecar proxies (v2.0)

---

## 5. Deployment as Code

### 5.1 Configuration Structure
Each environment has a `deployment-config.yaml` (with optional overlays).

**Example:**
```yaml
environment: prod
logicalModels:
  bpmn: "s3://models/process-v2.bpmn"
  openapi: "s3://models/apis/"
canonicalFormat: "cloudevents+jsonschema"

bindings:
  services:
    credit-check:
      protocol: grpc
      endpoint: "credit.internal:50051"
      tls: true
      timeout: "3s"
      retryPolicy: "prod-retry"
      credentials:
        secretRef: "prod/credit-mtls-cert"
  messageChannels:
    order-events:
      protocol: kafka
      brokers: ["kafka.prod:9092"]
      topic: "order-events"
      consumerGroup: "bpms-engine"

retryPolicies:
  prod-retry:
    maxAttempts: 3
    backoff: "exponential"
    initialInterval: "100ms"
    multiplier: 2.0
    maxInterval: "10s"
  deadLetter:
    enabled: true
    destination: "dlq://failed"

secretsResolver:
  type: "hashicorp-vault"
  address: "https://vault.prod:8200"
```

### 5.2 Validation & Dry-Run
- **CLI tool:** `bpms-validate --env prod --deployment-config prod.yaml`
- Validates:
  - Syntactic correctness.
  - Every logical service in BPMN has a binding.
  - Protocol adapter exists in compiled engine.
  - Retry policies reference valid definitions.
  - Secret references are resolvable (without exposing values).
- **Dry-run:** Outputs effective config (merged with base) without deploying.

### 5.3 Open Issues
- Dynamic configuration reload without engine restart (v1.2)
- Configuration drift detection between Git and running environment (v1.3)

---

## 6. Domains 3–13 (Brief Overview)

*These domains will be detailed in subsequent documents. For v1.0, we provide the agreed principles and deferred items.*

### Domain 3: State Management & Persistence (Pluggable)
- **Interface:** `IStateBackend` with methods: `Load(instanceId)`, `Save(snapshot)`, `AppendEvent(event)`.
- **Implementations:** In-memory (dev), PostgreSQL (default for prod), RocksDB (embedded), Cassandra (high scale).
- **Deferred:** Snapshot frequency optimization, state partitioning.

### Domain 4: Transaction Boundaries & Compensations
- **Interface:** `ITransactionManager` with `BeginTransaction()`, `Commit()`, `Rollback()`, `RegisterCompensation()`.
- **Implementations:** No-op (default), two-phase commit (for monolith), saga orchestration (for microservices).
- **Deferred:** Distributed transaction coordinator (v1.2).

### Domain 5: Workflow Versioning & Migration
- **Policy:** Version pinning; a model version remains active until zero running instances.
- **Migration:** Manual script support via `IMigration` interface.
- **Model evolution rules:** Additive changes compatible; subtractive changes require new version.
- **Deferred:** Automated instance migration (v2.0).

### Domain 6: Observability (Tracing, Metrics, Logging)
- **Interfaces:** `ITracer`, `IMeter`, `ILogger`.
- **Default:** OpenTelemetry exporter (OTLP).
- **Deferred:** Adaptive sampling, custom metrics DSL (v1.2).

### Domain 7: Security
- **Interfaces:** `IAuthenticator` (incoming), `IAuthorizer`, `ISecretResolver` (outgoing).
- **Default for v1.0:** JWT authentication, RBAC authorization (roles: admin, tenant-user), Kubernetes Secrets resolver.
- **Deferred:** Field-level authorization, OPA integration (v1.3).

### Domain 8: Agentic AI Extensions
- **Scope:** BPMN extended with `agentTask` and `skillDefinition` models.
- **Protocols:** MCP (Model Context Protocol), A2A (Agent-to-Agent), tool calls over HTTP/gRPC.
- **Deployment agnostic:** LLM endpoints as logical services (`llm://openai-gpt4`).
- **Deferred:** Full specification of agent lifecycle, prompt caching, streaming (v1.1).

### Domain 9: Event Sourcing & Replay
- **Event store:** Pluggable `IEventStore` (same as state backend or separate).
- **Replayability:** The engine can rebuild state by replaying events from a starting snapshot.
- **Event schema evolution:** Use versioned schemas (protobuf or JSON Schema with registry). `IEventMigrator` interface for custom transformations.
- **Deferred:** Automated schema migration tool (v1.2).

### Domain 10: Human Tasks Integration
- **Interface:** `IUserTaskProvider` – engine emits `UserTaskCreated` events; external work item engine polls or receives them.
- **Protocol:** CloudEvents over HTTP/Kafka.
- **Deferred:** Escalation, deadlines, out-of-office (handled by external engine – out of scope).

### Domain 11: Timer & Event Scheduling
- **Interface:** `ITimerScheduler` with `Schedule(delay, callbackId)`, `Cancel(callbackId)`.
- **Implementations:** In-memory (dev), PostgreSQL `pg_cron` or polling (prod), distributed (Kafka Streams).
- **Deferred:** Exactly-once timer delivery across cluster restarts (v1.1).

### Domain 12: Multi-Tenancy & Isolation
- **Tenant model:** Each state/event labeled with `tenantId`.
- **Isolation levels:** Database per tenant, schema per tenant, or row-level security (configurable per tenant).
- **Quotas:** Max concurrent instances, rate limits enforced by engine.
- **Deferred:** Tenant auto-provisioning (v1.2).

### Domain 13: Edge Cases – Idempotency, Ordering, Deduplication
- **Idempotency key storage:** Pluggable `IDeduplicationStore`. Default: PostgreSQL table with unique constraint.
- **Key format:** `{tenantId}:{workflowId}:{activityId}:{messageId}`.
- **Retention:** Keys kept for **max( workflow duration + 7 days, retry window + 24h )**.
- **Message ordering:** Engine does not guarantee order across instances; within an instance, order determined by BPMN sequence flows. Deployment can enforce ordering by configuring message channels with partition key = workflow ID.
- **Deferred:** Distributed deduplication store consistency across replicas (v1.1).

---

## 7. Cross-Cutting Concerns (Implemented in v1.0)

### 7.1 Unified Error & Retry Policy Language
- JSON/YAML DSL attached to any interaction.
- Keys: `maxAttempts`, `backoff.type` (fixed, exponential, none), `backoff.initialInterval`, `onErrors` (list of error types), `neverRetry`, `deadLetter`.
- All protocol adapters interpret this policy uniformly.

### 7.2 Pluggable Backends Summary
| Concern | Interface | Default v1.0 | Other options |
|---------|-----------|--------------|----------------|
| State storage | `IStateBackend` | PostgreSQL | In-memory, RocksDB |
| Transaction | `ITransactionManager` | No-op (saga orchestrator) | 2PC (monolith) |
| Observability | `IObservability` | OpenTelemetry (OTLP) | Prometheus, Jaeger |
| Security (incoming) | `IAuthenticator` | JWT | mTLS, API key |
| Security (outgoing) | `ISecretResolver` | Kubernetes Secrets | HashiCorp Vault |
| Timer | `ITimerScheduler` | In-memory | PostgreSQL polling |
| Deduplication | `IDeduplicationStore` | PostgreSQL | Redis |

---

## 8. Open Issues & Future Versions

The following items are **explicitly deferred** to later versions of this specification.

| Item | Target Version | Owner |
|------|----------------|-------|
| Schema registry integration for canonical messages | v1.1 | Architecture |
| Streaming gRPC, WebSocket protocol adapters | v1.2 | Engine Team |
| Dynamic configuration reload (no restart) | v1.2 | Engine Team |
| Automated workflow instance migration | v2.0 | Tools Team |
| Field-level authorization | v1.3 | Security |
| Full Agentic AI extension spec (MCP/A2A) | v1.1 | AI Integration |
| Automated event schema migration | v1.2 | Core |
| Exactly-once timer delivery | v1.1 | Core |
| Tenant auto-provisioning | v1.2 | Operations |
| Distributed deduplication store consistency | v1.1 | Core |
| Dynamic protocol discovery (sidecar proxies) | v2.0 | Engine Team |

---

## 9. Appendices

### Appendix A: Example BPMN + Deployment Configuration Flow
*(To be added in next revision)*

### Appendix B: Plugin Development Guide (ASP.NET Core AOT)
*(To be added in next revision)*

### Appendix C: Glossary of Terms
- **Deployment Agnostic:** The ability to run the same model binaries on any infrastructure stack without changes.
- **Logical Service Name:** A symbolic name (e.g., `credit-check`) used in models, bound to a physical endpoint via deployment config.
- **Canonical Message:** A CloudEvent with JSON Schema payload used for internal engine communication.
- **Idempotency Key:** A unique identifier for an incoming message, used to deduplicate retries.

---

## 10. Document Control

- **Approved by:** Architecture Board
- **Next review date:** 2026-09-15
- **Change log:**  
  - v1.0 (2026-06-15): Initial release.

---

**End of Document v1.0.0**
