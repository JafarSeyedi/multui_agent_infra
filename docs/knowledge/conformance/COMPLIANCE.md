# Compliance Document for Knowledge Layer Reorganization

## Overview
This document describes the reorganized knowledge layer in `engines/knowledge/`, created by consolidating previous separate engines (`engines/insight/`, `engines/semantic_graph/`, `engines/rag/graph/`, `engines/memory/`) into a unified knowledge runtime architecture following the no-code MDA2 (PIM→PSM→Code) model driver pattern.

## 1. ISDM Model Compliance

### Standards Supported
The ISDM model now supports three distinct BI Aggregation, ML Mining, and Process Mining domains:

#### BI Aggregation (Aggregated Analytics)
- **XMLA (XML for Analysis)**: Industry standard for data access in analytical systems using XML, SOAP, HTTP.
  - Model: `XmlaDiscoverRequest`, `XmlaDiscoverResponse`, `UnifiedBiAggregationDocument`, `XmlaTransport`
  - Parser/Writers: `xmla_parser.py`, `xmla_writer.py` (query_models/)
- **MDX (MultiDimensional eXpressions)**: Query language for OLAP cubes, Microsoft de facto standard.
  - Model: `MdxQuery`, `MdxAxis`, `UnifiedQueryDocument`
  - Parser/Writers: `mdx_parser.py`, `mdx_writer.py` (query_models/)
- **DAX (Data Analysis Expressions)**: Power BI/SSAS tabular query language.
  - Model: `DaxQuery`, `UnifiedQueryDocument`
  - Parser/Writers: `dax_parser.py`, `dax_writer.py` (query_models/)
- **SQL Tabular**: Transact-SQL for SSAS tabular models.
  - Model: `SqlTabularQuery`, `UnifiedQueryDocument`
  - Parser/Writers: `sql_tabular_parser.py`, `sql_tabular_writer.py` (query_models/)
- **M/Power Query**: Power Query formula language.
  - Model: `PowerQueryM`, `UnifiedQueryDocument`
  - Parser/Writers: `power_query_m_parser.py`, `power_query_m_writer.py` (query_models/)
- **JPQL (Java Persistence Query Language)**: ORM query language.
  - Model: `JpqlQuery`, `UnifiedQueryDocument`
  - Parser/Writers: `jpql_parser.py`, `jpql_writer.py` (query_models/)
- **OQL (Object Query Language)**: Object database query language.
  - Model: `OqlQuery`, `UnifiedQueryDocument`
  - Parser/Writers: `oql_parser.py`, `oql_writer.py` (query_models/)
- **GraphQL Query**: Query operation language for APIs.
  - Model: `GraphqlQueryDocument`, `UnifiedQueryDocument`
  - Parser/Writers: `graphql_query_parser.py`, `graphql_query_writer.py` (query_models/)
- **CWM (Common Warehouse Metamodel)**: OMG standard for metadata exchange in data warehousing.
  - Model: `CwmSchema`, `CwmClass`, `CwmAttribute`, `CwmAssociation`
  - Parser/Writers: `cwm_parser.py`, `cwm_writer.py`
- **Mondrian Schema XML**: XML format for Mondrian ROLAP server.
  - Model: `MondrianSchema`, `MondrianDimension`, `MondrianDimensionHierarchy`, `MondrianLevel`, `MondrianMeasure`
  - Parser/Writers: `mondrian_parser.py`, `mondrian_writer.py`
- **TMSL JSON**: Microsoft Tabular Model Scripting Language for SSAS tabular models.
  - Model: `TmslModel`, `TmslCommand`
  - Parser/Writers: `tmsl_parser.py`, `tmsl_writer.py`
- **CDM JSON**: Common Data Model standard for data schema and metadata.
  - Model: `CdmModel`, `CdmEntity`
  - Parser/Writers: `cdm_parser.py`, `cdm_writer.py`
- **Calcite JSON**: Apache Calcite model specification for relational algebra.
  - Model: `CalciteModel`, `CalciteSchema`
  - Parser/Writers: `calcite_parser.py`, `calcite_writer.py`
- **AWXML**: Analysis Services XML for SSAS instance configuration.
  - Model: `AwXmlModel`, `AwXmlDatabase`
  - Parser/Writers: `awxml_parser.py`, `awxml_writer.py`
- **SAP CDS XML**: SAP Core Data Services for data modeling.
  - Model: `SapCdsModel`, `SapCdsEntity`
  - Parser/Writers: `sap_cds_parser.py`, `sap_cds_writer.py`
- **Cognos FMF**: IBM Cognos Framework Manager metadata model.
  - Model: `CognosFmfModel`, `CognosPackage`
  - Parser/Writers: `cognos_fmf_parser.py`, `cognos_fmf_writer.py`
- **Tableau Hyper**: Tableau Hyper file format for in-memory data engine.
  - Model: `TableauHyperModel`, `TableauHyperTable`
  - Parser/Writers: `tableau_hyper_parser.py`, `tableau_hyper_writer.py`

#### ML Mining (Data Mining & Machine Learning)
- **PMML (Predictive Model Markup Language)**: XML-based standard (DMG, 1998, v4.2 2014).
  - Model: `PmmlModel`, `PmmlMiningSchema`, `PmmlMiningField`, `MiningModelType`
  - Parser/Writers: `pmml_parser.py`, `pmml_writer.py`
- **ONNX (Open Neural Network Exchange)**: Modern open standard for ML models (deep learning).
  - Model: `OnnxModel`, `OnnxGraph`, `OnnxNode`, `OnnxOpsetImport`
  - Parser/Writers: `onnx_parser.py`, `onnx_writer.py`

#### Process Mining (Event & Process Analysis)
- **XES (eXtensible Event Stream)**: IEEE 1849-2016 standard for event logs.
  - Model: `XesEventLog`, `XesTrace`, `XesEvent`, `XesClassifier`, `XesExtension`, `XesAttribute`
  - Parser/Writers: `xes_parser.py`, `xes_writer.py`
- **DMN (Decision Model and Notation)**: OMG standard (v1.4, April 2023) for repeatable decisions.
  - Model: `DmnDecisionTable`, `DmnDecisionRule`, `DmnDecisionAction`
  - Parser/Writers: `dmn_parser.py`, `dmn_writer.py`
- **DDF (Decision Discovery Framework)**: Algorithmic framework for extracting decision logic.
  - Model: `DdDecisionDiscoveryFramework`, `DdDecisionPoint`
  - Parser/Writers: `ddf_parser.py`, `ddf_writer.py`

## 2. KSDM Model Compliance

### Standards Supported
- **RDF (Resource Description Framework)**: W3C foundation standard for knowledge graphs (subject-predicate-object triples).
  - Model: `RdfGraph`, `RdfTriple`
  - Parser/Writers: `rdf_parser.py`, `rdf_writer.py`
- **RML (RDF Mapping Language)**: Standard for mapping data from CSV/JSON/XML into RDF KGs.
  - Model: `RmlMapping`, `RmlLogicalSource`, `RmlSubjectMap`, `RmlPredicateObjectMap`
  - Parser/Writers: `rml_parser.py`, `rml_writer.py`
- **GQL (Graph Query Language)**: ISO/IEC 39075 standard (2024) for property graph queries.
  - Model: `GqlSchema`, `GqlNodeType`, `GqlEdgeType`, `GqlProperty`
  - Parser/Writers: `gql_parser.py`, `gql_writer.py`

## 3. Unified Graph Engine Compliance

### RAG Graph Integration
- **GraphNode / GraphEdge**: Unified node/edge models (merged from RAG graph and KSDM)
- **UnifiedGraphEngine**: Single entry point for:
  - RAG-style graph building and entity extraction
  - Semantic graph pipeline (RDF/KSDM pipeline)
  - Unified retrieval API

## 4. Memory Engine Integration
- **KnowledgeMemoryEngine**: Integrated with the knowledge layer via `engines/knowledge/apps/memory/`
  - Shares graph state with `UnifiedGraphEngine`
  - Supports episodic, semantic, and short-term memory stubs

## 5. Reorganized Folder Structure

```
engines/knowledge/
├── __init__.py                    # Unified exports (QueryEngine, BiAggregationEngine, etc.)
├── base/                          # Base knowledge abstractions (empty)
├── documents/                     # Document-level abstractions (empty)
├── fusion/                        # Data fusion layer (empty)
├── query_models/                  # QueryEngine + parsers/writers for MDX/DAX/SQL/OQL/JPQL/GraphQL/XMLA
│   ├── __init__.py               # QueryEngine
│   ├── parsers/                  # 8 parser files (mdx, dax, sql_tabular, power_query_m, jpql, oql, graphql_query, xmla)
│   └── writers/                  # 8 writer files
├── graph/
│   ├── engine.py                 # UnifiedGraphEngine
│   ├── graph_models.py            # GraphNode, GraphEdge
│   ├── graph_builder.py           # RAG-style graph builder
│   ├── graph_store.py             # In-memory graph store
│   └── graph_retriever.py         # Graph retrieval
├── rules/                         # Rule engine (empty)
├── vector/                        # Vector engine (empty)
├── models/
│   ├── __init__.py               # All model exports
│   ├── isdm_models.py            # BI/ML/Process Mining models
│   ├── ksdm_models.py            # Knowledge graph models
│   └── media_types.py            # Knowledge media type registry (includes query format enums)
├── parsers/
│   ├── __init__.py               # All parser exports (including query_models re-exports)
│   ├── base.py                   # BaseDocumentParser
│   ├── bi/                       # CWM, Mondrian parsers (schema models)
│   ├── ml_mining/                # PMML, ONNX parsers
│   ├── process_mining/           # XES, DMN, DDF parsers
│   └── semantic_graph/           # RDF, RML, GQL parsers
├── writers/
│   ├── __init__.py               # All writer exports
│   ├── base.py                   # BaseDocumentWriter
│   ├── bi/                       # CWM, Mondrian writers (schema models)
│   ├── ml_mining/                # PMML, ONNX writers
│   ├── process_mining/           # XES, DMN, DDF writers
│   └── semantic_graph/           # RDF, RML, GQL writers
└── apps/
    ├── __init__.py               # All engine exports
    ├── bi_aggregation/
    │   └── engine.py             # BiAggregationEngine
    ├── ml_mining/
    │   └── engine.py             # MlMiningEngine
    ├── process_mining/
    │   └── engine.py             # ProcessMiningEngine
    ├── semantic_graph/
    │   └── engine.py             # SemanticGraphEngine
    └── graph/
        └── engine.py             # UnifiedGraphEngine
```

## 6. Removed from Original Structure
- `engines/insight/` → consolidated into `engines/knowledge/apps/`
- `engines/semantic_graph/` → consolidated into `engines/knowledge/apps/semantic_graph/`
- `engines/rag/` → moved to `engines/knowledge/apps/rag/` (original kept as re-export shim)
- `engines/memory/` (stubs) → integrated into `engines/knowledge/apps/memory/`

## 7. Compliance Status

### Models
| Domain | Status |
|--------|--------|
| BI Aggregation (XMLA/MDX/CWM/Mondrian/TMSL/CDM/Calcite/AWXML/SAP CDS/Cognos FMF/Tableau Hyper) | ✅ Defined |
| ML Mining (PMML/ONNX) | ✅ Defined |
| Process Mining (XES/DMN/DDF) | ✅ Defined |
| KG Pipeline (RDF/RML/GQL) | ✅ Defined |
| Unified Graph Engine | ✅ Defined |

### Parsers
| Format | Status |
|--------|--------|
| XMLA Discover | ✅ Stub (SOAP/XML parsing) |
| CWM XMI | ✅ Stub (XML parsing) |
| Mondrian Schema | ✅ Stub (XML parsing) |
| TMSL JSON | 🔲 Stub (requires TMSL schema) |
| CDM JSON | 🔲 Stub (requires CDM definitions) |
| Calcite JSON | 🔲 Stub (requires Calcite model) |
| AWXML | 🔲 Stub (requires AS config) |
| SAP CDS XML | 🔲 Stub (requires CDS schema) |
| Cognos FMF | 🔲 Stub (requires FMF spec) |
| Tableau Hyper | 🔲 Stub (requires Hyper API) |
| PMML | ✅ Partial (MiningModel header) |
| ONNX | 🔲 Stub (requires onnx package) |
| XES | ✅ Partial (IEEE 1849-2016 basic) |
| DMN | 🔲 Stub (requires full parser) |
| DDF | ✅ Partial (JSON parsing) |
| RDF | 🔲 Stub (requires rdflib) |
| RML | ✅ Partial (YAML/JSON) |
| GQL | 🔲 Stub (new ISO 2024 standard) |

### Writers
| Format | Status |
|--------|--------|
| XMLA Discover | ✅ Stub |
| CWM XMI | ✅ Stub |
| Mondrian Schema | ✅ Partial (basic structure) |
| TMSL JSON | 🔲 Stub (requires TMSL schema) |
| CDM JSON | 🔲 Stub (requires CDM definitions) |
| Calcite JSON | 🔲 Stub (requires Calcite model) |
| AWXML | 🔲 Stub (requires AS config) |
| SAP CDS XML | 🔲 Stub (requires CDS schema) |
| Cognos FMF | 🔲 Stub (requires FMF spec) |
| Tableau Hyper | 🔲 Stub (requires Hyper API) |
| PMML | ✅ Partial (MiningModel output) |
| ONNX | 🔲 Stub (requires onnx package) |
| XES | ✅ Partial (basic log structure) |
| DMN | 🔲 Stub |
| DDF | ✅ Partial (JSON output) |
| RDF | 🔲 Stub (requires rdflib) |
| RML | ✅ Partial (YAML output) |
| GQL | ✅ Stub |

### Runtime Engines
| Engine | Status |
|--------|--------|
| BiAggregationEngine | ✅ Skeleton |
| MlMiningEngine | ✅ Skeleton |
| ProcessMiningEngine | ✅ Skeleton |
| SemanticGraphEngine | ✅ Skeleton |
| UnifiedGraphEngine | ✅ Skeleton |
| KnowledgeRagEngine | ✅ Re-export |
| KnowledgeMemoryEngine | ✅ Skeleton |

## 8. MDA2 Model Driver Architecture
The knowledge engines follow Model Driver Architecture (MDA2) where:
- The **model** (`isdm_models.py`, `ksdm_models.py`) declares the PIM/PSM structure
- The **engine** runs the definition and operations against that model
- The **parser/writer** transforms between file formats and the model
- Each engine registers its parsers/writers via the unified interface

## 9. Test Coverage
- **29 tests passing** in `tests/knowledge/`
- Coverage: models, parsers, writers, engines (QueryEngine, BiAggregationEngine)
- Legacy tests: `tests/document/test_isdm_*.py`, `test_ksdm_*.py` remain unchanged
- Query model tests: 14 tests in `tests/knowledge/test_query_models.py` (MDX/DAX/SQL/OQL/JPQL/GraphQL/XMLA)

## 10. OSDM Agentic BPMN Extension Compliance

The agentic BPMN extension is defined in `engines/document/models/osdm_models.py` and follows the BPMN 2.0 extension mechanism (§14):

| Element | BPMN 2.0 Compliant | Extension Type |
|---|---|---|
| `AgenticTask` | ✅ | Standard extension of `Task` (§8.5) |
| `AgenticLane` | ✅ | Standard extension of `Lane` (§11.1) |
| `DivergingAgenticGateway` | ⚠️ | Extension of `Gateway` (§10.5) with custom routing |
| `MergingAgenticGateway` | ⚠️ | Extension of `Gateway` (§10.5) with custom merge |
| `AgenticMessageFlow` | ✅ | Standard extension of `MessageFlow` (§15.2.2) |

All classes inherit full BPMN 2.0 semantics from their parents. Gateway extensions require custom runtime logic beyond standard XOR/AND semantics.

See `docs/orchestration/compliance/COMPLIANCE_AGENTIC_BPMN.md` for full per-element compliance details.

## 11. Integration Points
- Memory integrates with graph via shared `UnifiedGraphEngine`
- RAG integration preserved via `KnowledgeRagEngine` re-export
- Semantic graph merged with RAG graph into unified `UnifiedGraphEngine`
- All parsers/writers register via `BaseDocumentParser`/`BaseDocumentWriter` contracts
- Agentic BPMN elements integrate with `engines/interaction/` at runtime via future compiler adapter
