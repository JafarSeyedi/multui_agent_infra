# Migration Report: Document Chunking + Embedding

**Directories analyzed:**
- `engines/document/chunking/` (4 files)
- `engines/document/embedding/` (3 files)

**Date:** 2026-06-13
**Type:** Read-only analysis

---

## 1. Pre-Refactor Analysis

### Chunking (`engines/document/chunking/`)

| File | Purpose | Lines |
|------|---------|-------|
| `__init__.py` | Re-exports `BaseChunker`, `ChunkingConfig`, `ChunkingResult`, `RecursiveTextChunker` | 12 |
| `base.py` | `BaseChunker` ABC — single async method `chunk_document(document, config?) → list[ChunkRecord]` | 20 |
| `models.py` | `ChunkingConfig` (pydantic) with defaults: size=800, overlap=120, min=120, separators=`["\n\n", "\n", ". ", " "]`, keep_paragraph_boundaries=True, include_page_markers=True. `ChunkingResult` wraps `list[ChunkRecord]`. | 19 |
| `recursive_chunker.py` | `RecursiveTextChunker` — recursive descent through separators, segment merging with overlap, SHA1-based chunk ID derivation. | 105 |

**Chunking algorithm (RecursiveTextChunker):**
1. Strip raw text from `BaseDocument.raw_text`
2. `_split_text`: recursively split by separator hierarchy (deeper separators for sub-segments). Falls back to `_hard_split` (fixed-width) if no separators match.
3. `_merge_segments`: recombine split segments respecting `chunk_size`, `chunk_overlap`, `min_chunk_size`, and `keep_paragraph_boundaries`.
4. `_build_chunk`: locate char offsets via `str.find()`, compute SHA1 digest of `"{document_id}:{index}:{text}"`, construct `ChunkRecord`.

### Embedding (`engines/document/embedding/`)

| File | Purpose | Lines |
|------|---------|-------|
| `__init__.py` | Re-exports `EmbeddingProvider`, `DocumentEmbeddingService`, `HashEmbeddingProvider` | 9 |
| `base.py` | `EmbeddingProvider` ABC — `embed_texts(texts) → list[list[float]]`, `embed_query(text) → list[float]` (default delegates to embed_texts) | 17 |
| `service.py` | `HashEmbeddingProvider` (dev/test fallback) and `DocumentEmbeddingService` (batching orchestrator) | 53 |

**Embedding flow (DocumentEmbeddingService):**
1. Accepts `Sequence[ChunkRecord]`
2. Batches chunks by `batch_size` (default 32)
3. Delegates each batch to `provider.embed_texts()`
4. Returns `dict[str, list[float]]` mapping `chunk_id → embedding_vector`

### `Any` usage

| Location | Usage | Risk |
|----------|-------|------|
| `ChunkRecord.metadata` | `dict[str, Any]` | Low — generic metadata bag |
| `ChunkingResult` (implied) | inherits `Any` in metadata | Low |
| `BaseDocument.metadata` | `dict[str, Any]` | Low |
| `DocumentIngestionResult.metadata` | `dict[str, Any]` | Low |

No unsafe `Any` casts in hot paths.

### Embedding models

No real embedding model is implemented in this directory. `HashEmbeddingProvider` is explicitly a deterministic fallback for tests/dev (SHA256 → dimension bucket → L2-normalize). The real sentence-transformers integration would live elsewhere (e.g., a `SentenceTransformerEmbeddingProvider` that this project hasn't written yet).

---

## 2. Rust Candidate Scoring (1–5)

| Component | Score | Rationale |
|-----------|-------|-----------|
| `RecursiveTextChunker._split_text` | **5** | Pure string splitting, recursion, separator iteration — CPU-bound, no Python-specific dependencies. Ideal for Rust rewrite. Could 3–10x throughput. |
| `RecursiveTextChunker._merge_segments` | **5** | String concatenation, overlap slice logic, loop-heavy. Same reasoning as split. Exactly the kind of hot loop Rust excels at. |
| `RecursiveTextChunker._build_chunk` | **4** | SHA1 hashing via `hashlib`, string find, construction of `ChunkRecord`. SHA1 is trivially replaceable with Rust's `sha1` crate. Char-offset search is a `find()` call — easy. |
| `RecursiveTextChunker.chunk_document` | **4** | Orchestration of above three methods. Async interface — needs PyO3 async bridge or `sync` + `run_in_executor`. |
| `HashEmbeddingProvider.embed_texts` | **3** | SHA256 hashing + L2 normalization. Good Rust candidate but it's a *fallback* provider — not the real production path. Only migrate if the real provider also moves. |
| `DocumentEmbeddingService.embed_chunks` | **2** | Pure orchestration — batched iteration + delegating to provider. The batching itself is trivial. Only migrate if the provider also migrates. |
| `EmbeddingProvider` ABC | **1** | Abstract interface. Stays in Python as trait bound for PyO3. |

**Net recommendation:** Migrate the entire chunking engine to Rust (score 4–5). Keep embedding as Python with PyO3 callouts for the hot path, unless sentence-transformers gains a Rust backend.

---

## 3. Ownership Map: Text → Chunks → Embeddings Data Flow

```
BaseDocument (raw_text: str)
    │
    ▼
RecursiveTextChunker.chunk_document(document, config?)
    │
    ├─ _split_text(text, separators, max_size) → list[str]
    │   └─ recursion: separators[0] → separators[1:] → _hard_split()
    │
    ├─ _merge_segments(segments, config) → list[str]
    │   └─ overlap logic, paragraph boundary preservation, min_chunk_size guard
    │
    └─ _build_chunk(document, index, text, full_text) → ChunkRecord
        ├─ SHA1(document_id:index:text) → chunk_id
        ├─ str.find(text) → start_char, end_char
        └─ metadata (source_format, chunker name, chunk_size)
    │
    ▼
list[ChunkRecord]
    │  Each ChunkRecord carries:
    │   - chunk_id, document_id, index
    │   - text, token_count_estimate
    │   - start_char, end_char
    │   - embeddings: list[EmbeddingRecord]  (empty at chunking time)
    │
    ▼
DocumentEmbeddingService.embed_chunks(chunks)
    │
    ├─ _batched(chunks, batch_size=32) → batches
    │
    └─ provider.embed_texts([chunk.text for chunk in batch]) → list[list[float]]
        │
        ▼
    dict[str, list[float]]       # chunk_id → embedding_vector
        │
        ▼
    ChunkRecord.embeddings populated later by caller
```

**Key data coupling:**
- `ChunkRecord.text` is the input to `embed_texts`
- `ChunkRecord.chunk_id` is the key in the returned dict
- Embedded chunks feed into `EmbeddingRecord` (document_id, chunk_id, vector, dim, provider)

---

## 4. Suggested PyO3 Binding

### Architecture

```
┌──────────────────────────────────────┐
│  Python Layer                         │
│                                      │
│  RecursiveTextChunker (thin wrapper) │
│  DocumentEmbeddingService (untouched)│
└──────────┬───────────────────────────┘
           │ PyO3 #[pyclass]
           ▼
┌──────────────────────────────────────┐
│  Rust Core (libchunker)              │
│                                      │
│  ChunkerConfig                       │
│  RecursiveChunker::chunk_document()  │
│    ├─ split_text()                   │
│    ├─ merge_segments()              │
│    └─ build_chunk()                 │
│                                      │
│  ChunkResult (pyclass)               │
└──────────────────────────────────────┘
```

### Suggested API

```rust
// lib.rs — pyo3 bindings

#[pyclass]
struct ChunkerConfig {
    chunk_size: usize,
    chunk_overlap: usize,
    min_chunk_size: usize,
    separators: Vec<String>,
    keep_paragraph_boundaries: bool,
}

#[pyclass]
struct ChunkResult {
    #[pyo3(get)]
    chunk_id: String,
    #[pyo3(get)]
    document_id: String,
    #[pyo3(get)]
    index: usize,
    #[pyo3(get)]
    text: String,
    #[pyo3(get)]
    token_count_estimate: usize,
    #[pyo3(get)]
    start_char: usize,
    #[pyo3(get)]
    end_char: usize,
    #[pyo3(get)]
    metadata: HashMap<String, String>,
}

#[pyfunction]
fn chunk_document(
    raw_text: &str,
    document_id: &str,
    config: &ChunkerConfig,
) -> Vec<ChunkResult> { ... }
```

### Python-side wrapper

```python
class RustRecursiveChunker(BaseChunker):
    def __init__(self):
        self._inner = libchunker.chunk_document

    async def chunk_document(self, document, config=None):
        effective = config or ChunkingConfig()
        # run_sync to avoid blocking event loop
        loop = asyncio.get_running_loop()
        chunks = await loop.run_in_executor(
            None, self._inner, document.raw_text or "",
            document.document_id, _to_rust_config(effective)
        )
        return [_to_python_chunk(c, document) for c in chunks]
```

### Keep as Python (no migration)
- `EmbeddingProvider` abstract class — interface only
- `DocumentEmbeddingService` — stays Python, calls into provider (which may be Python sentence-transformers)
- `HashEmbeddingProvider` — low value to migrate (test-only, trivial)

---

## 5. Libraries Analysis

### Current Python dependencies

| Library | Used In | Purpose | Rust Equivalent |
|---------|---------|---------|-----------------|
| `hashlib` (stdlib) | `recursive_chunker.py:90`, `service.py:24` | SHA1 for chunk IDs, SHA256 for hash embedding | `sha1` / `sha2` crates |
| `math` (stdlib) | `service.py:28-31` | L2 normalization (`sqrt`, `sum`) | `f32::sqrt`, iterator `.sum()` |
| `pydantic` | `models.py`, `ingestion_models.py` | Config/data models with validation | Not needed — `#[pyclass]` or `serde` |
| `abc` (stdlib) | `base.py` (both dirs) | Abstract base classes | Rust traits |
| `asyncio` (stdlib) | chunk_document is `async` | Async orchestration | `pyo3-asyncio` or `run_in_executor` |

### Sentence-transformers gap

No actual embedding model is instantiated here. `HashEmbeddingProvider` is a stub. A real `SentenceTransformerEmbeddingProvider` would depend on:
- `sentence-transformers` (PyTorch-backed, Python-only)
- `torch` (GPU inference)

**Migration constraint:** Sentence-transformers has no Rust native equivalent. The embedding provider abstraction *must* remain in Python. If you want GPU inference in Rust, options are:
- `candle` (HuggingFace Rust framework) — supports BERT-family models
- `ort` (ONNX Runtime bindings for Rust) — export SBERT to ONNX
- `tract` — lighter-weight inference

This is high-risk and low-priority. Recommend keeping embedding in Python.

### Chunking libraries (none used)

The chunker uses zero external libraries — pure Python string operations. This makes migration trivial: no dependency translation needed.

---

## 6. Performance Hot Paths

### Hot path 1: `RecursiveTextChunker._split_text` (lines 32–55)

**Why hot:** Recursive descent through document text. Each level of recursion re-splits text by separators. Worst case: O(n × s) where n is text length and s is separator depth. String splitting and concatenation in a loop.

**Rust advantage:**
- `str::split()` is a lazy iterator (no intermediate allocations like Python)
- `String` concatenation is explicit and can reuse capacity
- Recursion depth is stack-safe in Rust (small, fixed depth) or easily converted to iterative

**GPU relevance:** None. This is pure CPU-bound string processing.

### Hot path 2: `RecursiveTextChunker._merge_segments` (lines 60–85)

**Why hot:** Iterates all segments, concatenates strings, slices overlap windows. String slicing (`current[-config.chunk_overlap:]`) creates new strings in Python — allocation-heavy.

**Rust advantage:**
- Slice notation (`&str[current.len()-overlap..]`) is zero-copy
- `String` can be built with `push_str()` and `reserve()` to minimize reallocation
- Overlap logic can use `split_off()` or range slicing without copy

**GPU relevance:** None.

### Hot path 3: `RecursiveTextChunker._build_chunk` (lines 87–105)

**Why hot:** Called once per chunk. SHA1 hash + `str.find()` for char offsets.

**Rust advantage:**
- `sha1` crate is as fast as `hashlib` (typically faster due to SIMD)
- `str.find()` is same operation, similar performance
- `ChunkRecord` construction avoids Python object overhead

### Hot path 4: `HashEmbeddingProvider._embed_single` (lines 21–31)

**Why hot:** Called per text. Lowercases, splits, iterates tokens, SHA256 hash, L2 normalization.

**Rust advantage:**
- Token iteration without allocation (`text.split_whitespace()`)
- SHA256 via `sha2` crate
- Math operations with `f32` (explicit, no boxing)
- Normalization loop is trivially parallelizable

**GPU relevance:** None (this is a hash-based fallback, not neural).

### Hot path 5: `DocumentEmbeddingService.embed_chunks` (lines 43–49)

**Why hot:** Parallelism opportunity — each batch's `provider.embed_texts()` call is independent.

**GPU relevance:** If provider is sentence-transformers, this is **GPU-bound**. Batching (size=32) amortizes GPU launch overhead. The batching logic itself is trivial (slicing). NOT a Rust candidate — the latency is dominated by GPU inference.

### GPU vs CPU recommendation

| Path | Bound | Migrate? |
|------|-------|----------|
| `_split_text` | CPU | ✅ Yes |
| `_merge_segments` | CPU | ✅ Yes |
| `_build_chunk` | CPU | ✅ Yes |
| `_embed_single` (hash) | CPU | ⚠️ Low priority (test-only) |
| `embed_chunks` (real provider) | GPU | ❌ No — keep in Python |

---

## 7. Error Handling

### Current state

| Scenario | Current handling | Gap |
|----------|-----------------|-----|
| `document.raw_text` is `None` or empty | Returns `[]` (line 21-22) | Silent — caller gets empty list |
| `separators` exhausted | Falls to `_hard_split` (line 36, 41) | Graceful degradation, no error |
| `str.find()` returns -1 | `max(-1, 0)` → start=0, end=0 (line 88-89) | Silent — incorrect offsets for missing text |
| Empty segment after strip | Skipped (line 65-66) | Acceptable |
| Overlap > current chunk length | `current[-config.chunk_overlap:]` wraps silently (line 76) | Returns entire string — acceptable but undocumented |
| Negative batch_size | `ValueError` raised (line 39) | Clear |
| `HashEmbeddingProvider.norm == 0` | Returns unnormalized zero vector (line 29-30) | Degenerate case — acceptable for test code |

### Rust migration error strategy

```rust
#[derive(Debug, thiserror::Error)]
pub enum ChunkError {
    #[error("empty document text")]
    EmptyDocument,
    #[error("no valid separators and text exceeds max_size")]
    Overflow,
}

pub fn chunk_document(
    raw_text: &str,
    document_id: &str,
    config: &ChunkerConfig,
) -> Result<Vec<ChunkResult>, ChunkError> {
    let text = raw_text.trim();
    if text.is_empty() {
        return Err(ChunkError::EmptyDocument);  // explicit vs silent []
    }
    // ...
}
```

### Error handling recommendations

1. **Replace silent `[]` return** with a typed error enum for empty documents
2. **Replace silence on `str.find() == -1`** with a checked offset calculation or fallback to `0`
3. **Use Rust's `Result` type** — PyO3 converts `Err` to Python exceptions automatically
4. **Keep `batch_size <= 0` guard** in Python (`DocumentEmbeddingService`) — clean
5. **HashEmbeddingProvider degenerate norm** — acceptable; no change needed

---

## Summary

**Immediate Rust migration (high ROI):**
- `recursive_chunker.py` → Rust crate `libchunker` via PyO3
- `ChunkingConfig` → `#[pyclass]` in Rust
- `ChunkRecord` construction → `ChunkResult` in Rust

**Keep in Python:**
- `EmbeddingProvider` ABC — abstraction boundary
- `DocumentEmbeddingService` — thin orchestration, GPU-bound
- `HashEmbeddingProvider` — low-value test fallback
- Real sentence-transformers provider — must stay Python (or ONNX→Rust path, high effort)

**Data flow boundary:**
```
Python: BaseDocument.raw_text
    → [PyO3] → Rust: chunk_document() → Vec<ChunkResult>
    → [PyO3] → Python: list[ChunkRecord]
    → Python: DocumentEmbeddingService (GPU/CPU)
    → Python: dict[chunk_id → embedding]
```
