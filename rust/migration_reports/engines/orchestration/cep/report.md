# CEP Engine — Rust Migration Analysis

**Source:** `multi_agent_infra/engines/orchestration/cep/`
**Files:** 8 Python files (1102+ lines total)

---

## 1. Pre-refactor Analysis

### `Any` / `dict[str, Any]` Usage (Critical — Highest of All Engines)

| Location | Usage | Count |
|----------|-------|-------|
| `aggregator.py` | `data: list[Any]`, `context: dict[str, Any]`, return `Any` | ~35 sites |
| `pattern_matcher.py` | `buffer: list[dict[str, Any]]`, `context: dict[str, Any]` | ~25 sites |
| `rule_evaluator.py` | `field_value: Any`, `comp_value: Any`, `context: dict[str, Any]` | ~30 sites |
| `window_manager.py` | `event: dict[str, Any]`, `config: dict[str, Any]` | ~15 sites |
| `stream_processor.py` | `event: dict[str, Any]`, all event types as `Any` | ~15 sites |
| `event_store.py` | `payload: dict[str, Any]` | ~10 sites |
| `engine.py` | `definition.definition_xml` cast to `dict[str, Any]` | ~10 sites |

Every event that flows through the CEP pipeline is `dict[str, Any]`. Event types, fields, values — all untyped at the Python boundary.

### `isinstance` Chains (Medium)

- `aggregator.py:_extract_data` (lines 129–139): `isinstance(v, (int, float))`, `isinstance(value, (list, tuple))`, `isinstance(value, (int, float))` — 3-way check on every aggregate call.
- `aggregator.py:_agg_*` functions: all filter `isinstance(v, (int, float))` on data elements.
- `engine.py:execute_instance` (line 56): `isinstance(definition.definition_xml, dict)`.
- `stream_processor.py:process_batch` (lines 96–99): `RuntimeError` catch for event loop check.

### Dynamic Dispatch (High)

- **`_AGGREGATION_HANDLERS`** (aggregator.py:86–97): String-keyed dict mapping function names to `Callable[[list[Any]], Any]`. Classic dynamic dispatch.
- **`_OPERATOR_HANDLERS`** (rule_evaluator.py:77–89): String-keyed dict mapping operator names to condition evaluators. 11 operators.
- **`PatternMatcher.evaluate`** (pattern_matcher.py:86–99): `if/elif` dispatch on string operator (FOLLOWED_BY, OR, AND, REPEATED, ABSENCE, EXISTENCE).
- **`WindowType` / `WindowManager.push`** (window_manager.py:60–81): Takes `window_type: str` but never dispatches on it — all windows treated as unbounded append buffers.

### Global / Mutable State (Critical)

| Component | State | Scope |
|-----------|-------|-------|
| `PatternMatcher` | `_event_buffer: dict[str, list[dict[str, Any]]]` | Append-only per instance_id |
| `WindowManager` | `_windows: dict[str, WindowState]` | Events appended, mutated in-place |
| `Aggregator` | `_definitions: dict[str, AggregationDefinition]` | Read-only after registration, but mutable dict |
| `RuleEvaluator` | `_rules: dict[str, CEPRule]` | Read-only after registration |
| `CEPEventStore` | `_events: list[StoredEvent]` | Append-only list, mutable in-place |
| `StreamProcessor` | Owns 5 sub-components (event_store, pattern_matcher, rule_evaluator, window_manager, aggregator) | All mutable |

**Mutability problem:** `WindowManager.push()` mutates `WindowState` in place (line 74: `state.events.append(event)`). No immutability or snapshot semantics. PatternMatcher buffers are append-only lists — no compaction or eviction strategy.

### Event Buffer Bloat Risk

`PatternMatcher._event_buffer` (pattern_matcher.py:66) stores all events per instance indefinitely. `clear_buffer()` exists but is never called during normal execution. `WindowManager._windows` similarly never evicts based on time — events accumulate unbounded.

---

## 2. Migration Notes

**Score: 4/5** — Good Rust fit, but needs architectural refinement.

### Event Stream Processing

The CEP pipeline is: `Event → StreamProcessor → WindowManager → Aggregator → RuleEvaluator → PatternMatcher`

This maps to Rust's iterator pipeline model:

```rust
stream_processor
    .process(event)
    .window(window_config)
    .aggregate(agg_def)
    .evaluate_rules(rules)
    .match_patterns(patterns)
```

### Window Aggregation Mapping

| Python WindowType | Rust Equivalent |
|-------------------|-----------------|
| `TUMBLING` | Fixed-size `VecDeque<T>` with periodic drain |
| `SLIDING` | `VecDeque<T>` with slide interval emission |
| `SESSION` | `BinaryHeap<T>` keyed by gap threshold |
| `TIME` | Time-bounded `VecDeque<T>` with watermark eviction |
| `COUNT` | Bounded `VecDeque<T>` with max count |

**Current windows are unbounded** — no `WindowType` dispatch in `push()`. Rust can enforce eviction semantics at the type level.

### Rule Evaluator

Currently a Python expression evaluator calling `PythonEvaluator.evaluate()` for rule actions (rule_evaluator.py:157–158). The condition operators (`eq`, `gt`, `lt`, etc.) are pure functions that map trivially to Rust closures or an operator enum.

### Watermark Policy

`WatermarkPolicy` enum (stream_processor.py:25–28) is declared but never used for watermark logic — it's stored but no watermark advancement, late event handling, or out-of-order processing exists. This is a placeholder for future implementation. Rust makes it easier to add because the watermark state machine is explicit.

### `process_batch` Anti-pattern

`stream_processor.py:process_batch` (lines 87–114) attempts to run async `process()` synchronously via `asyncio.get_event_loop().run_until_complete()`. This will fail if no event loop is running. Rust's `async` handling is explicit — no hidden event loop assumptions.

---

## 3. Ownership Map

```
CEPEngine
 ├── StreamProcessor
 │    ├── event_store: CEPEventStore
 │    │    └── _events: Vec<StoredEvent>
 │    ├── pattern_matcher: PatternMatcher
 │    │    ├── _event_buffer: HashMap<String, Vec<Event>>
 │    │    └── _patterns: HashMap<String, PatternDefinition>
 │    ├── rule_evaluator: RuleEvaluator
 │    │    └── _rules: HashMap<String, CEPRule>
 │    ├── window_manager: WindowManager
 │    │    ├── _windows: HashMap<String, WindowState>
 │    │    │    └── events: Vec<Event>
 │    │    └── _definitions: HashMap<String, WindowDefinition>
 │    └── aggregator: Aggregator
 │         └── _definitions: HashMap<String, AggregationDefinition>
 └── ContextManager (shared from orchestration)
```

**Rust ownership pattern:**
- `CEPEngine` owns `StreamProcessor`, which owns all 5 sub-components
- Each sub-component owns its state `HashMap<String, T>` — clear ownership
- `WindowState.events` is `Vec<Event>` — Rust enforces ownership per element; no shared references
- `PatternMatcher._event_buffer` is `HashMap<String, Vec<Event>>` — owned per instance_id

**Key ownership insight:** All data flows are linear — an event enters `StreamProcessor`, gets stored, windowed, aggregated, and evaluated. No event reference escapes the pipeline, making ownership straightforward.

---

## 4. PyO3 Binding Structure

### Recommended Architecture

```
┌─────────────────────────────────────────────────┐
│                   Python                         │
│  CEPEngine.execute_instance(instance, defn)      │
│  StreamProcessor.process(event, instance)        │
│  RuleEvaluator.evaluate(rule_data, context)      │
│                                                   │
│  ┌───────────────────────────────────────────┐   │
│  │            PyO3 Bridge                     │   │
│  │  PyClass CEPEngine → Rust CEPEngine        │   │
│  │  PyClass StreamProcessor → ...             │   │
│  │  PyClass RuleEvaluator → ...               │   │
│  └───────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────┐
│                   Rust                           │
│  CEPEngine::execute_instance()                   │
│                                                   │
│  Window pipeline:                                 │
│    stream.process(event)                          │
│      → store(event)                              │
│      → window.push(event)   [VecDeque evict]     │
│      → aggregate(events)    [iterator fold]      │
│      → rules.evaluate(ctx)  [pattern match]      │
│      → patterns.match(buf)  [state machine]       │
│                                                   │
│  No GIL during window processing                  │
│  GIL re-acquired only for Python handler calls    │
└─────────────────────────────────────────────────┘
```

### PyO3 Callback Strategy

The `RuleEvaluator._evaluate_conditions` currently uses `PythonEvaluator` for dynamic expressions. In Rust, two strategies:

1. **Rust-native evaluator** (preferred): Replace `PythonEvaluator` with a Rust expression evaluator. Operators (`eq`, `gt`, `contains`) become Rust `match` arms. No GIL overhead.
2. **PyO3 fallback** (for complex actions): If rule actions need Python, pass a `py: Python<'_>` token and call back into Python only for the action execution. All condition logic stays in Rust.

---

## 5. Libraries Analysis

### External (stdlib only)

| Import | Files |
|--------|-------|
| `statistics` | `aggregator.py:8` — `mean()`, `median()`, `stdev()` |
| `logging` | `stream_processor.py`, `engine.py`, `rule_evaluator.py` |
| `dataclasses` | All files |
| `enum` | `aggregator.py`, `pattern_matcher.py`, `stream_processor.py`, `window_manager.py` |
| `typing` / `collections.abc` | All files |
| `datetime` | `event_store.py`, `rule_evaluator.py` |

### Internal Dependencies

| Import Path | Used By |
|-------------|---------|
| `..core.instance` (`ProcessInstance`) | `stream_processor.py`, `engine.py`, `window_manager.py`, `rule_evaluator.py` |
| `..core.engine` (`OrchestrationEngine`) | `engine.py` |
| `..core.event_bus` (`Event`, `EventType`) | `engine.py` |
| `..core.context` (`ContextManager`, `ContextScope`) | `engine.py` |
| `..runtime.state_manager` (`StateManager`) | `engine.py` |
| `..expression.evaluator` (`EvaluationContext`) | `rule_evaluator.py` |
| `..expression.python_evaluator` (`PythonEvaluator`) | `rule_evaluator.py` |

### `statistics` Library (stdlib)

The `statistics` module is used for `mean()`, `median()`, and `stdev()`. Rust equivalents:
- `mean()` → `sum / len` (with float handling)
- `median()` → sort + midpoint
- `stdev()` → variance computation

All are trivially implementable in 5–10 lines of Rust — no external crate needed for basic stats. For percentile, implement custom quantile function.

---

## 6. Performance Hot Paths

### Hot Path 1: Window Aggregation (Per-Event)

**Location:** `aggregator.py:aggregate()` (lines 104–118)

**Triggered:** Every time an aggregation is requested (engine.py:108, per aggregation config per instance).

**Current cost:** `_extract_data` scans context dict + type checks each value + `_compute` calls through handler dict.

**Rust optimization:** Pre-extract fields via struct access (no dict scan). Aggregation becomes `Iterator::fold()`:

```rust
fn aggregate<'a>(
    events: impl Iterator<Item = &'a Event>,
    field: &str,
    func: AggFn,
) -> f64 {
    match func {
        AggFn::Sum => events.map(|e| e.field_as_f64(field)).sum(),
        AggFn::Avg => { let v: Vec<_> = events.collect(); v.iter().sum::<f64>() / v.len() as f64 }
        AggFn::Count => events.count() as f64,
        // ...
    }
}
```

### Hot Path 2: Rule Evaluation (N Conditions Per Event)

**Location:** `rule_evaluator.py:_evaluate_conditions()` (lines 205–216)

**Triggered:** Per rule per event batch.

**Current cost:** Dict lookup per condition target + optional PythonEvaluator call + operator handler dispatch.

**Rust optimization:** Pre-parsed conditions stored as `Vec<Condition>`. Field extraction via typed access. Operator is a `match` on enum — no hash lookup.

### Hot Path 3: Pattern Matching (Buffer Scan)

**Location:** `pattern_matcher.py:_match_followed_by()` (lines 112–137)

**Triggered:** Per pattern evaluation (engine.py:85 — all patterns, all events).

**Current cost:** O(N × M) where N = events in buffer, M = required events in pattern. Scans buffer from `last_idx+1` each time — worst-case O(N×M).

**Rust optimization:** Indexed event buffer (`HashMap<event_type, Vec<&Event>>`). `FOLLOWED_BY` becomes a sequential scan over pre-indexed types.

### Hot Path 4: Event Store Linear Scan

**Location:** `event_store.py:query()` (lines 45–66)

**Triggered:** Any query by instance_id, event_type, or time range.

**Current cost:** O(N) linear scan of all events — no indexes.

**Rust optimization:** Indexed storage:
- `HashMap<instance_id, Vec<StoredEvent>>` for instance lookups
- `HashMap<event_type, Vec<usize>>` for type queries
- Events stored in `Vec<StoredEvent>` with indices

### Hot Path 5: Unbounded Buffer Growth

**Location:** `pattern_matcher.py:feed_event()` (lines 72–75) and `window_manager.py:push()` (line 74)

**Problem:** No eviction. Memory grows linearly with event volume. No watermark-based compaction.

**Rust solution:** `VecDeque` with capacity bounds + watermark-eviction logic. `WindowManager` enforces eviction based on window type (time/count) at the type level.

---

## 7. Error Handling

### Current Python Pattern

| Error Type | Location | Mechanism |
|------------|----------|-----------|
| `CEPExecutionError` | `engine.py:29` | `@dataclass(frozen=True)` inheriting `RuntimeError` |
| Execution failure | `engine.py:113–122` | `try/except Exception` → FAILED state, re-raises |
| Store error | `stream_processor.py:66–71` | Returns `StreamProcessingResult` with `errors` list |
| Rule action fail | `rule_evaluator.py:161–163` | Logs warning, continues with `action_error` in result |

### Error Handling Pattern: Result Object vs Exception

`StreamProcessingResult` (stream_processor.py:31–40) has an `errors: list[str]` field — errors are accumulated into the result rather than raised. This is a **success-with-warnings** pattern:

```python
result = StreamProcessingResult(
    event_id=event_id,
    event_type=event_type,
    processed=True,  # still "processed" even if errors?
    errors=[f"Store error: {e}"],
)
```

**Rust mapping:** Use `Result<StreamProcessingResult, ProcessingError>`. A store failure is `Err`, not a success with error strings. Separate "recoverable warning" from "processing failure."

### Edge Cases Currently Unhandled

| Edge Case | Current Behavior | Rust Should |
|-----------|------------------|-------------|
| Late events (past watermark) | No watermark tracking — accepted silently | Reject or route to late-event handler |
| Out-of-order events | No reordering — processed in arrival order | Buffer + sort by event timestamp |
| Empty window aggregation | Returns `None` for avg/stdev (division by zero implicitly avoided) | Return `Option<f64>` — type-safe |
| Window overflow | `max_count` eviction implemented (window_manager.py:78–79) | Retain this pattern with `VecDeque.truncate()` |
| Pattern buffer overflow | No limit — unbounded growth | Enforce capacity via bounded buffer |

### Expression Evaluation Errors

`rule_evaluator.py:_evaluate_single_condition` (lines 218–233):
- If `target_field` is set, `context.get()` returns `None` silently for missing keys
- If `expression` is set, `PythonEvaluator` exceptions are caught and return `False`
- No distinction between "condition evaluated to false" and "evaluation failed"

**Rust improvement:** `fn evaluate_condition(&self, ctx: &Context) -> Result<bool, EvalError>`. The caller chooses whether to treat `Err` as false or propagate.

---

## Summary

| Dimension | Score | Notes |
|-----------|-------|-------|
| Event stream fit | 4/5 | Iterator pipeline model maps naturally |
| Type safety gain | Critical | Eliminates all `dict[str, Any]` — the biggest win |
| Performance gain | High | VecDeque eviction, indexed storage, iterator chains |
| Migration complexity | Medium | Aggregation functions are trivial; expression eval needs bridging |
| Thread safety gain | High | Rust ownership prevents shared buffer mutation |
| Architectural gain | High | Forces watermark, eviction, and out-of-order handling to be explicit |

### Key Differences from CMMN Migration

| Aspect | CMMN | CEP |
|--------|------|-----|
| Core abstraction | State machine (explicit states + transitions) | Stream pipeline (event → window → aggregate → rule) |
| Rust primitive | `enum` + `transition()` method | `Iterator` + `VecDeque` + channels |
| Data volume | Low (one case at a time) | High (unbounded event stream) |
| Memory pressure | Low | High — eviction strategy critical |
| Expression eval | Sentry IfPart conditions | Rule conditions + actions |
| PyO3 complexity | Thin wrapper | May need Python callback for actions |
