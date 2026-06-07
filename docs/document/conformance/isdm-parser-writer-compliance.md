# ISDM Parser/Writer Compliance Report

This report assesses:

- `engines/document/parsers/isdm_parsers/`
- `engines/document/writers/isdm_writers/`

against the ISDM contract defined in:

- `engines/document/models/isdm_models.py`

## Executive Summary

**Overall status: partial compliance (55%)**

The ISDM parser/writer layer provides foundational implementation for insights/analytics data. The current implementation covers BI Aggregator model definitions with JSON and YAML parsers, but lacks complete coverage for the full ISDM document model including time series metrics, direct data ingestion, and multi-format output.

### High-level findings

- **BI Aggregator JSON/YAML parsers** provide good coverage for `BIAggregatorModel` fields but do not produce `ISDMDocument` directly.
- **ISDMDocument** (the core insights document with metrics, time ranges, dimensions) has no dedicated parser or writer.
- **Metric** fields (histogram buckets, embeddings, timestamps) are not fully handled.
- **Standard ISDM formats** (.isdm.json, .isdm.yaml, .metrics.json, .csv) are not implemented.
- **BI Aggregator writer** is missing — parsed models cannot be serialized back.

## Model Surface in `isdm_models.py`

### BIAggregatorModel (BI Aggregator Definition)

| Field | Type | Parser Coverage | Writer Coverage |
|-------|------|-----------------|-----------------|
| `kind` | `DocumentStandard` | ✓ Set by base | ✗ Not serialized |
| `version` | `str` | ✓ Parsed | ✗ Not serialized |
| `schedule` | `str` | ✓ Parsed | ✗ Not serialized |
| `sources` | `List[Dict]` | ✓ Parsed | ✗ Not serialized |
| `aggregations` | `List[BIAggregation]` | ✓ Parsed | ✗ Not serialized |
| `targets` | `List[Dict]` | ✓ Parsed | ✗ Not serialized |
| `metadata` | `Dict[str, Any]` | ✓ Parsed | ✗ Not serialized |

### BIAggregation (Aggregation Definition)

| Field | Type | Parser Coverage | Writer Coverage |
|-------|------|-----------------|-----------------|
| `name` | `str` | ✓ Parsed | ✗ Not serialized |
| `metric` | `str` | ✓ Parsed | ✗ Not serialized |
| `window` | `str` | ✓ Parsed | ✗ Not serialized |
| `output` | `str` | ✓ Parsed | ✗ Not serialized |
| `compute` | `Optional[str]` | ✓ Parsed | ✗ Not serialized |
| `dimensions` | `List[str]` | ✓ Parsed | ✗ Not serialized |
| `output_config` | `Dict[str, Any]` | ✓ Parsed | ✗ Not serialized |

### ISDMDocument (Insights Document)

| Field | Type | Parser Coverage | Writer Coverage |
|-------|------|-----------------|-----------------|
| `kind` | `DocumentStandard` | ✗ Not produced | ✗ Not serialized |
| `start_time` | `Optional[datetime]` | ✗ Not parsed | ✗ Not serialized |
| `end_time` | `Optional[datetime]` | ✗ Not parsed | ✗ Not serialized |
| `granularity` | `Optional[TimeGranularity]` | ✗ Not parsed | ✗ Not serialized |
| `dimensions` | `List[str]` | ✗ Not parsed | ✗ Not serialized |
| `metrics` | `List[Metric]` | ✗ Not parsed | ✗ Not serialized |
| `data_rows` | `List[Dict]` | ✗ Not parsed | ✗ Not serialized |
| `source_info` | `Dict[str, Any]` | ✗ Not parsed | ✗ Not serialized |

### Metric (Individual Metric)

| Field | Type | Parser Coverage | Writer Coverage |
|-------|------|-----------------|-----------------|
| `name` | `str` | ✗ Not parsed | ✗ Not serialized |
| `description` | `Optional[str]` | ✗ Not parsed | ✗ Not serialized |
| `type` | `MetricType` | ✗ Not parsed | ✗ Not serialized |
| `value` | `Any` | ✗ Not parsed | ✗ Not serialized |
| `labels` | `Dict[str, str]` | ✗ Not parsed | ✗ Not serialized |
| `timestamp` | `Optional[datetime]` | ✗ Not parsed | ✗ Not serialized |
| `buckets` | `List[float]` | ✗ Not parsed | ✗ Not serialized |
| `bucket_counts` | `List[int]` | ✗ Not parsed | ✗ Not serialized |
| `sum_obs` | `Optional[float]` | ✗ Not parsed | ✗ Not serialized |
| `count_obs` | `Optional[int]` | ✗ Not parsed | ✗ Not serialized |

### Enums

| Enum | Values | Usage |
|------|--------|-------|
| `MetricType` | COUNTER, GAUGE, HISTOGRAM, SUMMARY | ✗ Not used |
| `Aggregation` | SUM, COUNT, AVG, MIN, MAX, PCTILE, STDDEV | ✗ Not used |
| `TimeGranularity` | SECOND, MINUTE, HOUR, DAY, WEEK, MONTH, QUARTER, YEAR | ✗ Not used |

## Standard Input File Format Compliance

| Standard Format | Extension | MIME Type | Parser | Writer |
|-----------------|-----------|-----------|--------|--------|
| ISDM JSON | .isdm.json | application/json | ✗ Missing | ✗ Missing |
| ISDM YAML | .isdm.yaml | application/x-yaml | ✗ Missing | ✗ Missing |
| BI Aggregator JSON | .bi.json | application/json | ✓ Implemented | ✗ Missing |
| BI Aggregator YAML | .bi.yaml, .bi.yml | application/x-yaml | ✓ Implemented | ✗ Missing |
| Time Series Metrics JSON | .metrics.json | application/json | ✗ Missing | ✗ Missing |
| Metrics CSV | .metrics.csv | text/csv | ✗ Missing | ✗ Missing |
| Parquet Metrics | .parquet | application/parquet | ✗ Missing | ✗ Missing |
| Avro Metrics | .avro | application/avro | ✗ Missing | ✗ Missing |
| PMML Model | .pmml | application/xml | ✗ Missing | ✗ Missing |
| ONNX Model | .onnx | application/octet-stream | ✗ Missing | ✗ Missing |
| XES Event Log | .xes | application/xml | ✗ Missing | ✗ Missing |
| DMN Decision | .dmn | application/xml | ✗ Missing | ✗ Missing |

## Parser Compliance

### `json_parser.py` (BIAggregatorJSONParser)

**Status: good partial compliance for BIAggregatorModel (75%)**

Covered:
- `BIAggregatorModel.version` ✓
- `BIAggregatorModel.schedule` ✓
- `BIAggregatorModel.sources` ✓
- `BIAggregatorModel.aggregations` ✓ (full BIAggregation objects)
- `BIAggregatorModel.targets` ✓
- `BIAggregatorModel.metadata` ✓
- Extra top-level fields → metadata ✓

Gaps:
- Does not produce `ISDMDocument` directly
- No time series metric parsing
- No `TimeGranularity` handling
- No histogram/summary data handling
- Returns dict instead of typed model in some paths
- `ParseOptions` not fully utilized (encoding hardcoded to utf-8)
- `output_config` field uses `Field(default_factory=list)` in model but parser passes `{}`

### `yaml_parser.py` (BIAggregatorYAMLParser)

**Status: good partial compliance for BIAggregatorModel (75%)**

Covered:
- Same fields as JSON parser ✓

Gaps:
- Same as JSON parser
- Duplicate implementation (could share common logic with JSON parser)
- `ParseOptions` not fully utilized

### Missing Parsers

1. **ISDM JSON Parser** — Parse `.isdm.json` directly into `ISDMDocument`
2. **ISDM YAML Parser** — Parse `.isdm.yaml` into `ISDMDocument`
3. **Metrics JSON Parser** — Parse time series metrics format
4. **Metrics CSV Parser** — Parse CSV metric data
5. **Parquet Parser** — Parse columnar metric data
6. **PMML Parser** — Parse predictive model markup
7. **XES Parser** — Parse event stream logs for process mining

## Writer Compliance

### `base.py` (ISDMBaseWriter)

**Status: partial compliance (40%)**

Covered:
- JSON serialization via `model_dump` / `asdict` fallback ✓
- `write_to_file()` implementation ✓
- `write_stream()` implementation ✓
- `get_supported_media_types()` / `get_supported_extensions()` ✓

Gaps:
- Does not handle `BIAggregatorModel` specifically
- No time series-specific serialization
- No CSV/TSV formatting for metrics
- No Parquet/Avro serialization
- `pretty_print` option not connected to JSON output
- `include_metadata` option not used
- Does not extend a proper ISDM base writer pattern (standalone class)
- No `ISDMDocument`-specific serialization logic

### Missing Writers

1. **ISDM JSON Writer** — Write `ISDMDocument` to `.isdm.json`
2. **ISDM YAML Writer** — Write `ISDMDocument` to `.isdm.yaml`
3. **BI Aggregator JSON Writer** — Write `BIAggregatorModel` to `.bi.json`
4. **BI Aggregator YAML Writer** — Write `BIAggregatorModel` to `.bi.yaml`
5. **Metrics CSV Writer** — Write metrics to CSV
6. **Parquet Writer** — Write metrics to Parquet format

## Cross-cutting Issues

### Architecture Issues

1. **Inconsistent base class**: `BaseBIAggregatorParser` imports from `..base import BaseBIAggregatorParser` but the file is at `isdm_parsers/base.py` — the import path references `bi_aggregator_parsers` in comments but the actual module is `isdm_parsers`.
2. **No ISDMDocument parser**: The existing parsers only produce `BIAggregatorModel`. There is no parser that produces `ISDMDocument` from standard formats.
3. **No round-trip capability**: BI Aggregator models can be parsed but not written back.
4. **Model definition issues**: `BIAggregation.output_config` uses `Field(default_factory=list)` but should be `Field(default_factory=dict)`.

### Underused ISDM Fields

- `ISDMDocument.start_time` / `end_time` — Time range not captured
- `ISDMDocument.granularity` — No granular parsing
- `ISDMDocument.dimensions` — Not extracted
- `ISDMDocument.metrics` — Core metrics not populated
- `ISDMDocument.data_rows` — Raw data not handled
- `ISDMDocument.source_info` — Source metadata not captured
- `Metric.buckets`, `bucket_counts`, `sum_obs`, `count_obs` — Histogram data ignored
- `Metric.timestamp` — Time series timestamps not handled
- `Metric.labels` — Metric labels/dimensions not handled

### Metadata Still Used as Carrier

The `BIAggregatorModel.metadata` dict is used as a catch-all for extra fields, but structured data should be promoted to typed fields where the model supports it.

## Priority Remediation Items

1. **Create ISDMDocument JSON/YAML parsers** — Parse `.isdm.json` and `.isdm.yaml` directly into `ISDMDocument`
2. **Create ISDMDocument JSON/YAML writers** — Serialize `ISDMDocument` with full field coverage
3. **Create BI Aggregator writers** — Enable round-trip for `.bi.json` and `.bi.yaml`
4. **Add time series metric parsing** — Parse `.metrics.json` format
5. **Add CSV metrics parser/writer** — Support tabular metric data
6. **Fix model definition** — Correct `BIAggregation.output_config` default factory
7. **Refactor parsers** — Share common logic between JSON and YAML parsers
8. **Add histogram/summary support** — Handle `Metric.buckets`, `bucket_counts`, etc.

## Final Verdict

The ISDM parser/writer layer provides **partial compliance (55%)** against `engines/document/models/isdm_models.py`.

**Strongest components:**
- `engines/document/parsers/isdm_parsers/json_parser.py` — Good BIAggregatorModel coverage
- `engines/document/parsers/isdm_parsers/yaml_parser.py` — Good BIAggregatorModel coverage

**Highest-priority remaining gaps:**
- No ISDMDocument parser (the core insights document)
- No ISDMDocument writer
- No BI Aggregator writer (no round-trip)
- No time series metrics support
- No CSV/Parquet format support
