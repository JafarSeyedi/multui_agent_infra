# Detail Plan v1.2 — ISDM & ISDM Compliance Enhancement to 100%

## Current State

- **ISDM Overall Compliance**: ~55%
  - BIAggregatorModel parser coverage: 75%
  - ISDMDocument parser coverage: 0%
  - ISDMDocument writer coverage: 0%
  - BI Aggregator writer coverage: 0%
- **KSDM Overall Compliance**: ~50%
  - RML/YAML parser coverage: 60%
  - RML/YAML writer coverage: 50%
  - Native KSDM parser coverage: 0%
  - Native KSDM writer coverage: 35%
  - RDF format coverage: 0%

## Goals

1. Achieve **100% ISDM model field coverage** in parsers and writers
2. Achieve **100% KSDM model field coverage** in parsers and writers
3. Implement **all standard input format parsers** for ISDM and KSDM
4. Implement **all standard output format writers** for ISDM and KSDM
5. Enable **round-trip fidelity** for all supported formats
6. Ensure all implementations follow consistent base class patterns

---

## Phase 1: ISDM Native Document Support (Est: 12h)

### 1.1 — ISDM JSON Parser (3h)

- **File**: `engines/document/parsers/isdm_parsers/isdm_json_parser.py` (NEW)
- **Task**: Parse `.isdm.json` files directly into `ISDMDocument`
- **Input Format**:
  ```json
  {
    "version": "1.0",
    "start_time": "2024-01-01T00:00:00Z",
    "end_time": "2024-01-02T00:00:00Z",
    "granularity": "day",
    "dimensions": ["region", "product"],
    "metrics": [
      {
        "name": "revenue",
        "type": "gauge",
        "value": 150000.0,
        "labels": {"region": "EMEA"},
        "timestamp": "2024-01-01T12:00:00Z",
        "buckets": [0, 100, 500, 1000],
        "bucket_counts": [10, 25, 15, 5]
      }
    ],
    "data_rows": [{"region": "EMEA", "product": "A", "revenue": 75000}],
    "source_info": {"database": "analytics_warehouse"}
  }
  ```
- **Changes**:
  - Extend `BaseDocumentParser`
  - Parse all `ISDMDocument` fields including `Metric` objects
  - Handle `MetricType` enum conversion
  - Handle `TimeGranularity` enum conversion
  - Parse `datetime` fields with ISO format
  - Parse histogram data (`buckets`, `bucket_counts`, `sum_obs`, `count_obs`)
  - Set `kind = DocumentStandard.ISDM`
  - `supported_extensions = [".isdm.json"]`
  - `name = "isdm_json"`

### 1.2 — ISDM YAML Parser (2h)

- **File**: `engines/document/parsers/isdm_parsers/isdm_yaml_parser.py` (NEW)
- **Task**: Parse `.isdm.yaml` files into `ISDMDocument`
- **Changes**:
  - Same logic as ISDM JSON parser but with YAML input
  - `supported_extensions = [".isdm.yaml", ".isdm.yml"]`
  - `name = "isdm_yaml"`

### 1.3 — Metrics Time Series JSON Parser (2h)

- **File**: `engines/document/parsers/isdm_parsers/metrics_json_parser.py` (NEW)
- **Task**: Parse time series metrics format into `ISDMDocument`
- **Input Format**: Array of metric data points with timestamps
- **Changes**:
  - Parse time series JSON array format
  - Group by metric name and labels
  - Set `TimeGranularity` based on timestamp spacing
  - Infer `dimensions` from label keys
  - `supported_extensions = [".metrics.json"]`
  - `name = "metrics_json"`

### 1.4 — ISDM Metrics CSV Parser (2h)

- **File**: `engines/document/parsers/isdm_parsers/metrics_csv_parser.py` (NEW)
- **Task**: Parse CSV metric data into `ISDMDocument`
- **Input Format**: CSV with columns: metric_name, timestamp, value, [label_columns...]
- **Changes**:
  - Parse CSV with configurable delimiter
  - Auto-detect label columns vs metric columns
  - Group rows into `Metric` objects
  - `supported_extensions = [".metrics.csv"]`
  - `name = "metrics_csv"`

### 1.5 — ISDM Base Writer Refactoring (1.5h)

- **File**: `engines/document/writers/isdm_writers/base.py` (MODIFY)
- **Task**: Refactor `ISDMBaseWriter` to properly extend `BaseDocumentWriter`
- **Changes**:
  - Add ISDMWriteOptions with `include_metadata`, `pretty_print`, `include_histogram`
  - Implement `ISDMDocument`-specific serialization
  - Handle `Metric` objects with histogram data
  - Handle `datetime` ISO formatting
  - Handle `TimeGranularity` enum serialization
  - Set `name = "isdm_base"`, `supported_extensions = [".json"]`

### 1.6 — ISDM JSON Writer (1.5h)

- **File**: `engines/document/writers/isdm_writers/isdm_json_writer.py` (NEW)
- **Task**: Write `ISDMDocument` to `.isdm.json`
- **Changes**:
  - Extend `ISDMBaseWriter`
  - Output proper ISDM JSON schema format
  - `supported_extensions = [".isdm.json"]`, `name = "isdm_json"`

### 1.7 — ISDM YAML Writer (1h)

- **File**: `engines/document/writers/isdm_writers/isdm_yaml_writer.py` (NEW)
- **Task**: Write `ISDMDocument` to `.isdm.yaml`
- **Changes**:
  - Extend `ISDMBaseWriter`
  - Output proper ISDM YAML format
  - `supported_extensions = [".isdm.yaml", ".isdm.yml"]`, `name = "isdm_yaml"`

### 1.8 — ISDM CSV Metrics Writer (1.5h)

- **File**: `engines/document/writers/isdm_writers/metrics_csv_writer.py` (NEW)
- **Task**: Write `ISDMDocument` metrics to CSV
- **Changes**:
  - Extend `ISDMBaseWriter`
  - Output metrics as CSV rows with headers
  - `supported_extensions = [".metrics.csv"]`, `name = "metrics_csv"`

---

## Phase 2: BI Aggregator Round-trip Support (Est: 6h)

### 2.1 — BI Aggregator JSON Writer (2h)

- **File**: `engines/document/writers/isdm_writers/bi_aggregator_json_writer.py` (NEW)
- **Task**: Write `BIAggregatorModel` to `.bi.json`
- **Changes**:
  - Extend `ISDMBaseWriter`
  - Handle `BIAggregatorModel` serialization
  - Full `BIAggregation` field coverage including `output_config`
  - `supported_extensions = [".bi.json"]`, `name = "bi_aggregator_json"`

### 2.2 — BI Aggregator YAML Writer (1.5h)

- **File**: `engines/document/writers/isdm_writers/bi_aggregator_yaml_writer.py` (NEW)
- **Task**: Write `BIAggregatorModel` to `.bi.yaml`
- **Changes**:
  - Extend `ISDMBaseWriter`
  - YAML serialization of `BIAggregatorModel`
  - `supported_extensions = [".bi.yaml", ".bi.yml"]`, `name = "bi_aggregator_yaml"`

### 2.3 — Fix BIAggregation Model Definition (0.5h)

- **File**: `engines/document/models/isdm_models.py` (MODIFY)
- **Task**: Fix `output_config` field default factory
- **Changes**:
  - Change `output_config: Dict[str, Any] = Field(default_factory=list)` to `Field(default_factory=dict)`

### 2.4 — Refactor BI Aggregator Parsers (2h)

- **Files**: `engines/document/parsers/isdm_parsers/json_parser.py`, `yaml_parser.py` (MODIFY)
- **Task**: Refactor to use shared logic and fix type issues
- **Changes**:
  - Extract common field extraction logic
  - Fix `output_config` parsing (expect dict, not list)
  - Use `options.encoding` instead of hardcoded `utf-8`
  - Add proper error handling with typed exceptions
  - Ensure `supported_extensions` uses tuple format consistent with base class

---

## Phase 3: KSDM Native Document Support (Est: 12h)

### 3.1 — KSDM JSON Parser (2.5h)

- **File**: `engines/document/parsers/ksdm_parsers/ksdm_json_parser.py` (NEW)
- **Task**: Parse `.ksdm.json` files directly into `KSDMDocument`
- **Input Format**:
  ```json
  {
    "version": "1.0",
    "ontology": {"namespaces": {"ex": "http://example.org/"}},
    "entities": [
      {"id": "ent_1", "type": "Person", "label": "Alice", "properties": {"age": 30}, "embedding": [0.1, 0.2]}
    ],
    "relations": [
      {"id": "rel_1", "source_id": "ent_1", "target_id": "ent_2", "type": "worksFor", "weight": 0.9, "timestamp": "2024-01-01T00:00:00Z"}
    ],
    "attributes": {"graph_name": "org_chart"}
  }
  ```
- **Changes**:
  - Extend `BaseKSDMParser`
  - Parse all `KSDMDocument` fields
  - Parse `Entity.embedding` as `List[float]`
  - Parse `Relation.weight` as `float`
  - Parse `Relation.timestamp`
  - Handle `EntityType` enum conversion
  - Handle `RelationType` enum conversion
  - Handle unknown entity/relation types gracefully
  - `supported_extensions = [".ksdm.json"]`, `name = "ksdm_json"`

### 3.2 — KSDM YAML Parser (1.5h)

- **File**: `engines/document/parsers/ksdm_parsers/ksdm_yaml_parser.py` (NEW)
- **Task**: Parse `.ksdm.yaml` into `KSDMDocument`
- **Changes**:
  - Same logic as KSDM JSON parser
  - `supported_extensions = [".ksdm.yaml", ".ksdm.yml"]`, `name = "ksdm_yaml"`

### 3.3 — CSV Graph Parser (2h)

- **File**: `engines/document/parsers/ksdm_parsers/csv_graph_parser.py` (NEW)
- **Task**: Parse edge-list CSV into `KSDMDocument`
- **Input Format**: CSV with columns: source_id, target_id, relation_type, [properties...]
- **Changes**:
  - Parse CSV edge list
  - Auto-generate entity IDs from source/target columns
  - Support configurable column mapping
  - `supported_extensions = [".csv"]`, `name = "csv_graph"`

### 3.4 — KSDM Base Writer Refactoring (1.5h)

- **File**: `engines/document/writers/ksdm_writers/base.py` (MODIFY)
- **Task**: Refactor `KSDMBaseWriter` to properly extend `BaseDocumentWriter`
- **Changes**:
  - Add KSDMWriteOptions with `include_metadata`, `pretty_print`, `include_embeddings`
  - Implement proper `KSDMWriteOptions` handling
  - Handle `Entity.embedding` serialization
  - Handle `Relation.weight` and `Relation.timestamp` serialization
  - Handle `KSDMDocument.attributes` serialization
  - Set `name = "ksdm_base"`, `supported_extensions = [".json"]`

### 3.5 — KSDM JSON Writer (1.5h)

- **File**: `engines/document/writers/ksdm_writers/ksdm_json_writer.py` (NEW)
- **Task**: Write `KSDMDocument` to `.ksdm.json`
- **Changes**:
  - Extend `KSDMBaseWriter`
  - Output proper KSDM JSON schema format
  - Serialize embeddings, weights, timestamps, attributes
  - `supported_extensions = [".ksdm.json"]`, `name = "ksdm_json"`

### 3.6 — KSDM YAML Writer (1h)

- **File**: `engines/document/writers/ksdm_writers/ksdm_yaml_writer.py` (NEW)
- **Task**: Write `KSDMDocument` to `.ksdm.yaml`
- **Changes**:
  - Extend `KSDMBaseWriter`
  - `supported_extensions = [".ksdm.yaml", ".ksdm.yml"]`, `name = "ksdm_yaml"`

### 3.7 — CSV Graph Writer (1.5h)

- **File**: `engines/document/writers/ksdm_writers/csv_graph_writer.py` (NEW)
- **Task**: Write `KSDMDocument` to edge-list CSV
- **Changes**:
  - Extend `KSDMBaseWriter`
  - Output edges as CSV rows
  - Support configurable column mapping
  - `supported_extensions = [".csv"]`, `name = "csv_graph"`

### 3.8 — RML YAML Writer Refactoring (1.5h)

- **File**: `engines/document/writers/ksdm_writers/rml_yaml_writer.py` (MODIFY)
- **Task**: Refactor to extend `KSDMBaseWriter`
- **Changes**:
  - Change base class from `BaseDocumentWriter` to `KSDMBaseWriter`
  - Add embedding serialization to entity properties
  - Add weight/timestamp serialization to relation properties
  - Add `KSDMDocument.attributes` serialization

---

## Phase 4: RDF Format Support for KSDM (Est: 10h)

### 4.1 — Turtle RDF Parser (2.5h)

- **File**: `engines/document/parsers/ksdm_parsers/turtle_parser.py` (NEW)
- **Task**: Parse RDF Turtle (`.ttl`) format into `KSDMDocument`
- **Changes**:
  - Extend `BaseKSDMParser`
  - Parse Turtle triples into entities and relations
  - Map RDF types to `EntityType` enum
  - Extract labels from `rdfs:label`
  - Extract properties from datatype properties
  - Handle blank nodes
  - `supported_extensions = [".ttl", ".turtle"]`, `name = "turtle"`

### 4.2 — Turtle RDF Writer (2h)

- **File**: `engines/document/writers/ksdm_writers/turtle_writer.py` (NEW)
- **Task**: Write `KSDMDocument` to Turtle format
- **Changes**:
  - Extend `KSDMBaseWriter`
  - Serialize entities as RDF resources with types
  - Serialize relations as RDF triples
  - Use proper RDF namespaces
  - Serialize entity properties as datatype properties
  - `supported_extensions = [".ttl"]`, `name = "turtle"`

### 4.3 — JSON-LD Parser (2h)

- **File**: `engines/document/parsers/ksdm_parsers/jsonld_parser.py` (NEW)
- **Task**: Parse JSON-LD format into `KSDMDocument`
- **Changes**:
  - Extend `BaseKSDMParser`
  - Parse JSON-LD `@graph` structure
  - Map `@type` to `EntityType`
  - Extract `@id` as entity ID
  - Handle nested JSON-LD contexts
  - `supported_extensions = [".jsonld"]`, `name = "jsonld"`

### 4.4 — JSON-LD Writer (1.5h)

- **File**: `engines/document/writers/ksdm_writers/jsonld_writer.py` (NEW)
- **Task**: Write `KSDMDocument` to JSON-LD format
- **Changes**:
  - Extend `KSDMBaseWriter`
  - Output valid JSON-LD with `@context` and `@graph`
  - `supported_extensions = [".jsonld"]`, `name = "jsonld"`

### 4.5 — N-Triples Parser (1h)

- **File**: `engines/document/parsers/ksdm_parsers/ntriples_parser.py` (NEW)
- **Task**: Parse N-Triples format into `KSDMDocument`
- **Changes**:
  - Extend `BaseKSDMParser`
  - Parse line-based N-Triples format
  - `supported_extensions = [".nt"]`, `name = "ntriples"`

### 4.6 — N-Triples Writer (1h)

- **File**: `engines/document/writers/ksdm_writers/ntriples_writer.py` (NEW)
- **Task**: Write `KSDMDocument` to N-Triples format
- **Changes**:
  - Extend `KSDMBaseWriter`
  - Output N-Triples format
  - `supported_extensions = [".nt"]`, `name = "ntriples"`

---

## Phase 5: __init__ Updates and Registry (Est: 2h)

### 5.1 — ISDM Parsers __init__ (0.5h)

- **File**: `engines/document/parsers/isdm_parsers/__init__.py` (MODIFY)
- **Task**: Export all new parser classes

### 5.2 — ISDM Writers __init__ (0.5h)

- **File**: `engines/document/writers/isdm_writers/__init__.py` (MODIFY)
- **Task**: Export all new writer classes

### 5.3 — KSDM Parsers __init__ (0.5h)

- **File**: `engines/document/parsers/ksdm_parsers/__init__.py` (MODIFY)
- **Task**: Export all new parser classes

### 5.4 — KSDM Writers __init__ (0.5h)

- **File**: `engines/document/writers/ksdm_writers/__init__.py` (MODIFY)
- **Task**: Export all new writer classes

---

## Phase 6: Testing (Est: 12h)

### 6.1 — ISDM Model Tests (2h)

- **File**: `tests/document/test_isdm_models.py` (NEW)
- **Task**: Test ISDMDocument, BIAggregatorModel, Metric model instantiation and validation

### 6.2 — ISDM Parser Tests (2.5h)

- **File**: `tests/document/test_isdm_parsers.py` (NEW)
- **Task**: Test all ISDM parsers with sample data files
  - ISDM JSON parser
  - ISDM YAML parser
  - Metrics JSON parser
  - Metrics CSV parser
  - BI Aggregator JSON parser (existing)
  - BI Aggregator YAML parser (existing)

### 6.3 — ISDM Writer Tests (2h)

- **File**: `tests/document/test_isdm_writers.py` (NEW)
- **Task**: Test all ISDM writers
  - ISDM JSON writer
  - ISDM YAML writer
  - Metrics CSV writer
  - BI Aggregator JSON writer
  - BI Aggregator YAML writer
  - Round-trip tests (parse → write → parse)

### 6.4 — KSDM Model Tests (1.5h)

- **File**: `tests/document/test_ksdm_models.py` (NEW)
- **Task**: Test KSDMDocument, Entity, Relation model instantiation

### 6.5 — KSDM Parser Tests (2h)

- **File**: `tests/document/test_ksdm_parsers.py` (NEW)
- **Task**: Test all KSDM parsers
  - KSDM JSON parser
  - KSDM YAML parser
  - Turtle parser
  - JSON-LD parser
  - N-Triples parser
  - CSV graph parser
  - RML YAML parser (existing)

### 6.6 — KSDM Writer Tests (2h)

- **File**: `tests/document/test_ksdm_writers.py` (NEW)
- **Task**: Test all KSDM writers
  - KSDM JSON writer
  - KSDM YAML writer
  - Turtle writer
  - JSON-LD writer
  - N-Triples writer
  - CSV graph writer
  - RML YAML writer (existing)
  - Round-trip tests

---

## Phase 7: Documentation (Est: 6h)

### 7.1 — ISDM Technical Documentation (1.5h)

- **File**: `docs/engines/document/technical_doc/isdm_technical.md` (NEW)
- **Task**: Technical documentation for ISDM architecture, parsers, writers

### 7.2 — KSDM Technical Documentation (1.5h)

- **File**: `docs/engines/document/technical_doc/ksdm_technical.md` (NEW)
- **Task**: Technical documentation for KSDM architecture, parsers, writers

### 7.3 — ISDM User Guide (1.5h)

- **File**: `docs/engines/document/user_guide/isdm_user_guide.md` (NEW)
- **Task**: User-facing documentation for ISDM usage, examples, format reference

### 7.4 — KSDM User Guide (1.5h)

- **File**: `docs/engines/document/user_guide/ksdm_user_guide.md` (NEW)
- **Task**: User-facing documentation for KSDM usage, examples, format reference

---

## Total Estimated Time: ~60 hours

## Success Criteria

- [ ] All ISDM model fields covered by parsers and writers
- [ ] All KSDM model fields covered by parsers and writers
- [ ] Round-trip fidelity ≥95% for all supported formats
- [ ] All tests passing with ≥90% coverage
- [ ] Documentation complete for all public APIs
- [ ] All exports properly registered in __init__.py files
- [ ] No mypy type errors in new code
