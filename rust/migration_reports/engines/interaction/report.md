# Interaction Engine — Rust Migration Analysis

**Location:** `engines/interaction/`
**Backends:** `engines/interaction/backends/`
**Total Python files:** 16 (12 core + 4 backends)
**Purpose:** Multi-agent conversation strategies (debate, group-chat, broadcast, round-robin, self-refine, coordinator, ensemble)

---

## 1. Pre-Refactor Analysis

### 1.1 `Any` Usage

| File | Occurrences | Risk |
|------|-------------|------|
| `base_strategy.py` | 1 (`agent_registry` param) | Low — registry is a dict internally |
| `broadcast_strategy.py` | 2 (`_normalize_gather_results`, `_aggregate_outputs`) | Medium — isinstance chains on results |
| `coordinator_strategy.py` | 1 (`agent_registry` param) | Low |
| `debate_strategy.py` | 1 (`critique` payload) | Medium — dict/str branching |
| `ensemble_strategy.py` | 3 (`_normalize_output` param/return, `agent_registry`) | Medium — duck-typing on output |
| `group_chat_strategy.py` | 6 (`_extract_message`, `_extract_context_update`, `_extract_done_flag`, `_resolve_participants` params) | **High** — pervasive isinstance on agent outputs |
| `round_robin_strategy.py` | 1 (`storage` param) | Low |
| `self_refine_strategy.py` | 1 (`_extract_score` param) | Medium |
| `mediator.py` | 1 (`kwargs: Any`) | Low |
| `strategy_registry.py` | 0 | None |
| `interaction_models.py` | 2 (`context`, `metadata` fields) | Low — pydantic Any fields |
| `backends/autogen_backend.py` | 2 (`llm_config`, `strategy_overrides`) | Low |
| `backends/native_backend.py` | 1 (`strategy_overrides`) | Low |

**Hotspots:** `group_chat_strategy.py` is the worst offender — 6+ duck-typed `isinstance` checks on agent output. `broadcast_strategy.py` and `ensemble_strategy.py` follow.

### 1.2 `dict[str, Any]` / Type Aliases

All type aliases in `_types.py` resolve to `Any`:
- `FeelContext = dict[str, Any]`
- `MessagePayload = dict[str, Any]`
- `Metadata = dict[str, Any]`
- `RawData = dict[str, Any]`
- `VariableValue = Any`

This is intentional ("semantic intent over type safety") but every strategy blindly passes context dicts to agents. There are **zero TypedDicts** in the interaction layer.

### 1.3 `isinstance` Chains

| File | isinstance target | Count |
|------|------------------|-------|
| `broadcast_strategy.py:97-106` | `AgentOutput` / `BaseException` | 2 |
| `debate_strategy.py:88` | `dict` with `.get("approved")` | 1 |
| `ensemble_strategy.py:163-166` | duck-type `model_dump` / `dict` | 1 |
| `group_chat_strategy.py:167,172,194,207,220,234,247` | `dict` / `str` / `list` | 7+ |
| `self_refine_strategy.py:143-146` | `dict` with `.get("score")` | 1 |
| `round_robin_strategy.py` | implicit via `_run_agent` | 0 direct |

### 1.4 ABCs

| Class | File | Abstract Methods |
|-------|------|-----------------|
| `InteractionStrategy` | `base_strategy.py:16` | `execute(self, request)` |
| `BaseOrchestrationBackend` | `backends/base_backend.py:8` | `execute(self, request)` |

Both single-method ABCs. Straightforward to model as Rust traits.

---

## 2. Migration Notes — Score: **3/5**

**Why 3 (not lower):**
- **Medium complexity** — 7 strategy patterns each with distinct orchestration logic
- **Async Python → Rust async** — `asyncio.gather`, `await agent.run()` must become `tokio::spawn` / `join_all`
- **Dynamic dispatch** — strategy selection by string key (`scenario_name`) needs `enum` matching
- **Shared mutable context** — `FeelContext` (`dict[str, Any]`) is mutated by-reference throughout; Rust ownership model forces a redesign
- **7 strategies × varying complexity** = meaningful but bounded scope

**Why not higher (not 4-5):**
- **Thin orchestration** — strategies route messages, they don't do heavy computation
- **Single-responsibility** — each strategy is ~100-170 lines, self-contained
- **No CPU-bound compute** — all bottlenecks are I/O (agent calls)
- **Agent communication stays in Python** per requirement, reducing migration surface
- **Minimal dependency on external libs** — only AutoGen (which has native fallback)

---

## 3. Ownership Map

```
InteractionRequest ──> InteractionMediator ──> InteractionStrategy (ABC)
                                                      │
                          ┌───────────────────────────┬┼───────────────────────────┐
                          │                           ││                          │
                    BroadcastStrategy          CoordinatorStrategy        GroupChatStrategy
                    (parallel fan-out)         (sequential manager)      (round-robin turns)
                          │                           │                          │
                          ├── agent_registry.get()    ├── _run_agent()           ├── _run_agent()
                          ├── asyncio.gather()        ├── _run_validation()      ├── _extract_message()
                          └── _aggregate_outputs()    └── _aggregate()           └── _extract_done_flag()
                          │                           │                          │
                    DebateStrategy             EnsembleStrategy          RoundRobinStrategy
                    (proposer↔critic loop)     (voting/aggregation)      (sequential turns)
                          │                           │                          │
                          ├── _run_agent()            ├── _run_agent()           ├── _run_agent()
                          ├── history.append()        ├── _aggregate_votes()     └── history.append()
                          └── approval logic          └── Counter.most_common()
                          │
                    SelfRefineStrategy
                    (generate→critique→refine loop)
                          │
                          ├── _run_agent() (×3 roles)
                          ├── _extract_score()
                          └── convergence check
```

**Message flow:** `InteractionStrategy._run_agent()` → `agent_registry.get(name)` → `agent.run(input)` → `AgentOutput` → stored in `results: list[AgentOutput]`

**Bus flow:** `InteractionStrategy._emit()` → `message_bus.publish(AgentMessage)` — fire-and-forget events

---

## 4. PyO3 Binding Structure

### Recommended architecture:

```
┌─────────────────────────────────────────────────────────┐
│                     Python Layer                         │
│                                                         │
│  InteractionMediator (dispatch)                         │
│  AgentRegistry (dict[str, BaseAgent])                    │
│  MessageBus (pub/sub)                                   │
│  Agent.run() (Python agents stay in Python)             │
└──────────────────────┬──────────────────────────────────┘
                       │ PyO3 boundary
┌──────────────────────┴──────────────────────────────────┐
│                     Rust Layer                           │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │  InteractionStateMachine                          │   │
│  │  ┌────────────────┐  ┌─────────────────────────┐ │   │
│  │  │ Strategy Enum   │  │ ConversationHistory     │ │   │
│  │  │  - Broadcast    │  │  Vec<AgentMessage>      │ │   │
│  │  │  - RoundRobin   │  │  History compression    │ │   │
│  │  │  - GroupChat    │  │  Dedup / truncation     │ │   │
│  │  │  - Debate       │  │                         │ │   │
│  │  │  - Ensemble     │  └─────────────────────────┘ │   │
│  │  │  - Coordinator  │                              │   │
│  │  │  - SelfRefine   │  ┌─────────────────────────┐ │   │
│  │  └────────────────┘  │  StrategyContext          │ │   │
│  │                       │  - results: Vec<Output>   │ │   │
│  │  ┌────────────────┐  │  - history: Vec<Round>    │ │   │
│  │  │ Strategy trait  │  │  - metadata: HashMap      │ │   │
│  │  │  fn execute()   │  └─────────────────────────┘ │   │
│  │  │  fn context()   │                              │   │
│  │  │  fn stats()     │  Safety:                     │   │
│  │  └────────────────┘  - Context is behind Arc<RwLock>│ │
│  │                       - No shared mutable borrows  │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Output Aggregation Helpers                       │   │
│  │  - merge_outputs() : HashMap<String, Value>       │   │
│  │  - plurality_vote() : Option<String>              │   │
│  │  - majority_vote() : Option<String>               │   │
│  │  - extract_score() : f64                          │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Strategy Dispatch (Rust `enum` match):

```rust
#[pyclass]
enum StrategyKind {
    Broadcast,
    RoundRobin,
    GroupChat,
    Debate,
    Ensemble,
    Coordinator,
    SelfRefine,
}

#[pymethods]
impl InteractionStateMachine {
    fn execute(&self, request: PyObject) -> PyResult<PyObject> {
        match self.strategy {
            StrategyKind::Broadcast => self.run_broadcast(request),
            StrategyKind::Debate => self.run_debate(request),
            // ...
        }
    }
}
```

### What stays in Python:

| Component | Reason |
|-----------|--------|
| `AgentRegistry` | Holds `BaseAgent` instances — Python objects |
| `MessageBus` | Pub/sub with Python handlers, subscribers |
| `Agent.run()` | Each agent is a Python object (LLM calls, tool use) |
| `InteractionMediator` | Thin facade — mostly passes through |
| AutoGen integration | Heavy Python dependency |

### What goes to Rust:

| Component | Reason |
|-----------|--------|
| `InteractionStateMachine` | Core orchestration; type-safe enum dispatch |
| `ConversationHistory` | Vec-based, history management, truncation |
| `StrategyContext` | Typed state per-session |
| `Output aggregation` | Pure data transforms — no Python interaction |
| `Debate/SelfRefine loop controllers` | State machine loop logic |
| `RoundRobin turn management` | Counter + index arithmetic |

---

## 5. Libraries Analysis

### Internal imports (from `engines/`):

| Import source | Used by | Notes |
|--------------|---------|-------|
| `engines._types` | All strategies | Type aliases — trivial to replicate |
| `engines.agent.models` (AgentInput, AgentOutput) | All strategies | Pydantic — must model in Rust |
| `engines.agent.base_agents.base_agent` (BaseAgent) | broadcast, coordinator, mediator, models | Stays in Python |
| `engines.communication.buses.base_message_bus` (MessageBus) | base, coordinator, ensemble, group_chat, backends | Stays in Python |
| `engines.communication.buses.message_models` (AgentMessage) | interaction_models (re-export), ensemble | Pydantic model |

### External imports:

| Library | File | Usage | Migration impact |
|---------|------|-------|-----------------|
| `pydantic` | `interaction_models.py`, backends | `BaseModel` for request/result | Replace with `#[pyclass]` / serde |
| `autogen` | `backends/autogen_backend.py` | AutoGen GroupChat wrapper | Stays in Python entirely |
| `asyncio` | `broadcast_strategy.py` | `asyncio.gather` | → `tokio::join_all` / `futures::join_all` |
| `threading.RLock` | `strategy_registry.py` | Thread-safe registry | → `std::sync::RwLock` / `Mutex` |
| `collections.Counter` | `ensemble_strategy.py` | Majority voting | → `HashMap` count or `itertools::counts` |
| `datetime` | Throughout | Timestamps | → `chrono` or `std::time` |
| `uuid` | `interaction_models.py` | Workflow IDs | → `uuid` crate |
| `functools.cached_property` | `autogen_backend.py` | Lazy check | → `OnceCell` / `OnceLock` |

### Migration difficulty by library:

| Library | Difficulty | Strategy |
|---------|-----------|----------|
| pydantic | Medium | `#[pyclass]` + `serde` for same ergonomics |
| autogen | N/A | Keep in Python (fallback path only) |
| asyncio | Low | tokio is a direct analog |
| threading.RLock | Low | `std::sync::Mutex` or `RwLock` |
| collections.Counter | Low | Trivial HashMap impl |

---

## 6. Performance Hot Paths

### 6.1 Message Routing (Medium frequency)

- **Where:** `_run_agent()` called by every strategy (~7-20 calls per workflow)
- **Cost:** Dict lookup in `agent_registry` + await `agent.run()` (LLM call — milliseconds to seconds)
- **Rust migration impact:** The dict lookup disappears (registry stays in Python, PyO3 call overhead per agent)
- **Verdict:** Rust provides minimal perf gain here — agent execution dominates

### 6.2 Strategy Selection (Low frequency)

- **Where:** `NativeOrchestrationBackend._build_strategy()` and `InteractionMediator.execute()`
- **Cost:** Dict lookup by string key
- **Rust migration impact:** Enum match replaces string lookup — negligible gain
- **Verdict:** Only valuable for type safety, not speed

### 6.3 Conversation History Management (Medium frequency)

- **Where:** `broadcast_strategy.py` (no history), `debate_strategy.py` (appends per round), `group_chat_strategy.py` (builds messages), `round_robin_strategy.py` (appends history), `coordinator_strategy.py` (accumulates)
- **Cost:** `list.append()` + `dict(context)` copy per agent call
- **Rust migration impact:** `Vec` with pre-allocated capacity + no GIL during mutation
- **Verdict:** Moderate gain — context dict copying is the real cost (stays in Python)

### 6.4 Parallel Agent Execution (Medium frequency)

- **Where:** `broadcast_strategy.py:27-28` — `asyncio.gather` for all agents
- **Cost:** N agents × LLM call time (parallel)
- **Rust migration impact:** `tokio::join_all` — equivalent perf, no meaningful gain
- **Verdict:** I/O bound; Rust cannot speed up LLM calls

### 6.5 Output Aggregation (Low frequency)

- **Where:** `_aggregate_outputs` (broadcast), `_aggregate_votes` (ensemble)
- **Cost:** Iteration over small lists (typically 2-10 agents)
- **Rust migration impact:** Negligible — lists are tiny
- **Verdict:** Not worth migrating for perf

### 6.6 Event Emission (Low frequency)

- **Where:** `_emit()` called per agent turn
- **Cost:** Creates `AgentMessage`, awaits `message_bus.publish()`
- **Rust migration impact:** Bus stays in Python; PyO3 boundary penalty for each event
- **Verdict:** If bus is hot path, consider batch events

### Performance Summary

| Path | Frequency | Est. cost | Rust benefit |
|------|-----------|-----------|-------------|
| Agent execution (`_run_agent`) | Per turn | High (LLM) | None (I/O bound) |
| Context dict copy | Per turn | Medium | Medium (avoid alloc) |
| History management | Per turn | Low-medium | Low-Medium |
| Output aggregation | Per workflow | Low | None |
| Event emission | Per turn | Low | Negative (PyO3 boundary) |
| Strategy selection | Per workflow | Negligible | Low |

**Net performance impact of Rust migration: Minimal to negative.** The hot path is awaiting Python agents (LLM calls). Rust would add PyO3 boundary crossing overhead per agent invocation. The primary motivation should be **type safety and correctness**, not performance.

---

## 7. Error Handling

### Current patterns:

| Pattern | Used in | Rust equivalent |
|---------|---------|-----------------|
| `try/except` wrapping `agent.run()` | `base_strategy.py:96-118`, `broadcast.py:65-90` | `Result<AgentOutput, PyErr>` |
| `return_exceptions=True` in gather | `broadcast_strategy.py:28` | Individual `Result` per future |
| `isinstance(item, BaseException)` normalization | `broadcast_strategy.py:99` | `Result::Err` mapping |
| Early return on error | `debate.py:57`, `self_refine.py:52` | `?` operator |
| Error accumulation in context | `coordinator.py:69-71`, `ensemble.py:58-60` | `Vec<(String, String)>` in context |
| `if output.error` branches | Every strategy | `match result { Ok(v) => ..., Err(e) => ... }` |
| `error: str | None` fields | `AgentOutput`, `InteractionResult` | `Option<String>` |
| `status` literal enum | `InteractionResult` | `enum Status { Success, Partial, Failed }` |
| `notes: list[str]` for tracing | `InteractionResult`, `autogen_backend.py` | `Vec<String>` |
| Missing agent → error output | `base_strategy.py:89-94` | `None` check → `Err` variant |

### Strengths:
- Every agent call is wrapped in try/except — no unhandled agent failures
- `return_exceptions=True` prevents one agent crash from killing the whole broadcast
- Error accumulation (not just fail-fast) in coordinator/ensemble
- Structured `AgentOutput.error` field with string messages

### Weaknesses:
- `error: str | None` is type-unsafe — no error code/enum differentiation
- Error propagation is ad-hoc (some strategies break, others accumulate)
- No typed error hierarchy — everything is a string
- Context mutation means error state is shared across turns (mutable alias risk)
- Missing agent detection returns `AgentOutput` with error string (not exceptional) — inconsistent with try/except pattern

### Rust migration improvements:
- `enum StrategyError { AgentNotFound, AgentFailed(String), Internal(String) }`
- `Result<T, StrategyError>` enforced at compile time
- Error variants can carry structured metadata (agent_id, round, turn)
- `?` operator for early returns removes ad-hoc break logic
- Accumulated errors in `Vec<(usize, StrategyError)>` (typed, not dict soup)

---

## Summary Table

| Criterion | Score | Rationale |
|-----------|-------|-----------|
| `Any` severity | 6/10 | 15+ occurrences, concentrated in group_chat |
| isinstance chains | 5/10 | Duck-typing on agent output payloads |
| ABC complexity | 1/10 | Two single-method ABCs — trivial to trait |
| Error handling | 5/10 | Wrapped but untyped; accumulation is mixed |
| Performance gain | 2/10 | I/O bound; Rust adds PyO3 overhead |
| Type safety gain | 8/10 | Enum dispatch, typed context, Result types |
| Migration complexity | 3/10 | Self-contained, bounded scope, 7 patterns |
| **Overall** | **~4/10** | **High-value for correctness; low-value for speed** |

**Recommendation:** Migrate the **state machine and strategy dispatch** to Rust for type safety. Keep agent calls and message bus in Python. The conversation history (`Vec<AgentMessage>`) is the best candidate for a shared Rust-owned structure accessed via PyO3.
