# Utility Modules — Rust Migration Report

## Files Analyzed
- `__init__.py` (31 lines) — re-exports
- `graph_utils.py` (90 lines) — DAG operations (topological sort, cycle detection, shortest path)
- `id_generator.py` (47 lines) — thread-safe ID generation
- `json_parser.py` (28 lines) — JSON load/dump wrappers
- `time_utils.py` (53 lines) — duration parsing, epoch conversion
- `type_converter.py` (65 lines) — type coercion (bool, int, float, string)
- `xml_parser.py` (31 lines) — XML parse → dict

## 1. Pre-refactor Patterns

| Pattern | Files | Details |
|---------|-------|---------|
| `Any` | graph_utils.py:6, id_generator.py:8, json_parser.py:7,23, type_converter.py:6,15,44,60, xml_parser.py:6 | Widespread — generic payloads, return types |
| `dict[str, Any]` | graph_utils.py:17, type_converter.py:60 | Node payload, `coerce_type` accepts `Any` |
| `isinstance` | type_converter.py:16,18,20,26,29,37 | Type dispatch in conversion functions |
| Global state | id_generator.py:21-22 | `ClassVar` counter + threading lock |
| Mutable defaults | None | No mutable default arguments |

## 2. Migration Notes & Rust Score

| File | Lines | Complexity | Rust Score | Notes |
|------|-------|-----------|------------|-------|
| graph_utils.py | 90 | Low | 5/5 | Pure algorithms, no I/O. Direct translation. |
| id_generator.py | 47 | Low | 5/5 | `AtomicU64` instead of `Lock`, `uuid` crate. |
| json_parser.py | 28 | Low | 5/5 | Thin `serde_json` wrapper. |
| time_utils.py | 53 | Low | 5/5 | Regex for duration → `chrono::Duration`. |
| type_converter.py | 65 | Low | 5/5 | Pure type dispatch. `TryFrom` traits. |
| xml_parser.py | 31 | Low | 5/5 | `quick-xml` or `serde-xml-rs`. |

**Overall**: 5/5. All utility modules are pure functions or simple state holders. Zero external dependency concerns beyond standard Rust crates. This is the highest-priority migration target.

## 3. Ownership Map

```
graph_utils:
  DagNode, DagEdge (value types)
  topological_sort(), has_cycle(), shortest_path() (free functions)
  _build_index() (private helper)

id_generator:
  IdGenerator (struct with atomic counter)
  IdPrefix (value type)

json_parser:
  loads_json(), dumps_json() (free functions)
  JsonParseError (error type)

time_utils:
  utc_now(), to_epoch_ms(), parse_duration() (free functions)
  DurationError (error type)

type_converter:
  coerce_type() (free function)
  _to_bool, _to_int, _to_float, _to_json_value (private converters)
  _TYPE_MAP (static dispatch table)
  ConversionError (error type)

xml_parser:
  parse_xml(), xml_to_dict() (free functions)
  XmlParseError (error type)
```

## 4. PyO3 Binding Structure

```rust
#[pyclass]
struct IdGenerator { prefix: String, counter: AtomicU64 }

// Free functions exposed as module-level functions
#[pyfunction]
fn topological_sort(nodes: Vec<DagNode>, edges: Vec<DagEdge>) -> PyResult<Vec<String>> { ... }

#[pyfunction]
fn coerce_type(value: &PyAny, target: &str) -> PyResult<PyObject> { ... }

// etc.
```

## 5. Libraries Analysis

| Current Python | Rust Equivalent | Notes |
|---------------|----------------|-------|
| `threading.Lock` | `std::sync::atomic::AtomicU64` | Lock-free counter |
| `uuid.uuid4()` | `uuid` crate | UUID generation |
| `json` | `serde_json` | JSON parsing |
| `re` (regex) | `regex` crate | Duration string parsing |
| `xml.etree.ElementTree` | `quick-xml` | XML parsing |
| `collections.abc` | `std::collections` | Hash maps, iterators |
| `datetime` / `timezone` | `chrono` | UTC timestamps, duration |
| `functools` | N/A | Not used |

## 6. Performance Hot Paths

- `topological_sort()` — O(V + E). Used for process/state workflow validation. Linear time.
- `shortest_path()` — O(V + E) BFS. Used rarely.
- `IdGenerator.next_id()` — Lock contented in multi-threaded Python. Rust `AtomicU64` is wait-free.
- `parse_duration()` — Regex match + O(1) computation.
- `coerce_type()` — O(1) hash lookup + conversion.
- All graph functions: no heap allocations beyond result `Vec`.

## 7. Error Handling

| Python | Rust Strategy |
|--------|---------------|
| `JsonParseError(ValueError)` | `thiserror::Error` |
| `XmlParseError(ValueError)` | `thiserror::Error` |
| `ConversionError(ValueError)` | `thiserror::Error` |
| `DurationError(ValueError)` | `thiserror::Error` |
| `raise ValueError("Cycle detected")` in topo sort | `Result<Vec<String>, GraphError::Cycle>` |
| `except (TypeError, ValueError)` → custom error | `.map_err(|e| JsonParseError(e.to_string()))` |
