# Writers Migration Report: Rust Readiness Analysis

**Date:** 2026-06-13  
**Scope:** `engines/document/writers/` — 197 Python files across 14 SDM writer families  
**Analysis Type:** Static code review for Rust migration preparation (read-only)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture Overview](#2-architecture-overview)
3. [Type System Readiness](#3-type-system-readiness)
4. [Library Dependency Map](#4-library-dependency-map)
5. [Performance Hot Paths](#5-performance-hot-paths)
6. [Error Handling Analysis](#6-error-handling-analysis)
7. [Ownership & Data Flow](#7-ownership--data-flow)
8. [PyO3 Binding Structure](#8-pyo3-binding-structure)
9. [Writer-by-Writer Scoring](#9-writer-by-writer-scoring)
10. [Cross-Cutting Concerns](#10-cross-cutting-concerns)
11. [Recommended Migration Order](#11-recommended-migration-order)

---

## 1. Executive Summary

| Metric | Value |
|--------|-------|
| Total Python files | 197 |
| Total lines of code | ~25,000+ |
| Distinct writer families | 14 (USDM, PSDM, CSDM, DSDM, ESDM, MSDM, KSDM, LSDM, SSDM, TSDM, BAM, VSDM, OSDM) |
| External library deps | ~20+ |
| Async patterns | All writers use `async def write()` |
| Type safety | Mixed — Pydantic models good, `dict[str, Any]` pervasive |
| Error handling | Flat hierarchy, generic `Exception` catches |
| XML string building | Major anti-pattern — string concatenation for OOXML |

**Overall Rust migration score: 3.0 / 5** (moderate readiness — high complexity but strong typing opportunity).

### Migration Complexity by Domain

| Domain | Score | Key Challenge |
|--------|-------|---------------|
| TEXT (Markdown, TXT, LaTeX) | 5/5 | Simple string formatting only |
| DSDM JSON/YAML/CBOR/MsgPack | 5/5 | Thin wrappers over `node_to_python` |
| MSDM (DDL, Protobuf, XSD) | 4/5 | SQL generation, schema enumeration |
| USDM HTML | 4/5 | Template rendering, no binary |
| USDM LaTeX | 4/5 | LaTeX string escaping only |
| USDM RTF | 3/5 | RTF control word formatting |
| ESDM CSV/TSV | 4/5 | Simple columnar output |
| ESDM XLSX | 2/5 | Zip packaging + XML + styles caching |
| PSDM PPTX | 2/5 | Like DOCX — ZIP + 6+ XML parts |
| USDM DOCX | 2/5 | ZIP + OOXML string building (high complexity) |
| USDM PDF | 2/5 | Full PDF 1.7 object serialization, encryption |
| CSDM DWG | 1/5 | Binary DWG spec, need binary crate |
| BAM | 4/5 | Simple JSON/YAML |
| LSDM XES | 3/5 | XML-based event log |
| SSDM OpenAPI/GraphQL | 3/5 | JSON serialization of service models |

---

## 2. Architecture Overview

### Base Class Hierarchy

```
BaseDocumentWriter (ABC)          ← base.py
├── USDM writers                  ← usdm_writers/
│   ├── DOCXWriter                ← docx/ (8 files)
│   ├── HTMLWriter                ← html/ (1 file)
│   ├── LatexWriter               ← latex/ (1 file)
│   ├── MarkdownWriter            ← markdown/ (1 file)
│   ├── PDFWriter                 ← pdf/ (13 files)
│   ├── RTFWriter                 ← rtf/ (1 file)
│   └── TXTWriter                 ← txt/ (1 file)
├── PSDM writers                  ← psdm_writers/
│   ├── PPTXWriter                ← pptx/ (19 files)
│   ├── RevealJS / Shower /       ← revealjs/, shower/
│       ImpressJS / HeedJS /      ← impressjs/, heedjs/
│       DeckJS / StageCraft       ← deckjs/, stagecraft/
├── CSDM writers                  ← csdm_writers/
│   ├── DWGWriter                 ← 58 lines, delegates to DWG pipeline
│   ├── DXFWriter / IFCWriter     ← dxf, ifc
│   └── STEPWriter / STLWriter   ← step, stl
├── DSDM writers                  ← dsdm_writers/ (16 files)
│   ├── BaseDSDMWriter (ABC)      ← base_dsdm_writer.py
│   ├── JSON / YAML / XML / CBOR  ← thin serializers
│   ├── BSON / MsgPack / Protobuf ← binary serializers
│   └── SQL / MongoDB / Redis / Cassandra  ← DB-target writers
├── ESDM writers                  ← esdm_writers/
│   ├── ESDMBaseWriter (ABC)      ← base.py
│   ├── XLSXWriter                ← xlsx/ (15 files)
│   └── CSV / TSV                 ← in esdm_writer.py
├── MSDM writers                  ← msdm_writers/ (18 files)
│   ├── BaseMSDMWriter (ABC)      ← base_msdm_writer.py
│   ├── SqlDDLWriter / ...        ← SQL DDL generation
│   └── Neo4jSchemaWriter / ...   ← graph DB schemas
├── KSDM writers                  ← ksdm_writers/
│   ├── BI aggregation (9 files)
│   ├── ML mining (4 files)
│   ├── Process mining / Semantic graph
├── SSDM writers                  ← ssdm_writers/ (9 files)
│   ├── BaseSSDMWriter (ABC)
│   ├── OpenAPI / GraphQL / AsyncAPI
│   └── MCP / Proto / Python service
├── OSDM writers                  ← osdm_writers/ (12 files)
│   ├── BPMN / CMMN / DMN / EPC / PNML XML
│   └── PrefectDAG / SCXML / XPD
├── TSDM writers                  ← tsdm_writers/ (2 files)
│   ├── TsdmJsonWriter
│   └── BaseTSDMWriter
├── LSDM writers                  ← lsdm_writers/ (4 files)
│   ├── XES / CEF / Syslog / ES Bulk
├── BAM writers                   ← bam_writers/ (3 files)
│   ├── BamJsonWriter / BamYamlWriter
└── VSDM writers                  ← vsdm_writers/ (0 files — empty)
```

### Write Interface (all writers)

```python
class BaseDocumentWriter(ABC):
    async def write(self, document: BaseDocument) -> bytes: ...
    async def write_stream(self, document: BaseDocument) -> AsyncIterator[bytes]: ...
    async def write_to_file(self, document, target, options=None): ...
    def get_supported_media_types(self) -> list[str]: ...
    def get_supported_extensions(self) -> list[str]: ...
```

### Common Anti-Pattern: `_convert_X_to_Y(document) -> str` then `.encode()`

Every writer follows this pattern: convert Pydantic document model → string → `.encode(encoding)`. This is straightforward to migrate: the string-building becomes a `String` / `format!()` / `write!()` output.

---

## 3. Type System Readiness

### Strengths

| Aspect | Details |
|--------|---------|
| **Pydantic v2 base models** | `WriteOptions`, `WriteResult`, `BaseDocument`, `USDMDocument` all typed Pydantic models — excellent for Rust `struct` with `serde` |
| **Rich enum usage** | `ElementType`, `VersionIncrement`, `VersionWriteStrategy`, `WriteTarget`, `SoftDeleteStrategy` — maps directly to Rust `enum` |
| **Nested typed models** | `RichTextContent → RichTextSpan[]`, `TableContent → TableRow → TableCell` — clean tree structure |
| **Generic document model** | `BaseDocument` → `USDMDocument`, `DataDocument`, `ESDMDocument`, etc. — maps to trait hierarchy |

### Weaknesses

| Pattern | Frequency | Risk |
|---------|-----------|------|
| `dict[str, Any]` for metadata | Very High | ~100+ uses across all writers. Obscures real types. |
| `Any` type annotations | High | `document: Any`, `options: dict[str, Any]`, `content: Any` |
| `getattr(document, ...)` dynamic access | Medium | Circumvents type system: `getattr(document, "stylesheet", None)` |
| `hasattr` checks | Medium | `hasattr(content, "elements")` — used in image handler recursion |
| `cast()` calls | Low | `cast(PSDMDocument, document)` — workaround for abstract base |
| `_meta` dict on models | Medium | `chart._meta["rId"]`, `drawing._meta["rId"]` — runtime mutable state |
| `**options.model_dump()` | Medium | Pydantic → dict conversion loses type safety |

### Rust Type Translation

```rust
// Python: class WriteOptions(BaseModel):
//   encoding: str = "utf-8"
//   pretty_print: bool = False
//   custom: dict[str, Any] = {}

struct WriteOptions {
    encoding: String,           // default "utf-8"
    pretty_print: bool,         // default false
    custom: HashMap<String, Value>,  // serde_json::Value
}
```

---

## 4. Library Dependency Map

### USDM Writers — Text Formats

| Format | Python Library | Rust Alternative | Migration Difficulty |
|--------|---------------|------------------|---------------------|
| **Markdown** | stdlib string | `std::format!` | Trivial |
| **TXT** | stdlib string | `std::format!` | Trivial |
| **HTML** | `html` stdlib | `std::format!` + escaping | Easy |
| **LaTeX** | stdlib string | `std::format!` + escaping | Easy |
| **RTF** | stdlib string | `std::format!` + control words | Medium |

### USDM Writers — Binary/Office Formats

| Format | Python Library | Rust Alternative | Migration Difficulty |
|--------|---------------|------------------|---------------------|
| **DOCX** | `xml.etree.ElementTree`, `zipfile` | `quick-xml` + `zip` crate | Hard |
| **PPTX** | `xml.etree.ElementTree`, `zipfile` | `quick-xml` + `zip` crate | Hard |
| **XLSX** | `xml.etree.ElementTree`, `zipfile` | `rust_xlsxwriter` or `quick-xml` | Hard |
| **PDF** | Custom full PDF generator | `printpdf`, `genpdf`, `pdf_writer` | Very Hard |

### DSDM Writers — Data Formats

| Format | Python Library | Rust Alternative | Migration Difficulty |
|--------|---------------|------------------|---------------------|
| **JSON** | `json` stdlib | `serde_json` | Trivial |
| **YAML** | `yaml` (PyYAML) | `serde_yaml` | Trivial |
| **XML** | `xml.etree.ElementTree` | `quick-xml`, `serde-xml-rs` | Medium |
| **CBOR** | `cbor2` | `ciborium`, `serde_cbor` | Easy |
| **MessagePack** | `msgpack` | `rmp-serde` | Easy |
| **BSON** | `bson` | `bson` (mongodb driver) | Easy |
| **Protobuf** | `google.protobuf` | `prost` | Medium |
| **Pickle** | `pickle` stdlib | **NO** (security risk) | N/A |

### MSDM Writers — Schema Formats

| Format | Python Library | Rust Alternative | Migration Difficulty |
|--------|---------------|------------------|---------------------|
| **SQL DDL** | `sqlalchemy` | `sqlx`, `diesel`, or string gen | Medium |
| **Neo4j** | `neo4j` | `neo4rs` | Medium |
| **Protobuf** | `google.protobuf` | `prost` | Medium |
| **XSD** | `xml.etree.ElementTree` | `quick-xml` + schema gen | Hard |
| **GraphQL** | stdlib string | `std::format!` | Medium |
| **OpenAPI** | `json` stdlib | `serde_json` | Easy |
| **PlantUML** | stdlib string | String generation | Easy |
| **Thrift IDL** | stdlib string | String generation | Medium |
| **UML XMI** | `xml.etree.ElementTree` | `quick-xml` | Medium |

### OSDM Writers — Orchestration Formats

| Format | Python Library | Rust Alternative | Migration Difficulty |
|--------|---------------|------------------|---------------------|
| **BPMN XML** | `xml.etree.ElementTree` | `quick-xml` | Hard |
| **CMMN XML** | `xml.etree.ElementTree` | `quick-xml` | Hard |
| **DMN XML** | `xml.etree.ElementTree` | `quick-xml` | Hard |
| **EPC** | `xml.etree.ElementTree` | `quick-xml` | Hard |
| **PNML** | `xml.etree.ElementTree` | `quick-xml` | Hard |
| **GraphML** | `xml.etree.ElementTree` | `quick-xml` | Hard |
| **XPD** | `xml.etree.ElementTree` | `quick-xml` | Hard |
| **SCXML** | `xml.etree.ElementTree` | `quick-xml` | Medium |

### DB-Target DSDM Writers

| Writer | Python Library | Rust Alternative | Notes |
|--------|---------------|------------------|-------|
| **SQL** | sqlalchemy | `sqlx` / `diesel` | Runtime DB writes |
| **MongoDB** | `motor` | `mongodb` driver | Live collection insert |
| **Redis** | `redis.asyncio` | `redis-rs` | Key-value set |
| **Cassandra** | `cassandra-driver` | `cassandra-rs` | Prepared statements |

### KSDM Writers — ML/Business Intelligence

| Writer | Python Library | Notes |
|--------|---------------|-------|
| **PMML** | stdlib XML | XML generation — `quick-xml` |
| **ONNX** | protobuf | `prost` for protobuf serialization |
| **Sklearn/PyTorch** | `json` stdlib | JSON model card writing |
| **Tableau Hyper** | `tableauhyperapi` | Proprietary — Python wrapper only |
| **Mondrian** | stdlib XML | XML schema generation |
| **CDM** | stdlib XML | Common Data Model XML |
| **CWM** | stdlib XML | Common Warehouse Metamodel |

---

## 5. Performance Hot Paths

### Hot Path 1: DOCX XML String Building

**Location:** `docx_builder.py` (735 lines), `docx_style_builder.py` (396 lines)
**Pattern:** String concatenation for OOXML parts
```python
lines.append(f'  <w:pPr>{''.join(ppr_parts)}</w:pPr>')
```
**Rust Impact:** `format!` / `write!` macros would be faster. Use `quick-xml` with `Writer` API for zero-copy XML building.

### Hot Path 2: PDF Object Serialization

**Location:** `pdf_writer.py` `_PDFObjectSerializer.serialize()` (lines 118-166)
**Pattern:** Sequential bytearray appending for PDF structure
```python
buf += b"xref\n"
buf += f"0 {len(self._objects) + 1}\n".encode("ascii")
```
**Rust Impact:** `Vec<u8>` building with `write!` is comparable. The xref offset tracking maps naturally.

### Hot Path 3: PPTX ZIP Packaging

**Location:** `ppt/writer.py` `_build_package()` (line 89)
**Pattern:** ZIP writing with `zipfile.ZipFile`
**Rust Impact:** `zip` crate with `ZipWriter` — direct equivalent.

### Hot Path 4: XLSX Shared String Table

**Location:** `esdm_writers/base.py` `_add_shared_string()` (line 116)
**Pattern:** Dict-based string deduplication
**Rust Impact:** `HashMap<String, u32>` — standard, very fast.

### Hot Path 5: XML ElementTree Building (OSDM/BPMN)

**Location:** `osdm_writers/bpmn_xml_writer.py` (802 lines)
**Pattern:** Deeply nested `SubElement` tree
```python
root = Element(f"{{{ns}}}definitions")
SubElement(root, f"{{{ns}}}process", ...)
```
**Rust Impact:** `quick-xml` `Writer` will eliminate namespace string formatting overhead.

### Hot Path 6: SSDM → JSON (OpenAPI)

**Location:** `ssdm_writers/openapi_writer.py` (345 lines)
**Pattern:** Build Python dict → `json.dumps()`
**Rust Impact:** `serde_json::to_string()` with `#[derive(Serialize)]` — zero-touch.

### Hot Path 7: DrawingML Helpers

**Location:** `drawingml_helpers.py` (231 lines)
**Pattern:** Heavily called XML helpers for PPTX shapes
**Rust Impact:** Inline functions, hot loop optimization.

### Performance Summary

| Writer | Est. throughput (current) | Rust perf gain | Bottleneck |
|--------|--------------------------|----------------|------------|
| TXT/Markdown/LaTeX | High | 1-2x | Minimal |
| DOCX | Medium | 3-5x | XML strings + ZIP |
| PPTX | Medium | 3-5x | XML + ZIP + media |
| XLSX | Medium | 3-5x | Shared strings + ZIP |
| PDF | Low | 5-10x | Full PDF serialization |
| OSDM XML | Medium | 2-3x | Deep XML trees |
| DSDM JSON/YAML | High | 2-3x | serde overhead low |

---

## 6. Error Handling Analysis

### Exception Hierarchy

```
DocumentError (Exception)
├── DocumentParseError
├── DocumentWriteError      ← used by all writers
├── DocumentValidationError
│   └── SchemaValidationError
├── UnsupportedFormatError
├── BinaryEncodingError
├── StreamingError
├── RegistryError
├── CompressionError
└── ContentDetectionError
```

### Common Anti-Pattern: Broad Exception Catching

Every writer catches all exceptions and wraps in `DocumentWriteError`:

```python
try:
    # conversion logic
    return result
except Exception as e:
    raise DocumentWriteError(f"Failed: {e}") from e
```

**This loses error context.** Rust's `Result<T, E>` with `thiserror` or `anyhow` would provide:
- Typed error variants per writer
- `#[from]` for automatic conversion
- Backtrace capture via `std::backtrace`

### Error Handling Recommendations

| Python Pattern | Rust Replacement |
|----------------|------------------|
| `raise DocumentWriteError(...)` | `Err(DocumentWriteError::new(...))` |
| `except Exception as e: raise X(e)` | `.map_err(|e| X::from(e))?` |
| `assert isinstance(...)` | Type-level guarantee via generics |
| `raise ValueError(...)` | `Err(anyhow!("..."))` or custom variant |
| `raise TypeError(...)` | Compile-time type checking |
| Plain `pass` on errors | `Result::ok()` or explicit match |

---

## 7. Ownership & Data Flow

### Current Python Data Flow

```
Parsers → Typed Document Model (Pydantic)
                      ↓
            DocumentWriter.write(document)
                      ↓
            Internal _convert() method
                      ↓
            String/bytes builder
                      ↓
            .encode(encoding) → bytes
```

### Ownership in Rust

The write path naturally maps to owned values:

```rust
fn write(&self, document: &DocumentType) -> Result<Vec<u8>, WriterError>
```

Key observations:
1. **Read-only access:** Writers never mutate the document model — `&` references suffice.
2. **No shared state:** Writers own their options (`WriteOptions`) and counters (footnote count, list depth).
3. **Stateful writers:** `HTMLWriter` accumulates `self._footnotes`, `LatexWriter` tracks `self._indent_level`, `self._list_stack`. These map to mutable struct fields.
4. **No circular references:** Simple ownership tree — Writer owns Options owns Config.

### Stateful Fields Per Writer

| Writer | Mutable State | Rust Equivalent |
|--------|--------------|-----------------|
| HTMLWriter | `_footnote_counter`, `_footnotes`, `_endnotes` | `&mut self` fields |
| LatexWriter | `_indent_level`, `_list_stack` | Stack via `Vec` |
| RTFWriter | `_font_table`, `_color_table`, `_list_depth` | `HashMap` fields |
| TXTWriter | `_list_depth`, `_list_counters`, `_footnote_counter` | `Vec<i32>`, counter |
| PPTXWriter | `_next_rid`, `_media_counter`, `_chart_counter` | Atomic counters |
| XLSXWriter | `_shared_strings`, `_style_cache`, `_font_cache` | Cached collections |

---

## 8. PyO3 Binding Structure

### Recommended Architecture

```
pyo3_bindings/
├── lib.rs              ← PyO3 init, module registration
├── writers/
│   ├── mod.rs
│   ├── base.rs         ← PyDocumentWriter trait → Python class
│   ├── usdm/
│   │   ├── markdown_writer.rs
│   │   ├── html_writer.rs
│   │   ├── latex_writer.rs
│   │   ├── docx_writer.rs
│   │   ├── pdf_writer.rs
│   │   └── rtf_writer.rs
│   ├── dsdm/
│   │   ├── json_writer.rs
│   │   ├── yaml_writer.rs
│   │   └── xml_writer.rs
│   ├── esdm/
│   │   ├── xlsx_writer.rs
│   │   └── csv_writer.rs
│   ├── msdm/
│   │   ├── sql_ddl_writer.rs
│   │   └── neo4j_schema_writer.rs
│   ├── psdm/
│   │   └── pptx_writer.rs
│   └── osdm/
│       └── bpmn_writer.rs
└── types/
    ├── mod.rs           ← Pydantic model → PyAny conversion
    ├── write_options.rs
    ├── write_result.rs
    └── document_wrapper.rs
```

### Key Binding Pattern

```python
# Python side (current):
class MarkdownWriter(BaseDocumentWriter):
    async def write(self, document):
        return self._convert_usdm_to_markdown(document).encode(...)
```

```rust
// Rust side (PyO3):
#[pyclass]
struct MarkdownWriter {
    options: WriteOptions,
}

#[pymethods]
impl MarkdownWriter {
    #[new]
    fn new(options: Option<WriteOptions>) -> Self { ... }

    fn write(&self, py: Python, document: &PyAny) -> PyResult<Vec<u8>> {
        let doc: USDMDocument = document.extract()?;
        let result = self.convert_to_markdown(&doc);
        Ok(result.into_bytes())
    }

    // async requires pyo3-asyncio
    fn write_stream<'p>(&'p self, py: Python<'p>, document: &PyAny)
        -> PyResult<&'p PyAny> { ... }
}
```

### Async Handling

All writers are `async def`. For PyO3:
- Use `pyo3-asyncio` to bridge Rust async → Python async.
- Or offer sync Rust API + PyO3 async wrapper.
- Streaming (`AsyncIterator[bytes]`) → Rust `futures::Stream<Item=bytes::Bytes>`.

---

## 9. Writer-by-Writer Scoring

### Legend
- **5/5:** Trivial — direct string formatting, no binary deps
- **4/5:** Easy — `serde` serialization, standard library only
- **3/5:** Medium — XML or complex escaping, some library deps
- **2/5:** Hard — ZIP + XML binary packaging, significant library
- **1/5:** Very Hard — Binary format with no mature Rust crate

### USDM Writers

| Writer | Files | LOC | Score | Rationale |
|--------|-------|-----|-------|-----------|
| TXTWriter | 1 | 365 | **5/5** | Plain text. Pure string formatting. No dependencies. |
| MarkdownWriter | 1 | 286 | **5/5** | String formatting with `#` prefixes, `|` tables. |
| LatexWriter | 1 | 636 | **4/5** | LaTeX escaping + string wrapping. Easy but long. |
| HTMLWriter | 1 | 713 | **4/5** | String building + `html.escape`. Long but simple. |
| RTFWriter | 1 | 629 | **3/5** | RTF control word format. Stateful font/color tables. |
| DOCXWriter | 8 | ~2,400 | **2/5** | XML string building (quick-xml could simplify) + ZIP packaging. |
| PDFWriter | 13 | ~2,200 | **2/5** | Full PDF 1.7 spec. Own object model (xref, streams, encryption). |

### PSDM Writers

| Writer | Files | LOC | Score | Rationale |
|--------|-------|-----|-------|-----------|
| PPTXWriter | 19 | ~3,500 | **2/5** | Largest writer. ZIP + 6+ XML parts + media + charts + animation. |
| RevealJS/HTML | ~1 each | ~200 | **4/5** | HTML template generation. |
| ImpressJS/DeckJS | ~1 each | ~200 | **4/5** | HTML/CSS/JS template generation. |
| StageCraft | ~1 | ~200 | **4/5** | Similar to RevealJS. |

### DSDM Writers

| Writer | LOC | Score | Rationale |
|--------|-----|-------|-----------|
| JSONWriter | 25 | **5/5** | `json.dumps()` → `serde_json::to_string()` |
| YAMLWriter | 24 | **5/5** | `yaml.dump()` → `serde_yaml::to_string()` |
| CBORWriter | 24 | **5/5** | `cbor2.dumps()` → `ciborium::into_writer()` |
| MsgPackWriter | 28 | **5/5** | `msgpack.packb()` → `rmp_serde::to_vec()` |
| BSONWriter | 33 | **5/5** | `bson.encode()` → `bson::to_document()` |
| XMLWriter | 134 | **3/5** | ElementTree → quick-xml with schema ordering |
| ProtobufWriter | 45 | **4/5** | `prost` with FileDescriptorSet |
| PickleWriter | small | **1/5** | **Do NOT migrate** — security risk. |
| SQLDataWriter | 120 | **3/5** | SQL string generation + runtime DB writes |
| MongoDBWriter | 65 | **3/5** | Delegates to BSON + live collection |
| RedisWriter | 57 | **4/5** | Delegates to JSON + live set |
| CassandraWriter | 50 | **3/5** | CQL generation + prepared statements |
| CSV/TSV | 20 | **5/5** | Columnar text output |

### ESDM Writers

| Writer | Files | LOC | Score | Rationale |
|--------|-------|-----|-------|-----------|
| CSV/TSV | 1 | 143 | **5/5** | Built into esdm_writer.py. `csv.writer`. |
| XLSX | 15 | ~3,500 | **2/5** | ZIP + XML + styles/sub-system + shared strings + pivot + VBA. |

### MSDM Writers

| Writer | LOC | Score | Rationale |
|--------|-----|-------|-----------|
| SqlDDLWriter | 313 | **4/5** | SQL string generation + optional runtime DB. Clean mapping. |
| Neo4jSchemaWriter | 170 | **4/5** | Cypher string generation + runtime. |
| ProtoMsdmWriter | ~100 | **4/5** | Protobuf `.proto` file generation. |
| JSONSchemaWriter | ~100 | **4/5** | JSON schema output → `serde_json` |
| XSDWriter | ~100 | **3/5** | XML Schema → `quick-xml` |
| PlantUMLWriter | ~100 | **5/5** | String diagram format. |
| ThriftIDLWriter | ~100 | **4/5** | IDL string generation. |
| PythonModelWriter | ~100 | **5/5** | Python source code generation (irrelevant) |
| TypeScriptInterfaceWriter | ~100 | **N/A** | TS output (keep as-is in Python or skip) |
| ERDWriter | ~100 | **4/5** | Entity relationship diagrams (text). |
| GraphQLSchemaWriter | ~100 | **4/5** | GraphQL SDL string generation. |
| OWLWriter | ~100 | **3/5** | XML/rdf → `quick-xml` |

### KSDM Writers

| Writer | Score | Rationale |
|--------|-------|-----------|
| PMMLWriter | **3/5** | XML generation for PMML 4.x |
| ONNXWriter | **4/5** | Protobuf serialization → `prost` |
| SklearnWriter | **5/5** | JSON model card |
| PyTorchWriter | **5/5** | JSON model card |
| RDFWriter | **3/5** | Turtle/N-Triples serialization |
| RMLWriter | **4/5** | RDF Mapping Language (text) |
| Mondrian/CWM/etc. | **3/5** | XML schema generators |

### SSDM Writers

| Writer | LOC | Score | Rationale |
|--------|-----|-------|-----------|
| OpenAPIWriter | 345 | **4/5** | Dict building → `serde_json`. Clean model mapping. |
| GraphQLServiceWriter | 313 | **4/5** | SDL string building. |
| AsyncAPIWriter | ~100 | **4/5** | JSON → `serde_json` |
| MCPWriter | ~100 | **4/5** | JSON-RPC model writer. |
| ProtoServiceWriter | ~100 | **4/5** | `.proto` file generation. |
| PythonServiceWriter | ~100 | **N/A** | Python code gen (skip or reimplement) |
| WSDLWriter | ~100 | **2/5** | Complex XML schema + SOAP descriptors. |
| YANGWriter | ~100 | **3/5** | YANG module generation (text format). |

### OSDM Writers

| Writer | LOC | Score | Rationale |
|--------|-----|-------|-----------|
| BPMNXMLWriter | 802 | **2/5** | Very deep XML tree, 30+ model types. |
| CMMNXMLWriter | ~200 | **3/5** | Case management XML. |
| DMNXMLWriter | ~200 | **3/5** | Decision model XML. |
| PNMLWriter | ~200 | **3/5** | Petri net XML. |
| EPCWriter | ~150 | **3/5** | Event Process Chain XML. |
| GraphMLWriter | ~150 | **4/5** | Graph markup XML. |
| PrefectDAGWriter | ~150 | **4/5** | Prefect YAML/JSON. |
| SCXMLWriter | ~200 | **3/5** | State chart XML. |
| XPDWriter | ~150 | **3/5** | XML Process Definition. |
| UMLStateMachineWriter | ~200 | **3/5** | UML state machine text. |
| CEPWriter | ~100 | **4/5** | Complex Event Processing patterns. |

### LSDM Writers

| Writer | Score | Rationale |
|--------|-------|-----------|
| XESWriter | **3/5** | Event log XML standard. |
| CEFWriter | **5/5** | Common Event Format (line-oriented text). |
| SyslogWriter | **5/5** | Text log format. |
| ESBulkWriter | **5/5** | Elasticsearch NDJSON. |

### BAM & TSDM Writers

| Writer | Score | Rationale |
|--------|-------|-----------|
| BamJsonWriter | **5/5** | `json.dumps()` → `serde_json` |
| BamYamlWriter | **5/5** | `yaml.dump()` → `serde_yaml` |
| TsdmJsonWriter | 209 LOC | **4/5** | Pure JSON with conditional fields. Complex `isinstance` chain. |

---

## 10. Cross-Cutting Concerns

### 10.1 Async → Sync

All 197 files use `async def write()`. For Rust:
- **Option A:** Keep async (Tokio) — better for streaming, DB operations.
- **Option B:** Offer sync API — writers are CPU-bound (string formatting, ZIP compression).

**Recommendation:** Sync for pure format generators (Markdown, JSON, XML, LaTeX). Async for DB-targeted writers (MongoDB, Redis, Cassandra, SQL).

### 10.2 XML Generation Strategy

Three patterns exist:
1. **String concat** (DOCX, RTF): `f"<w:t>{text}</w:t>"` — Fast but fragile.
2. **ElementTree** (OSDM, XLSX base, XML writer): `SubElement(root, tag, attrib)` — Slower but well-formed.
3. **Template** (minimal in HTML/LaTeX): `{{ content }}` — Custom template engine.

**Rust strategy:** Use `quick-xml` `Writer` for all XML. The `Event` API matches ElementTree patterns; `Writer` with `write_event` matches string building.

### 10.3 ZIP Packaging

DOCX, PPTX, XLSX all use `zipfile.ZipFile` in-memory. The `zip` crate provides `ZipWriter` with identical semantics. Streaming ZIP is possible for large documents.

### 10.4 Encoding

Every writer has `encoding: str = "utf-8"`. UTF-8 is the default. Rust's `String` / `Vec<u8>` handles this natively — no migration work needed for encoding.

### 10.5 Shared DrawingML Helpers

`drawingml_helpers.py` (231 LOC) is imported by PPTX writers. It builds XML fragments for colors, fills, lines, effects, 3D, and text. This should become a shared Rust module under `writers/psdm/shared/`.

### 10.6 Versioning Strategy

`versioning.py` implements `VersioningContext` for file naming:
- `OVERWRITE`, `NEW_VERSION`, `AUTO_INCREMENT` strategies
- Semantic version parsing (`major.minor.patch`)
- Path pattern matching via regex

This is completely self-contained (stdlib only) and trivial to migrate.

### 10.7 `node_to_python` Dependency

DSDM writers (JSON, YAML, CBOR, BSON, MsgPack) all depend on `dsdm_parsers.dsdm_utils.node_to_python` to convert `DataNode` tree → Python dict. This means the DSDM parser's Python-specific tree structure propagates into writers.

**For Rust:** Define a `ToJsonValue` trait on `DataNode` that directly produces `serde_json::Value`, avoiding the intermediate Python dict.

### 10.8 Conditional Library Imports

Several writers use try/except for optional dependencies:
```python
try:
    from neo4j import AsyncGraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
```

In Rust, use Cargo feature flags: `#[cfg(feature = "neo4j")]`.

### 10.9 File Size Estimation

| Writer Group | Est. Rust LOC | Dev Effort | Priority |
|-------------|---------------|------------|----------|
| DSDM (JSON/YAML/CBOR/MsgPack/BSON) | 500 | 1 week | P0 — Highest ROI |
| TXT/Markdown/LaTeX/HTML/RTF | 2,000 | 2 weeks | P0 — Simple, high value |
| MSDM (all 18 writers) | 3,000 | 3 weeks | P1 — Moderate complexity |
| SSDM (all 9 writers) | 2,000 | 2 weeks | P1 |
| LSDM | 500 | 3 days | P1 |
| BAM/TSDM | 300 | 2 days | P1 |
| ESDM XLSX | 3,500 | 4 weeks | P2 — High complexity |
| USDM DOCX | 2,400 | 3 weeks | P2 |
| USDM PDF | 2,200 | 3 weeks | P2 |
| PSDM PPTX | 3,500 | 4 weeks | P2 |
| OSDM (all XML) | 3,000 | 3 weeks | P2 |
| CSDM DWG/DXF | 2,000 | 4 weeks | P3 — Needs binary crate research |

---

## 11. Recommended Migration Order

### Phase 1: Quick Wins (Estimated: 2-3 weeks)
Focus on zero-dependency, pure-string writers.

1. **DSDM JSON/YAML/CBOR/MsgPack/BSON** — Trivial `serde` wrappers
2. **USDM TXT** — Plain text only
3. **USDM Markdown** — String formatting
4. **BAM JSON/YAML** — Tiny files
5. **TSDM JSON** — Single file
6. **LSDM CEF/Syslog/ES Bulk** — Line-oriented text
7. **MSDM PlantUML, PythonModel** — String generation

### Phase 2: String Formatters (Estimated: 3-4 weeks)
Simple escaping and formatting.

1. **USDM HTML** — HTML escaping + string building
2. **USDM LaTeX** — LaTeX escaping + macros
3. **USDM RTF** — RTF control words
4. **MSDM SQL DDL, GraphQL SDL** — Schema text generation
5. **SSDM OpenAPI, AsyncAPI** — `serde_json` with dict building
6. **MSDM Thrift IDL, TypeScript** — Code generation
7. **MSDM JSON Schema** — `serde_json`

### Phase 3: XML Writers (Estimated: 4-6 weeks)
Everything using `xml.etree.ElementTree`.

1. **DSDM XML** — Simple tree-to-XML
2. **MSDM XSD, OWL, UML XMI** — XML Schema generators
3. **KSDM PMML, Mondrian, CWM, CDM** — XML BI models
4. **OSDM BPMN, CMMN, DMN, PNML, GraphML, SCXML** — Deep XML
5. **LSDM XES** — Event log XML
6. **KSDM RDF** — Turtle/XML RDF

### Phase 4: ZIP + XML (Big Three) (Estimated: 10-12 weeks)

1. **ESDM XLSX** — Largest standalone writer
2. **USDM DOCX** — Word documents
3. **PSDM PPTX** — Presentations

Each requires: ZIP packaging + quick-xml generation + shared string/border/font caching.

### Phase 5: Complex Binary (Estimated: 8-10 weeks)

1. **USDM PDF** — Full PDF 1.7 spec + encryption + optimization
2. **CSDM DWG** — Requires binary spec analysis
3. **CSDM DXF** — ASCII CAD format
4. **KSDM Tableau Hyper** — Proprietary binary
5. **MSDM Protobuf** — FileDescriptorSet integration

### Phase 6: Database Writers (Estimated: 4-6 weeks)

1. **MSDM SQL DDL DB apply** — `sqlx` async engine
2. **DSDM SQLDataWriter** — `sqlx`
3. **DSDM MongoDB** — `mongodb` crate
4. **DSDM Redis** — `redis-rs`
5. **DSDM Cassandra** — `cassandra-rs`
6. **MSDM Neo4j** — `neo4rs`

---

## Appendix A: Key File Inventory

| File Path | Version | Lines | Writer |
|-----------|---------|-------|--------|
| `writers/base.py` | Base class | 69 | All |
| `writers/versioning.py` | Strategy pattern | 85 | All |
| `writers/drawingml_helpers.py` | Shared helpers | 231 | PSDM |
| `writers/usdm_writers/txt/txt_writer.py` | TXT | 365 | USDM |
| `writers/usdm_writers/markdown/markdown_writer.py` | Markdown | 286 | USDM |
| `writers/usdm_writers/latex/latex_writer.py` | LaTeX | 636 | USDM |
| `writers/usdm_writers/html/html_writer.py` | HTML5 | 713 | USDM |
| `writers/usdm_writers/rtf/rtf_writer.py` | RTF 1.9.1 | 629 | USDM |
| `writers/usdm_writers/docx/docx_writer.py` | DOCX | 262 | USDM |
| `writers/usdm_writers/docx/docx_builder.py` | DOCX XML | 735 | USDM |
| `writers/usdm_writers/docx/docx_style_builder.py` | Styles | 396 | USDM |
| `writers/usdm_writers/docx/docx_math_writer.py` | LaTeX→OMML | 547 | USDM |
| `writers/usdm_writers/docx/docx_zip_packager.py` | ZIP | 385 | USDM |
| `writers/usdm_writers/docx/docx_image_handler.py` | Images | 313 | USDM |
| `writers/usdm_writers/pdf/pdf_writer.py` | PDF | 730 | USDM |
| `writers/usdm_writers/pdf/pdf_objects.py` | PDF obj | 502 | USDM |
| `writers/usdm_writers/pdf/content_writer.py` | PDF content | 313 | USDM |
| `writers/usdm_writers/pdf/layout_builder.py` | PDF layout | 223 | USDM |
| `writers/psdm_writers/pptx/writer.py` | PPTX | 538 | PSDM |
| `writers/psdm_writers/pptx/slide_writer.py` | Slides | 204 | PSDM |
| `writers/psdm_writers/pptx/shape_writer.py` | Shapes | est. 300 | PSDM |
| `writers/dsdm_writers/base_dsdm_writer.py` | DSDM base | 102 | DSDM |
| `writers/dsdm_writers/xml_writer.py` | XML | 134 | DSDM |
| `writers/esdm_writers/base.py` | ESDM base | 311 | ESDM |
| `writers/esdm_writers/esdm_writer.py` | ESDM facade | 143 | ESDM |
| `writers/msdm_writers/base_msdm_writer.py` | MSDM base | 180 | MSDM |
| `writers/msdm_writers/sql_ddl_writer.py` | SQL DDL | 313 | MSDM |
| `writers/msdm_writers/neo4j_schema_writer.py` | Neo4j | 170 | MSDM |
| `writers/ssdm_writers/openapi_writer.py` | OpenAPI | 345 | SSDM |
| `writers/ssdm_writers/graphql_service_writer.py` | GraphQL | 313 | SSDM |
| `writers/osdm_writers/bpmn_xml_writer.py` | BPMN XML | 802 | OSDM |
| `writers/tsdm_writers/tsdm_json_writer.py` | TSDM JSON | 209 | TSDM |

## Appendix B: Library Migration Table

| Python Library | Rust Crate | Maturity | Notes |
|---------------|-----------|----------|-------|
| `json` | `serde_json` | ⭐⭐⭐ | Production-grade |
| `yaml` | `serde_yaml` | ⭐⭐⭐ | Production-grade |
| `cbor2` | `ciborium` | ⭐⭐⭐ | Active |
| `msgpack` | `rmp-serde` | ⭐⭐⭐ | Active |
| `bson` | `bson` (mongodb) | ⭐⭐⭐ | Active |
| `protobuf` | `prost` | ⭐⭐⭐ | Production-grade |
| `xml.etree.ElementTree` | `quick-xml` | ⭐⭐⭐ | Fast, low-level |
| `zipfile` | `zip` | ⭐⭐⭐ | Active |
| `sqlalchemy` | `sqlx` | ⭐⭐⭐ | Async-native |
| `sqlalchemy` | `diesel` | ⭐⭐⭐ | Sync ORM |
| `motor` (MongoDB) | `mongodb` | ⭐⭐⭐ | Official driver |
| `neo4j` | `neo4rs` | ⭐⭐ | Active |
| `cassandra-driver` | `cassandra-rs` | ⭐⭐ | Less mature |
| `redis.asyncio` | `redis-rs` | ⭐⭐⭐ | Active |
| `reportlab` (PDF) | `printpdf` | ⭐⭐ | Basic features |
| `reportlab` | `genpdf` | ⭐⭐ | Layout support |
| `reportlab` | `pdf_writer` | ⭐⭐ | Low-level, flexible |
| `python-pptx` | None | ⭐ | **No mature crate** — build custom |
| `python-docx` | `docx-rs` | ⭐⭐ | Basic support only |
| `openpyxl` | `rust_xlsxwriter` | ⭐⭐⭐ | Active, feature-rich |
| `openpyxl` | `calamine` | ⭐⭐⭐ | Read-only |
| `elasticsearch` | `elasticsearch-rs` | ⭐⭐⭐ | Official client |

---

*Report generated by static analysis of `engines/document/writers/`. All 197 Python files were enumerated; ~30 key files were read in full for detailed analysis.*
