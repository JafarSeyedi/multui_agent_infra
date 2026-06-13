# Multi-Agent Orchestration — Rust Migration Report

## Files Analyzed
- `__init__.py` (34 lines) — re-exports
- `engine.py` (128 lines) — `MultiAgentEngine`
- `mediator.py` (232 lines) — `AgentMediator` (ABC), `MultiAgentMediator`
- `agent_executor.py` (116 lines) — `AgentExecutor`
- `coordination_handler.py` (83 lines) — `CoordinationHandler`
- `interaction_handler.py` (68 lines) — `InteractionHandler`
- `message_router.py` (116 lines) — `MessageRouter`
- `negotiation_handler.py` (98 lines) — `NegotiationHandler`
- `protocol_handler.py` (73 lines) — `ProtocolHandler`

## 1. Pre-refactor Patterns

| Pattern | Files | Details |
|---------|-------|---------|
| `Any` | mediator.py:13, agent_executor.py:10, engine.py:11, etc. | Widespread — `Metadata`, `MessagePayload`, result values |
| `dict[str, Any]` | mediator.py:15, engine.py:29-34, agent_executor.py:57-71, etc. | `Metadata`, `RawData`, configuration |
| `isinstance` | mediator.py:45 | `isinstance(definition.definition_xml, dict)` |
| Global state | None | No mutable module-level state |
| Mutable defaults | engine.py:30-34 | `field(default_factory=list/dict)` — safe |

## 2. Migration Notes & Rust Score

| File | Lines | Complexity | Rust Score | Notes |
|------|-------|-----------|------------|-------|
| engine.py | 128 | Medium | 4/5 | Coordinates mediator + state_manager. Async. |
| mediator.py | 232 | High | 3/5 | **Largest file.** Abstract base + concrete impl. Manages 5 sub-handlers. Complex workflow orchestration. |
| agent_executor.py | 116 | Low | 4/5 | Retry logic, event publishing. |
| coordination_handler.py | 83 | Low | 5/5 | Pattern dispatch, simple stubs. |
| interaction_handler.py | 68 | Low | 5/5 | Stateful conversation handler. |
| message_router.py | 116 | Low | 4/5 | Message log, broadcast, `asyncio.ensure_future` → `tokio::spawn`. |
| negotiation_handler.py | 98 | Low | 5/5 | State machine over negotiation phases. |
| protocol_handler.py | 73 | Low | 5/5 | Protocol state machine. |

**Overall**: 4.4/5. The handler pattern is cleanly separated. The mediator is the central complexity — it wires all handlers together and manages workflow execution.

## 3. Ownership Map

```
MultiAgentEngine
 ├── MultiAgentMediator
 │    ├── CoordinatorHandler
 │    ├── InteractionHandler
 │    ├── ProtocolHandler
 │    ├── NegotiationHandler
 │    ├── AgentExecutor
 │    └── MessageRouter
 ├── ContextManager
 ├── StateManager
 └── conversation_state: HashMap<String, MessagePayload>

Handlers → state pattern:
 AgentExecutor: behaviors registry + retry
 CoordinationHandler: pattern dispatch (orchestration/choreography/consensus)
 InteractionHandler: turn-based messaging
 MessageRouter: addressable delivery + broadcast
 NegotiationHandler: phase machine + offer management
 ProtocolHandler: FIPA protocol state machine
```

## 4. PyO3 Binding Structure

```rust
#[pyclass]
struct MultiAgentEngine { ... }

#[pyclass]
struct MultiAgentMediator { ... }

#[pyclass]
struct AgentExecutor { ... }

#[pyclass]
struct MessageRouter { ... }

// Simple handlers as #[pyclass] or exposed as engine methods
```

## 5. Libraries Analysis

| Current Python | Rust Equivalent | Notes |
|---------------|----------------|-------|
| `asyncio` | `tokio` | Async workflow execution |
| `dataclasses` | `#[derive(Clone)]` | Direct |
| `enum` | Native enums | Direct |
| `abc.ABC` | Trait + `dyn` | Abstract base mediator pattern |

**No external crates needed for core logic.** Would depend on `tokio` for async.

## 6. Performance Hot Paths

- `MultiAgentMediator.execute_workflow()` — sequential execution: coordinate → interactions → protocols → negotiation → agents. Each step involves state tracking + variable setting. Could be parallelized in Rust via `tokio::join!`.
- `MessageRouter.route()` — O(1) log + event publish.
- `AgentExecutor.execute_with_retry()` — up to `retry_count + 1` calls. Simple loop.
- All handlers use `instance.set_variable()` which is a dict write.

## 7. Error Handling

| Python | Rust Strategy |
|--------|---------------|
| `MultiAgentExecutionError` | `thiserror` enum, part of `MediationResult` |
| `MediationResult` (success + errors) | `Result<MediationOk, MediationError>` |
| `except Exception as exc: errors.append(str(exc))` | Propagate typed errors |
| `getattr(plan, ...)` default fallback | `plan.coordination_pattern.unwrap_or("orchestration")` |
