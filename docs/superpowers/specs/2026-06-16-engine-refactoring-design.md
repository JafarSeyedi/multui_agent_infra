# Engine Refactoring Design — Communication & Distributed System Layers

**Date:** 2026-06-16  
**Status:** Approved for implementation  
**Based on:** `deployment_agnostic_specification_v1_0_2.md`, `capability_based_taxonomy.md`

---

## 1. Overview

Refactor the monorepo `engines/` structure to align with the 16 core domains from the v1.0.2 specification. The per-engine model/parser/writer pattern is enforced: each engine has its own `models/` folder with format-named parsers and writers inside. The `common/` folder pattern is eliminated — code is repeated per engine where needed.

---

## 2. Phase Plan — 4 Phases

| Phase | Engines | Depends On |
|-------|---------|------------|
| **1 — Foundation** | communication, state, config, security, persistence | Nothing |
| **2 — Infrastructure** | observability, events, consistency | Phase 1 |
| **3 — Domain Services** | artifacts, provenance, masking | Phase 1,2 |
| **4 — Application** | gateway, integration, agentic, ui-backend | Phase 1,2,3 |

Existing engines (orchestration, interaction, agent, memory, knowledge, storage, tools, document, skill) are migrated gradually in later rounds — not now.

---

## 3. Per-Engine Template

Every engine must follow this structure:

```
engines/<name>/
├── __init__.py
├── plugin.py                       # Base ABC for backends — no registry, no dynamic load
│
├── models/
│   ├── <name>_models.py            # All domain-specific data models
│   ├── parsers/
│   │   ├── openapi_parser.py       # Named by spec/standard format
│   │   ├── bpmn_parser.py
│   │   ├── asyncapi_parser.py
│   │   ├── grpc_proto_parser.py
│   │   └── <name>_config_parser.py # Custom YAML/JSON config format
│   └── writers/
│       ├── openapi_writer.py
│       ├── bpmn_writer.py
│       ├── asyncapi_writer.py
│       └── <name>_config_writer.py
│
├── <sub_module>/                   # Semantic sub-modules
│   ├── plugin.py                   # Sub-plugin ABC if needed
│   ├── backends/                   # Each backend its own folder
│   └── decorators/                 # Composables (logging, metrics, circuit breaker)
│
└── tests/
```

### Rules

1. **Models are at engine level**, not in sub-modules. One `models/` folder per engine.
2. **Parser/writer names** reflect the standard file format they handle (`openapi_parser.py`, `bpmn_parser.py`). Our own config formats use `<engine>_config_parser.py`.
3. **No `common/` folder** in any engine. Duplicate where needed.
4. **No `bridge.py` or facade** — engines import each other directly.
5. **Backend implementations** each get their own folder, not a single file.
6. **Core logic** can be many files, not a single `<name>_engine.py`.

---

## 4. Plugin Model (Deployment-Agnostic)

No dynamic plugin loading, no persistent registry, no decorator-based registration — deferred.

```python
# engines/<name>/plugin.py
class SomePlugin(ABC):
    """Base class. Config selects backend at runtime by import path."""
    @abstractmethod
    async def do_something(self) -> None: ...
```

```yaml
# deployment-config.yaml selects:
engine_name:
  backend: "engines.<name>.<sub_module>.backends.specific_backend"
  config:
    ...
```

All backends are compiled in. Config provides the dotted import path. No runtime discovery.

---

## 5. Storage Architecture

Domain engines use existing `engines/storage/` — they do not embed backends.

Existing storage structure is kept:
```
engines/storage/
├── base_storage.py
├── relational/           # SQL databases (PostgreSQL, MySQL, SQLite, etc.)
├── key_value/            # Redis, etcd, Consul KV
├── object/               # S3, MinIO, GCS
├── vector/               # pgvector, Weaviate, Qdrant
├── graph/                # Neo4j, Neptune
├── timeseries/           # InfluxDB, TimescaleDB
├── stream/               # Kafka, Pulsar
├── cache/                # Caching layer
└── event_log/            # Event log storage
```

Domain engines import storage plugins:
- `engines/state/` → `engines/storage/relational/` + `engines/storage/key_value/`
- `engines/persistence/` → `engines/storage/vector/` + `engines/storage/object/`
- `engines/events/` → `engines/storage/stream/` + `engines/storage/relational/`

---

## 6. Engine-by-Engine Specification

### 6.1 `engines/communication/` — Domain 3 (Inter-Service Communication)

Replaces current `engines/communication/`. Unifies `buses/` + `common/transport/` + `messaging/adapters/`.

```
engines/communication/
├── plugin.py                       # BaseChannel ABC
│
├── models/
│   ├── communication_models.py     # ChannelMessage, ChannelConfig, Session, Endpoint
│   ├── parsers/
│   │   ├── asyncapi_parser.py      # Event-driven API specs
│   │   ├── openapi_parser.py       # REST API specs
│   │   ├── grpc_proto_parser.py    # Protobuf service definitions
│   │   └── communication_config_parser.py
│   └── writers/
│       ├── asyncapi_writer.py
│       ├── openapi_writer.py
│       └── communication_config_writer.py
│
├── pubsub/                         # PubSubChannel(BaseChannel)
│   ├── plugin.py
│   ├── backends/
│   │   ├── in_memory/
│   │   ├── redis/
│   │   ├── kafka/
│   │   ├── rabbitmq/
│   │   └── topic/
│   └── decorators/
│       ├── durable.py
│       ├── logging.py
│       ├── metrics.py
│       └── circuit_breaker.py
│
├── request_reply/                  # RequestReplyChannel(BaseChannel)
│   ├── plugin.py
│   ├── backends/
│   │   ├── in_memory/
│   │   ├── grpc/
│   │   ├── http/
│   │   └── request_reply/
│   └── decorators/
│
├── priority/                       # PriorityChannel(BaseChannel)
│   ├── plugin.py
│   ├── backends/
│   │   └── priority_message/
│   └── decorators/
│
├── transport/                      # Wire protocols (low-level, used by channel backends)
│   ├── plugin.py
│   ├── backends/
│   │   ├── http/
│   │   ├── grpc/
│   │   ├── websocket/
│   │   └── stdio/
│
├── discovery/                      # Service discovery (shared by pubsub + integration)
│   ├── plugin.py
│   ├── backends/
│   │   ├── kubernetes/
│   │   ├── consul/
│   │   └── static/
│
└── load_balancing/                 # Load balancing (shared by pubsub + integration)
    ├── plugin.py
    ├── backends/
    │   ├── round_robin/
    │   └── least_connections/

```

**Migration from current `engines/communication/`:**
- `buses/AgentMessage` → `models/communication_models.py`
- `buses/base_message_bus.py` → `pubsub/plugin.py`
- `buses/kafka_bus.py` → `pubsub/backends/kafka/`
- `buses/rabbitmq_bus.py` → `pubsub/backends/rabbitmq/`
- `common/transport/base.py` → `transport/plugin.py`
- `common/transport/kafka_client.py` → `transport/backends/kafka/` (or check if needed at all)
- `common/transport/mcp_adapter.py` + `consumption/mcp_client_adapter.py` → merge into `integration/consumption/mcp_client_adapter.py`
- `consumption/` → `integration/` in `engines/integration/`
- `exposure/` → `gateway/` in `engines/gateway/`
- `bindings/` → `models/` parsers/writers or `integration/mcp_client/`
- `messaging/adapters/` (empty stubs) → removed

### 6.2 `engines/state/` — Domain 7 (State & Caching)

```
engines/state/
├── plugin.py                       # IStateBackend, ICache, IDistributedLock ABCs
├── models/
│   ├── state_models.py             # WorkflowSnapshot, StateEntry, CacheEntry
│   ├── parsers/
│   │   └── state_config_parser.py
│   └── writers/
│       └── state_config_writer.py
├── backends/                       # Wraps engines/storage/ providers
│   ├── sql/                        # Uses engines/storage/relational/
│   ├── redis/                      # Uses engines/storage/key_value/
│   └── in_memory/                  # Dev/test
└── tests/
```

### 6.3 `engines/config/` — Domain 8 (Configuration & Secrets)

```
engines/config/
├── plugin.py                       # IConfigSource, ISecretResolver ABCs
├── models/
│   ├── config_models.py            # DeploymentConfig, SecretRef, ConfigEntry
│   ├── parsers/
│   │   └── config_yaml_parser.py
│   └── writers/
│       └── config_yaml_writer.py
├── sources/                        # IConfigSource implementations
│   ├── file/
│   ├── kubernetes_configmap/
│   └── consul/
├── resolvers/                      # ISecretResolver implementations
│   ├── environment/
│   ├── file/
│   └── vault/
└── tests/
```

### 6.4 `engines/security/` — Domain 12 (Security)

```
engines/security/
├── plugin.py                       # IAuthenticator, IAuthorizer ABCs
├── models/
│   ├── security_models.py          # AuthenticationResult, AuthorizationContext
│   ├── parsers/
│   │   └── security_config_parser.py
│   └── writers/
│       └── security_config_writer.py
├── authenticators/
│   ├── jwt/
│   ├── mtls/
│   ├── api_key/
│   └── oauth2/
├── authorizers/
│   └── opa/
└── tests/
```

### 6.5 `engines/persistence/` — Domain 16 (Data Persistence & Storage)

Wraps `engines/storage/` for specific use cases (vector, graph, blob).

```
engines/persistence/
├── plugin.py                       # IVectorStore, IBlobStorage, IGraphStore ABCs
├── models/
│   ├── persistence_models.py
│   ├── parsers/
│   │   └── persistence_config_parser.py
│   └── writers/
│       └── persistence_config_writer.py
├── vector/                         # Wraps engines/storage/vector/
│   ├── pgvector/
│   └── qdrant/
├── blob/                           # Wraps engines/storage/object/
│   ├── s3/
│   └── file/
└── tests/
```

### 6.6 `engines/observability/` — Domain 11 (Observability)

```
engines/observability/
├── plugin.py                       # ILogger, IMetrics, ITracer, IAlerting
├── models/
│   ├── observability_models.py
│   ├── parsers/
│   │   └── observability_config_parser.py
│   └── writers/
│       └── observability_config_writer.py
├── exporters/                      # OpenTelemetry, Prometheus, etc.
│   ├── otlp/
│   └── prometheus/
├── alerting/
│   └── rules_engine/
└── tests/
```

### 6.7 `engines/events/` — Domain 9 (Event Streaming & CEP)

```
engines/events/
├── plugin.py                       # IEventStore, ICepEngine
├── models/
│   ├── event_models.py             # CloudEvent wrapper, CepRule, CepEvent
│   ├── parsers/
│   │   └── event_config_parser.py
│   └── writers/
│       └── event_config_writer.py
├── stores/                         # IEventStore — wraps engines/storage/stream/
│   ├── kafka/
│   └── sql/
├── cep/                            # ICepEngine
│   ├── kafka_streams/
│   └── esper/
└── tests/
```

### 6.8 `engines/consistency/` — Domain 10 (Data Consistency & Distributed Transactions)

```
engines/consistency/
├── plugin.py                       # ITransactionManager
├── models/
│   ├── consistency_models.py       # SagaStep, CompensationAction, OutboxEntry
│   ├── parsers/
│   │   └── consistency_config_parser.py
│   └── writers/
│       └── consistency_config_writer.py
├── saga/                           # Saga orchestrator
│   └── orchestrator.py
├── outbox/                         # Outbox relay
│   └── relay.py
└── tests/
```

### 6.9 `engines/artifacts/` — Domain 20 (Artifact Processing & Abstraction)

```
engines/artifacts/
├── plugin.py                       # IArtifactProcessor, IChunker, IEmbedder
├── models/
│   ├── artifact_models.py
│   ├── parsers/
│   └── writers/
├── chunking/
│   ├── sentence/
│   └── fixed_size/
├── embedding/
│   ├── mock/
│   └── onnx/
├── lifecycle/
└── tests/
```

### 6.10 `engines/provenance/` — Domain 42 (Code & Model Provenance)

```
engines/provenance/
├── plugin.py                       # IProvenanceRecorder, IModelResolver
├── models/
│   ├── provenance_models.py
│   ├── parsers/
│   └── writers/
├── recorders/
│   ├── event_store/
│   └── mlflow/
├── resolvers/
│   ├── file/
│   └── mlflow/
└── tests/
```

### 6.11 `engines/masking/` — Domain 65 (Data Masking & Test Data)

```
engines/masking/
├── plugin.py                       # IDataMasker, ITestDataGenerator
├── models/
│   ├── masking_models.py
│   ├── parsers/
│   └── writers/
├── maskers/
│   ├── jsonpath/
│   └── faker/
├── generators/
│   └── bogus/
└── tests/
```

### 6.12 `engines/gateway/` — Domain 5 (Northbound Exposure)

```
engines/gateway/
├── plugin.py                       # IApiGateway
├── models/
│   ├── gateway_models.py
│   ├── parsers/
│   │   ├── openapi_parser.py
│   │   └── gateway_config_parser.py
│   └── writers/
│       ├── openapi_writer.py
│       └── gateway_config_writer.py
├── backends/
│   ├── rest/
│   ├── grpc/
│   ├── mcp/                        # MCP server
│   └── a2a/                        # Agent-to-Agent
├── rate_limiting/
├── auth/
└── tests/
```

### 6.13 `engines/integration/` — Domain 6 (Southbound Integration & Transformation)

```
engines/integration/
├── plugin.py                       # ITransformer, EAI pattern executors
├── models/
│   ├── integration_models.py
│   ├── parsers/
│   │   └── integration_config_parser.py
│   └── writers/
│       └── integration_config_writer.py
├── consumption/                    # Migrated from communication/consumption/
│   ├── binding_loader.py
│   ├── client_generator.py
│   ├── service_discovery.py
│   ├── transport_factory.py
│   ├── request_builder.py
│   ├── circuit_breaker.py
│   ├── mcp_service.py
│   └── mcp_client_adapter.py
├── transformation/                 # EAI patterns
│   ├── transformer.py
│   ├── splitter.py
│   ├── aggregator.py
│   ├── enricher.py
│   └── router.py
└── tests/
```

### 6.14 `engines/agentic/` — Domain 13 (Agentic Systems & AI-Native)

```
engines/agentic/
├── plugin.py                       # IAgentInvoker, ISkillRegistry
├── models/
│   ├── agentic_models.py           # AgentContext, SkillDefinition, ToolDefinition
│   ├── parsers/
│   │   └── agentic_config_parser.py
│   └── writers/
│       └── agentic_config_writer.py
├── invokers/
│   ├── mcp/
│   └── a2a/
├── memory/
│   ├── short_term/
│   └── vector/
├── skills/
│   ├── local/
│   └── remote/
└── tests/
```

### 6.15 `engines/ui-backend/` — Domain 14 (UI Backend & BFF)

```
engines/ui-backend/
├── plugin.py                       # IUserTaskProvider, IRealTimePush
├── models/
│   ├── ui_backend_models.py
│   ├── parsers/
│   └── writers/
├── bff/                            # Backend-For-Frontend logic
├── realtime/                       # WebSocket/SSE push
└── tests/
```

---

## 7. Agent Engine Imports

Agent engines (AutoGen, CrewAI, LangGraph wraps) import channels directly with no bridge layer:

```python
from engines.communication.pubsub import PubSubChannel
from engines.communication.request_reply import RequestReplyChannel
from engines.communication.models.communication_models import ChannelMessage
```

This is the stable API surface.

---

## 8. Cross-Cutting Architectural Rules

| Rule | Description |
|------|-------------|
| **No common/ folder** | Each engine duplicates needed utility code |
| **No dynamic plugin loading** | All backends compiled in; config selects by import path |
| **Models at engine level** | One `models/` per engine, not nested in sub-modules |
| **Parser/writer by format name** | `openapi_parser.py`, not `yaml_parser.py` |
| **Backends in own folders** | Each backend implementation gets `backends/<name>/` |
| **Storage via engines/storage/** | Domain engines wrap storage, don't embed backends |
| **Direct imports between engines** | No bridge.py, no facade layer |
| **Existing engines not migrated yet** | Gradual migration in later phases |

---

## 9. Migration from Current `engines/communication/`

| Current | New Location |
|---------|-------------|
| `buses/message_models.py` (AgentMessage) | `models/communication_models.py` (ChannelMessage) |
| `buses/base_message_bus.py` | `pubsub/plugin.py` (PubSubChannel) |
| `buses/kafka_bus.py`, `rabbitmq_bus.py`, etc. | `pubsub/backends/<name>/` |
| `common/transport/base.py` | `transport/plugin.py` |
| `common/transport/mcp_adapter.py` | `integration/consumption/mcp_client_adapter.py` (merge) |
| `consumption/mcp_client_adapter.py` | `integration/consumption/mcp_client_adapter.py` (merge) |
| `consumption/binding_loader.py` etc. | `integration/consumption/` |
| `exposure/` | `gateway/` (separate engine) |
| `bindings/` | Split into `models/` parsers/writers + `integration/consumption/` |
| `messaging/adapters/` (empty stubs) | **Removed** |
| `common/serialization/` | Duplicate in `models/writers/` as needed |
| `common/auth/` | Migrate to `engines/security/` |

---

## 10. Implementation Priority per Phase

### Phase 1 — Foundation (do first)
1. `engines/communication/` — full restructure with Channel abstraction, migrate all 8 bus backends
2. `engines/state/` — IStateBackend, ICache, IDistributedLock wrapping engines/storage/
3. `engines/config/` — IConfigSource, ISecretResolver
4. `engines/security/` — IAuthenticator, IAuthorizer
5. `engines/persistence/` — IVectorStore, IBlobStorage wrapping engines/storage/

Then Phase 2–4 in order as defined in Section 2.
