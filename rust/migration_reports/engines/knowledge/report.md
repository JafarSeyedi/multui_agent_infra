# Knowledge Engine — Rust Migration Analysis

## 1. Pre-refactor Analysis: `Any`, `dict[str, Any]`, `isinstance` chains

### Pervasive `Any` usage

| Pattern | Occurrences | Files |
|---------|-------------|-------|
| `llm: Any` | ~40+ | proxies.py, query_rewriter.py, embedding.py, reranker.py, gap_detector.py, coverage_scorer.py, memory_retriever.py, entity_extractor.py, relation_builder.py, relation_ranker.py, feedback_controller.py, etc. |
| `**kwargs: Any` | ~20+ | All engine `load`/`parse`/`convert`/`write` methods |
| `engine: Any` | ~5 | proxies.py (`KnowledgeMediator`) |
| `config: dict \| None = None` | 1 | `KnowledgeRagEngine.__init__` |
| `results: dict[str, Any]` | 2 | proxies.py `query_all`, `get_model_info` |

### `isinstance` chains

- `ml_mining/engine.py:133-175` — Auto-detect parser from bytes content: checks bytes headers, tries `onnx`, `pickle`, `torch` in sequence (6 branches)
- `entity_extractor.py:75-81` — LLM interface dispatch (`complete`, `generate`, `ainvoke`)
- `relation_builder.py:108-114` — Same LLM dispatch pattern
- `proxies.py:25-26, 31-32, 37-38, 43-44` — Duck-typing `hasattr` checks for `query`, `search`, `ingest`
- `embedding.py:28-38` — Duck-typing `hasattr` for `aembed`, `embed`, `encode`, `__call__`

### `dict[str, Any]` patterns

| File | Purpose |
|------|---------|
| `proxies.py:71` | `query_all` result aggregation |
| `rag/models.py:9` | Document metadata bags |
| `retrieval/retriever_result.py:15` | `meta` bag on every result |
| `ml_mining/engine.py:291` | `get_model_info` output |
| `semantic_graph/engine.py:323,352` | `get_statistics`, `get_metadata` output |
| `research/memory/reasoning/reasoning_event.py:25` | Event metadata |
| `research/evaluation/evaluation_controller.py:51` | Evaluation result |

### Migration strategy

**Priority 1 (define typed interfaces first):**
- `LLMProvider` trait in Rust — unify `complete`/`generate`/`ainvoke` variants
- `EngineConfig` struct — replace `config: dict | None`
- `RetrievalMeta` struct — replace `meta: dict[str, Any]` on `RetrievalResult`

**Priority 2 (generic graph traversal):**
- `GraphNode`/`GraphEdge`/`KnowledgeGraph` — already typed via `ksdm_models`, but instantiations use `Any`
- `AdjacencyList<K, V>` generic — replace `defaultdict(list)` patterns

---

## 2. Migration Notes — Scores (1–5)

| Component | Score | Rationale |
|-----------|-------|-----------|
| **RAG Retrieval** (vector, BM25, hybrid) | **2** | I/O bound (vector DB, document store). Python orchestration OK. |
| **RAG Reranking** | **2** | Token-overlap scoring is pure logic, but called on sequence of chunks. Lightweight. |
| **Embedding Computation** | **1** | GPU-bound via sentence-transformers / ONNX. Keep in Python. |
| **ML Mining Converters** (tree, regression, clustering, SVM, neural, preprocessing) | **4–5** | Pure computation: ONNX protobuf construction, numpy array manipulation, attribute flattening. Highest ROI for Rust. |
| **ML Mining Inference** (predict via ONNX) | **3** | ONNX runtime call — I/O to native lib. Moderate benefit. |
| **ML Mining Metrics** | **4** | Pure numpy math (accuracy, F1, MSE, R2). Straightforward Rust impl. |
| **Knowledge Graph Traversal** (BFS, shortest path, subgraph) | **4** | Graph algorithms on in-memory adjacency lists. `petgraph` ideal. |
| **Semantic Graph** (RDF parse, query) | **2** | Parser dispatch via rdflib → Python bridge. Keep in Python. |
| **Process Mining** (DMN generation, event analysis) | **2** | Logic-heavy but uses document model types. Low performance sensitivity. |
| **BI Aggregation** (parse/write 9 formats) | **1** | IO + parser dispatch. Keep in Python. |
| **Research Agent** (LLM orchestration, evaluation) | **1** | LLM-bound. Keep in Python. |
| **Query Engine** (language detection, parse/write) | **1** | String parsing, IO. Keep in Python. |
| **Reasoning Memory** (tree, events, tracing) | **2** | In-memory event store. Low performance impact. |
| **Observability** (telemetry, metrics) | **1** | Lightweight counters, IO. Keep in Python. |

### Recommendation by priority

```
RUST FIRST (score 4-5):    ML mining converters (5), ML metrics (4), graph traversal (4)
BRIDGE (score 3):          ONNX inference (3)
STAY PYTHON (score 1-2):   RAG orchestration, LLM calls, embedding, parsers, BI, research agent, observability
```

---

## 3. Ownership Map

```
                    ┌─────────────────────────────────────┐
                    │         KnowledgeMediator            │  PY (stays)
                    │  (proxy.py — routes to engines)     │
                    └──────────┬──────────────────────────┘
                               │
          ┌────────────────────┼────────────────────┬──────────────────┐
          ▼                    ▼                    ▼                  ▼
┌─────────────────┐  ┌─────────────────┐  ┌───────────────┐  ┌───────────────┐
│   QueryEngine   │  │  MlMiningEngine │  │SemanticGraph  │  │BiAggregation  │
│   (query/)      │  │  (ml_mining/)   │  │ (semantic_    │  │ (bi_aggrega-  │
│   PY — stays    │  │  PY/BRIDGE/RUST │  │  graph/)      │  │  tion/)       │
│                  │  │                 │  │ PY (stays)    │  │ PY (stays)    │
└─────────────────┘  └─────────────────┘  └───────────────┘  └───────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                       KnowledgeRagEngine                              │  PY — stays
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────────┐   │
│  │Retrieval │  │Reranking │  │Planning  │  │ResearchAgent       │   │
│  │ vector   │→│ token-   │→│ adaptive │→│ autonomous loop     │   │
│  │ BM25     │  │ overlap  │  │ heuristic│  │ graph-enhanced     │   │
│  │ keyword  │  │          │  │          │  │ summarization      │   │
│  │ hybrid   │  │          │  │          │  │ evaluation          │   │
│  └──────────┘  └──────────┘  └──────────┘  └────────────────────┘   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │Agentic   │  │Evidence  │  │Reflection│  │Learning  │            │
│  │ multi-   │→│ cluster  │→│ loop     │→│ policy   │            │
│  │ hop      │  │ (sklearn)│  │ (LLM)    │  │ (q-table)│            │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘            │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                       Graph Layer                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐   │
│  │EntityExtract │→│RelationBuild │→│GraphIndex (adj list)      │   │
│  │ LLM + regex  │  │ LLM + pattern│  │ BFS traversal            │   │  RUST
│  └──────────────┘  └──────────────┘  │ shortest path            │   │  (petgraph)
│                                       │ subgraph extraction      │   │
│  ┌──────────────┐  ┌──────────────┐  └──────────────────────────┘   │
│  │GraphTraverser│  │GraphPersist  │                                  │
│  │ (BFS)        │→│ (SQLite)     │                                  │
│  └──────────────┘  └──────────────┘                                  │
└──────────────────────────────────────────────────────────────────────┘
```

### Ownership Boundaries

| Boundary | Rust side | Python side | Mechanism |
|----------|-----------|-------------|-----------|
| Converters ↔ Engine | `fn convert(graph) -> Vec<u8>` | `MlMiningEngine.predict()` | PyO3 `#[pyclass]` exposing `convert_to_onnx` |
| Graph traversal ↔ ResearchAgent | `GraphEngine` struct with `neighbors`, `shortest_path` | `ResearchAgent.run()` calls via PyO3 | PyO3 `GraphEngine` class |
| Metrics ↔ MlMiningEngine | `MetricsCalculator` free functions | `MlMiningEngine.evaluate()` | PyO3 module `knowledge_ml_metrics` |
| Vector search ↔ Retrieval pipeline | ANN index (Rust via `kiddo`/`instant-distance`) | `VectorRetriever.search()` | PyO3 bridge to existing vector DB |

---

## 4. PyO3 Binding Structure

### Proposed module layout

```
knowledge_engine (Python package — stays)
├── rag/                     ← stays Python
├── query/                   ← stays Python
├── bi_aggregation/          ← stays Python
├── process_mining/          ← stays Python
├── ml_mining/               ← stays Python, bridges to:
│   └── _rust/               ← PyO3 extension module
│       ├── converters/
│       │   ├── tree         ← RUST: TreeEnsembleClassifier/Regressor → ONNX protobuf
│       │   ├── regression   ← RUST: LinearClassifier/Regressor → ONNX protobuf
│       │   ├── clustering   ← RUST: KMeans centroid/Label → ONNX protobuf
│       │   ├── svm          ← RUST: SVM → ONNX protobuf
│       │   ├── neural       ← RUST: NN ops → ONNX protobuf
│       │   └── preprocessing← RUST: Scaler/Normalizer → ONNX protobuf
│       ├── metrics          ← RUST: MetricsCalculator (accuracy, f1, mse, r2, mape)
│       └── validation       ← RUST: graph validation, schema checks
├── graph/
│   └── _rust/               ← PyO3 extension module
│       ├── engine           ← RUST: GraphIndex (petgraph), BFS, shortest_path
│       └── traversal        ← RUST: multi-hop BFS traversal
└── semantic_graph/          ← stays Python
```

### Key PyO3 bindings

```rust
// ml_mining/_rust/src/converters/mod.rs
#[pyclass]
struct RustConverter {
    registry: HashMap<OpType, Box<dyn Fn(&ModelGraph) -> Vec<u8>>>,
}

#[pymethods]
impl RustConverter {
    fn can_convert(&self, graph: &PyAny) -> PyResult<bool>;
    fn convert(&self, graph: &PyAny) -> PyResult<Vec<u8>>;
}

// ml_mining/_rust/src/metrics/mod.rs
#[pyfunction]
fn calc_metrics(y_true: Vec<f64>, y_pred: Vec<f64>, metrics: Vec<String>) -> PyResult<HashMap<String, f64>>;

// graph/_rust/src/engine.rs
#[pyclass]
struct RustGraphEngine {
    index: DiGraph<GraphNode, GraphEdge>,
}

#[pymethods]
impl RustGraphEngine {
    #[new]
    fn new() -> Self;
    fn add_node(&mut self, node: GraphNode);
    fn add_edge(&mut self, edge: GraphEdge);
    fn neighbors(&self, node_id: &str, depth: usize) -> Vec<GraphEdge>;
    fn shortest_path(&self, src: &str, dst: &str) -> Option<Vec<GraphNode>>;
    fn subgraph(&self, node_ids: Vec<String>) -> KnowledgeGraph;
    fn statistics(&self) -> HashMap<String, PyObject>;
}
```

### Bridge pattern for converters

```python
# ml_mining/engine.py (modified)
from knowledge_engine.ml_mining._rust import RustConverter

class MlMiningEngine:
    def __init__(self):
        self._rust_converter = RustConverter()  # ← Rust-backed

    async def _convert_to_onnx(self) -> bytes:
        rust_bytes = self._rust_converter.convert(self._doc.model_graph)
        if rust_bytes:
            return rust_bytes
        # fallback to Python-only conversion for unhandled graph types
        return self._python_convert_to_onnx()
```

---

## 5. Libraries Analysis

| Python Library | Rust Equivalent | Migration Viability | Notes |
|---------------|-----------------|---------------------|-------|
| `sklearn` (KMeans) | `linfa` (clustering) | Medium | Used only in `evidence_clusterer.py`. Could extract cluster labels in Python and pass to Rust. |
| `sklearn` (model parse) | None (PyO3 bridge) | Low | `SklearnParser` reads pickle format. Keep in Python. |
| `onnxruntime` | `ort` (Rust crate) | Medium | `MlMiningEngine.predict()` calls ONNX session. Could pass bytes to Rust `ort` session, but Python bridge to already-loaded session is simpler. |
| `onnx` (model builder) | `oxiri` / build ONNX protobuf manually | High | **Primary Rust target.** Converters already just build protobuf bytes. Use `prost` to construct ONNX proto in Rust. `onnx` crate's `helper::make_node` is trivial to replicate. |
| `rdflib` | `sophia_rs` / `oxrdf` | Medium | `RdfParser` uses `rdflib` to parse Turtle. `sophia_rs` can parse RDF in Rust. But parser is called via sync `run_in_executor` — low perf gain. |
| `networkx` | `petgraph` | High | **Primary Rust target.** `GraphIndex`, `MemoryGraphStore`, `SemanticGraphEngine` all do BFS/adjacency — natural fit for `petgraph::DiGraph`. |
| `sentence-transformers` | None | None | GPU-bound Python. Keep as-is. Bridge via PyO3 to pass text, receive vectors. |
| `langchain` / `llama-index` | None | None | Python-only orchestration. Keep. |
| `numpy` | `ndarray` (Rust) | High | Used in `ml_mining/engine.py` for predict input, `metrics.py` for calculations. Rust `ndarray` + `sprs` can replace. |
| `torch` (retriever trainer) | `candle` / `tch-rs` | Low | `RetrieverTrainer` uses tiny loss computation. Keep in Python. |
| `fastapi` / `websockets` | `actix-web` / `axum` | Low | Dashboard API server. Keep in Python — not a hot path. |
| `sqlite3` (graph_persistence) | `rusqlite` | Medium | `GraphPersistence` uses SQLite for node/edge storage. Trivial Rust migration but low performance impact. |
| `psutil` | None | N/A | `MemoryUsageTracker.` Keep in Python. |
| `asyncio` | `tokio` | N/A | Orchestration async. Keep in Python — use `pyo3-asyncio` for calling Rust from async Python. |

### Library Replacements Priority

```
HIGH (directly replace):   numpy → ndarray, networkx → petgraph, onnx → prost+protobuf
MEDIUM (bridge):           sklearn (clustering) → linfa, onnxruntime → ort, sqlite3 → rusqlite
LOW (keep Python):         sentence-transformers, langchain, torch, fastapi, rdflib, psutil
```

---

## 6. Performance Hot Paths

### Hot Path #1: Embedding Search (ANN)
- **Location**: `rag/retrieval/vector_retriever.py:17-40`
- **Operation**: `embedding_model.embed_one(query)` → `vector_db.query(vector=embedding, top_k=top_k)`
- **Boundary**: I/O (network call to vector DB) + CPU (embedding model forward pass)
- **Migration**: **Keep in Python.** Embedding is GPU-bound. Vector DB query is network I/O. No Rust benefit.

### Hot Path #2: BM25 Scoring
- **Location**: `rag/retrieval/bm25_retriever.py:54-85`
- **Operation**: Tokenize query → iterate all chunks → compute BM25 TF-IDF scores → sort
- **Boundary**: CPU (string tokenization, math). O(N * M) where N=docs, M=query terms.
- **Migration**: **Medium benefit.** Could port to Rust via `tantivy` (full-text search) for persistent BM25 index. Python in-memory version is adequate for <100K docs.

### Hot Path #3: Graph Traversal (BFS)
- **Location**: `graph/research/graph_index.py:52-71`, `semantic_graph/engine.py:235-271,273-308`
- **Operation**: BFS neighbor retrieval, shortest path BFS
- **Boundary**: CPU + memory (adjacency dict traversal)
- **Migration**: **High benefit.** `petgraph` BFS is 10-50x faster than Python dict-based BFS on large graphs.

### Hot Path #4: ONNX Converter — Tree Ensemble
- **Location**: `ml_mining/converters/tree_converter.py:67-281`
- **Operation**: Flatten tree nodes → map attributes → build ONNX protobuf
- **Boundary**: CPU (attribute extraction, protobuf serialization)
- **Migration**: **Highest benefit.** Pure computation, no external deps. Rust protobuf building with `prost` eliminates Python overhead.

### Hot Path #5: ONNX Converter — Neural Network
- **Location**: `ml_mining/converters/neural_converter.py:76-151`
- **Operation**: Iterate NN nodes → map OpType to ONNX op → build protobuf
- **Boundary**: CPU
- **Migration**: **High benefit.** Same pattern as tree converter.

### Hot Path #6: Similarity Scoring
- **Location**: `rag/reranking/reranker.py:17-31`, `rag/compression/embedding_compressor.py:38-41`
- **Operation**: Token overlap, cosine similarity via numpy
- **Boundary**: CPU (string ops, math)
- **Migration**: **Medium benefit.** Rust `ndarray` dot product faster than numpy for small arrays. But volume is low (top-k chunks, k ≤ 20).

### Hot Path #7: Fused Weighted Scoring
- **Location**: `rag/retrieval/hybrid_retriever_super.py:120-185`
- **Operation**: Normalize → softmax → fusion MLP → graph boost → rerank → sort
- **Boundary**: CPU
- **Migration**: **Low benefit.** Pipeline is small and runs once per query.

### Hot Path Summary

```
Path                   Type       Volume      Rust ROI
─────────────────────────────────────────────────────────
BM25 scoring           CPU/O(N)   per query   Medium
Graph BFS              CPU        per query   HIGH
Tree converter         CPU        per model   HIGHEST
Neural converter       CPU        per model   HIGH
Metrics calc           CPU        per eval    HIGH
Reranker scoring       CPU        per query   Medium
Similarity / dot prod  CPU        per query   Medium
Fusion pipeline        CPU        per query   Low
Embedding search       GPU/IO     per query   None
ONNX inference         Native     per query   None
```

---

## 7. Error Handling

### Current patterns

| Pattern | Count | Examples |
|---------|-------|----------|
| `raise ValueError(...)` | 20+ | `chunking.py:12-16`, `embedding.py:19`, `embedding.py:40`, `rag/planner/adaptive_planner.py` (none), `ml_mining/engine.py:129-131,312,362,423` |
| `raise RuntimeError(...)` | 10+ | All sync-vs-async guard methods in engines |
| `raise LookupError(...)` | 2 | `knowledge_rag_engine.py:332,340` |
| `raise TypeError(...)` | 5 | `embedding.py:40`, `entity_extractor.py:82`, `relation_builder.py:115` |
| `try/except Exception: pass` or `continue` | 15+ | `query_rewriter.py` (LLM parse), `entity_extractor.py:41-43` (JSON parse), `relation_builder.py:38-41` (JSON parse), `hybrid_retriever_plus.py:51-53,65-68` (LLM), `bi_aggregation/engine.py:120-122` (parser detect) |
| `logger.warning(...)` | 1 | `proxies.py:80` |
| `hasattr` guard (duck-typing) | 15+ | All `_complete()` style dispatchers, `proxies.py` ensure pattern |
| Sync/async duality guard | 8 | Every engine: `try: asyncio.get_running_loop() except RuntimeError: return asyncio.run(...)` |

### Anti-patterns found

1. **Blind except** → `ml_mining/converters/clustering_converter.py:115-116`: `try: onnx.checker.check_model(model_def) except Exception: pass`. Silently swallows model validation failures.
2. **JSON parse with bare except** → `entity_extractor.py:41-43, relation_builder.py:38-41, answer_planner.py:61-63`: `try: json.loads(response) except Exception: return []`. Swallows malformed LLM output.
3. **Silent fallback** → `hybrid_retriever_super.py:117`: `except Exception: return {"vector": 0.5, "keyword": 0.3, "graph": 0.2}`. LLM errors silently ignored.
4. **Atomically wrong sync/async guards** → Every engine's `load()` / `convert()` / `write()` method implements the same pattern. Error-prone in nested async contexts.
5. **`_to_text` / `_to_evidence` with `getattr` chains** → 10+ places retrieve `.chunk.text` from heterogeneous result types. Silent on missing attributes.

### Rust error handling strategy

```rust
// Use Result<T, RustConversionError> everywhere
#[derive(Debug, thiserror::Error)]
pub enum RustConversionError {
    #[error("No converter registered for graph type")]
    NoConverter,
    #[error("Missing required attribute: {0}")]
    MissingAttribute(String),
    #[error("ONNX validation failed: {0}")]
    OnnxValidation(String),
    #[error("Protobuf error: {0}")]
    Protobuf(#[from] prost::EncodeError),
}

// No bare unwrap() — use anyhow context or thiserror
pub fn convert(graph: &ModelGraph) -> Result<Vec<u8>, RustConversionError> {
    let converter = find_converter(graph)
        .ok_or(RustConversionError::NoConverter)?;
    converter.convert(graph)
}

// Attribute access — use Option and return explicit error
impl ModelNode {
    fn require_float_attr(&self, name: &str) -> Result<f64, RustConversionError> {
        self.attributes.get(name)
            .and_then(|a| a.float_value)
            .ok_or_else(|| RustConversionError::MissingAttribute(name.to_string()))
    }
}

// PyO3 boundary — convert Rust errors to Python exceptions
impl From<RustConversionError> for PyErr {
    fn from(err: RustConversionError) -> PyErr {
        match err {
            RustConversionError::NoConverter => PyValueError::new_err(err.to_string()),
            RustConversionError::MissingAttribute(_) => PyValueError::new_err(err.to_string()),
            RustConversionError::OnnxValidation(_) => PyRuntimeError::new_err(err.to_string()),
            RustConversionError::Protobuf(_) => PyValueError::new_err(err.to_string()),
        }
    }
}
```

### Sync/async boundary recommendation

Replace the error-prone sync/async duality pattern with:

```rust
// Rust side — always async via PyO3 + pyo3-asyncio
#[pyfunction]
fn py_convert(graph: &PyAny) -> PyResult<Vec<u8>> {
    // Called from async Python — no sync fallback needed
    convert(&deserialize_graph(graph)?)
}
```

Python side eliminates the `try: asyncio.get_running_loop() except RuntimeError:` pattern entirely when calling into Rust.
