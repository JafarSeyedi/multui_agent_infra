# Migration Report: `engines/agent/skill/` (Skill Engine)

**Note**: This is a subpackage of `engines/agent/`, not the standalone `engines/skill/` described in AGENTS.md. The standalone directory does not exist yet.

**Scored**: 2/5 — low migration priority. Heavy Python ecosystem coupling (file I/O, YAML, LLM text generation). Core execution pipeline is straightforward but surrounded by Python-specific infrastructure.

---

## 1. Pre-refactor Analysis

### `Any` / `dict[str, Any]` Usage (Moderate)

| File | Issue |
|------|-------|
| `skill.py` | `_skills_data: dict[str, dict[str, Any]]` — nested untyped dict |
| `models.py` | `SkillOutput.output_schema: dict[str, Any] \| None`, `SkillStep.output_schema: dict[str, Any] \| None` — schema documents as blobs |
| `executor.py` | `LLMClient.generate_structured_output(..., output_schema: dict[str, Any])`, all `**kwargs: Any` passthrough |
| `executor.py` | `SkillExecutor.execute` Protocol returns `Any` |
| `adapters.py` | `BaseSkillExecutor._llm_client: Any`, `MCPAdapter._client: Any` |
| `mcp_client.py` | Module-level `ClientSession: Any = None`, all `Any` type stubs |

### `isinstance` Chains

- `executor.py` — none directly, but pervasive type checking via try/except/fallback pattern (structured → text → JSON parse)
- `adapters.py:45` — `hasattr(self._client, "call_tool")` duck-typing

### Global State

- `mcp_client.py:7-16` — **Module-level mutable type stubs** (`ClientSession: Any = None`, `StdioServerParameters: Any = None`, `stdio_client: Any = None`) — mutated at import time via lazy `try: from mcp import ...`. This is a global-side-effect pattern that breaks in Rust.

---

## 2. Migration Notes (Score 2/5)

| Component | Rust Candidate | Reasoning |
|---|---|---|
| **SkillLoader** | Low | `os.walk` + file I/O + YAML frontmatter parsing + regex splitting. Pure Python ecosystem. |
| **BatchSkillExecutor** | Medium | Builds prompt string, calls LLM, handles structured/text fallback. The pipeline logic is simple but LLM integration is Python-heavy. |
| **StepWiseSkillExecutor** | Medium | Same as batch, plus iterative context accumulation per step. |
| **LLMClient** (ABC) | Low | Abstract interface for LLM calls. The actual implementation will always be Python (HTTP to OpenAI/anthropic). |
| **MCPClient** | Low | Direct MCP SDK coupling (`mcp` PyPI package). The SDK is Python-native. |
| **MCPAdapter** | Medium | Thin adapter — `hasattr` check then delegate. Trivial to rewrite. |
| **Skill Models** (SkillInput, SkillOutput, etc.) | Medium | Pydantic -> serde conversion is straightforward. |

### Python-specific constructs blocking migration

- `os.walk` filesystem traversal
- `yaml.safe_load` frontmatter parsing
- `re.split` with multiline regex
- `json.loads` fallback parsing
- `mcp` Python SDK imports with lazy `try/except`
- All `**kwargs` passthrough to LLM client

---

## 3. Ownership Map

```
SkillLoader (owns all skill data at startup)
  ├── owns: skills_directory: str
  ├── owns: _skills_data: dict[str, dict]  <- map of identifier -> {skill, base_path}
  ├── loads: SKILL.md files via os.walk + YAML
  └── methods: get_skill(), list_skills(), get_skill_by_name()

BatchSkillExecutor
  └── refs: LLMClient (ABC), SkillLoader

StepWiseSkillExecutor
  ├── refs: LLMClient (ABC), SkillLoader
  └── owns: step_results list (built iteratively)

MCPClient (connection lifecycle)
  ├── owns: server_command | server_url
  ├── owns: session (ClientSession, optional)
  └── owns: _stdio_context (async context manager)

MCPAdapter
  └── refs: mcp_client (Any, duck-typed)

BaseSkillExecutor (template method)
  └── refs: _llm_client: Any
```

### Mutability Risks

- `skill.py:_skills_data` is populated once in `__init__` via `_load_all_skills()` — effectively immutable after construction, but typed as mutable `dict`.
- `mcp_client.py` module-level globals are mutated at **import time** — hazard for Rust FFI initialization.

---

## 4. PyO3 Binding Structure

```
┌──────────────────────────────────────────────────────────┐
│                    Python Layer                           │
│                                                          │
│  SkillLoader (os.walk + yaml + file I/O)                  │
│  MCPClient (mcp SDK)                                      │
│  LLMClient impls (HTTP to external APIs)                  │
│  Skill models (Pydantic -> serde bridge)                  │
└───────────────────────┬──────────────────────────────────┘
                        │ PyO3 bridge
                        ▼
┌──────────────────────────────────────────────────────────┐
│                    Rust Core                              │
│                                                          │
│  BatchSkillExecutor  (prompt building + dispatch logic)   │
│  StepWiseSkillExecutor (step iteration logic)             │
│  MCPAdapter           (thin adapter)                      │
│  BaseSkillExecutor    (template method trait)             │
└──────────────────────────────────────────────────────────┘
```

**Boundary strategy**: Only the executor logic (prompt construction, output schema building, fallback orchestration) benefits from Rust. File loading, YAML parsing, MCP SDK, and LLM HTTP clients stay in Python.

---

## 5. Libraries Analysis

| Import | Source | Migration Impact |
|--------|--------|-----------------|
| `yaml` (PyYAML) | External | File I/O stays in Python |
| `json` | Stdlib | `serde_json` in Rust |
| `re` | Stdlib | `regex` crate. But frontmatter parsing stays in Python (tied to file I/O). |
| `os` + `os.walk` | Stdlib | File scanning stays in Python |
| `mcp` (MCP SDK) | External (conditional) | MCP client stays in Python |
| `logging` | Stdlib | `tracing` / `log` crate |
| `abc.ABC` | Stdlib | `trait` + `dyn` |

---

## 6. Performance Hot Paths

| Hot Path | Location | Current Cost | Rust Opportunity |
|----------|----------|-------------|------------------|
| **Output schema building** | `executor.py:37-84` | Called per skill execution. Loops over `SkillOutput` list and builds `dict`. | Zero-allocation struct construction in Rust |
| **Prompt string construction** | `executor.py:122-149`, `220-245` | String concatenation + `json.dumps` per invocation | `format!` + `serde_json::to_string` — minor gain |
| **Step-wise iteration** | `executor.py:217-273` | Python `for` loop with accumulated context dict updates per step | Iteration is Python-bound (LLM call is bottleneck) |
| **Structured output -> text fallback** | `executor.py:153-175` | try/except + `json.loads` retry | `Result::or_else` is idiomatic |
| **Reference file loading** | `models.py:44-59` | File I/O per skill execution via `get_reference_content` | Cache in Rust with `OnceCell` |

### Key Insight

**There are no CPU hot paths in this engine.** All execution is bottlenecked on LLM HTTP calls (latency measured in seconds). Migration to Rust provides no performance benefit for the executor itself. The value would be in type safety and error handling.

---

## 7. Error Handling

| Pattern | Prevalence | Rust Translation |
|---------|-----------|-----------------|
| `raise ValueError(...)` | 4 sites | `Result::Err` via `thiserror` |
| `raise FileNotFoundError(...)` | `models.py:58` | `Result::Err` — let caller handle |
| `raise RuntimeError(...)` | `executor.py:175` | `Result::Err` |
| `raise ImportError(...)` | `mcp_client.py:30` | Compile-time in Rust (features) |
| `logger.warning(...)` + fallback | 5+ sites — structured output → text fallback chain | `Result::or_else` |
| Silent catch `except _` | `executor.py:222` — `except (json.JSONDecodeError, KeyError, ValueError)` in state machine | `Option` with explicit ignore |
| `print()` (not logger) | `skill.py:44,52,64,87` | Remove — use `tracing` or `log` |

### Issues

- **Inconsistent logging**: `skill.py` uses `print()` instead of `logger` — not acceptable for production Rust.
- **Fallback chain not typed**: The structured → text → JSON parse chain is expressed as nested try/except. Rust `Result` combinators would make each fallback explicit.
- **MCP import gating**: The `try: from mcp import ...` pattern is a Python workaround for optional dependencies. In Rust, use `cfg!(feature = "mcp")` or Cargo feature gates.

---

## Migration Strategy

### Recommended: Leave in Python

The skill engine is deeply coupled to:
1. Filesystem traversal (`os.walk`)
2. YAML frontmatter parsing (`yaml.safe_load`)
3. MCP Python SDK
4. LLM HTTP client abstractions

Migrating the ~350 lines of executor logic provides negligible performance gain and introduces a complex PyO3 boundary for marginal type safety improvement.

### If forced: Only migrate `executor.py` + `models.py`

Create Rust crate `skill-executor` with:
- `Skill`, `SkillInput`, `SkillOutput`, `SkillStep` structs (`#[pyclass]` + `serde`)
- `BatchSkillExecutor` and `StepWiseSkillExecutor` with `LLMClient` as a `dyn` trait passed via PyO3
- Leave `SkillLoader`, `MCPClient`, `MCPAdapter` in Python
