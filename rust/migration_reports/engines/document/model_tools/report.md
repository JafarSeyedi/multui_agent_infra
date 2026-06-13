# Rust Migration Report: `engines/document/model_tools`

**Date:** 2026-06-13
**Analyzed by:** OpenCode

---

## 1. Pre-Refactor Analysis

### Skeleton Files (Empty Stubs)

The majority of files in this package are **empty stubs** (0 bytes). These represent unimplemented placeholders for future work:

| Path | Status |
|------|--------|
| `__init__.py` | Empty |
| `configuration.py` | Empty |
| `diff_engine.py` | Empty |
| `diff_sql_writer.py` | Empty |
| `format_converters/__init__.py` | Empty |
| `format_converters/converter_base.py` | Empty |
| `format_converters/docx_to_pdf.py` | Empty |
| `format_converters/docx_to_pptx.py` | Empty |
| `format_converters/generic_converter.py` | Empty |
| `format_converters/json_to_docx.py` | Empty |
| `format_converters/json_to_pdf.py` | Empty |
| `format_converters/markdown_to_docx.py` | Empty |
| `format_converters/markdown_to_pdf.py` | Empty |
| `format_converters/pdf_to_docx.py` | Empty |
| `format_converters/ppt_to_docx.py` | Empty |
| `format_converters/ppt_to_pdf.py` | Empty |
| `format_converters/xlsx_to_docx.py` | Empty |
| `format_converters/xlsx_to_pdf.py` | Empty |
| `format_converters/xlsx_to_ppt.py` | Empty |
| `model_standard_converters/csdm_to_usdm_adapter.py` | Empty |
| `model_standard_converters/esdm_to_usdm_adapter.py` | Empty |
| `model_standard_converters/psdm_to_usdm_adapter.py` | Empty |
| `model_standard_converters/usdm_to_pdf_adapter.py` | Empty |
| `report_generators/__init__.py` | Empty |
| `report_generators/data_*_report_generator.py` (12 files) | Empty |
| `report_generators/schema_report_generator.py` | Empty |
| `report_generators/service_report_generator.py` | Empty |

### Populated Files (4 converters + 1 init)

Only 4 Python files contain real implementation logic:

1. **`ksdm_bi_converter.py`** — `BiAggregationConverter` (38 lines)
2. **`ksdm_to_dsdm_converter.py`** — `KsdmToDsdmConverter` (272 lines, the largest)
3. **`ksdm_to_rdf_converter.py`** — `KsdmToRdfConverter` (213 lines)
4. **`msdm_to_ksdm_graph_converter.py`** — `MsdmToKsdmGraphConverter` (122 lines)
5. **`__init__.py`** — Exports 4 converters from `model_standard_converters`

### `Any` Usage

Minimal. Used only in method signatures for property dict types:
- `dict[str, Any]` for graph node/edge properties (KSDM models)
- `value: Any` on DSDM `DataValue`
- Type erasure in `BiAggregationConverter` via `cls: Any = writer_map.get(target_format)`

### Converter Patterns

All populated converters use **staticmethod-only classes** with no inheritance from `converter_base.py` (which is empty). No abstract base classes. No Protocol/ABC. No registry pattern.

**Pattern summary:**
```
class XConverter:
    @staticmethod
    def convert_a_to_b(...) -> ResultType:
        ...
    @staticmethod
    def convert_b_to_a(...) -> SourceType:
        ...
```

---

## 2. Migration Notes: Rust Candidate Scoring (1-5)

| Module | Score | Rationale |
|--------|-------|-----------|
| `ksdm_bi_converter.py` | **3** | Thin dispatch layer. Would be a simple `match` in Rust. Low complexity but tightly coupled to async Python writers via `asyncio.run()`. |
| `ksdm_to_dsdm_converter.py` | **5** | Highest-impact candidate. Deep tree traversal, nested loops over nodes/edges/properties. 272 lines of pure data transformation with no Python-ecosystem dependencies. Type mapping (`_type_of`) maps cleanly to Rust enums. |
| `ksdm_to_rdf_converter.py` | **4** | String-heavy IRI construction, RDF triple generation. No rdflib dependency — uses custom `RdfTriple`/`RdfGraph` models. String formatting for Turtle-style literals would benefit from Rust's `format!`. Reified RDF statements are pure logic. |
| `msdm_to_ksdm_graph_converter.py` | **4** | Pydantic model field access + validation loops. Clean data flow. Entity→GraphNode/Edge transformation, constraint checking. No Python-specific patterns beyond enum matching. |
| `format_converters/` (all stubs) | **1** | Empty files. No migration value until implemented. |
| `report_generators/` (all stubs) | **1** | Empty files. No migration value until implemented. |
| `csdm_to_usdm_adapter.py` | **1** | Empty stub. |
| `esdm_to_usdm_adapter.py` | **1** | Empty stub. |
| `psdm_to_usdm_adapter.py` | **1** | Empty stub. |
| `usdm_to_pdf_adapter.py` | **1** | Empty stub. |

**Priority order for migration:** `ksdm_to_dsdm` → `ksdm_to_rdf` → `msdm_to_ksdm_graph` → `ksdm_bi_converter` → (stubs when implemented)

---

## 3. Ownership Map: Data Flow Through Converters

```
MSDMDocument ──→ MsdmToKsdmGraphConverter ──→ KnowledgeGraph (template)
                                                     │
                     ┌───────────────────────────────┤
                     │                               │
                     ▼                               ▼
          KsdmToDsdmConverter              KsdmToRdfConverter
                     │                               │
                     ▼                               ▼
              DataDocument                      RdfGraph
              (DSDM tree)                   (triple list)
                     │
                     │
                     ▼
          DataDocument.infer_msdm()
                     │
                     ▼
              MSDMDocument (round-trip)

UnifiedBiAggregationDocument ──→ BiAggregationConverter ──→ bytes
                                     │ dispatch to:
                                     ├── CwmWriter
                                     ├── MondrianSchemaWriter
                                     ├── XmlaWriter
                                     ├── TmslWriter
                                     ├── CdmWriter
                                     ├── CalciteWriter
                                     ├── AwxmlWriter
                                     ├── SapCdsWriter
                                     └── CognosFmfWriter
```

**Empty adapter slots (named but unimplemented):**
- `csdm_to_usdm_adapter.py` — CSDM (CAD) → USDM (text)
- `esdm_to_usdm_adapter.py` — ESDM (spreadsheet) → USDM (text)
- `psdm_to_usdm_adapter.py` — PSDM (presentation) → USDM (text)
- `usdm_to_pdf_adapter.py` — USDM (text) → PDF

**Empty format converters (all unimplemented):**
- Between .docx, .pdf, .pptx, .xlsx, .json, .md — 13 files, all empty

---

## 4. Suggested PyO3 Binding

### Strategy

Since most files are empty stubs, the near-term strategy should be:

1. **Direct Rust rewrite** of the 4 populated converters as a Rust crate `model_tools_rs`
2. **PyO3 bindings** only for the Python-facing entry points, primarily `BiAggregationConverter` which must integrate with Python async writers

### PyO3 Binding Surface

```text
┌─────────────────────────────────────────────────┐
│                    Python                        │
│  BiAggregationConverter.convert()                │
│         │  (PyO3 bridge)                         │
│         ▼                                        │
│  rust.model_tools                                │
│  ┌─────────────────────────────────────────────┐ │
│  │  bi_converter::convert(doc, target_format)  │ │
│  │     → delegates to Python writers via        │ │
│  │       PyO3 call (asyncio.run equivalent)     │ │
│  │                                              │ │
│  │  ksdm_to_dsdm::knowledge_graph_to_data(...)  │ │
│  │  ksdm_to_dsdm::data_document_to_kg(...)      │ │
│  │                                              │ │
│  │  ksdm_to_rdf::knowledge_graph_to_rdf(...)    │ │
│  │  ksdm_to_rdf::rdf_to_knowledge_graph(...)    │ │
│  │                                              │ │
│  │  msdm_to_ksdm::msdm_to_kg_template(...)      │ │
│  │  msdm_to_ksdm::validate_kg(...)              │ │
│  └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

### PyO3 Binding Functions

```rust
// bi_converter.rs — PyO3 only for dispatch to Python writers
#[pyfunction]
fn bi_convert(doc: PyObject, target_format: &str) -> PyResult<Vec<u8>>;

// ksdm_to_dsdm.rs — Pure Rust, no PyO3 needed beyond data access
#[pyfunction]
fn knowledge_graph_to_data_document(kg: KnowledgeGraph, ...) -> DataDocument;

// ksdm_to_rdf.rs — Pure Rust
#[pyfunction]
fn knowledge_graph_to_rdf(kg: KnowledgeGraph, ...) -> RdfGraph;

// msdm_to_ksdm_graph.rs — Pure Rust
#[pyfunction]
fn msdm_to_knowledge_graph_template(doc: MSDMDocument) -> KnowledgeGraph;
```

### Model Structs in Rust

The 4 Python model classes used (`KnowledgeGraph`, `GraphNode`, `GraphEdge`, `DataDocument`, `DataNode`, `DataValue`, `MSDMDocument`, `Entity`, `Attribute`, `ScalarType`, `DataType`, `RdfGraph`, `RdfTriple`) need Rust equivalents. These map well to Rust `struct` + `enum` patterns.

---

## 5. Libraries Analysis

### RDF Converter (rdflib → sophia_rs?)

`ksdm_to_rdf_converter.py` does **not use rdflib**. It uses custom `pydantic` models:

```python
class RdfTriple(BaseModel):
    subject: str
    predicate: str
    object_: str
    graph: str | None = None

class RdfGraph(BaseModel):
    graph_name: str | None = None
    triples: list[RdfTriple]
```

**Migration options:**
| Approach | Pros | Cons |
|----------|------|------|
| **Custom Rust structs** | No external dep; exact semantics match; full control | No SPARQL/OWL support |
| **sophia_rs** | Industry standard; supports Turtle/JSON-LD/RDF XML | Additional dependency; may be overkill for simple triple model |
| **oxrdf** (from oxigraph) | Fast triple store; SPARQL support | Heavier dependency |

**Recommendation:** Use custom Rust structs for the converter itself (matching current code), and optionally use `sophia_rs` only if RDF serialization/deserialization is needed later. The current code only constructs string-based IRIs and Turtle-style literals — no actual RDF API is used.

### Format Converters

All 13 format converter files are empty stubs. For Rust migration:
- **DOCX/PPTX/XLSX parsing**: `calamine` (xlsx), `docx-rs` (docx), or custom ZIP+XML parsing
- **PDF**: `printpdf` or `lopdf`
- **Markdown**: `pulldown-cmark`
- **JSON**: `serde_json`

Since these are not yet implemented in Python, the Rust implementation can be designed without Python parity concerns.

### BI Aggregation Writers

`BiAggregationConverter` dispatches to 9 Python writer classes (CWM, Mondrian, XMLA, TMSL, CDM, Calcite, AWXML, SAP CDS, Cognos FMF) via `asyncio.run(cls().write(doc))`. These writers are in `engines/document/writers/ksdm_writers/bi_aggregation/`. For Rust migration, each writer would need its own Rust implementation or the converter would remain a thin PyO3 bridge.

---

## 6. Performance Hot Paths: Format Conversion Loops

### `ksdm_to_dsdm_converter.py` — HOT

**`knowledge_graph_to_data_document`:**
- Outer loop: `for i, node in enumerate(kg.nodes)` — linear over N nodes
- Inner loop: `for k, v in (node.properties or {}).items()` — linear over M properties per node
- O(N × M) property flattening into DataNode tree

**`_graph_edge_to_data_node`** and **`_graph_node_to_data_node`**:
- Each creates 5+ `DataNode` children with path strings (`f"/nodes/{node_id}/..."`)
- Path construction via f-strings in Rust would be `format!()` — similar cost

**`_data_node_to_graph_node` / `_data_node_to_graph_edge`:**
- Child scanning: `for c in node.children` — linear
- `_get_properties` scans children twice (once in caller, once for properties)

**`infer_msdm` on DataDocument:**
- Recursive tree walk with entity creation for each OBJECT node
- Could be deep for deeply nested JSON/XML

### `ksdm_to_rdf_converter.py` — MEDIUM

**`knowledge_graph_to_rdf`:**
- Loop over nodes: O(N) with per-node property triple generation: O(N × M)
- Loop over edges: O(E) 
- Edge reification: O(E × P) where P = non-iri properties
- All string concatenation for IRI building

**`rdf_to_knowledge_graph`:**
- Two passes over all triples (O(T) each) — first to collect subjects/objects, second to build nodes
- Edge candidate filtering: O(T) with string operations

### `msdm_to_ksdm_graph_converter.py` — LOW

- Single pass over entities (O(E)) — negligible
- Validation is O(N × A) where A = attributes per entity

### `ksdm_bi_converter.py` — NEGLIGIBLE

- Dictionary lookup + one async call. No loops.

---

## 7. Error Handling

### Current Python Error Handling

| Converter | Error Approach |
|-----------|---------------|
| `BiAggregationConverter` | `ValueError(f"Unknown target format: {target_format}")` — single error case |
| `KsdmToDsdmConverter` | **No explicit error handling.** `_get_scalar` returns `None` silently. `_data_node_to_graph_node`/`_data_node_to_graph_edge` return `None` on kind mismatch. Silent `None` propagation. |
| `KsdmToRdfConverter` | **No error handling.** Assumes input is valid. String formatting failures would raise unhandled exceptions. |
| `MsdmToKsdmGraphConverter` | Returns `list[str]` errors from validation methods. Best error pattern in the codebase. |

### Critical Gaps

1. **No custom exception types** — all converters rely on built-in `ValueError` or implicit panics
2. **No Result types** — validation returns error lists, but no typed error enums
3. **Silent None propagation** — `_get_scalar` can return `None` which becomes `""` in callers
4. **No input validation** — no preconditions checked before conversion

### Rust Migration Recommendations

```rust
// Define error types
#[derive(Debug, thiserror::Error)]
pub enum ConversionError {
    #[error("Unknown target format: {0}")]
    UnknownFormat(String),
    #[error("Missing required field '{field}' on node '{node_id}'")]
    MissingField { field: String, node_id: String },
    #[error("Type mismatch: expected {expected}, got {actual}")]
    TypeMismatch { expected: String, actual: String },
    #[error("Invalid RDF value: {0}")]
    InvalidRdfValue(String),
    #[error("Internal error: {0}")]
    Internal(String),
}

// Use Result<T, ConversionError> consistently
pub fn knowledge_graph_to_data_document(kg: &KnowledgeGraph, ...) -> Result<DataDocument, ConversionError>;
pub fn data_document_to_knowledge_graph(doc: &DataDocument) -> Result<KnowledgeGraph, ConversionError>;
```

**Pattern for validation (matching `MsdmToKsdmGraphConverter`):**
```rust
pub fn validate_knowledge_graph(kg: &KnowledgeGraph, schema: &MSDMDocument) -> HashMap<String, Vec<String>>;
```

---

## Summary

| Metric | Count |
|--------|-------|
| Total files | 44 |
| Empty stub files | 38 |
| Populated Python files | 5 (4 converters + 1 init) |
| Total lines of real code | ~645 |
| Rust migration priority (5 scale) | 2 converters rated 5/4, 2 rated 3/4 |
| External Python libs used | 0 (no rdflib, no converters imported) |
| Pydantic models referenced | KnowledgeGraph, GraphNode, GraphEdge, DataDocument, DataNode, DataValue, MSDMDocument, Entity, Attribute, ScalarType, RdfGraph, RdfTriple |
