# KSDM Parser/Writer Compliance Report

This report assesses:

- `engines/document/parsers/ksdm_parsers/`
- `engines/document/writers/ksdm_writers/`

against the KSDM contract defined in:

- `engines/document/models/ksdm_models.py`

## Executive Summary

**Overall status: partial compliance (50%)**

The KSDM parser/writer layer provides foundational implementation for knowledge graph data. The current implementation covers RML/YAML parsing for graph extraction and basic JSON output, but lacks complete coverage for the full KSDM document model including RDF, Turtle, JSON-LD, CSV, and other standard graph serialization formats.

### High-level findings

- **RML/YAML parser** provides partial coverage for extracting entities and relations from RML mappings, but uses heuristic type inference.
- **RML/YAML writer** can serialize KSDM documents back to RML format, but does not extend the base writer class.
- **KSDMDocument JSON** serialization exists in the base writer but is generic (no KSDM-specific formatting).
- **Standard RDF formats** (Turtle, JSON-LD, RDF/XML, N-Triples, N-Quads) are completely unimplemented.
- **Entity.embedding** field is not handled by any parser or writer.
- **Relation.timestamp** for temporal graphs is not handled.

## Model Surface in `ksdm_models.py`

### KSDMDocument (Knowledge Graph Document)

| Field | Type | Parser Coverage | Writer Coverage |
|-------|------|-----------------|-----------------|
| `kind` | `DocumentStandard` | ✓ Set by base | ✗ Not serialized |
| `ontology` | `Dict[str, Any]` | ✓ Stored (raw RML) | ✓ Serialized (RML only) |
| `entities` | `List[Entity]` | ✓ Extracted | ✓ Serialized (RML only) |
| `relations` | `List[Relation]` | ✓ Extracted | ✓ Serialized (RML only) |
| `attributes` | `Dict[str, Any]` | ✗ Not populated | ✗ Not serialized |

### Entity (Graph Node)

| Field | Type | Parser Coverage | Writer Coverage |
|-------|------|-----------------|-----------------|
| `id` | `str` | ✓ Generated | ✓ Serialized |
| `type` | `EntityType` | ✓ Inferred (heuristic) | ✗ Not mapped to RML types |
| `label` | `Optional[str]` | ✓ From source name | ✓ Serialized |
| `properties` | `Dict[str, Any]` | ✓ Basic extraction | ✓ Basic serialization |
| `embedding` | `List[float]` | ✗ Not extracted | ✗ Not serialized |

### Relation (Graph Edge)

| Field | Type | Parser Coverage | Writer Coverage |
|-------|------|-----------------|-----------------|
| `id` | `str` | ✓ Generated | ✓ Serialized |
| `source_id` | `str` | ✓ Generated | ✓ Serialized |
| `target_id` | `str` | ✓ Generated | ✓ Serialized |
| `type` | `RelationType` | ✓ Inferred (heuristic) | ✓ Serialized |
| `properties` | `Dict[str, Any]` | ✓ Basic extraction | ✓ Basic serialization |
| `weight` | `float` | ✗ Not extracted | ✗ Not serialized |
| `timestamp` | `Optional[Any]` | ✗ Not extracted | ✗ Not serialized |

### Enums

| Enum | Values | Usage |
|------|--------|-------|
| `EntityType` | PERSON, ORGANIZATION, LOCATION, EVENT, WORK, CONCEPT, ITEM | ✓ Heuristic inference in RML parser |
| `RelationType` | WORKS_FOR, LOCATED_IN, PART_OF, FRIEND_OF, FOLLOWS, BASED_ON, RELATED_TO | ✓ Heuristic inference in RML parser |

## Standard Input File Format Compliance

| Standard Format | Extension | MIME Type | Parser | Writer |
|-----------------|-----------|-----------|--------|--------|
| KSDM JSON | .ksdm.json | application/json | ✗ Missing | ✗ Missing |
| KSDM YAML | .ksdm.yaml | application/x-yaml | ✗ Missing | ✗ Missing |
| RDF Turtle | .ttl, .turtle | text/turtle | ✗ Missing | ✗ Missing |
| RDF/XML | .rdf, .rdfxml | application/rdf+xml | ✗ Missing | ✗ Missing |
| JSON-LD | .jsonld | application/ld+json | ✗ Missing | ✗ Missing |
| N-Triples | .nt | application/n-triples | ✗ Missing | ✗ Missing |
| N-Quads | .nq | application/n-quads | ✗ Missing | ✗ Missing |
| TriG | .trig | application/trig | ✗ Missing | ✗ Missing |
| RML YAML | .rml.yaml, .rml.yml | application/yaml | ✓ Implemented | ✓ Implemented |
| RML XML | .rml.xml | application/rml+xml | ✗ Missing | ✗ Missing |
| CSV Graph | .csv | text/csv | ✗ Missing | ✗ Missing |

## Parser Compliance

### `base.py` (BaseKSDMParser)

**Status: foundational (provides interface only)**

The base parser provides:
- `parse_bytes()` → `KSDMDocument` ✓
- `parse_path()` → `KSDMDocument` ✓
- `parse_stream()` → `KSDMDocument` ✓
- Media type detection ✓
- Abstract `_parse_to_knowledge_graph()` method ✓

### `rml_yaml_parser.py` (RMLYAMLParser)

**Status: partial compliance (60%)**

Covered:
- `KSDMDocument.ontology` ✓ (stores raw RML mapping)
- `KSDMDocument.entities` ✓ (extracted from sources and mappings)
- `KSDMDocument.relations` ✓ (extracted from predicate-object maps)
- `Entity.id` ✓ (generated from hash)
- `Entity.type` ✓ (keyword-based heuristic inference)
- `Entity.label` ✓ (from source/mapping name)
- `Entity.properties` ✓ (basic extraction)
- `Relation.id` ✓ (generated)
- `Relation.source_id` / `target_id` ✓ (generated from hash)
- `Relation.type` ✓ (predicate-based heuristic inference)
- `Relation.properties` ✓ (basic extraction)

Gaps:
- `KSDMDocument.attributes` not populated
- `Entity.embedding` not extracted
- `Relation.weight` not extracted
- `Relation.timestamp` not parsed for temporal graphs
- Entity type inference is heuristic (keyword matching), not semantic
- Relation type inference is heuristic (predicate keyword matching)
- No RDF/Turtle parsing
- No JSON-LD parsing
- No CSV graph parsing
- No N-Triples/N-Quads parsing
- `Entity.properties` only captures source definition, not rich attributes
- `Relation.properties` only captures mapping definition
- Source entity and target entity IDs use different hash functions, causing mismatches
- No deduplication of entities across multiple mappings

### Missing Parsers

1. **KSDM JSON Parser** — Parse `.ksdm.json` directly into `KSDMDocument`
2. **KSDM YAML Parser** — Parse `.ksdm.yaml` into `KSDMDocument`
3. **Turtle Parser** — Parse RDF Turtle format using `rdflib`
4. **RDF/XML Parser** — Parse RDF/XML format
5. **JSON-LD Parser** — Parse JSON-LD format
6. **N-Triples Parser** — Parse N-Triples format
7. **N-Quads Parser** — Parse N-Quads format
8. **CSV Graph Parser** — Parse edge-list CSV format
9. **RML XML Parser** — Parse RML in XML format

## Writer Compliance

### `base.py` (KSDMBaseWriter)

**Status: partial compliance (35%)**

Covered:
- JSON serialization via `model_dump` / `asdict` fallback ✓
- `write_to_file()` implementation ✓
- `write_stream()` implementation ✓
- `get_supported_media_types()` / `get_supported_extensions()` ✓

Gaps:
- Generic JSON output, not KSDM-specific formatting
- No Turtle/RDF output
- No JSON-LD serialization
- No CSV edge-list output
- No N-Triples/N-Quads output
- `pretty_print` option not connected to JSON output
- Does not extend `BaseDocumentWriter` (standalone class)
- No ontology serialization
- No embedding vector serialization
- No namespace handling for RDF output

### `rml_yaml_writer.py` (RMLYAMLWriter)

**Status: partial compliance (50%)**

Covered:
- `KSDMDocument.ontology` → RML prefix structure ✓
- `KSDMDocument.entities` → RML sources ✓
- `KSDMDocument.relations` → RML predicate-object maps ✓
- `Entity.properties` → RML predicate-object entries ✓
- `Relation.type` → RML predicate ✓
- `Relation.source_id` / `target_id` → RML subject/object ✓

Gaps:
- Does not extend `KSDMBaseWriter` (extends `BaseDocumentWriter` directly)
- `Entity.embedding` not serialized
- `Relation.weight` not serialized
- `Relation.timestamp` not serialized
- `KSDMDocument.attributes` not serialized
- Limited RML specification coverage (no joins, no complex mappings)
- Entity type not mapped to RML class types
- No support for named graphs
- No ontology/RDF schema output
- Source and target entity lookups are fragile (ID-based matching)

### Missing Writers

1. **KSDM JSON Writer** — Write `KSDMDocument` to `.ksdm.json`
2. **KSDM YAML Writer** — Write `KSDMDocument` to `.ksdm.yaml`
3. **Turtle Writer** — Write `KSDMDocument` to Turtle format
4. **RDF/XML Writer** — Write `KSDMDocument` to RDF/XML
5. **JSON-LD Writer** — Write `KSDMDocument` to JSON-LD
6. **N-Triples Writer** — Write `KSDMDocument` to N-Triples
7. **CSV Graph Writer** — Write `KSDMDocument` to edge-list CSV

## Cross-cutting Issues

### Architecture Issues

1. **Inconsistent base class**: `RMLYAMLWriter` extends `BaseDocumentWriter` directly instead of `KSDMBaseWriter`.
2. **No RDF library dependency**: No `rdflib` usage for standard RDF format handling.
3. **Heuristic type inference**: Entity and relation type inference is keyword-based, not semantic.
4. **ID generation inconsistency**: Entity IDs use `hash(source_name) % 10000` which can cause collisions.
5. **No ontology normalization**: The `ontology` field stores raw format-specific data, not normalized ontology.

### Underused KSDM Fields

- `Entity.embedding` — Vector embeddings for similarity search not utilized
- `Relation.weight` — Edge weight/strength not captured
- `Relation.timestamp` — Temporal graph support missing
- `KSDMDocument.attributes` — Global graph attributes not normalized
- `KSDMDocument.ontology` — Only stores raw RML, not normalized ontology

### Round-trip Limitations

- RML → KSDM → RML round-trip loses entity type information
- Entity properties are not fully preserved in round-trip
- Relation properties are not fully preserved in round-trip
- No other format round-trips are possible (no other parsers/writers)

## Priority Remediation Items

1. **Create KSDM JSON/YAML parsers** — Parse `.ksdm.json` and `.ksdm.yaml` directly into `KSDMDocument`
2. **Create KSDM JSON/YAML writers** — Enable native KSDM serialization
3. **Add RDF/Turtle parser** — Parse `.ttl` format using `rdflib`
4. **Add RDF/Turtle writer** — Write `KSDMDocument` to Turtle format
5. **Add JSON-LD parser/writer** — Support semantic web interoperability
6. **Add CSV graph parser/writer** — Support simple edge-list interchange
7. **Refactor RML writer** — Extend `KSDMBaseWriter` consistently
8. **Add embedding support** — Handle `Entity.embedding` in all parsers/writers
9. **Add temporal graph support** — Handle `Relation.timestamp`
10. **Fix entity ID generation** — Use deterministic, collision-free IDs

## Final Verdict

The KSDM parser/writer layer provides **partial compliance (50%)** against `engines/document/models/ksdm_models.py`.

**Strongest components:**
- `engines/document/parsers/ksdm_parsers/rml_yaml_parser.py` — Partial entity/relation extraction
- `engines/document/writers/ksdm_writers/rml_yaml_writer.py` — Partial RML serialization

**Highest-priority remaining gaps:**
- No native KSDM JSON/YAML parser/writer
- No RDF format support (Turtle, JSON-LD, RDF/XML, N-Triples)
- No CSV graph interchange
- Entity/relation fields (embedding, weight, timestamp) not handled
- Inconsistent writer base class hierarchy
