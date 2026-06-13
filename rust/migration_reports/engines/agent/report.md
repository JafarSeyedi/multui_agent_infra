# Migration Report: `engines/agent/`

**Scored**: 3/5 — partial Rust migration viable. State machine agent + skill execution pipeline are Rust-friendly. Content model layer is pure Pydantic (~3000 lines) with no business logic — Python stays.

---

## 1. Pre-refactor Analysis

### `Any` / `dict[str, Any]` Usage (Heavy)

| File | Issue |
|------|-------|
| `builders.py` | `_vector_db: Any`, `_storage: Any`, `with_extra(**kwargs: Any)` — no type narrowing |
| `factories.py` | `SkillAgentFactory.create(..., skill_loader: Any, llm_client: Any)`, `StateMachineAgentFactory.create(..., state_machine_doc: Any)` |
| `state_machine_agent.py` | `state_machine_doc: Any`, `self.state_machine: Any`, all state/transition variables typed `Any` — pervasive, ~15 occurrences |
| `mediator.py` | `input_data: AgentInput \| RawData` where `RawData = dict[str, Any]` |
| `agent_registry.py` | `async def run(..., input_data: RawData)` |
| `base_agent.py` | `run(input_data: Any)`, `_validate_input(input_data: Any)` |
| `skill_agent.py` | `skill_executor: SkillExecutor` is a `Protocol`, `vector_db: Any`, `storage: Any` |

### `isinstance` Chains

- `base_agent.py:78-90` — `_validate_input` / `_validate_output`: three-way isinstance dispatch (`AgentInput`, `BaseModel`, `dict`)
- `mediator.py:43` — `isinstance(input_data, dict)` to coerce `RawData` into `AgentInput`
- `state_machine_agent.py:153-157` — `isinstance(skill_result, dict)` / `isinstance(skill_result, list)` on execution results

### Global State

- `factories.py:16` — `AgentFactory._registry: dict[str, type[BaseAgent]]` is a **class-level mutable dict** — process-global registry, test isolation hazard.
- `agent_registry.py` — `self.agents: dict[str, BaseAgent]` is instance-level but singleton-like in practice.

---

## 2. Migration Notes (Score 3/5)

| Component | Rust Candidate | Reasoning |
|---|---|---|
| **BaseAgent** (ABC, Generic) | Medium | Core control flow (run → validate → execute → log) maps to a trait. But `run_sync` asyncio dance is Python-specific. |
| **StateMachineAgent** | **High** | State machine execution (states, transitions, guards) is a classic Rust domain. `_execute_state_machine` loop with visited-set loop detection is trivial in Rust. Guard evaluation via `safe_expr_eval` can be a native expression evaluator. |
| **SkillAgent** | **High** | `execute()` dispatch to batch/stepwise executor is straightforward. LLM client call is async but abstractable. |
| **Content models** (110 agents) | **Zero** | Pure Pydantic I/O models — 3000 lines across 12 files. No business logic. Keep in Python with PyO3 bridge. |
| **SafeEval** | **Medium** | AST-walking expression evaluator is doable in Rust (use `syn` or hand-written recursive descent). Security model is simpler in Rust (no `eval()` at all). |
| **TextRewriterAgent** | Low | Heavy LLM coupling and `hasattr` dispatch — Python idiom. |
| **InteractionAgent** | Low | Tightly coupled to `NativeOrchestrationBackend`, `MessageBus` — Python async ecosystem. |

### Python-specific constructs blocking full migration

- `inspect.isawaitable()` in `_invoke_execute`
- `hasattr` duck-typing in `TextRewriterAgent` and `MCPAdapter`
- `asyncio.get_running_loop()` guard in `run_sync`
- `BaseModel.model_dump()` for serialization
- Content models inherit from `AgentInput`/`AgentOutput` (Pydantic)

---

## 3. Ownership Map

```
AgentRegistry (lifecycle owner)
  ├── owns: dict[str, BaseAgent]
  ├── injects: VectorDBAdapter, LogStorage
  └── spawns: agent.run(input_data)
  
AgentMediator (communication hub)
  ├── owns: dict[str, BaseAgent]
  ├── send(sender, recipient, input) -> AgentOutput
  └── broadcast(sender, input) -> dict[str, AgentOutput]

BaseAgent (trait/abstract)
  ├── run(input) -> output
  │   ├── _validate_input()  <- type-coercion bridge
  │   ├── execute()           <- abstract, subclass implements
  │   └── _log_execution()    <- storage persistence
  └── subclasses:
      ├── StateMachineAgent
      │   ├── owns: StateMachineDocument
      │   ├── owns: BatchSkillExecutor + StepWiseSkillExecutor
      │   └── owns: SkillLoader + LLMClient (refs)
      ├── SkillAgent
      │   └── owns: SkillExecutor (batch or stepwise)
      └── TextRewriterAgent
          └── owns: llm (duck-typed)

AgentFactory (creational)
  └── class-level _registry: dict[str, type[BaseAgent]]  <-- MUTABLE GLOBAL
```

### Mutability Risks

- `AgentFactory._registry` is mutated by `register()` — thread-unsafe, test-interference.
- `AgentRegistry.agents` is mutated externally after `register()` (no encapsulation).
- `BaseAgent.metadata` (`dict[str, Any]`) is shared by reference — unintended mutation possible.

---

## 4. PyO3 Binding Structure

```
┌─────────────────────────────────────────────────────────┐
│                     Python Layer                         │
│                                                         │
│  models.py (AgentInput, AgentOutput)                     │
│  content/models/*.py (110 agent I/O models)              │
│  factories.py (AgentFactory scaffolding)                 │
│  agent_registry.py (Python-side lifecycle)               │
└──────────────────────┬──────────────────────────────────┘
                       │ PyO3 bridge
                       ▼
┌─────────────────────────────────────────────────────────┐
│                     Rust Core                            │
│                                                         │
│  AgentRegistry   (state machine lifecycle)               │
│  AgentMediator   (routing)                               │
│  BaseAgent       (trait)                                 │
│  StateMachineAgent (state execution engine)              │
│  SkillAgent      (skill dispatch)                        │
│  SafeEval        (expression evaluator)                  │
└─────────────────────────────────────────────────────────┘
```

**Boundary strategy**: Rust owns all execution logic. Python owns all Pydantic model definitions and content agent I/O schemas. PyO3 structs mirror `AgentInput`/`AgentOutput` via `#[pyclass]` with `serde` serialization.

---

## 5. Libraries Analysis

| Import | Source | Migration Impact |
|--------|--------|-----------------|
| `pydantic.BaseModel` | External | Replace with `serde` + `#[pyclass]` for boundary types |
| `engines.storage.vector.base.VectorDBAdapter` | Internal | Must be PyO3-exported from storage crate |
| `engines.storage.event_log.base.LogStorage` | Internal | Must be PyO3-exported from storage crate |
| `engines.document.models.osdm_models.StateMachineDocument` | Internal | OSDM crate must export via PyO3 |
| `engines.communication.buses.base_message_bus.MessageBus` | Internal | Must be PyO3-exported from communication crate |
| `engines.interaction.*` | Internal | Python-only (too coupled) |
| `engines.agent.skill.*` | Internal subpackage | Being migrated alongside |

---

## 6. Performance Hot Paths

| Hot Path | Location | Current Cost | Rust Opportunity |
|----------|----------|-------------|------------------|
| **State machine execution loop** | `state_machine_agent.py:127-172` | Python `while` loop with attribute-access-heavy `getattr()` calls per iteration | Zero-cost state machine in Rust with enum dispatch |
| **Transition guard evaluation** | `state_machine_agent.py:242-261` | AST walk via `safe_expr_eval` on every transition | Native expression evaluator in Rust |
| **Skill dispatch** | `state_machine_agent.py:183-228` | JSON parse + `getattr` chain per state visit | Rust struct deserialization |
| **Agent execution logging** | `base_agent.py:98-118` | Pydantic model_dump + async storage call | Could be fire-and-forget in Rust |
| **Content model validation** | All content model files | Pydantic validation on every agent I/O | Keep in Python — not hot |
| **TextRewriterAgent** | `text_rewriter.py:47-64` | `hasattr` chain per LLM call | Python-only (LLM abstraction) |

### Measured Bottlenecks (Estimated)

1. `safe_expr_eval` in guard evaluation — invoked potentially hundreds of times per state machine run
2. `getattr(state, ...)` churn — Python attribute lookup on dynamic objects
3. `isinstance` dispatch in `_validate_input`/`_validate_output` — repeated per agent invocation

---

## 7. Error Handling

| Pattern | Prevalence | Rust Translation |
|---------|-----------|-----------------|
| `raise ValueError(...)` | ~10 sites | `Result::Err(...)` with `thiserror` |
| `raise ImportError(...)` | `state_machine_agent.py:49` | Compile-time — not needed |
| `raise RuntimeError(...)` | 3 sites (run_sync guard, MCP, executor) | `Result::Err` |
| `raise KeyError(...)` | `agent_registry.py:38` | `Option` → `unwrap_or_else` |
| Exception swallowing | `state_machine_agent.py:259` — `except Exception: return False` in guard eval | `Result::unwrap_or(false)` |
| Exception swallowing | `state_machine_agent.py:222` — bare `except _` in skill parsing | `Option::and_then` |
| try/except with fallback | `executor.py:153-175`, `executor.py:248-268` — structured output → text → JSON parse | `Result::or_else` chain |

### Issues

- **Silent failure**: `_execute_state_skill` at line 222 catches all exceptions and returns `None` — state machine silently continues. Rust's `Result` typing would force explicit handling.
- **Guard evaluation** at line 259: `except Exception: return False` — a malformed guard silently falls through. Rust would require explicit error variant.
- **Late import** at `state_machine_agent.py:45`: `from engines.document.models.osdm_models import StateMachineDocument` — deferred to avoid circular imports. Rust's module system eliminates this pattern.

---

## Migration Strategy

### Phase 1: Rust State Machine Engine
Migrate `StateMachineAgent` + `SafeEval` → Rust crate `agent-state-machine`. Export via PyO3 with `AgentInput`/`AgentOutput` structs.

### Phase 2: Rust Agent Core
Migrate `BaseAgent` trait + `AgentMediator` + `AgentRegistry` → Rust crate `agent-core`. Python keeps all content model I/O types.

### Phase 3: Hybrid
Python content models import Rust agent types via PyO3. `AgentFactory._registry` becomes a Rust struct. `InteractionAgent` stays in Python forever.
