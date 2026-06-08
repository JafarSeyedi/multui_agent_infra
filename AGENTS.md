# AGENTS.md — multi-agent-infra

## Quick start

```bash
# run all knowledge tests
python3 -m pytest tests/knowledge/ -v

# run a single test file
python3 -m pytest tests/knowledge/test_writers.py -v

# no Makefile, no pre-commit, no CI workflows in this repo
```

## Architecture

Monorepo under `engines/` with 10 engine packages:

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

## Key architectural facts

- **Agent flow**: Orchestrator → AgentInput → AgentAdapter → Agent → AgentOutput. Adapters convert between base and agent-specific models.
- **Tools layer**: LLM, RAG, Search, MCP are all Tools, not Agents. Agents decide, Tools execute.
- **Document models** (`engines/document/models/`) follow the *SDM pattern: USDM (text), PSDM (presentation), ESDM (spreadsheet), DSDM (data), CSDM (CAD), MSDM (schema), SSDM (service), ISDM (insights), KSDM (knowledge graph), OSDM (orchestration), TSDM (tools).
- **Knowledge engines** (`engines/knowledge/apps/`) import from `engines.document.*` for models/parsers/writers. The `engines/knowledge/{parsers,writers,models}/` directories are thin re-export wrappers for backward compat.
- **Knowledge `__init__.py`** only eagerly imports the 5 stable engines (bi_aggregation, ml_mining, process_mining, semantic_graph, graph). RAG and memory engines are excluded because they have missing transitive dependencies.
- **`KnowledgeRagEngine`** cannot be imported directly — it depends on `engines.knowledge.rag.{services,llm,research}` modules that don't exist. If you need it, create stubs first.
- **`UnifiedGraphEngine` ↔ `SemanticGraphEngine` circular dependency**: `UnifiedGraphEngine.__init__` must pass `unified_engine=self` to `SemanticGraphEngine()` to avoid infinite recursion. This is already fixed.

## Test conventions

- `tests/knowledge/` has conftest.py with custom `event_loop` fixture (creates new asyncio loop per test).
- `asyncio_mode = auto` in pyproject.toml — async tests are auto-detected.
- No integration test prerequisites (no DB, no external services needed for knowledge tests).
- 2 tests in `test_engines.py` are skipped (RAG/memory) due to missing dependencies.

## Framework & toolchain quirks

- **pydantic v2** — uses `model_fields` dict, not `__fields__`. `ConfigDict` replaces `Config` class. `@validator` → `@field_validator`.
- **mypy + ruff** are installed but no dedicated config beyond the minimal `pyproject.toml` mypy settings (just `exclude = []`).
- A `mypy_errors.txt` exists at root — likely a dump of type-check output.
- **SQLAlchemy 2.0+** with async support (`sqlalchemy[asyncio]`).
- **Alembic** configured (`alembic.ini`) — DB migrations in `migrations/`.
- **Multiple RAG frameworks**: both llama-index and langchain+langgraph are installed and may be used in different components.
- **Graph persistence** (`rag/research/graph/graph_persistence.py`) creates a local SQLite file `research_graph.db` at init — not suitable for concurrent or production use as-is.

## Important constraints

- **`engines/document/models/media_types.py`** is the single source of truth for `DocumentFormat` enum and `MEDIA_TYPES` registry. Format enums live here, not in model files.
- **`engines/knowledge/models/media_types.py`** has `KnowledgeMediaType` (a separate pydantic model with richer metadata) — kept for backward compat but the document layer uses `MediaType` from `engines.document.models.media_types`.
- Format enum values use snake_case keys (`xes_xml`, `cwm_xmi`, `rdf_turtle`) — the old `bi_model_json`/`rdfxml` style is gone.
- `.gitignore` excludes `prompts/` — don't store generated prompts in git.
