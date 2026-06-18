# DECISION MATRIX: .NET LIBRARY SELECTION FOR THE POLYMORPHIC DISTRIBUTED BPMS PLATFORM

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

*This decision matrix is part of the Architecture Document and should be reviewed and updated as new libraries emerge and existing libraries evolve.*