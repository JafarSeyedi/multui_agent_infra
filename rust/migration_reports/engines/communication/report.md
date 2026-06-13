# Communication Engine — Rust Migration Analysis

**Source:** `engines/communication/` (62 Python files, ~4200 lines)
**Date:** 2026-06-13

---

## 1. Pre-refactor Analysis

### 1.1 Type Laxity: `Any` and `dict[str, Any]`

| Pattern | Count | Locations |
|---------|-------|-----------|
| `Any` (bare) | 47 | `circuit_breaker.py:39`, `client_generator.py:5,29`, `mcp_adapter.py:8,179`, `mcp_service.py:5,88`, `server_builder.py:6,122`, `kafka_client.py:8` + 35 elsewhere |
| `dict[str, Any]` | 38 | `binding_parser.py:7,19`, `binding_writer.py:7,37,69`, `server_builder.py:96,122`, `request_builder.py:5`, `exposure/` writers, `serialization/*` |
| `isinstance` chains | 19 | `mcp_adapter.py:180-188` (3-deep), `amqp_client.py:150-161`, `kafka_client.py:140-151`, `base.py:31`, `json_serializer.py:15-29`, `protobuf_serializer.py:35-36`, `grpc_client.py:178-184,201-204,223-230` |

### 1.2 Global State & Mutable Defaults

| Issue | Count | Locations |
|-------|-------|-----------|
| `logger = logging.getLogger(__name__)` (module-level) | 9 | Every bus impl, `mcp_client_adapter.py`, `bridge.py` |
| Mutable default args (`dict`, `list`) | 12 | `binding_loader.py:47` `cls({})`, `priority_bus:28`, `service_discovery:29` `static_endpoints={}`, `transport_factory:19`, `bridge.py:62` |
| Module-level `BROADCAST = "*"` | 1 | `in_memory_message_bus.py:12` |
| Module-level `_LAZY` dict in `__init__` | 1 | `__init__.py:28` |
| `# type: ignore` | 5 | `kafka_bus.py:7` (x2), `kafka_client.py:41,53`, `mcp_adapter.py:98`, `http_client.py:92,123` |

### 1.3 Async Patterns

- **`asyncio.gather(*[...], return_exceptions=True)`** used in 4 bus impls (in_memory, kafka, topic, priority) — good pattern to port.
- **`asyncio.Lock()`** in 3 bus impls for concurrent handler registration.
- **`asyncio.create_task()` for consumer loops** in kafka, redis, priority, durable buses.
- **`asyncio.Queue`** in `durable_message_bus.py` for buffering.
- **`asyncio.Future`** used for await-in-callback in `mcp_adapter.py`, `amqp_client.py`.

### 1.4 Exception Swallowing

- Broad `except Exception` with log-and-continue in 6 bus listeners (kafka, rabbitmq, redis, topic, priority, durable).
- `except (ValueError, KeyError): pass` in 3 unsubscribe methods.
- Empty `except Exception` in `service_discovery.py:78`, `amqp_client.py:139,145`.
- `try/except Exception` with fallback in `avro_serializer.py` import handling.

---

## 2. Migration Notes (Score 1-5)

| Component | Score | Rationale |
|-----------|-------|-----------|
| **JSON Serializer** (`json_serializer.py`) | **5** | Pure data transform. `json.dumps`/`json.loads` → `serde_json`. Zero I/O. Trivial. |
| **Avro Serializer** (`avro_serializer.py`) | **4** | `fastavro` → `apache-avro` crate. Schema-based serde. Python fallback behavior (no schema → JSON) must be mirrored. |
| **Protobuf Serializer** (`protobuf_serializer.py`) | **4** | Dynamic message class loading via `__import__` is Python-specific. Protobuf codegen in Rust uses `prost`/`tonic-build` — need a different dynamic-dispatch approach. |
| **Message Models** (`message_models.py`) | **5** | Simple `pydantic.BaseModel` → Rust `struct` with `serde::Serialize/Deserialize`. `datetime::utcnow` trivial. |
| **Circuit Breaker** (`circuit_breaker.py`) | **4** | Pure state machine with async lock. Straightforward Rust translation with `tokio::sync::Mutex`. |
| **InMemoryMessageBus** | **5** | `HashMap` + `gather` pattern. No external deps. Ideal first Rust target. |
| **TopicMessageBus** | **5** | Same as in-memory but topic-routed. |
| **RequestReplyBus** | **4** | RPC pattern with timeout. Uses `asyncio.wait_for` → `tokio::time::timeout`. |
| **PriorityMessageBus** | **4** | `heapq` → `BinaryHeap` in Rust. One consumer task loop. |
| **DurableMessageBus** | **4** | `asyncio.Queue` → `tokio::sync::mpsc` bounded channel. |
| **HTTP Transport** (`http_client.py`) | **2** | `aiohttp` → `reqwest` (Rust). TLS, retry, connection pool, timeout all exist in reqwest. Python-specific lazy import pattern must be handled differently. |
| **gRPC Transport** (`grpc_client.py`) | **1** | `grpcio` dynamic stubs → `tonic` in Rust. Dynamic stub resolution (URL-parsed method paths) is harder in tonic which uses compile-time generated code. Python's `channel.unary_unary(f"/{method}", ...)` is unique. |
| **Kafka Transport** (`kafka_client.py`, `kafka_bus.py`) | **2** | `aiokafka` → `rdkafka` crate. Reply correlation pattern (produce + consume reply) maps well. Consumer group management is similar. |
| **AMQP Transport** (`amqp_client.py`, `rabbitmq_bus.py`) | **2** | `aio_pika` → `lapin` crate. Exchange/queue declare, publish/consume, reply-to pattern all map. |
| **Redis Pub/Sub** (`redis_pub_sub_bus.py`) | **2** | `redis.asyncio` → `redis-rs` with `tokio` feature. Pub/sub listener task pattern identical. |
| **Service Discovery** (`service_discovery.py`) | **2** | Kubernetes client (`kube-rs`), DNS (`trust-dns-resolver`). Python dynamic `getattr(self, f"_resolve_{backend.value}")` dispatch is hard in Rust. |
| **Auth** (`auth/`) | **3** | JWT, API key, OAuth2, mTLS — all have Rust equivalents (`jsonwebtoken`, `oauth2` crate). OAuth2Provider in Rust needs `reqwest` for token exchange. |
| **Binding Parser/Writer** (`bindings/`) | **3** | YAML/JSON parsing → `serde_yaml`/`serde_json`. Python `try/except ValueError` enum fallback pattern is verbose but doable. |
| **NorthBound Server Builder** | **3** | Dispatch table with handler registry. Higher-level orchestration. Some value in Rust (performance of dispatch), but Python interop for handler callbacks complicates. |
| **MCP Adapter** (`mcp_adapter.py`) | **1** | STDIO subprocess (Python `asyncio.create_subprocess_exec`) + JSON-RPC. SSE/HTTP fallback. Dynamic transport selection. Heavy Python ecosystem coupling. |
| **MCPService / MCPClientAdapter** | **1** | Subprocess management, JSON-RPC protocol, lazy connection proxy. Tightly coupled to `asyncio.subprocess`. Hard to migrate without PyO3 bridge. |

### Migration Priority Order

```
Phase 1 (Score 4-5): models, serializers (JSON/Avro), circuit_breaker, in_memory/topic bus
Phase 2 (Score 3-4): priority_bus, durable_bus, request_reply_bus, auth helpers, binding writers
Phase 3 (Score 2-3): HTTP transport, Kafka transport, AMQP transport, service_discovery
Phase 4 (Score 1-2): gRPC transport, Redis bus, MCP adapters, server_builder
```

---

## 3. Ownership Map

### Message Flow

```
Producer/Agent
    │ publish(msg)
    ▼
┌─────────────────────────────────────────────────────┐
│                     MessageBus                      │
│  ┌─────────────┐  ┌──────────┐  ┌────────────────┐  │
│  │ InMemoryBus  │  │ KafkaBus │  │ RabbitMQBus    │  │
│  │ (no deps)    │  │ (aiokfk) │  │ (aio_pika)     │  │
│  └─────────────┘  └──────────┘  └────────────────┘  │
│  ┌─────────────┐  ┌──────────┐  ┌────────────────┐  │
│  │ RedisBus     │  │ Priority│  │ TopicBus       │  │
│  │ (redis-py)   │  │ (heapq) │  │ (in-mem topic) │  │
│  └─────────────┘  └──────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────┘
    │ handler(msg)
    ▼
Consumer/Agent Handler
```

### Bus Lifecycle

| Phase | Method | Rust Equivalent |
|-------|--------|----------------|
| Init | `__init__()` | `new()` constructor |
| Connect | `start()` | `connect()` or `new()` with connection |
| Register | `subscribe()` | `subscribe().await` |
| Send | `publish()` | `publish().await` |
| Unregister | `unsubscribe()` | Channel drop / `unsubscribe().await` |
| Shutdown | `stop()` | `close()` / `Drop` impl |

### Ownership Rule

```
One Producer → N messages → Bus (routes by recipient/topic) → N Consumers
  - Bus owns the routing table (_subscribers, _handlers, _topics)
  - Bus owns background tasks (consumer loops, listener tasks)
  - Handlers are borrowed (Callable references)
  - Bridge decorates bus (wraps pattern)
```

---

## 4. PyO3 Binding Structure

### Recommended Architecture

```
┌──────────────────────────────────┐
│        Python (PyO3)            │
│  ┌────────────────────────────┐  │
│  │ Transport Layer (stays)    │  │
│  │  HTTPTransport (aiohttp)   │  │
│  │  GRPCTransport (grpcio)    │  │
│  │  KafkaTransport (aiokafka) │  │
│  │  MCPAdapter (subprocess)   │  │
│  └────────────────────────────┘  │
│              │ PyO3 bridge        │
│              ▼                    │
│  ┌────────────────────────────┐  │
│  │ Rust Extension Module      │  │
│  │  Serializers (serde)       │  │
│  │  Circuit Breaker (tokio)   │  │
│  │  Message Models            │  │
│  │  InMemory Bus              │  │
│  └────────────────────────────┘  │
└──────────────────────────────────┘
```

### PyO3 Trait Mapping

| Python ABC | PyO3 Equivalent | Notes |
|------------|----------------|-------|
| `MessageBus` | `#[pyclass(subclass)]` + `PyObject` protocol | Python subclasses can extend |
| `MessageSerializer` | `#[pyclass]` + `__call__` | `serialize`/`deserialize` methods |
| `AbstractTransport` | Keep in Python | Too coupled to async Python libs |
| `CircuitBreaker` | `#[pyclass]` | Pure state machine, trivial PyO3 |

### Key Bridge Decisions

1. **Serializers → Rust, bridged back**: `JSONSerializer`, `AvroSerializer` in Rust with `serde`. Python calls `rust_serialize(payload)` which returns `PyBytes`.
2. **MessageBus trait → PyO3 trait**: Bus abc could become a Rust trait, but Python impls (Kafka, RabbitMQ, Redis) would need to be subclassed via `#[pyclass(subclass)]`.
3. **Transport → stays Python**: Too many Python-native async I/O libs. Rust won't reimplement `aiohttp`, `aiokafka`, `aio_pika` etc.
4. **CircuitBreaker → Rust**: Pure logic, no I/O. Easy win.
5. **Bridge pattern → stays Python**: Thin decorator over `MessageBus`. Not worth moving.

---

## 5. Libraries Analysis

| Python Library | Rust Alternative | Migration Difficulty | Notes |
|---------------|-----------------|---------------------|-------|
| `aiohttp` | `reqwest` | Medium | Session management, connection pool, TLS. Python lazy-import pattern not needed in Rust. |
| `grpcio` | `tonic` + `prost` | **Hard** | Python uses dynamic stubs (`unary_unary(f"/{method}", ...)`). Tonic needs compile-time `protoc`-generated code. Dynamic dispatch requires `tonic::transport::Channel` with manual proto serialization. |
| `aiokafka` | `rdkafka` | Medium | Producer/Consumer APIs map well. Reply correlation pattern exists in both. `rdkafka` is C-based (librdkafka bindings). |
| `aio_pika` | `lapin` | Medium | Exchange/queue declare, publish, consume patterns map directly. AMQP `reply_to` pattern in both. |
| `redis` (`redis.asyncio`) | `redis-rs` | Medium | Pub/sub + channel/listen pattern. `redis-rs` async with `tokio-comp` feature. |
| `fastavro` | `apache-avro` | Medium | `schemaless_writer`/`schemaless_reader` → Avro crate's `write`/`read`. Schema handling is more explicit in Rust. |
| `protobuf` (dynamic) | `prost` + `tonic-build` | **Hard** | Python loads message classes dynamically by module path. Rust needs compile-time `.proto` compilation or a dynamic proto registry. |
| `kubernetes` | `kube-rs` | Medium | `client.CoreV1Api().read_namespaced_service_status()` → `kube::Api::<Service>::get()`. Async patterns differ. |
| `yaml` (PyYAML) | `serde_yaml` | Easy | Pure parsing. No ecosystem coupling. |
| `pydantic` | `serde` | Easy | `BaseModel` → `#[derive(Serialize, Deserialize)]`. Validation in Rust is manual. |
| `ssl` | `rustls` / `native-tls` | Medium | Python `ssl.SSLContext` → `rustls::ClientConfig` or `native_tls::TlsConnector`. |
| `asyncio` | `tokio` | Systemic | Every async pattern maps: `asyncio.gather` → `tokio::join!`/`futures::future::join_all`, `asyncio.Lock` → `tokio::sync::Mutex`, `asyncio.create_task` → `tokio::spawn`, `asyncio.Queue` → `tokio::sync::mpsc`, `asyncio.Future` → `tokio::sync::oneshot`. |
| `asyncio.subprocess` | `tokio::process` | Medium | STDIO JSON-RPC in MCP adapter. |
| `json` (stdlib) | `serde_json` | Easy | |
| `jwt` (stdlib base64) | `jsonwebtoken` | Medium | Python's `auth/jwt.py` is a header-setter only. Real JWT validation needs `jsonwebtoken` crate. |
| `oauth2` (custom impl) | `oauth2` crate | Medium | `ClientCredentials` token exchange. Python's `OAuth2TokenProvider` is a stub. |
| `heapq` | `std::collections::BinaryHeap` | Easy | `prioritized_message_bus.py` uses min-heap for message priority. |
| `dataclasses` | `struct` / `#[derive(Clone, Debug)]` | Easy | |

---

## 6. Performance Hot Paths

| Hot Path | Frequency | Current | Rust Opportunity |
|----------|-----------|---------|-----------------|
| **Message serialization** | Every message (all buses, all transports) | `AgentMessage.model_dump_json().encode()` | `serde_json::to_vec()` — 10-50x faster |
| **JSON deserialization** | Every message received | `AgentMessage.model_validate_json()` | `serde_json::from_slice()` — 10-50x faster |
| **Avro binary ser/deser** | Every message if configured | `fastavro.schemaless_writer/reader` | avro-rs crate — 5-10x faster |
| **Transport encoding** | Every outbound call | `_coerce_payload()` isinstance chains (3+ branches) | Static dispatch in Rust — 0 overhead |
| **Circuit breaker state transitions** | Every invocation | `asyncio.Lock` + `time.monotonic()` | `tokio::sync::Mutex` — similar, but no GIL contention |
| **Handler dispatch** | Every message | `asyncio.gather(*[h(msg) for h in handlers])` | `tokio::join_all()` — similar performance |
| **Priority queue push/pop** | Every publish | `heapq.heappush` + `asyncio.Lock` | `BinaryHeap` — similar |
| **Kafka reply correlation** | Every request-reply | `consumer.getmany()` polling loop | `rdkafka` consumer — callback-driven, no polling |
| **DNS resolution** | Every first call per operation | `socket.getaddrinfo()` (blocking in async) | `trust-dns-resolver` with async — no blocking |

### Estimated Performance Gains (Rust)

| Component | Gain Estimate | Reason |
|-----------|--------------|--------|
| JSON Serialization | 10-50x | Serde zero-copy, no GIL, no encoding round-trip |
| Avro Serialization | 5-10x | No GIL, no Python object overhead |
| InMemory Bus dispatch | 2-5x | No GIL on subscriber list iteration |
| Circuit Breaker | 2-3x | Pure logic, no Python overhead |
| HTTP transport | ~1.5x | reqwest vs aiohttp — similar internals |
| Kafka/AMQP transport | ~1-2x | librdkafka/lapin — similar performance to Python bindings |

---

## 7. Error Handling

### Error Patterns by Source

| Source | Error Pattern | Current Handling | Rust Strategy |
|--------|--------------|-----------------|---------------|
| **Connection** (all transports) | Connection refused, timeout | `try/except Exception` → `raise RuntimeError(msg)` | `Result<_, TransportError>` enum — `ConnectionError`, `TimeoutError` |
| **Serialization** | Invalid payload, schema mismatch | `try/except` → fallback to JSON, or `raise` | `Result<_, SerdeError>` — compile-time type safety |
| **Deserialization** | `model_validate_json()` failure | Unhandled (panic in handler) | `serde_json::from_slice()` returns `Result` — propagate |
| **Subscription** | Duplicate/unsubscribe missing | `try/except (ValueError, KeyError): pass` | Return `Result<_, BusError>` — no silent swallowing |
| **Publish** | No handler/queue/subscriber | Log warning, `return` silently | `Option` → explicit `None` check |
| **Circuit breaker** | Open state | `raise RuntimeError("Circuit breaker is open")` | Custom `CircuitBreakerError` type |
| **Timeout** | Request/reply timeout | `asyncio.TimeoutError` → `TimeoutError` re-raise | `tokio::time::error::Elapsed()` → `TimeoutError` |
| **Retry** | Transient failures | `asyncio.sleep(min(2.0, 0.1 * 2**attempt))` | Exponential backoff with jitter in Rust |
| **Unsubscribe** | Handler not found | `except ValueError: pass` | `HashMap::remove()` returns `Option` — explicit |

### Error Type Hierarchy (Rust Design)

```rust
#[derive(Debug, thiserror::Error)]
pub enum BusError {
    #[error("connection failed: {0}")]
    Connection(String),
    #[error("timeout after {0}ms")]
    Timeout(u64),
    #[error("serialization error: {0}")]
    Serialization(#[from] serde_json::Error),
    #[error("circuit breaker is open for operation '{0}'")]
    CircuitOpen(String),
    #[error("no handler registered for {0}")]
    NoHandler(String),
    #[error("bus not started: call start() first")]
    NotStarted,
}
```

### Circuit Breaker State Machine

```
CLOSED ──(failure_count >= threshold)──▶ OPEN ──(recovery_timeout elapsed)──▶ HALF_OPEN
  ▲                                         │                                     │
  │                                         │                                     │
  └──────────(success)──────────────────────┘                                     │
  ▲                                                                               │
  └────────────────────────(success)──────────────────────────────────────────────┘
                                                                   │
                                           (failure on half-open)──▶ OPEN (restart timeout)
```

Current Python uses `asyncio.Lock` for thread safety. Rust can use `tokio::sync::Mutex` or an `Atomic` state machine for the hot path (state reads).

---

## Appendix: File Inventory

| File | Lines | Role | Migrate Score |
|------|-------|------|---------------|
| `__init__.py` | 65 | Lazy imports | 5 (trivial) |
| `bridge.py` | 67 | Decorator pattern | 5 |
| `buses/base_message_bus.py` | 39 | ABC | 5 |
| `buses/message_models.py` | 17 | Models | 5 |
| `buses/in_memory_message_bus.py` | 47 | Simple bus | 5 |
| `buses/topic_message_bus.py` | 40 | Topic bus | 5 |
| `buses/request_reply_bus.py` | 39 | RPC bus | 4 |
| `buses/priority_message_bus.py` | 72 | Priority bus | 4 |
| `buses/durable_message_bus.py` | 53 | Queue bus | 4 |
| `buses/kafka_bus.py` | 71 | Kafka bus | 2 |
| `buses/rabbitmq_bus.py` | 73 | AMQP bus | 2 |
| `buses/redis_pub_sub_bus.py` | 69 | Redis bus | 2 |
| `common/serialization/json_serializer.py` | 29 | JSON serde | 5 |
| `common/serialization/avro_serializer.py` | 64 | Avro serde | 4 |
| `common/serialization/protobuf_serializer.py` | 49 | Protobuf | 4 |
| `common/transport/base.py` | 51 | Transport ABC | 5 |
| `common/transport/http_client.py` | 152 | HTTP | 2 |
| `common/transport/grpc_client.py` | 237 | gRPC | 1 |
| `common/transport/kafka_client.py` | 173 | Kafka | 2 |
| `common/transport/amqp_client.py` | 168 | AMQP | 2 |
| `common/transport/mcp_adapter.py` | 198 | MCP | 1 |
| `common/auth/auth_manager.py` | 46 | Auth dispatch | 3 |
| `common/auth/jwt.py` | 20 | JWT header | 3 |
| `common/auth/api_key.py` | 20 | API key | 3 |
| `common/auth/oauth2.py` | 55 | OAuth2 | 3 |
| `common/auth/mtls.py` | 28 | mTLS | 3 |
| `consumption/circuit_breaker.py` | 115 | CB state machine | 4 |
| `consumption/models.py` | 19 | Models | 5 |
| `consumption/binding_loader.py` | 249 | Binding catalog | 3 |
| `consumption/client_generator.py` | 153 | Invocation client | 2 |
| `consumption/request_builder.py` | 137 | Request builder | 3 |
| `consumption/transport_factory.py` | 49 | Factory | 3 |
| `consumption/service_discovery.py` | 158 | Service discovery | 2 |
| `consumption/mcp_service.py` | 95 | MCP service | 1 |
| `consumption/mcp_client_adapter.py` | 100 | MCP client | 1 |
| `consumption/mcp_binding_loader.py` | 127 | MCP binding | 1 |
| `exposure/server_builder.py` | 129 | Server builder | 3 |
| `exposure/kubernetes_manifest_writer.py` | 62 | K8s manifest | 3 |
| `exposure/gateway_config_writer.py` | 39 | Gateway config | 3 |
| `exposure/docker_compose_writer.py` | 36 | Docker Compose | 3 |
| `exposure/mcp_server_writer.py` | 46 | MCP writer | 3 |
| `messaging/channel_manager.py` | 93 | Channel manager | 2 |
| `messaging/message_binding_writer.py` | 20 | Binding writer | 3 |
| `messaging/message_binding_parser.py` | 42 | Binding parser | 3 |
| `messaging/adapters/kafka_adapter.py` | 0 | Stub | — |
| `messaging/adapters/nats_adapter.py` | 0 | Stub | — |
| `messaging/adapters/amqp_adapter.py` | 0 | Stub | — |
| `bindings/binding_parser.py` | 186 | Parse bindings | 3 |
| `bindings/binding_writer.py` | 88 | Write bindings | 3 |
| `bindings/mcp_binding_writer.py` | 68 | MCP writer | 3 |
