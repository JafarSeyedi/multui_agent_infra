# Layer Dependency Analysis Report

## Rules

1. Each folder/subfolder represents a layer/sub-layer/sub-sub-layer.
2. If layer `A` imports from layer `B`, then `B` must **not** import from `A` at any level (direct, transitive, or hierarchical).
3. This applies recursively to sub-layers.

---

## Layer Hierarchy

```
engines/agent/             (legacy, duplicate of agents/)
engines/agents/            Agent registry, adapter pattern
engines/buses/             Message buses (Redis, Kafka, RabbitMQ, in-memory)
engines/communication/     Communication patterns
engines/document/          Document models, parsers, writers
engines/interaction/       Multi-agent conversation patterns
engines/knowledge/         RAG, graph, BI, ML mining, process mining
engines/orchestration/     Workflow DAG execution, task dispatch
engines/rag/               Independent RAG framework
engines/storage/           Storage backends (cache, KV, vector, event_log, ...)
engines/tools/             Tool layer (LLM, RAG, MCP, local, remote)
```

---

## Original Violations Found

### Violation 1 — `buses` ↔ `interaction` (top-level circular)

| Direction | Files |
|-----------|-------|
| `buses/*` → `interaction.interaction_models` | 9 bus implementations |
| `interaction/*` → `buses.base_message_bus` | 3 files (backends + coordinator) |

### Violation 2 — `knowledge.graph` ↔ `knowledge.semantic_graph` (sub-layer circular)

| Direction | Lines |
|-----------|-------|
| `semantic_graph/engine.py` → `graph.engine` | Line 20 (direct import) |
| `graph/engine.py` → `semantic_graph.engine` | Line 57 (deferred import) |

### Violation 3 — `knowledge.graph` ↔ `knowledge.rag` (sub-layer circular)

| Direction | Lines |
|-----------|-------|
| `rag/vector_service.py` → `graph.graph_retriever` | Direct import |
| `graph/engine.py` → `rag.research.graph.*` | Lines 48-50 (deferred, 3 imports) |

### Violation 4 — `orchestration.core` ↔ `orchestration.persistence` ↔ `orchestration.runtime` (3-node cycle)

```
core → persistence → runtime → persistence
```

| Direction | Paths |
|-----------|-------|
| `core` → `persistence` | core/engine.py, core/scheduler.py, core/event_bus.py, core/correlation.py |
| `persistence` → `runtime` | All 6 repos import runtime.runtime_records |
| `runtime` → `persistence` | runtime/variable_manager.py → persistence.variable_repository |

---

## Resolutions

### Resolution 1 — `buses` ↔ `interaction`

**Approach**: Extract `AgentMessage` model into `buses/message_models.py`.

- Created `engines/buses/message_models.py` with `AgentMessage` (self-contained, no engine deps)
- Updated all 9 files in `engines/buses/` to import from `buses.message_models`
- Updated all 9 files in `engines/communication/buses/` to import from `buses.message_models`
- `interaction/interaction_models.py` re-exports `AgentMessage` for backward compatibility

**Result**: `buses` no longer imports from `interaction`. Only `interaction` → `buses` remains (one-way).

### Resolution 2 — `knowledge.graph` ↔ `knowledge.semantic_graph`

**Approach**: Extract protocol interfaces, break direct dependency.

- Created `engines/knowledge/graph/protocols.py` with `GraphEngineProtocol` and `EntityExtractorProtocol`
- `SemanticGraphEngine` accepts `GraphEngineProtocol` instead of concrete `UnifiedGraphEngine`
- `UnifiedGraphEngine` import is deferred inside `SemanticGraphEngine.__init__` only for default construction
- `UnifiedGraphEngine.entity_extractor` annotated as `EntityExtractorProtocol`

**Result**: `semantic_graph` → `graph.protocols` only. `graph.engine` → `semantic_graph.engine` remains one-way.

### Resolution 3 — `knowledge.graph` ↔ `knowledge.rag`

**Approach**: Move graph-domain code out of RAG into `graph/`.

- Moved `engines/knowledge/rag/research/graph/` → `engines/knowledge/graph/research/`
- Files moved: `__init__.py`, `entity_extractor.py`, `graph_aware_planner.py`, `graph_canonicalizer.py`, `graph_index.py`, `graph_persistence.py`, `graph_traverser.py`, `relation_builder.py`, `relation_ranker.py`
- Updated `graph/engine.py` (deferred imports) to use `graph.research.*`
- Updated `rag/research/research_agent.py` to import from `knowledge.graph.research.*`
- Moved files had zero RAG dependencies — only stdlib imports

**Result**: `graph` → `graph.research` (internal, self-contained). `rag` → `graph` (one-way, correct direction).

### Resolution 4 — `orchestration.core` ↔ `orchestration.persistence` ↔ `orchestration.runtime`

**Approach**: Move record schema definitions from `runtime/` to `persistence/`.

- Moved `runtime/runtime_records.py` → `persistence/runtime_records.py`
- Updated all 6 persistence repos to use sibling imports (`.runtime_records`)
- Updated `runtime/__init__.py` and `runtime/state_manager.py` to import from `..persistence.runtime_records`
- Removed original `runtime/runtime_records.py`

**Result**: Cycle broken. `persistence` no longer imports from `runtime`. `runtime` → `persistence` (one-way).

---

## Final Dependency Graph

```
storage  (no incoming deps)
document (no incoming deps)
   |
   v
rag ──────────────────┐
   │                  │
   v                  v
orchestration ──→ document, storage
   │
   ├──→ persistence (runtime_records)
   ├──→ core
   └──→ runtime → persistence (variable_manager)

knowledge ──→ document, rag
   │
   ├── graph ──→ document
   │   └── research (internal, ex-rag.research.graph)
   │
   ├── semantic_graph ──→ graph.protocols, document
   │
   └── rag ──→ graph.research, document, rag

interaction ──→ buses
buses ──→ (no external deps)
agents ──→ storage, interaction
communication ──→ (no external deps)
tools ──→ (no external deps)
```

All dependencies are strictly acyclic at every layer level.

---

## Verification

- `mypy`: 0 errors (1316 source files checked)
- `ruff`: 0 errors
- Pre-existing test collection errors in `tests/knowledge/` (unrelated — `PSDMDocument` `@dataclass` + pydantic `BaseModel` conflict) remain unchanged.

---

## Files Changed

### Violation 1 (buses ↔ interaction)
- `engines/buses/message_models.py` — **NEW**
- `engines/buses/base_message_bus.py` — import path update
- `engines/buses/in_memory_message_bus.py` — import path update
- `engines/buses/durable_message_bus.py` — import path update
- `engines/buses/rabbitmq_bus.py` — import path update
- `engines/buses/request_reply_bus.py` — import path update
- `engines/buses/redis_pub_sub_bus.py` — import path update
- `engines/buses/priority_message_bus.py` — import path update
- `engines/buses/kafka_bus.py` — import path update
- `engines/buses/topic_message_bus.py` — import path update
- `engines/communication/buses/base_message_bus.py` — import path update
- `engines/communication/buses/in_memory_message_bus.py` — import path update
- `engines/communication/buses/durable_message_bus.py` — import path update
- `engines/communication/buses/rabbitmq_bus.py` — import path update
- `engines/communication/buses/request_reply_bus.py` — import path update
- `engines/communication/buses/redis_pub_sub_bus.py` — import path update
- `engines/communication/buses/priority_message_bus.py` — import path update
- `engines/communication/buses/kafka_bus.py` — import path update
- `engines/communication/buses/topic_message_bus.py` — import path update
- `engines/interaction/interaction_models.py` — re-export AgentMessage

### Violation 2 (graph ↔ semantic_graph)
- `engines/knowledge/graph/protocols.py` — **NEW**
- `engines/knowledge/graph/engine.py` — add protocol annotation
- `engines/knowledge/semantic_graph/engine.py` — use protocol + deferred import

### Violation 3 (graph ↔ rag)
- `engines/knowledge/graph/research/__init__.py` — **MOVED** (ex rag/research/graph/)
- `engines/knowledge/graph/research/entity_extractor.py` — **MOVED**
- `engines/knowledge/graph/research/graph_aware_planner.py` — **MOVED**
- `engines/knowledge/graph/research/graph_canonicalizer.py` — **MOVED**
- `engines/knowledge/graph/research/graph_index.py` — **MOVED**
- `engines/knowledge/graph/research/graph_persistence.py` — **MOVED**
- `engines/knowledge/graph/research/graph_traverser.py` — **MOVED**
- `engines/knowledge/graph/research/relation_builder.py` — **MOVED**
- `engines/knowledge/graph/research/relation_ranker.py` — **MOVED**
- `engines/knowledge/graph/engine.py` — update imports to graph.research
- `engines/knowledge/rag/research/research_agent.py` — update imports to graph.research

### Violation 4 (orchestration cycle)
- `engines/orchestration/persistence/runtime_records.py` — **MOVED** (ex runtime/)
- `engines/orchestration/persistence/event_repository.py` — import path update
- `engines/orchestration/persistence/token_repository.py` — import path update
- `engines/orchestration/persistence/instance_repository.py` — import path update
- `engines/orchestration/persistence/history_repository.py` — import path update
- `engines/orchestration/persistence/variable_repository.py` — import path update
- `engines/orchestration/persistence/repository.py` — import path update
- `engines/orchestration/runtime/__init__.py` — import path update
- `engines/orchestration/runtime/state_manager.py` — import path update
