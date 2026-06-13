# Migration Report: `engines/memory/`

**Scored**: 4/5 — strong Rust migration candidate. Clean interfaces, minimal external dependencies, well-defined Strategy pattern with Proxy decorators. The in-memory backend with Jaccard similarity search is a straightforward Rust implementation.

---

## 1. Pre-refactor Analysis

### `Any` / `dict[str, Any]` Usage (Minimal)

| File | Issue |
|------|-------|
| `models.py` | `MemoryItem.metadata: dict[str, Any]` — by-design generic metadata bag |
| `models.py` | `MemoryQuery.filter_metadata: dict[str, Any] \| None` — same, by design |
| `base.py` | `remember(key, content, metadata: dict[str, Any] \| None)` — acceptable |
| `base.py` | `stats() -> dict[str, Any]` — acceptable for generic stats |
| `mediator.py` | `_listeners: list[Any]` — listener list, type-erased |
| `proxies.py` | `LazyMemoryBackend.__init__(..., factory: Any, **factory_kwargs: Any)` — factory is generic callable |

This codebase is the **cleanest** of the three. `Any` usage is confined to intentional generic extension points.

### `isinstance` Chains

None. The code uses type hints and pattern matching through the backend interface dispatch.

### Global State

None. All state is instance-level. `MemoryMediator` maintains `_listeners` per instance, `InMemoryBackend._items` per instance, `CachingMemoryBackend._cache` per instance.

---

## 2. Migration Notes (Score 4/5)

| Component | Rust Candidate | Reasoning |
|---|---|---|
| **MemoryBackend** (ABC/Strategy) | **High** | Clean trait — `store`, `retrieve`, `search`, `forget`, `clear`, `count`. Maps directly to Rust trait + `dyn`. |
| **InMemoryBackend** | **High** | `HashMap<String, MemoryItem>` + Jaccard similarity search. Pure data structures, no I/O. |
| **NullMemoryBackend** | **High** | Trivial no-op implementations. |
| **CachingMemoryBackend** | **High** | LRU cache via `OrderedDict`. Use `lru::LruCache` crate or `HashMap` + `LinkedHashSet`. |
| **LazyMemoryBackend** | **High** | `OnceLock<Box<dyn MemoryBackend>>` — deferred initialization. |
| **MemoryMediator** | Medium | Mediator pattern with primary/secondary backends + listener notification. Translated cleanly, but async event broadcasting is Python-framework-specific. |
| **BaseMemory** | Medium | High-level abstraction. Mostly delegates to backend. |
| **Models** (MemoryItem, etc.) | **High** | Dataclasses with slots → Rust structs with `serde`. Minimal fields. |

### Python-specific constructs

- `dataclass(slots=True)` — Rust structs are slot-native
- `time.time()` in default `field` — `Instant::now()` in Rust
- `time.monotonic()` for search timing — `Instant::now().elapsed()`
- `OrderedDict` for LRU — `lru::LruCache` or `hashlink::LinkedHashMap`

---

## 3. Ownership Map

```
MemoryMediator (coordination hub)
  ├── owns: _primary: MemoryBackend
  ├── owns: _secondary: MemoryBackend
  └── owns: _listeners: Vec<Box<dyn MemoryEventListener>>

CachingMemoryBackend (decorator)
  ├── owns: _backend: Box<dyn MemoryBackend>
  └── owns: _cache: LruCache<String, MemoryItem>

LazyMemoryBackend (deferred init)
  ├── owns: _factory: Box<dyn Fn() -> Box<dyn MemoryBackend>>
  └── owns: _backend: OnceLock<Box<dyn MemoryBackend>>

InMemoryBackend (leaf)
  ├── owns: _items: HashMap<String, MemoryItem>
  └── owns: _next_id: u64
```

### Ownership Clarity

Clean single-ownership tree. No shared mutable references. `CachingMemoryBackend` wraps a `MemoryBackend` box. `MemoryMediator` composes two backends. `LazyMemoryBackend` uses a factory closure. All relationships are straightforward to express in Rust's ownership model.

---

## 4. PyO3 Binding Structure

```
┌─────────────────────────────────────────────────────────┐
│                    Python Layer                           │
│                                                          │
│  MemoryMediator (event listener glue)                     │
│  Python-side integration entry points                     │
│  Any future non-Rust backends (Redis, Postgres)           │
└───────────────────────┬──────────────────────────────────┘
                        │ PyO3 bridge
                        ▼
┌─────────────────────────────────────────────────────────┐
│                    Rust Core                              │
│                                                          │
│  MemoryBackend trait     (Strategy interface)             │
│  InMemoryBackend         (HashMap + Jaccard search)       │
│  CachingMemoryBackend    (LRU decorator)                  │
│  LazyMemoryBackend       (OnceCell deferred init)         │
│  NullMemoryBackend       (no-op)                          │
│  MemoryItem / MemoryQuery / MemoryResult (serde structs)  │
└─────────────────────────────────────────────────────────┘
```

**Recommended binding**: Export all four backend implementations + three model types as `#[pyclass]`. The `MemoryBackend` trait becomes a `#[pyclass(subclass)]` or a `PyBackend` wrapper that delegates to Python callers.

---

## 5. Libraries Analysis

| Import | Source | Migration Impact |
|--------|--------|-----------------|
| `dataclasses` | Stdlib | Use Rust structs |
| `time` | Stdlib | `std::time::Instant` |
| `collections.OrderedDict` | Stdlib | `lru::LruCache` or `hashlink::LinkedHashMap` |
| `abc.ABC` | Stdlib | `trait` keyword |
| `typing` | Stdlib | Rust generics + `dyn` |
| `engines.memory.models.*` | Internal | Move to Rust crate |

**No external dependencies.** This is the key advantage — the memory engine depends only on Python stdlib and its own models. Zero migration friction from a dependency standpoint.

---

## 6. Performance Hot Paths

| Hot Path | Location | Current Cost | Rust Opportunity |
|----------|----------|-------------|------------------|
| **InMemoryBackend.search** | `backends.py:63-73` | O(n) scan of all items, Jaccard similarity per item, sort by score. All Python loops. | Rust would be **significantly faster** — tight loop with SIMD-able string ops. |
| **Jaccard `_score`** | `backends.py:84-97` | Set intersection/union via Python `set` objects + metadata matching. | Rust: `HashSet` ops or sorted vectors + `itertools`. |
| **CachingMemoryBackend cache eviction** | `proxies.py:92-94` | `OrderedDict.popitem(last=False)` per eviction. | `lru::LruCache` is O(1). |
| **CachingMemoryBackend retrieve** | `proxies.py:68-76` | Dict lookup + `move_to_end`. | `lru::LruCache::get` is O(1). |
| **MemoryMediator write fan-out** | `mediator.py:29-45` | Sequential `await` to primary + secondary + listener notify. | Tokio `join!` for concurrent fan-out. |

### Estimated Performance Gain

- **Search**: 10-50x for in-memory search with large datasets (eliminating Python set object overhead)
- **Cache**: 5-10x for LRU operations (no Python dict overhead)
- **Write fan-out**: ~1.5x from concurrent execution via `tokio::join!`

---

## 7. Error Handling

| Pattern | Prevalence | Rust Translation |
|---------|-----------|-----------------|
| `return None` for not-found | `retrieve`, `forget` | `Option<T>` — perfect match |
| `return 0` for empty count | `backends.py:81-82` | `usize` zero |
| `return MemoryResult(items=[])` | `NullMemoryBackend.search` | `MemoryResult { items: vec![], .. }` |
| `_notify` silent catch | `mediator.py:78-83` — `except Exception: pass` | `Result::ok()` or explicit error channel |
| No `raise` in hot paths | — | All operations are infallible |

### Key Observations

- **No error handling needed for core paths**. Store, retrieve, forget, clear, count are all infallible operations on the in-memory backend.
- `_notify` silently swallows listener errors — acceptable for a notification system. Rust would make this explicit via `tokio::spawn` + `forget` pattern.
- The clean error contract makes this an ideal first Rust migration target.

---

## Migration Strategy

### Phase 1 (Single PR): Full Rust Migration

This engine is small enough (~360 lines total across 6 files) to migrate entirely in one pass.

1. Create `memory-core` Rust crate with:
   - `MemoryBackend` trait (store, retrieve, search, forget, clear, count)
   - `InMemoryBackend` — `HashMap<String, MemoryItem>` + Jaccard search
   - `NullMemoryBackend` — trait methods returning empty/success defaults
   - `CachingMemoryBackend` — generic LRU over any `MemoryBackend`
   - `LazyMemoryBackend` — `OnceLock` deferred init from factory
   - `MemoryMediator` — primary/secondary delegation + listener channel
   - `MemoryItem`, `MemoryQuery`, `MemoryResult` — serde structs

2. Export via PyO3 with `#[pyclass]` wrappers:
   - `PyMemoryMediator` — main entry point
   - `PyInMemoryBackend`, `PyNullMemoryBackend`, etc.
   - Model types as `#[pyclass(getter, setter)]`

3. Python code becomes pure Pydantic-free import wrappers:
   ```python
   # engines/memory/__init__.py
   from ._rust import MemoryMediator, InMemoryBackend, MemoryItem
   ```

### Risk Assessment

| Risk | Mitigation |
|------|-----------|
| Jaccard behavior differences | Write property tests comparing Python vs Rust output on random data |
| `time.time()` vs `Instant::now()` epoch mismatch | Document that `MemoryItem.timestamp` changes from Unix epoch to `Duration::from(Instant)`. Use `SystemTime::now()` if epoch needed. |
| Listener API | Keep `MemoryMediator._notify` in Python via PyO3 callback. Or replace with Rust `tokio::sync::broadcast`. |
