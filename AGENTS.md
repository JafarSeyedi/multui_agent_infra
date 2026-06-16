# AGENTS.md — multi-agent-infra

## Quick start

```bash
# run all knowledge tests
python3 -m pytest engines/knowledge/tests/ -v

# run a single test file
python3 -m pytest engines/knowledge/tests/test_writers.py -v

# run all orchestration tests
python3 -m pytest engines/orchestration/tests/ -v

# run all tools tests
python3 -m pytest engines/tools/tests/ -v

# run all communication tests
python3 -m pytest engines/communication/tests/ -v

# run all state tests
python3 -m pytest engines/state/tests/ -v

# run all config tests
python3 -m pytest engines/config/tests/ -v

# run all security tests
python3 -m pytest engines/security/tests/ -v

# run all persistence tests
python3 -m pytest engines/persistence/tests/ -v

# no Makefile, no pre-commit, no CI workflows in this repo
```

## Architecture

Monorepo under `engines/` with 14 engine packages:

| Engine | Location | Purpose |
|--------|----------|---------|
| orchestration | `engines/orchestration/` | Workflow DAG execution, task dispatch |
| interaction | `engines/interaction/` | Multi-agent conversation patterns (debate, group-chat) |
| agents | `engines/agent/` | Agent registry, adapter pattern (AgentInput → AgentSpecificInput) |
| tools | `engines/tools/` | Tool layer (LLM, RAG, MCP, local, remote) |
| document | `engines/document/` | Document parsing/writing, media types, models (USD/PSD/ESD/…SDM) |
| knowledge | `engines/knowledge/` | RAG, graph, BI, ML mining, process mining engines |
| communication | `engines/communication/` | Message buses, communication patterns |
| storage | `engines/storage/` | Storage backends |
| skill | `engines/skill/` | Skill engine |
| memory | `engines/memory/` | Memory engine |
| state | `engines/state/` | State management, caching, distributed locks |
| config | `engines/config/` | Configuration loading, secret resolution |
| security | `engines/security/` | Authentication, authorization |
| persistence | `engines/persistence/` | Vector store, blob storage |

## Key architectural facts

- **Agent flow**: Orchestrator → AgentInput → AgentAdapter → Agent → AgentOutput. Adapters convert between base and agent-specific models.
- **Tools layer**: LLM, RAG, Search, MCP are all Tools, not Agents. Agents decide, Tools execute.
- **Engine-specific SDM models live in their owning engine** (not in `engines/document/`): KSDM models are now per-engine under `engines/knowledge/{engine}/models/`, OSDM + BAM → `engines/orchestration/models/`, TSDM → `engines/tools/models/`. Each model dir has `{engine}_models.py`, `parsers/` and `writers/` subdirectories. The document engine keeps USDM, PSDM, ESDM, DSDM, CSDM, MSDM, SSDM, ISDM, LSDM.
- **Knowledge engines** import models/parsers/writers from their own per-engine `models/` package. Use `engines.knowledge.{engine}.models` instead of the old centralized `engines.knowledge.models`. Backward-compat wrappers have been removed.
- **Knowledge `__init__.py`** only eagerly imports the 5 stable engines (bi_aggregation, ml_mining, process_mining, semantic_graph, graph). RAG and memory engines are excluded because they have missing transitive dependencies.
- **`KnowledgeRagEngine`** cannot be imported directly — it depends on `engines.knowledge.rag.{services,llm,research}` modules that don't exist. If you need it, create stubs first.
- **`UnifiedGraphEngine` ↔ `SemanticGraphEngine` circular dependency**: `UnifiedGraphEngine.__init__` must pass `unified_engine=self` to `SemanticGraphEngine()` to avoid infinite recursion. This is already fixed.
- **Semantic graph parsers** (`RdfParser`, `RmlParser`) implement sync `parse()` + async `parse_bytes()`/`parse_path()`/`parse_stream()` (had to add abstract method impls to make them instantiable). `SemanticGraphEngine` wraps sync `parse()` in `loop.run_in_executor()`.

## Test conventions

- `engines/knowledge/tests/` has conftest.py with custom `event_loop` fixture (creates new asyncio loop per test).
- `asyncio_mode = auto` in pyproject.toml — async tests are auto-detected.
- No integration test prerequisites (no DB, no external services needed for knowledge tests).
- 2 tests in `test_engines.py` are skipped (RAG/memory) due to missing dependencies.
- 171 total knowledge tests (15 BI aggregation + 67 ML mining + 36 Phase E + 14 query models + 44 semantic graph + 25 process mining).
- Phase E tests in `test_ml_mining_phase_e.py` — sklearn/PyTorch parser, converter→ORT inference, engine predict/evaluate, metrics, validation, full pipeline.
- Semantic graph tests in `test_semantic_graph.py` — RDF parse, graph API, traversal, shortest path, subgraph, statistics, validate, convert, write round-trip, edge cases.

## Framework & toolchain quirks

- **pydantic v2** — uses `model_fields` dict, not `__fields__`. `ConfigDict` replaces `Config` class. `@validator` → `@field_validator`.
- **mypy + ruff** are installed but no dedicated config beyond the minimal `pyproject.toml` mypy settings (just `exclude = []`).
- A `mypy_errors.txt` exists at root — likely a dump of type-check output.
- **SQLAlchemy 2.0+** with async support (`sqlalchemy[asyncio]`).
- **Alembic** configured (`alembic.ini`) — DB migrations in `migrations/`.
- **Multiple RAG frameworks**: both llama-index and langchain+langgraph are installed and may be used in different components.
- **Graph persistence** (`rag/research/graph/graph_persistence.py`) creates a local SQLite file `research_graph.db` at init — not suitable for concurrent or production use as-is.

## Execution preferences

- **Plan execution default**: inline (subagent-driven available on request)

## Important constraints

- **`engines/document/models/media_types.py`** is the single source of truth for `DocumentFormat` enum and `MEDIA_TYPES` registry. Format enums live here, not in model files.
- **`engines/knowledge/models/`** has been removed — KSDM models are now per-engine under `engines/knowledge/{engine}/models/`.
- Format enum values use snake_case keys (`xes_xml`, `cwm_xmi`, `rdf_turtle`) — the old `bi_model_json`/`rdfxml` style is gone.
- `.gitignore` excludes `prompts/` — don't store generated prompts in git.
