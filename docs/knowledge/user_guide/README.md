# Knowledge Layer — User Guide

## 1. Introduction

The knowledge layer implements a unified runtime for BI Aggregation, ML Mining, Process Mining, and Knowledge Graph (KG Pipeline) tasks. It was reorganized from separate engines (`engines/insight/`, `engines/semantic_graph/`, `engines/rag/`, `engines/memory/`) into a single `engines/knowledge/` namespace following the no-code MDA2 model driver architecture.

## 2. Quick Start

### Python API

```python
from engines.knowledge import (
    BiAggregationEngine,
    QueryEngine,
    MlMiningEngine,
    ProcessMiningEngine,
    SemanticGraphEngine,
    UnifiedGraphEngine,
)
```

### QueryEngine Usage

```python
# Parse MDX query
engine = QueryEngine()
doc = await engine.async_parse("SELECT [Measures].[Sales] ON COLUMNS FROM [AdventureWorks]")
print(doc.mdx.cube_name)  # AdventureWorks

# Detect language
lang = engine.detect_language("SELECT * FROM Cube")  # QueryLanguage.MDX

# Convert between formats
await engine.async_parse("EVALUATE 'Sales'")
dax_text = await engine.async_convert(QueryLanguage.DAX)
```

# BI Aggregation
bi = BiAggregationEngine()
bi.register_parser("mondrian_schema_xml", MondrianSchemaParser())
doc = await bi.parse("sales.mondrian.xml")

# ML Mining
ml = MlMiningEngine()
ml.register_parser("pmml_xml", PmmlParser())
ml_doc = await ml.parse("model.pmml")

# Process Mining
pm = ProcessMiningEngine()
pm.register_parser("xes_xml", XesParser())
pm_doc = await pm.parse("event_log.xes")

# Semantic Graph
sg = SemanticGraphEngine()
sg.register_parser("rdf_turtle", RdfParser())
kg_doc = await sg.parse("ontology.ttl")

# Unified Graph
graph = UnifiedGraphEngine()
graph.add_node("n1", "Alice", "Person", {"age": 30})
graph.add_edge("n1", "n2", "KNOWS")
neighbors = graph.get_neighbors("n1")
```

## 3. Supported File Formats

### BI Aggregation
| Format | Extension | Standard |
|--------|-----------|----------|
| XMLA Discover | `.xmla_discover.xml`, `.xmla.xml` | XMLA (OLE DB for OLAP) |
| XMLA Execute | `.xmla.xml` | XMLA |
| MDX Query | `.mdx` | Microsoft MDX |
| DAX Query | `.dax` | Microsoft DAX |
| DAX REST JSON | `.json` | Power BI REST API |
| SQL Tabular | `.sql.tabular`, `.tsql` | Transact-SQL |
| M/Power Query | `.m`, `.pq` | Power Query M |
| JPQL | `.jpql` | Java Persistence Query Language |
| OQL | `.oql` | Object Query Language |
| GraphQL Query | `.gql` | GraphQL Query |
| Mondrian Schema | `.mondrian.xml`, `.schema.xml` | Mondrian ROLAP |
| CWM XMI | `.cwm`, `.cwm.xml` | OMG CWM 1.1 |
| TMSL JSON | `.tmsl.json` | Microsoft Tabular Model Scripting Language |
| CDM JSON | `.cdm.json` | Common Data Model |
| Calcite JSON | `.calcite.json` | Apache Calcite |
| AWXML | `.aw.xml` | Analysis Services |
| SAP CDS XML | `.cds.xml` | SAP Core Data Services |
| Cognos FMF | `.fmf`, `.fmf.xml` | IBM Cognos Framework Manager |
| Tableau Hyper | `.hyper` | Tableau Hyper |

### ML Mining
| Format | Extension | Standard |
|--------|-----------|----------|
| PMML | `.pmml`, `.pmml.xml` | DMG PMML 4.2 |
| ONNX | `.onnx`, `.pb` | ONNX 1.0 |

### Process Mining
| Format | Extension | Standard |
|--------|-----------|----------|
| XES | `.xes`, `.xes.xml` | IEEE 1849-2016 |
| DMN | `.dmn`, `.dmn.xml` | OMG DMN 1.4 |
| DDF | `.ddf.json` | Decision Discovery Framework |

### Knowledge Graph Pipeline
| Format | Extension | Standard |
|--------|-----------|----------|
| RDF Turtle | `.ttl` | W3C RDF 1.1 |
| RDF/XML | `.rdf`, `.owl` | W3C RDF/XML |
| RML YAML | `.rml.yaml` | RDF Mapping Language |
| GQL Schema | `.gql.schema` | ISO/IEC 39075 |

## 4. Model Reference

### UnifiedBiAggregationDocument
```python
UnifiedBiAggregationDocument(
    title="BI Aggregation",
    document_id="bi-001",
    bi_format=BiAggregationFormat.MONDRIAN_SCHEMA_XML,
    mondrian_schema=MondrianSchema(...),  # or xmla_discover_request, etc.
    media_type=MEDIA_TYPES["mondrian_schema_xml"],
)
```

### MlMiningDocument
```python
MlMiningDocument(
    title="ML Model",
    document_id="ml-001",
    model_type=MiningModelType.DECISION_TREE,
    pmml_model=PmmlModel(...),
    media_type=MEDIA_TYPES["pmml_xml"],
)
```

### ProcessMiningDocument
```python
ProcessMiningDocument(
    title="Process Mining Result",
    document_id="pm-001",
    xes_log=XesEventLog(...),
    dmn_decision_table=DmnDecisionTable(...),
    media_type=MEDIA_TYPES["xes_xml"],
)
```

### KSDMDocument
```python
KSDMDocument(
    title="Knowledge Graph",
    document_id="kg-001",
    entities=[Entity(id="e1", type=EntityType.PERSON, label="Alice")],
    relations=[Relation(id="r1", source_id="e1", target_id="e2", type=RelationType.WORKS_FOR)],
    media_type=MEDIA_TYPES["json"],
)
```

## 5. Engine Reference

### QueryEngine
```python
engine = QueryEngine()
doc = await engine.async_parse("SELECT [Measures].[Sales] ON COLUMNS FROM [AdventureWorks]")
# or detect language first
lang = engine.detect_language("EVALUATE 'Sales'")  # QueryLanguage.DAX
doc = await engine.async_parse("EVALUATE 'Sales'", language=lang)

# Convert between query languages
output = await engine.async_convert(QueryLanguage.MDX)
table = engine.to_flat_table()
```

### BiAggregationEngine
```python
engine = BiAggregationEngine()
engine.register_parser("xmla_discover_xml", XmlaDiscoverParser())
engine.register_parser("mondrian_schema_xml", MondrianSchemaParser())
engine.register_writer("mondrian_schema_xml", MondrianSchemaWriter())
doc = await engine.parse("warehouse.mondrian.xml")
```

### UnifiedGraphEngine
```python
engine = UnifiedGraphEngine()
engine.register_parser("rdf_turtle", RdfParser())
engine.register_parser("rml_yaml", RmlParser())
engine.register_writer("rdf_turtle", RdfWriter())
kg_doc = await engine.parse("ontology.ttl")

# Also supports direct graph operations
engine.add_node("n1", "Product A", "Product", {"price": 100})
engine.add_edge("n1", "n2", "BELONGS_TO")
friends = engine.get_neighbors("n1")
kg = engine.to_knowledge_graph()
```

### KnowledgeRagEngine
```python
from engines.knowledge.rag.knowledge_rag_engine import KnowledgeRagEngine
rag = KnowledgeRagEngine()
# Uses internal graph, retrieval, and reflection modules
```

## 6. Custom Format Extension

To add a new format:

1. Add enum value to `BiAggregationFormat`, `MlMiningFormat`, `ProcessMiningFormat`, or `KgPipelineFormat`
2. Add `KnowledgeMediaType` entry to `KNOWLEDGE_MEDIA_TYPES`
3. Create parser/writer in `engines/knowledge/parsers/{category}/` and `engines/knowledge/writers/{category}/`
4. Register with the engine

## 7. Integration Notes

- **Memory**: `KnowledgeMemoryEngine` shares graph state via `UnifiedGraphEngine`
- **RAG**: Original `engines/rag/` preserved as re-export shim for backward compatibility
- **Semantic Graph**: Merged with RAG graph into `UnifiedGraphEngine` — no duplicate graph state
- **Document engine**: `engines/document/models/` provides `BaseDocument` and `DocumentStandard`

## 8. Troubleshooting

### `ImportError: cannot import name X from engines.document.models`
Ensure you've installed project dependencies (`pip install -e .`) and that Python path includes project root.

### Parser returns `ParseResult` with `document` field
Always access parsed document via `result.document`, not directly from `parse()`.

### Writer `write()` is sync, not async
All knowledge writers are synchronous. Use `writer.write(document, destination)` directly without `await`.

### `rdflib` or `onnx` not found
These are optional. Install separately: `pip install rdflib onnx`. Parsers/writers for these formats return `NotImplementedError` if the package is missing.

## 9. Compliance

For detailed compliance reports see:
- `docs/engines/knowledge/conformance/COMPLIANCE.md` — Overall compliance
- `docs/engines/knowledge/conformance/COMPLIANCE_MODELS.md` — Model-to-standard mapping
- `docs/engines/knowledge/conformance/COMPLIANCE_PARSERS_WRITERS.md` — Parser/writer compliance
- `docs/engines/knowledge/conformance/COMPLIANCE_ENGINES.md` — Engine compliance
- `docs/engines/knowledge/plan/extension_plan.md` — Open issues and roadmap
