# Tools Engine — Rust Migration Report

**Source:** `multi_agent_infra/engines/tools/`
**Scanned:** 16 files (4 core + 12 adapters)
**Boundary:** Orchestrator → `ToolRegistry.execute()` → executor dispatch

---

## 1. Pre-Refactor Analysis

### 1.1 `Any` and `dict[str, Any]` Counts

| Construct | Count | Files |
|-----------|-------|-------|
| `kwargs: Any` | 14 | `base_executor.py:26`, `tool_registry.py:37`, all 12 `execute()` methods |
| `Callable[..., Any]` | 2 | `python_function_executor.py:14,16` |
| `list[dict[str, Any]]` | 1 | `composite_executor.py:27` |
| `dict[str, Any]` (via RawData) | 2 | `_types.py:33`, `parameter_mapper.py` |
| `dict[str, Any]` (via MessagePayload, FeelContext, Metadata) | 3 | `_types.py:20,27,30` (not used in tools/) |

**Total:** ~20 `Any`-typed parameters across all executor `execute()` methods + 6 `dict[str, Any]` type alias references.

### 1.2 isinstance Chains

**None found.** No isinstance branching exists in this layer — all dispatch is done via class-based polymorphism (ABC → concrete executor).

### 1.3 ABCs and Protocols

| Item | Type | Location |
|------|------|----------|
| `BaseToolExecutor(ABC)` | Abstract class | `base_executor.py:22` |
| `@abstractmethod execute(**kwargs) -> ToolResult` | Abstract method | `base_executor.py:26` |
| `@abstractmethod name -> str` | Abstract property | `base_executor.py:30` |
| `@abstractmethod description -> str` | Abstract property | `base_executor.py:35` |
| Protocols | **0** | Not used |

**14 concrete subclasses** of `BaseToolExecutor` exist. No `isinstance` checks are needed — the registry owns them by name.

### 1.4 Supporting Types

**`ToolResult`** (`base_executor.py:10-19`): Simple success/failure container with optional `data` and `error` fields. Used as return type for all executor calls.

**`ParameterMapper`** (`parameter_mapper.py:8-23`): Pure data transformation — renames keys via a dict mapping, validates required params. Stateless helper, not an executor.

---

## 2. Migration Notes (Score 1–5)

### 2.1 Scores

| Component | Score | Reasoning |
|-----------|-------|-----------|
| `ToolResult` | **5** | Simple struct — `success: bool`, `data: Option<VariableValue>`, `error: Option<String>`. No Python-specific behavior. |
| `ParameterMapper` | **4–5** | Pure `HashMap<String, String>` rename + `validate()` returns missing keys. Zero Python dependency. |
| `BaseToolExecutor` trait | **4** | Clean trait: `async fn execute(&self, params: HashMap<String, Value>) -> ToolResult`. 3 method interface. |
| `ToolRegistry` | **4** | `HashMap<String, Arc<dyn ToolExecutor>>` with register/get/execute/list. Thin wrapper. |
| `CompositeExecutor` | **3–4** | Linear iteration with early exit. No Python-specific logic, but it delegates to generic trait objects. |
| `CLIExecutor` | **2–3** | `asyncio.create_subprocess_shell` → Rust would use `tokio::process::Command`. Doable but platform-sensitive. |
| `FileExecutor` | **2–3** | `tokio::fs` replacement is straightforward, but path handling would need native Rust equivalents. |
| `DBQueryExecutor` | **2** | SQL string passthrough. The driver ecosystem differs (sqlx/tokio-postgres vs asyncpg). Bridge complexity. |
| `HTTPToolExecutor` / `HTTPServiceExecutor` | **2–3** | `reqwest` can replace `httpx`. Auth token management is simple. Keep in Python unless high throughput needed. |
| `GrpcToolExecutor` | **2–3** | `tonic` for gRPC, but proto management and Python ↔ gRPC bridge adds complexity. |
| `TCPSocketExecutor` | **2–3** | `tokio::net::TcpStream`. Straightforward but niche usage. |
| `MCPToolExecutor` | **2** | MCP is protocol-level. Implementing the MCP client in Rust is plausible but significant work. |
| `MessageBusExecutor` | **2–3** | Transport-agnostic stub. Real implementations (Kafka/RabbitMQ) have Rust clients (rdkafka/lapin). |
| `MIBSNMPExecutor` | **2** | SNMP requires C/libnetsnmp bindings or pure-Rust snmp crate. Niche. |
| `YANGNetconfExecutor` | **2** | NETCONF over SSH — `ssh2` crate or subprocess to `netconf-console`. Niche. |
| `AIModelExecutor` | **1–2** | LLM inference (OpenAI API, etc.) — `reqwest` HTTP calls. Stub now, but real impl is API-dependent. |
| `PythonFunctionExecutor` | **1** | **PYTHON_ONLY.** Wraps arbitrary Python `Callable` objects. Cannot migrate without a `PyObject` bridge. |

### 2.2 Migration Strategy Summary

**Phase 1 (Score 4–5):** `ToolResult`, `ParameterMapper`, `BaseToolExecutor` trait definition (as an `#[pyclass]` trait or Rust-native trait), `ToolRegistry`.

**Phase 2 (Score 3–4):** `CompositeExecutor`.

**Stay in Python (Score 1–2):** All I/O-bound executors (HTTP, gRPC, MCP, CLI, SNMP, NETCONF, DB) + `PythonFunctionExecutor`.

---

## 3. Ownership Map

```
Orchestrator
  └─ ToolRegistry                          (engines/tools/tool_registry.py)
       ├─ _executors: dict[str, BaseToolExecutor]
       │
       ├─ register(executor)               name → executor registration
       ├─ unregister(name)                 removal
       ├─ get(name) → executor             lookup
       ├─ execute(name, **kwargs)          dispatch + error boundary
       └─ list_tools() → metadata[]        discovery for agents
```

**Key observation:** The Orchestrator holds a single `ToolRegistry` instance and calls `execute(name, **kwargs)`. The registry owns all executors and acts as a mediator. No circular ownership.

**Agent interaction pattern:** Agents never hold direct executor references. They call `tool_registry.execute("tool_name", ...)`. This is already a mediator pattern — ideal for Rust trait dispatch.

---

## 4. PyO3 Binding Structure

### 4.1 Recommended Binding Architecture

```
┌─────────────────────────────────────┐
│         Python (agents/tools)       │
│                                     │
│  Orchestrator                       │
│    │                                │
│    └─ ToolRegistry.execute()        │
│         │                           │
│         ├─ Rust ToolRegistry        │  ← PyO3 bound
│         │   └─ HashMap<String,      │
│         │        Box<dyn Executor>> │
│         │                           │
│         ├─ Rust ParameterMapper     │  ← PyO3 bound
│         │                           │
│         └─ Python executors         │  ← stay in Python (PyO3 subclass)
│              ├─ HTTPToolExecutor     │
│              ├─ CLIExecutor          │
│              ├─ PythonFunctionExec.  │
│              └─ ...                  │
└─────────────────────────────────────┘
```

### 4.2 Binding Details

**Migration candidates (Rust-native, PyO3-bound):**

```rust
// tool_result.rs — fully Rust
#[pyclass]
struct ToolResult {
    success: bool,
    data: Option<PyObject>,  // bridges to Python objects
    error: Option<String>,
}

// parameter_mapper.rs — fully Rust
#[pyclass]
struct ParameterMapper {
    mapping: HashMap<String, String>,
}
#[pymethods]
impl ParameterMapper {
    fn map(&self, params: HashMap<String, PyObject>) -> HashMap<String, PyObject>;
    fn validate(&self, params: HashMap<String, PyObject>, required: Vec<String>) -> Vec<String>;
}

// tool_registry.rs — Rust-native, thin PyO3 wrapper
#[pyclass]
struct ToolRegistry {
    executors: HashMap<String, Py<PyAny>>,  // Python executor objects
}
#[pymethods]
impl ToolRegistry {
    fn register(&mut self, executor: &PyAny);
    fn execute(&self, py: Python, name: &str, kwargs: HashMap<String, PyObject>) -> PyResult<ToolResult>;
}
```

**Executor binding pattern:**
- `BaseToolExecutor` stays as a Python ABC (per score 1–2 decision)
- Rust `ToolRegistry.execute()` uses `PyAny::call()` to invoke Python executor objects
- Hot path: registry lookup (Rust `HashMap::get`) is fast; parameter marshaling (Rust → Python) is the bottleneck

**Alternative (full Rust trait dispatch):**
```rust
#[async_trait]
trait ToolExecutor: Send + Sync {
    async fn execute(&self, params: HashMap<String, Value>) -> ToolResult;
    fn name(&self) -> &str;
    fn description(&self) -> &str;
}
```
Then wrap Python executors as: `struct PyExecutor { inner: Py<PyAny> }` implementing `ToolExecutor` via `Python::with_gil`.

---

## 5. External Libraries Analysis

### 5.1 Imports by File

| File | Imports | External |
|------|---------|----------|
| `base_executor.py` | `abc`, `typing.Any`, `.._types.VariableValue` | **None** |
| `parameter_mapper.py` | `typing.Any`, `.._types.RawData` | **None** |
| `tool_registry.py` | `logging`, `typing.Any`, `BaseToolExecutor`, `ToolResult` | **None** |
| `cli_executor.py` | `asyncio`, `typing.Any` | **None** |
| All other adapters | `typing.Any`, `BaseToolExecutor`, `ToolResult` | **None** |
| `python_function_executor.py` | `typing.Any`, `collections.abc.Callable` | **None** |

### 5.2 External Dependencies

| Library | Used By | Purpose |
|---------|---------|---------|
| `asyncio` | `cli_executor.py` | Subprocess management |
| `abc` | `base_executor.py` | Abstract base class |
| `logging` | `tool_registry.py` | Error/warning logging |

**No `httpx`, `aiohttp`, `grpcio`, `pysnmp`, `ncclient`, or other I/O libraries are actually imported in the current codebase.** All network/database/message-bus executors are stubs with hardcoded return values. Real implementations would require those libraries.

**Rust equivalents for migrated components:**

| Python | Rust |
|--------|------|
| `dict[str, str]` | `HashMap<String, String>` |
| `kwargs: Any` | `HashMap<String, Value>` (serde_json::Value or similar) |
| `RawData` (`dict[str, Any]`) | `HashMap<String, serde_json::Value>` |
| `asyncio.create_subprocess_shell` | `tokio::process::Command` |
| `ABC` + `@abstractmethod` | `#[async_trait] pub trait ToolExecutor` |
| `logging` | `tracing` / `log` crate |
| `type.__subclasses__` / isinstance | Static dispatch via trait objects |

---

## 6. Performance Hot Paths

### 6.1 Parameter Mapping / Marshaling (every tool call)

`ParameterMapper.map()` is called on every `ToolRegistry.execute()` invocation. It iterates over a `RawData` dict and renames keys. Current implementation:

```python
for key, value in params.items():
    target_key = self._mapping.get(key, key)
    mapped[target_key] = value
```

**Rust migration benefit:** `HashMap::get` with zero-copy string slicing. No Python GIL contention during mapping. Estimated 10–50x speedup on this single operation, but it's O(n) on param count (typically <20 params) so absolute gain is small.

### 6.2 Tool Dispatch (registry lookup)

`ToolRegistry.execute()` does:
1. `self._executors.get(name)` — O(1) dict lookup
2. `await executor.execute(**kwargs)` — awaits/starts the tool

**Rust migration benefit:** Dict lookup is already O(1). The gain comes from avoiding GIL overhead during the dispatch path when routing from Orchestrator through ToolRegistry to executor. **Marginal** — only matters at >1000 TPS.

### 6.3 Composite Sequencing

`CompositeExecutor` runs executors sequentially with early exit. In Rust, async trait dispatching avoids Python context-switch overhead between steps.

### 6.4 What is NOT a hot path

- **`list_tools()`** — called rarely (agent discovery). No optimization needed.
- **`register()`/`unregister()`** — called once per executor lifecycle. Irrelevant.
- **Validator checks** (`validate()`) — O(n) on `required` list. Negligible.

### 6.5 True Bottleneck: Python↔Rust Crossing

Every executor call that stays in Python requires: Rust HashMap → Python dict conversion → GIL acquire → `PyAny::call()` → GIL release → Python dict → Rust conversion of result. This crossing cost can **exceed** the gain of fast registry lookup. Profile before committing.

**Recommendation:** Only migrate `ToolRegistry.execute()` if you keep executors in Rust, OR if the Orchestrator is also migrated to Rust and can call Rust-native `ToolRegistry::execute()` without crossing the boundary.

---

## 7. Error Handling

### 7.1 Error Patterns

| Pattern | Location | Behavior |
|---------|----------|----------|
| Tool not found | `tool_registry.py:39-40` | Returns `ToolResult(False, error=f"Unknown tool '{name}'")` |
| Execution exception | `tool_registry.py:43-45` | Catches `Exception`, logs via `logger.exception()`, returns `ToolResult(False, error=str(exc))` |
| Unknown function | `python_function_executor.py:30-31` | Returns `ToolResult(False, error=f"Unknown function '{fn_name}'")` |
| Function exception | `python_function_executor.py:37-38` | Returns `ToolResult(False, error=str(exc))` |
| No command | `cli_executor.py:23-24` | Returns `ToolResult(False, error="No command provided")` |
| Subprocess failure | `cli_executor.py:32-33` | `ToolResult(proc.returncode == 0, ...)` — checks return code |
| Composite step fail | `composite_executor.py:31-32` | Returns `ToolResult(False, data=results, error=f"Step '{executor.name}' failed")` |
| All other executors | N/A | Always return `ToolResult(True, ...)` — stub implementations assume success |

### 7.2 Error Handling Characteristics

- **No custom exception types.** All errors are `str` strings in `ToolResult.error`.
- **No retry logic** at the tools layer (expected to be handled by Orchestrator).
- **No partial failure** handling via `ToolResult` (success/failure is binary).
- **PythonFunctionExecutor** has the most complex error surface (arbitrary callable → arbitrary exception).
- **CLIExecutor** is the only executor that checks non-OK return values (subprocess returncode).
- **CompositeExecutor** stops on first failure without rollback of prior successful steps.

### 7.3 Rust Migration — Error Handling Recommendations

```rust
#[derive(Debug, thiserror::Error)]
pub enum ToolError {
    #[error("Unknown tool '{0}'")]
    NotFound(String),
    #[error("Execution failed: {0}")]
    Execution(String),
}
```

Keep the `ToolResult` pattern for Python bridge compatibility. For Rust-native tool dispatch, use `Result<ToolResult, ToolError>` and convert to `ToolResult` at the PyO3 boundary.

The `PythonFunctionExecutor` error path (`arbitrary Python exception → str`) is already the most Python-specific error handling. This reinforces its score-1 PYTHON_ONLY classification.

---

## Summary Table

| File | LOC | Score | Migrate? | Notes |
|------|-----|-------|----------|-------|
| `base_executor.py` | 37 | 4 | Yes (trait) | ABC → Rust `#[async_trait]` |
| `tool_registry.py` | 45 | 4 | Yes | HashMap + dispatch logic |
| `parameter_mapper.py` | 23 | 4–5 | Yes | Pure data transform |
| `composite_executor.py` | 33 | 3–4 | Maybe | Sequential composition |
| `cli_executor.py` | 34 | 2–3 | No | Subprocess I/O |
| `file_executor.py` | 26 | 2–3 | No | Filesystem I/O |
| `python_function_executor.py` | 38 | 1 | **No** | PYTHON_ONLY |
| `http_tool_executor.py` | 26 | 2–3 | No | HTTP I/O |
| `http_service_executor.py` | 25 | 2–3 | No | HTTP I/O |
| `grpc_tool_executor.py` | 25 | 2–3 | No | gRPC I/O |
| `tcp_socket_executor.py` | 26 | 2–3 | No | Socket I/O |
| `mcp_tool_executor.py` | 25 | 2 | No | MCP protocol |
| `message_bus_executor.py` | 26 | 2–3 | No | Message bus I/O |
| `mib_snmp_executor.py` | 26 | 2 | No | SNMP I/O |
| `yang_netconf_executor.py` | 26 | 2 | No | NETCONF I/O |
| `db_query_executor.py` | 25 | 2 | No | SQL I/O |
| `ai_model_executor.py` | 25 | 1–2 | No | LLM inference |
| `__init__.py` (x2) | 39+31 | 5 | Yes | Re-exports |
