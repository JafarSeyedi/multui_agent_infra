# ADT Integration — Master Specification

Date: 2026-06-15

Scope: Map Google ADT (Agent Development Toolkit) features against the
existing multi-agent-infra codebase and define phased implementation.

---

## 1. Architecture Principles

- **Plugin-first**: Session, Memory, Artifact services are ABCs with
  in-memory defaults; swap implementations without changing agent code.
- **Consistent patterns**: All new additions follow the existing
  models/parsers/writers pattern used throughout the codebase.
- **Separation of concerns**: Sessions (turn-to-turn), Memory (cross-session
  recall), Artifacts (binary persistence) are distinct services.
- **Backend-agnostic model layer**: No hard coupling to Gemini types;
  adapters where needed.

---

## 2. Phase 1: Session & Runtime

### 2.1 Session Model

```python
class Session(BaseModel):
    id: str
    app_name: str
    user_id: str
    session_id: str
    state: dict[str, Any]          # persisted across turns
    events: list[Event]
    created_at: datetime
    updated_at: datetime
```

### 2.2 Event Model

```python
class Event(BaseModel):
    id: str
    invocation_id: str
    author: str                    # "user" or agent name
    content: Content | None
    actions: EventActions           # state_delta, artifact_delta
    timestamp: datetime
```

### 2.3 SessionService (Plugin ABC)

```python
class BaseSessionService(ABC):
    async def create_session(app_name, user_id, session_id) -> Session
    async def get_session(app_name, user_id, session_id) -> Session | None
    async def list_sessions(app_name, user_id) -> list[Session]
    async def delete_session(app_name, user_id, session_id) -> None
    async def append_event(session, event) -> None

class InMemorySessionService(BaseSessionService):
    # dict[(app_name, user_id, session_id), Session]
```

### 2.4 Runner

```python
class Runner:
    def __init__(self, agent, app_name, session_service, ...)
    async def run_async(user_id, session_id, new_message) -> AsyncIterator[Event]
```

Creates/loads sessions, creates invocations, delegates to agent,
yields events, persists via SessionService.

---

## 3. Phase 2: Callback System

### 3.1 Hook points

| Hook | Signature | Guardrail |
|---|---|---|
| `before_agent_callback` | `(CallbackContext) -> Content \| None` | Return Content to skip agent |
| `after_agent_callback` | `(CallbackContext) -> None` | Cleanup / logging |
| `before_model_callback` | `(Ctx, LlmRequest) -> LlmResponse \| None` | Return response to skip LLM |
| `after_model_callback` | `(Ctx, LlmResponse) -> LlmResponse \| None` | Filter / reformat |
| `before_tool_callback` | `(ToolContext, args) -> dict \| None` | Return dict to skip tool |
| `after_tool_callback` | `(ToolContext, result) -> dict \| None` | Post-process result |

### 3.2 Guardrail semantics

Return `None` → proceed. Return response → skip next step.
Enables: caching, guardrails, dynamic injection, auth checks.

### 3.3 Context objects

```python
class CallbackContext:
    agent_name, session, state, invocation_id
    async save_artifact(filename, data, mime_type) -> int

class ToolContext(CallbackContext):
    tool_name
    async search_memory(query) -> SearchMemoryResponse
```

---

## 4. Phase 3: Agent Patterns

### 4.1 RoutedAgent

Explicit routing function selects sub-agent per turn.

```python
class RoutedAgent(Agent):
    agents: dict[str, Agent]
    router: Callable

    # On failure before output: router recalled with errorContext
    # Failed keys cannot be re-selected
```

### 4.2 Planners

```python
class BuiltInPlanner:
    thinking_config: ThinkingConfig  # budget, include_thoughts

class PlanReActPlanner:
    pass  # Forces plan → action → reasoning structure
```

### 4.3 Streaming Agent

Transport-layer concern (WebSocket/SSE). Detailed streaming design
deferred to transport-layer phase; core engine produces async iterators.

---

## 5. Phase 4: Memory & Artifacts

### 5.1 Memory Service

```python
class BaseMemoryService(ABC):
    async add_session_to_memory(session: Session) -> None
    async search_memory(app_name, user_id, query) -> SearchMemoryResponse
```

- `InMemoryMemoryService` → keyword search, `engines/memory/`
- Integration: `engines/knowledge/` RAG engines can implement same ABC
- Built-in tools: `PreloadMemoryTool`, `load_memory`

### 5.2 Artifact Service

```python
class BaseArtifactService(ABC):
    async save_artifact(app, user, session, filename, data, mime) -> int
    async load_artifact(app, user, session, filename, version) -> Part | None
    async list_artifact_keys(app, user, session) -> list[str]
    async delete_artifact(app, user, session, filename) -> None
```

- `InMemoryArtifactService` → dict of Part objects
- Namespacing: `user:` prefix = cross-session, plain = session-scoped
- Integration with `engines/document/`: document models (BaseDocument)
  can be stored as artifacts; artifact service = binary storage,
  document engine = parse/write semantics

---

## 6. Phase 5: I/O & YAML Configuration

### 6.1 Agent model extensions

```python
class AgentDefinition(BaseModel):
    # ...existing fields
    input_schema: type[BaseModel] | None
    output_schema: type[BaseModel] | None
    output_key: str | None
    include_contents: Literal["default", "none"] = "default"
```

### 6.2 YAML Agent Config

Follow models/parsers/writers pattern:

```yaml
# agents/weather-agent.yaml
name: weather_agent
model: gemini-flash-latest
description: Returns current weather
instruction: Use the weather tool.
tools: [weather_api]
input_schema:
  city: string
output_schema:
  temperature: number
  conditions: string
output_key: last_weather
```

### 6.3 Context Caching & Compaction (sketches)

```python
class ContextCacheConfig:
    min_tokens: int = 0
    ttl_seconds: int = 1800
    cache_intervals: int = 10
```

Compaction: sliding window — when events exceed N invocations,
older events are summarized and replaced with a summary event.

---

## 7. Phase 6: Search Grounding

Both tools live in `engines/tools/` following existing tool patterns:

- **GoogleSearchTool**: public web, Google AI Studio / Vertex auth
- **VertexAiSearchTool**: enterprise Agent Search datastores, Vertex only

Both return `groundingMetadata` (chunks, supports, retrieval queries).

---

## 8. Phase 7: Cross-cutting Plugins & LiteLLM

### 8.1 Plugins

```python
class BasePlugin(ABC):
    # Implements any subset of callback hooks
    async on_before_agent(ctx), on_after_agent(ctx)
    async on_before_model(ctx, req), on_after_model(ctx, resp)
    # ... all 6 hook points

# Registered on Runner, applies globally
runner = Runner(agent=root, plugins=[LoggingPlugin(), PolicyPlugin()])
```

### 8.2 LiteLLM integration

```python
class LiteLLMInterface:
    async generate(model: str, messages, config) -> LlmResponse
```

`LlmAgent` uses `LiteLLMInterface` instead of hardcoded Gemini client.
Backend abstraction — analogues to our `BaseOrchestrationBackend`.

---

## Appendices

### A. Existing codebase state (pre-implementation)

- `engines/agent/protocols.py`: A2AProtocol (JSON-RPC), FIPAProtocol
- `engines/agent/backends/autogen_backend.py`: AutoGen GroupChat (native fallback)
- `engines/agent/strategies/`: broadcast, debate, coordinator, ensemble,
  round_robin, self_refine, group_chat
- `engines/orchestration/multi_agent/`: MultiAgentEngine, MultiAgentMediator
  with handlers (coordination, interaction, protocol, negotiation, executor)
- `engines/tools/models/code_execution/`: Code Execution already exists

### B. File naming conventions

- YAML configs: `agents/<agent-name>.yaml`
- Session services: `engines/session/` (or `engines/storage/`)
- Memory services: extend `engines/memory/`
- Artifact services: `engines/artifact/` (or align with `engines/document/`)
