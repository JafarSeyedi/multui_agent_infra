# Parser Migration Analysis Report

**Generated:** 2026-06-13
**Codebase:** `/home/sjfs/autogen_project/multi_agent_infra/engines/document/parsers`
**Total Python files:** 164
**Total lines:** ~55,364

---

## 1. Overall Architecture

### Hierarchy

```
parsers/base.py               →  BaseDocumentParser (ABC) + ParseOptions (Pydantic)
parsers/__init__.py           →  exports: HTMLDocumentParser, HtmlParser, LatexParser, MarkdownParser
  ├── osdm_parsers/           →  BaseOSDMParser → BaseDocumentParser (BPMN, DMN, CMMN, EPC, PNML, ...)
  ├── usdm_parsers/           →  BaseDocumentParser directly (HTML, DOCX, PDF, RTF, LaTeX, Markdown, TXT)
  ├── dsdm_parsers/           →  BaseDSDMParser → BaseDocumentParser (JSON, XML, YAML, CSV, Protobuf, ...)
  ├── csdm_parsers/           →  BaseDocumentParser directly (DWG/DXF via ODA bridge)
  ├── esdm_parsers/           →  BaseSpreadsheetParser → BaseDocumentParser (XLSX, Parquet, CSV, fixed-width)
  ├── msdm_parsers/           →  BaseMSDMParser → BaseDocumentParser (JSON Schema, XSD, UML/XMI, SQL DDL, ...)
  ├── ssdm_parsers/           →  BaseSSDMParser → BaseDocumentParser (OpenAPI, AsyncAPI, WSDL, gRPC, YANG, ...)
  ├── tsdm_parsers/           →  BaseTSDMParser → BaseDocumentParser (JSON-based tool SDM)
  ├── lsdm_parsers/           →  BaseDocumentParser directly (XES, Syslog, CEF, ES Bulk)
  ├── bam_parsers/            →  BaseBAMParser → BaseDocumentParser (YAML/JSON monitoring dashboards)
  ├── ksdm_parsers/           →  Various (BI, ML, process mining, semantic graph, query models)
  ├── psdm_parsers/           →  BaseDocumentParser directly (PPTX via ZIP/XML)
  └── drawingml/              →  Utility parsers (charts, diagrams, images, shapes — no base class)
```

### Common Parse Interface

Every parser implements `parse_bytes(data, document_id, source_name, metadata, options)` returning a `BaseDocument` (Pydantic model). All parsing is `async def` — even when the actual work is synchronous, it's wrapped in an async signature.

---

## 2. Pre-refactor Analysis by Subdirectory

### 2.1 `usdm_parsers/` (58 files, ~25,831 lines) — **LARGEST**

| Metric | Count |
|--------|-------|
| Total files | 58 (5 sub-dirs: docx, pdf, html, latex, markdown, rtf, txt) |
| `Any` type annotations | ~25 |
| `dict[str, Any]` usage | ~180+ |
| `isinstance` chains | ~30 |
| Mutable default args | ~10 (`metadata: dict[str, Any] \| None = None` is safely None-defaulted, but some `options: Any = None` exist) |
| Global state | None |
| `# type: ignore` | 18 (all in `pdf/` — PyMuPDF, cv2, pytesseract, camelot, arabic_reshaper, networkx) |
| XML/HTML parsing | `xml.etree.ElementTree` in docx/; `html.parser.HTMLParser` in html/ |
| `@abstractmethod` | 3 (in base.py) |
| **Rust migration blockers** | Extreme — PDF uses `pdfplumber`, `fitz`, `camelot`, `pytesseract`, `cv2`, `PIL`; DOCX uses `lxml`-like patterns through `ElementTree` on ZIP contents; LaTeX is regex-based state machine |

**Sub-directories:**
- **html/** (7 files) — Python `html.parser` based state machine. Heavy `dict[str, Any]` style tracking. 1266-line main parser. **Moderate Rust candidate** — HTML tokenization is well-understood.
- **docx/** (27 files) — ZIP+XML parsing. ~5000+ lines total. **Hard to migrate** — relies on ZIP file access, XML traversal, no pure Rust OOXML parser exists at feature parity.
- **pdf/** (7 files) — `pdfplumber`, `PyMuPDF`, `camelot`, `pytesseract`, `cv2`, `PIL`. **Must stay in Python** — no Rust PDF lib covers all these features.
- **latex/** (6 files) — Regex-based recursive descent. Pure string processing. **Good Rust candidate** — regex + state machine maps well.
- **markdown/** (1 file) — Single ~1300-line parser. **Good Rust candidate** — many Rust markdown crates exist.
- **rtf/** (1 file) — ~843-line state machine. **Good Rust candidate** — RTF is a well-defined token stream.
- **txt/** (1 file) — Trivial. **Trivial Rust candidate.**

### 2.2 `osdm_parsers/` (19 files, ~4,767 lines)

| Metric | Count |
|--------|-------|
| `Any` type annotations | ~8 |
| `dict[str, Any]` usage | ~10 |
| `isinstance` chains | **Massive** — ~250+ (BPMN reference resolver is an `isinstance` chain of 50+ branches) |
| `# type: ignore` | 0 |
| XML parsing | `xml.etree.ElementTree` in every XML parser (BPMN, DMN, CMMN, PNML, GraphML, EPC, SCXML) |
| `@abstractmethod` | 1 (in base_osdm_parser.py) |
| **Assessment** | All XML-based. Two-pass pattern (parse+resolve references). Pure parsing logic. **Excellent Rust candidate** — `roxmltree` + `quick-xml` can replace `ElementTree`. The isinstance chains become `match` on enum variants in Rust. |

**Parsers:** BPMN (675 lines), CMMN, DMN, EPC, PNML, GraphML, SCXML, CEP, XPD, Prefect DAG, UML State Machine — all XML + AST-to-model mapping.

### 2.3 `msdm_parsers/` (19 files, ~6,972 lines)

| Metric | Count |
|--------|-------|
| `Any` type annotations | ~5 |
| `dict[str, Any]` usage | ~30 |
| `isinstance` chains | ~20 |
| `# type: ignore` | 0 |
| `@abstractmethod` | 1 (in base_msdm_parser.py) |
| **Assessment** | Schema/metadata parsers: JSON Schema, XSD, UML/XMI, SQL DDL, GraphQL, TypeScript, Thrift, Protobuf, OWL, etc. Pure text parsing — no I/O. **Excellent Rust candidate.** `serde_json` for JSON Schema, `quick-xml` for XSD/UML. The `resolve_references` two-pass pattern maps to `Rc<RefCell<>>` or `Arc<Mutex<>>` in Rust. |

### 2.4 `dsdm_parsers/` (17 files, ~1,377 lines)

| Metric | Count |
|--------|-------|
| `Any` type annotations | ~6 |
| `dict[str, Any]` usage | ~15 |
| `isinstance` chains | ~10 |
| `# type: ignore` | 3 (msgpack, bson, mongodb) |
| `@abstractmethod` | 2 (in base_dsdm_parser.py) |
| **Assessment** | Data format parsers: JSON, XML, YAML, CSV, Protobuf, MsgPack, BSON, CBOR, Pickle, SQL, Cassandra, MongoDB, Redis. **Mixed:** JSON/XML/YAML/CSV → excellent Rust candidates (`serde_json`, `quick-xml`, `serde_yaml`, `csv`). Binary formats (Protobuf, MsgPack, BSON, CBOR) also have Rust crates. Pickle and SQL must stay — pickle is Python-specific, SQL uses async DB drivers. MongoDB/Redis/Cassandra are DB clients, not parsers. |

### 2.5 `ksdm_parsers/` (30 files, ~4,131 lines)

| Metric | Count |
|--------|-------|
| `Any` type annotations | ~20 |
| `dict[str, Any]` usage | ~30 |
| `isinstance` chains | ~15 |
| `# type: ignore` | 2 (joblib, sklearn) |
| `@abstractmethod` | 0 |
| **Assessment** | **Must stay in Python.** Sub-dirs: `bi_aggregation/` (XML/JSON BI model parsers), `ml_mining/` (sklearn/pytorch/onnx/pmml introspection), `process_mining/` (JPRM/YPRM), `semantic_graph/` (RDF, RML), `query_models/` (DAX, MDX, JPQL, OQL, SQL, GraphQL, PowerQuery M, XMLA). The ML parsers use `pickle`, `joblib`, `torch`, `onnx` — Python-only. BI parsers (Mondrian, CDM, CWM, Cognos) are XML-based and could be Rust candidates. Semantic graph uses `rdflib` — must stay. Query model parsers are text parsers — could be candidates. |

### 2.6 `psdm_parsers/` (16 files, ~2,103 lines)

| Metric | Count |
|--------|-------|
| `Any` type annotations | ~3 |
| `dict[str, Any]` usage | ~15 |
| `isinstance` chains | ~5 |
| `# type: ignore` | 0 |
| `@abstractmethod` | 0 |
| **Assessment** | PPTX ZIP+XML parsing. 401-line main parser coordinating 14 sub-modules. **Hard to migrate** — ZIP file access, XML traversal, image extraction, OLE embedding. Some sub-parsers (shape, table, theme) are pure XML transforms → could be extracted as Rust crate. |

### 2.7 `ssdm_parsers/` (10 files, ~4,211 lines)

| Metric | Count |
|--------|-------|
| `Any` type annotations | ~3 |
| `dict[str, Any]` usage | ~25 |
| `isinstance` chains | ~5 |
| `# type: ignore` | 0 |
| `@abstractmethod` | 1 (in base_ssdm_parser.py) |
| **Assessment** | OpenAPI (552 lines), AsyncAPI, WSDL, gRPC, YANG, MCP, Python service, GraphQL service. Pure text/YAML/XML parsing. **Excellent Rust candidate.** OpenAPI parser uses `yaml` + `json` → `serde_yaml` + `serde_json`. WSDL is XML → `quick-xml`. YANG is a text format → `nom` or `pest`. |

### 2.8 `esdm_parsers/` (21 files, ~3,374 lines)

| Metric | Count |
|--------|-------|
| `Any` type annotations | ~3 |
| `dict[str, Any]` usage | ~20 |
| `isinstance` chains | ~5 |
| `# type: ignore` | 0 |
| `@abstractmethod` | 1 (in base_spreadsheet_parser.py) |
| **Assessment** | XLSX ZIP+XML (13 files), Parquet/Arrow binary, CSV, fixed-width. **Mixed:** XLSX → hard (openpyxl via ElementTree on ZIP). Parquet → `pyarrow` dependent, must stay. CSV → trivial candidate. Fixed-width → good candidate. |

### 2.9 `csdm_parsers/` (5 files, ~891 lines)

| Metric | Count |
|--------|-------|
| `Any` type annotations | ~5 |
| `dict[str, Any]` usage | ~10 |
| `isinstance` chains | ~5 |
| `# type: ignore` | 1 (`import odapython` — Python-specific C extension) |
| `@abstractmethod` | 0 |
| **Assessment** | **Must stay in Python.** Uses `odapython` (Open Design Alliance C++ bridge) for DWG/DXF. No Rust alternative for ODA. The `CSDMLoader` and `CSDMRelationshipResolver` could theoretically be extracted, but the ODA bridge is the bottleneck. |

### 2.10 `drawingml/` (5 files, ~705 lines)

| Metric | Count |
|--------|-------|
| `Any` type annotations | ~2 |
| `dict[str, Any]` usage | ~5 |
| `isinstance` chains | ~2 |
| `# type: ignore` | 0 |
| `@abstractmethod` | 0 |
| **Assessment** | Utility XML parsers for OOXML DrawingML (charts, diagrams, shapes, images). Pure XML → `xml.etree.ElementTree`. **Good Rust candidate** — `quick-xml` or `roxmltree`. Shared by PSDM and USDM (used by both PPTX and DOCX parsers). |

### 2.11 `lsdm_parsers/` (5 files, ~475 lines)

| Metric | Count |
|--------|-------|
| `Any` type annotations | ~2 |
| `dict[str, Any]` usage | ~5 |
| `isinstance` chains | ~2 |
| `# type: ignore` | 0 |
| `@abstractmethod` | 0 |
| **Assessment** | XES XML parser (113 lines), Syslog, CEF, ES Bulk. XES is XML → Rust candidate. Syslog/CEF are regex-based → Rust candidate. ES Bulk is JSON → Rust candidate. |

### 2.12 `tsdm_parsers/` (3 files, ~278 lines)

| Metric | Count |
|--------|-------|
| `Any` type annotations | ~1 |
| `dict[str, Any]` usage | ~3 |
| `isinstance` chains | 0 |
| `# type: ignore` | 0 |
| `@abstractmethod` | 1 |
| **Assessment** | Tiny — JSON-based tool schema parsing. **Trivial Rust candidate.**

### 2.13 `bam_parsers/` (4 files, ~134 lines)

| Metric | Count |
|--------|-------|
| `Any` type annotations | ~3 |
| `dict[str, Any]` usage | ~5 |
| `isinstance` chains | 0 |
| `# type: ignore` | 0 |
| `@abstractmethod` | 1 |
| **Assessment** | Tiny — YAML/JSON monitoring dashboard parser. **Trivial Rust candidate.**

---

## 3. Migration Notes — Rust Candidate Scoring

### Priority Matrix

| Priority | Subdirectory | Rationale | Lines |
|----------|-------------|-----------|-------|
| **1** | `osdm_parsers/` | Pure XML→model mapping. Two-pass pattern maps to Rust enums + Rc. No I/O. | 4,767 |
| **1** | `msdm_parsers/` | Pure text/schema parsing. JSON Schema, XSD, GraphQL schema, SQL DDL. No I/O. | 6,972 |
| **1** | `ssdm_parsers/` | OpenAPI, AsyncAPI, WSDL, YANG — all pure text/XML/YAML. No I/O. | 4,211 |
| **2** | `dsdm_parsers/` (subset) | JSON, XML, YAML, CSV, CBOR, MsgPack, BSON — pure format conversion. Exclude DB clients. | ~800 |
| **2** | `drawingml/` | Shared XML utility used by PPTX and DOCX. Pure XML transforms. | 705 |
| **2** | `lsdm_parsers/` | XES (XML), Syslog/CEF (regex), ES Bulk (JSON). Pure parsing. | 475 |
| **2** | `tsdm_parsers/` | Tiny JSON parser. | 278 |
| **2** | `bam_parsers/` | Tiny YAML/JSON parser. | 134 |
| **3** | `usdm_parsers/html/` | HTML parser — state machine, but Python `html.parser` is idiosyncratic. | ~2,500 |
| **3** | `usdm_parsers/latex/` | Regex-based LaTeX parser. Pure text. | ~1,500 |
| **3** | `usdm_parsers/markdown/` | Markdown → USDM model. Many Rust MD crates exist. | ~1,300 |
| **3** | `usdm_parsers/rtf/` | RTF state machine. Pure text. | ~843 |
| **3** | `usdm_parsers/txt/` | Trivial text parser. | <100 |
| **4** | `esdm_parsers/` (CSV, fixed-width) | Simple format parsers. | ~500 |
| **4** | `ksdm_parsers/bi_aggregation/` | XML-based BI model parsers (Mondrian, CDM, etc). | ~1,500 |
| **5** | **Must stay in Python** | See "Must Stay" section below | ~28,000 |

### Must Stay in Python

| Subdirectory | Reason |
|-------------|--------|
| `usdm_parsers/pdf/` | `pdfplumber`, `PyMuPDF`, `camelot`, `pytesseract`, `cv2`, `PIL` — no Rust equivalent at feature parity |
| `usdm_parsers/docx/` | ZIP+XML traversal, 27 files. No Rust OOXML parser matches feature set |
| `csdm_parsers/` | `odapython` C++ bridge — proprietary ODA SDK |
| `ksdm_parsers/ml_mining/` | `pickle`, `joblib`, `torch`, `sklearn`, `onnx` — Python ML runtime |
| `ksdm_parsers/semantic_graph/` | `rdflib` — RDF graph library |
| `ksdm_parsers/process_mining/` | Python-specific format (JPRM/YPRM is internal JSON) |
| `dsdm_parsers/pickle_parser/` | Python pickle — Python-only |
| `dsdm_parsers/sql_parser/`, `mongodb_parser/`, `cassandra_parser/`, `redis_parser/` | Database client drivers |
| `psdm_parsers/pptx/` | ZIP+XML + media extraction — complex OOXML feature set |
| `esdm_parsers/xlsx/` | ZIP+XML + formulas, charts, pivot tables — complex OOXML |

---

## 4. Ownership Map

### Data Flow

```
Raw Bytes (bytes)
    │
    ▼
  Parser.parse_bytes()   ←  async def, reads entire payload
    │
    ├── Text decode (if text format)
    ├── XML parse (xml.etree.ElementTree / lxml)
    ├── JSON parse (json module)
    ├── ZIP open + XML parse (DOCX, PPTX, XLSX)
    └── Binary deserialize (msgpack, protobuf, etc.)
    │
    ▼
  Intermediate Representation (dict[str, Any] / custom objects)
    │
    ├── Two-pass: first pass collects elements with string refs
    └── Second pass: resolve_references() connects refs
    │
    ▼
  Typed Pydantic Model (BaseDocument subclass)
    │
    ▼
  Caller (engine layer)
```

### Who Owns Intermediate Representations?

**Nobody explicitly** — the intermediate state lives in:
1. **Parser instance fields** (`self.element_stack`, `self.current_*`) — stateful SAX-like pattern in HTML, RTF parsers
2. **Local variables** (`all_elements: dict[str, Any]`) in BPMN/OSDM parsers
3. **String-based reference IDs** that are resolved in a second pass

This is a Rust-migration hazard: the stateful parser pattern (mutating `self` fields) doesn't map cleanly to Rust's ownership model without `RefCell` or state machine encoding.

### Model Ownership

Models live in `engines/document/models/` — separate from parsers. Each SDM has its own model module:
- `osdm_models.py` → `BPMNDocument`, `BaseOSDMDocument`
- `usdm_models.py` → `USDMDocument`
- `dsdm_models.py` → `DataDocument`, `DataNode`
- `msdm_models.py` → `MSDMDocument`, `Entity`, `Attribute`
- `ssdm_models.py` → `SSDMDocument`
- `esdm_models.py` → `Workbook`, `Worksheet`
- `psdm_models.py` → `PSDMDocument`
- `ksdm_models.py` → `SemanticGraphDocument`, `MlMiningDocument`
- `lsdm_models.py` → `EventLogDocument`
- `tsdm_models.py` → `TSDMDocument`
- `bam_models.py` → `MonitoringDashboardDocument`
- `csdm_core.py` → `CSDMDocument`
- `base.py` → `BaseDocument` (Pydantic BaseModel)

**For Rust migration:** Models must be re-defined as Rust `struct` with `#[derive(Serialize, Deserialize)]` or custom serde impls. The Pydantic validation logic (`@field_validator`, `ConfigDict`) must be re-implemented.

---

## 5. Suggested PyO3 Binding Structure

### Crate Layout

```
rust/engines/document/parsers/
├── Cargo.toml              # workspace member
├── src/
│   ├── lib.rs              # PyO3 module registration
│   ├── base.rs             # ParseOptions, BaseDocumentParser trait
│   ├── models/             # Rust equivalents of Pydantic models
│   │   ├── mod.rs
│   │   ├── osdm.rs
│   │   ├── usdm.rs
│   │   ├── dsdm.rs
│   │   ├── msdm.rs
│   │   └── ssdm.rs
│   ├── osdm_parsers/       # Crate: osdm_parsers
│   │   ├── mod.rs
│   │   ├── bpmn_parser.rs  # BPMN 2.0 XML → BPMNDocument
│   │   ├── dmn_parser.rs
│   │   ├── cmmn_parser.rs
│   │   ├── epc_parser.rs
│   │   ├── pnml_parser.rs
│   │   └── reference_resolver.rs
│   ├── msdm_parsers/       # Crate: msdm_parsers
│   │   ├── mod.rs
│   │   ├── json_schema.rs
│   │   ├── xsd_parser.rs
│   │   ├── uml_xmi.rs
│   │   └── sql_ddl.rs
│   ├── ssdm_parsers/       # Crate: ssdm_parsers
│   │   ├── mod.rs
│   │   ├── openapi.rs
│   │   ├── asyncapi.rs
│   │   ├── wsdl.rs
│   │   └── yang.rs
│   ├── dsdm_parsers/       # Crate: dsdm_parsers
│   │   ├── mod.rs
│   │   ├── json_parser.rs
│   │   ├── xml_parser.rs
│   │   ├── yaml_parser.rs
│   │   ├── csv_parser.rs
│   │   └── binary_parsers.rs
│   ├── drawingml/          # Shared crate (used by PSDM and USDM)
│   │   ├── mod.rs
│   │   ├── chart.rs
│   │   ├── diagram.rs
│   │   ├── shape.rs
│   │   └── image.rs
│   ├── lsdm_parsers/
│   │   ├── mod.rs
│   │   └── xes_parser.rs
│   ├── tsdm_parsers/
│   │   └── mod.rs
│   └── bam_parsers/
│       └── mod.rs
├── pyo3_bridge/            # Separate crate for PyO3 bindings
│   ├── Cargo.toml
│   └── src/
│       ├── lib.rs          # #[pyfunction] wrappers
│       ├── osdm_bridge.rs  # BPMNParser → Python callable
│       ├── msdm_bridge.rs
│       └── ssdm_bridge.rs
```

### Shared Logic Candidates

These parsers share patterns that could be a shared Rust utility crate:
1. **XML parsing** — `osdm_parsers/`, `msdm_parsers/xsd.uml_xmi`, `ssdm_parsers/wsdl`, `lsdm_parsers/xes`, `drawingml/` all use `xml.etree.ElementTree`. A shared `xml_utils` crate with namespace handling, tag dispatch, and attribute extraction.
2. **Reference resolution** — `osdm_parsers/` (BPMN), `msdm_parsers/` (schema), `csdm_parsers/` all use a two-pass pattern with string ID resolution. A shared `ref_resolver` generic component.
3. **OOXML utilities** — `drawingml/` is already shared between PPTX and DOCX parsers. A `ooxml_utils` crate for ZIP archive navigation, relationship resolution, content type detection.

### PyO3 Integration Strategy

```rust
// Pseudocode for PyO3 bridge
#[pyclass]
struct BpmnParser {
    inner: osdm_parsers::BpmnParser,
}

#[pymethods]
impl BpmnParser {
    #[pyo3(signature = (data, document_id, source_name, metadata=None, options=None))]
    fn parse_bytes(&self, data: &[u8], document_id: &str, source_name: &str,
                   metadata: Option<HashMap<String, PyObject>>,
                   options: Option<ParseOptions>) -> PyResult<PyObject> {
        let doc = self.inner.parse(data)?;
        // Convert Rust BPMNDocument → Python dict/Pydantic model
        Ok(doc.into_py(py))
    }
}
```

---

## 6. Libraries Analysis

### XML Parsing

| Python Library | Files Using | Rust Equivalent | Migratable? |
|---------------|-------------|-----------------|-------------|
| `xml.etree.ElementTree` | 40+ files across osdm, msdm, ssdm, lsdm, drawingml, dsdm, esdm, psdm, usdm/docx | `quick-xml` (streaming), `roxmltree` (DOM) | ✅ Yes — core pattern |
| `lxml` | `usdm_parsers/docx` (implied via ElementTree on large XML) | `roxmltree` + `xmltree` | ✅ Yes for read-only |
| `html.parser` | `usdm_parsers/html/` | `html5ever`, `ego-tree` | ✅ Yes (Servo's html5ever) |
| `defusedxml` | `usdm_parsers/pdf/metadata_extractor.py` | `quick-xml` + custom entity expansion check | ✅ Yes |

### PDF Parsing

| Python Library | Files Using | Rust Equivalent | Migratable? |
|---------------|-------------|-----------------|-------------|
| `pdfplumber` | `usdm_parsers/pdf/` | `pdf-extract`, `pdf` | ⚠️ Partial — extraction far less mature |
| `PyMuPDF (fitz)` | `usdm_parsers/pdf/` | `pdf-extract`, `pdf`, `lopdf` | ⚠️ Partial |
| `camelot` | `usdm_parsers/pdf/` | None | ❌ Must stay in Python |
| `pytesseract` | `usdm_parsers/pdf/` | `tesseract` via `leptess` | ⚠️ Possible but complex |
| `pdf2image` | `usdm_parsers/pdf/` | `pdf` crate + `image` crate | ⚠️ Partial |
| `cv2` | `usdm_parsers/pdf/` | `opencv` crate | ⚠️ Possible but heavy |

### Excel / Spreadsheet

| Python Library | Files Using | Rust Equivalent | Migratable? |
|---------------|-------------|-----------------|-------------|
| `openpyxl` | `esdm_parsers/xlsx/` | `calamine` (read), `rust_xlsxwriter` (write) | ⚠️ Partial — formulas, charts, pivot tables not supported |
| `pyarrow` | `esdm_parsers/binary_parser.py` | `arrow` crate | ✅ Yes |

### Binary Formats

| Python Library | Files Using | Rust Equivalent | Migratable? |
|---------------|-------------|-----------------|-------------|
| `msgpack` | `dsdm_parsers/msgpack_parser.py` | `rmp-serde` | ✅ Yes |
| `protobuf` | `dsdm_parsers/protobuf_parser.py`, `msdm_parsers/proto_msdm_parser.py` | `prost`, `protobuf` | ✅ Yes |
| `bson` | `dsdm_parsers/bson_parser.py`, `mongodb_parser.py` | `bson` crate | ✅ Yes |
| `cbor` | `dsdm_parsers/cbor_parser.py` | `ciborium`, `serde_cbor` | ✅ Yes |
| `pickle` | `dsdm_parsers/pickle_parser.py`, `ksdm_parsers/ml_mining/sklearn_parser.py` | None | ❌ Python-only |
| `joblib` | `ksdm_parsers/ml_mining/sklearn_parser.py` | None | ❌ Python-only |

### ML / Data Science

| Python Library | Files Using | Rust Equivalent | Migratable? |
|---------------|-------------|-----------------|-------------|
| `sklearn` | `ksdm_parsers/ml_mining/sklearn_parser.py` | `linfa`, `smartcore` | ❌ Different API, model formats incompatible |
| `torch` | `ksdm_parsers/ml_mining/pytorch_parser.py` | `tch-rs`, `candle`, `burn` | ❌ Python model introspection |
| `onnx` | `ksdm_parsers/ml_mining/onnx_parser.py` | `onnx` crate | ✅ Yes — ONNX is a protobuf format |
| `rdflib` | `ksdm_parsers/semantic_graph/` | `rio` (RDF I/O), `sophia` | ✅ Yes — RDF is well-supported in Rust |

### Text / Structured

| Python Library | Files Using | Rust Equivalent | Migratable? |
|---------------|-------------|-----------------|-------------|
| `json` (stdlib) | 20+ files | `serde_json` | ✅ Yes |
| `yaml` (PyYAML) | `ssdm_parsers/openapi.py`, `bam_parsers/bam_yaml_parser.py` | `serde_yaml` | ✅ Yes |
| `csv` (stdlib) | `dsdm_parsers/csv_tsv_parser.py`, `esdm_parsers/delimited_parser.py` | `csv` crate | ✅ Yes |
| `re` (stdlib) | 20+ files | `regex` crate | ✅ Yes |

---

## 7. Performance Hot Paths

### HOT_PATH Candidates

| Parser | Why | Estimated Impact |
|--------|-----|-----------------|
| **BPMN XML** (`osdm_parsers/bpmn_xml_parser.py`, 675 lines) | Two-pass: parse + resolve. XML DOM building + isinstance chains. Every element traversed twice. | Medium |
| **HTML Parser** (`usdm_parsers/html/html_parser.py`, 1266 lines) | Full SAX-style HTML traversal. Many string concat operations, style stack manipulations. | High |
| **DOCX Parser** (`usdm_parsers/docx/docx_parser.py`, 1321 lines + 26 helper files) | ZIP decompress → XML parse per part → DOCX model → USDM model. Heavy allocation. | Highest |
| **PDF Content Extractor** (`usdm_parsers/pdf/content_extractor.py`, 1049 lines) | OCR (tesseract), image processing (cv2), table extraction (camelot). Not CPU-bound in Python per se, but slow due to Python overhead. | High |
| **RTF Parser** (`usdm_parsers/rtf/rtf_parser.py`, 843 lines) | State machine + many string operations. | Medium |
| **OpenAPI Parser** (`ssdm_parsers/openapi_parser.py`, 552 lines) | YAML/JSON → 20+ model types. Many small allocations. | Medium |
| **JSON Schema** (`msdm_parsers/json_schema_parser.py`, 405 lines) | Recursive descent with $ref resolution. Many string manipulations. | Medium |
| **SkLearn Parser** (`ksdm_parsers/ml_mining/sklearn_parser.py`, 519 lines) | Pickle deserialize + model graph introspection + isinstance dispatch. | Medium |

### Zero-Copy Candidates

Patterns that benefit from Rust's zero-copy:

1. **Namespace stripping in XML** — `tag[1:].split('}', 1)` in XML parsers → `quick-xml` provides namespace-aware API without allocation
2. **String enum mapping** — `TASK_TAG_MAP` in BPMN parser → Rust `match &str` with no allocation
3. **CSS style parsing** — `parse_inline_style()` splitting on `;` and `:` → `nom` parser on `&str`
4. **File extension detection** — `Path(source_name).suffix` → `std::path::Path::extension()`
5. **HTML entity replacement** — `entities.html5.get(f"&{name};")` → `html5ever` handles entities natively

### Repeated String Operations

- **HTML parser:** `"".join(self.current_text)` on every `_flush_current_text()` — many times per document
- **RTF parser:** `"".join(self.current_text)` in a 843-line state machine
- **BPMN parser:** `f"{{{ns}}}{tag}"` namespace wrapping repeatedly
- **DOCX parser:** `f"{{{ns}}}tag"` pattern on every XML element access
- **OpenAPI parser:** `str(global_sec)`, `str(value)` — many string conversions

---

## 8. Error Handling

### Custom Exception Classes

- `DocumentParseError` in `usdm_parsers/` (from `models/exceptions.py`)
- `ValueError` used throughout (bare raises in many parsers)
- `RuntimeError("Failed to parse DWG file: ...")` in `csdm_parsers/csdm_parser.py`

### Exception Swallowing

- `oda_bridge.py:20` — `except: pass` (catches all exceptions, returns default)
- `oda_bridge.py:30` — `except: return None`
- `oda_bridge.py:37` — `except: return None`
- `oda_bridge.py:43` — `except: return None`
- `oda_bridge.py:48` — `except: return False`
- `oda_bridge.py:57` — bare except catching all XData failures
- `bpmn_xml_parser.py` — many `except Exception: pass` in reference resolver
- `diagram_parser.py:65` — `except Exception: return None`

### Functions Returning None on Failure

- `parse_diagram_ref()` → `Optional[DrawingContent]`
- `resolve_diagram()` → `Optional[DrawingContent]`
- `resolve_image()` → `Optional[DrawingContent]`
- `resolve_chart()` → `Optional[DrawingContent]`
- `ODABridge.extract_table()` → `list[ODAObjectProxy]` (empty on failure)
- `ODAObjectProxy.read_xdata()` → `dict[str, Any]` (empty on failure)
- `ODAHandle.from_obj()` → `ODAHandle("0")` on failure

### For Rust Migration

- Replace `Optional[T]` returns with `Result<T, ParseError>`
- The bare `except:` patterns in `oda_bridge.py` must become typed error handling
- `DocumentParseError` should become `ParseError` enum in Rust with typed variants

---

## 9. Mutable Default Arguments

Found patterns (safe and unsafe):

- `metadata: dict[str, Any] | None = None` — **safe** (None default, new dict created)
- `options: ParseOptions | None = None` — **safe**
- `default: Any = None` — **safe**
- `model: Any` (no default) — **fine**
- `data: dict[str, Any] = {}` — **NOT FOUND** (all use None default with `or {}`)

**Verdict:** No dangerous mutable default args found. Python typing in this codebase is cautious about this pattern.

---

## 10. Summary of Rust Migration Priority

### Tier 1 — Immediate Rust Candidates (no I/O, pure text/XML parsing)
1. **`osdm_parsers/`** — All XML-based. ~4,767 lines. Priority 1.
2. **`msdm_parsers/`** — Schema/metadata parsers. ~6,972 lines. Priority 1.
3. **`ssdm_parsers/`** — API/service definition parsers. ~4,211 lines. Priority 1.
4. **`drawingml/`** — Shared OOXML utilities. ~705 lines. Priority 2.
5. **`lsdm_parsers/`** — XES, Syslog, CEF. ~475 lines. Priority 2.
6. **`tsdm_parsers/`** — Tiny tool SDM. ~278 lines. Priority 2.
7. **`bam_parsers/`** — Tiny monitoring dashboard. ~134 lines. Priority 2.

### Tier 2 — Rust Candidates with Python Bridge
8. **`dsdm_parsers/`** (subset) — JSON, XML, YAML, CSV, CBOR, MsgPack, BSON. ~800 lines. Priority 2.
9. **`usdm_parsers/html/`** — HTML. ~2,500 lines. Priority 3.
10. **`usdm_parsers/latex/`** — LaTeX. ~1,500 lines. Priority 3.
11. **`usdm_parsers/markdown/`** — Markdown. ~1,300 lines. Priority 3.
12. **`usdm_parsers/rtf/`** — RTF. ~843 lines. Priority 3.
13. **`esdm_parsers/`** (CSV/fixed-width) — Simple formats. ~500 lines. Priority 4.
14. **`ksdm_parsers/bi_aggregation/`** — XML BI models. ~1,500 lines. Priority 4.

### Tier 3 — Must Stay in Python (~28,000 lines)
- `usdm_parsers/pdf/` — Heavy Python dependency (pdfplumber, cv2, pytesseract)
- `usdm_parsers/docx/` — Complex OOXML + ZIP
- `csdm_parsers/` — odapython C++ bridge
- `ksdm_parsers/ml_mining/` — Python ML runtime
- `ksdm_parsers/semantic_graph/` — rdflib
- `psdm_parsers/pptx/` — Complex OOXML + ZIP
- `esdm_parsers/xlsx/` — Complex OOXML + ZIP
- `dsdm_parsers/` (DB clients, pickle) — Python/runtime specific

### Estimated Rust Migration Effort

| Tier | Lines | Rust Crate Estimate | PyO3 Effort |
|------|-------|---------------------|-------------|
| Tier 1 | ~16,900 | 4-6 crates | 2-3 days |
| Tier 2 | ~6,900 | 4-5 crates | 2-3 days |
| **Total** | **~23,800** | **8-11 crates** | **4-6 days** |

The remaining ~28,000 lines stay in Python for the foreseeable future.

---

## 11. Key Architectural Observations

1. **All parsers are async even when sync.** The `async def parse_bytes` signature is universal, but most parsers do synchronous work inside. This is a Python concession — Rust should use `async` only where actual I/O happens.

2. **Stateful parser pattern is dominant.** The HTML, RTF, and DOCX parsers store parsing state in `self.*` fields. This is antithetical to Rust's ownership model. For Rust, prefer:
   - **Pure functions** with `&[u8]` inputs → `Result<Model, Error>`
   - **Nom/combine combinators** for text formats
   - **Visitor pattern** for XML (quick-xml's `Reader` + custom `Event` handler)

3. **Pydantic models are the output boundary.** The Rust parsers must produce models that can be serialized to Python-compatible dicts. Using `serde` with `#[serde(rename = "camelCase")]` or Pydantic-compatible field names is critical.

4. **Reference resolution is a two-pass pattern.** BPMN, JSON Schema, MSDM, CSDM all use string IDs in first pass, then resolve to object references in second pass. In Rust, use indices (`usize` into `Vec<T>`) or `Arc` for shared references.

5. **Lots of isinstance dispatch.** The BPMN parser has 50+ `isinstance` branches in the reference resolver. In Rust, this becomes `match` on an enum variant — much faster and type-safe.
