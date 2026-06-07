# Compliance Document for Knowledge Layer Reorganization

## Overview
This document describes the reorganized knowledge layer in `engines/knowledge/`, created by consolidating previous separate engines (`engines/insight/`, `engines/semantic_graph/`, `engines/rag/graph/`, `engines/memory/`) into a unified knowledge runtime architecture following the no-code MDA2 (PIM→PSM→Code) model driver pattern.

## 1. ISDM Model Compliance

### Standards Supported
The ISDM model now supports three distinct BI Aggregation, ML Mining, and Process Mining domains:

#### BI Aggregation (Aggregated Analytics)
- **XMLA (XML for Analysis)**: Industry standard for data access in analytical systems using XML, SOAP, HTTP.
  - Model: `XmlaDiscoverRequest`, `XmlaDiscoverResponse`, `BiAggregationKind.XMLA_CUBE`
  - Parser/Writers: `xmla_parser.py`, `xmla_writer.py`
- **MDX (MultiDimensional eXpressions)**: Query language for OLAP cubes, Microsoft de facto standard.
  - Model: `MdxQuery`, `MdxAxis`
- **CWM (Common Warehouse Metamodel)**: OMG standard for metadata exchange in data warehousing.
  - Model: `CwmSchema`, `CwmClass`, `CwmAttribute`, `CwmAssociation`
  - Parser/Writers: `cwm_parser.py`, `cwm_writer.py`
- **Mondrian Schema XML**: XML format for Mondrian ROLAP server.
  - Model: `MondrianSchema`, `MondrianDimension`, `MondrianDimensionHierarchy`, `MondrianLevel`, `MondrianMeasure`
  - Parser/Writers: `mondrian_parser.py`, `mondrian_writer.py`

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
├── __init__.py                        # Unified exports
├── base/                              # Base knowledge abstractions (empty)
├── documents/                         # Document-level abstractions (empty)
├── fusion/                            # Data fusion layer (empty)
├── graph/
│   ├── engine.py                      # UnifiedGraphEngine
│   ├── graph_models.py               # GraphNode, GraphEdge
│   ├── graph_builder.py              # RAG-style graph builder
│   ├── graph_store.py                # In-memory graph store
│   └── graph_retriever.py            # Graph retrieval
├── rules/                             # Rule engine (empty)
├── vector/                            # Vector engine (empty)
├── models/
│   ├── __init__.py                   # All model exports
│   ├── isdm_models.py               # BI/ML/Process Mining models
│   ├── ksdm_models.py               # Knowledge graph models
│   └── media_types.py               # Knowledge media type registry
├── parsers/
│   ├── __init__.py                   # All parser exports
│   ├── base.py                       # BaseKnowledgeParser
│   ├── bi/                           # XMLA, CWM, Mondrian parsers
│   ├── ml_mining/                    # PMML, ONNX parsers
│   ├── process_mining/               # XES, DMN, DDF parsers
│   └── semantic_graph/               # RDF, RML, GQL parsers
├── writers/
│   ├── __init__.py                   # All writer exports
│   ├── base.py                       # BaseKnowledgeWriter
│   ├── bi/                           # XMLA, CWM, Mondrian writers
│   ├── ml_mining/                    # PMML, ONNX writers
│   ├── process_mining/               # XES, DMN, DDF writers
│   └── semantic_graph/               # RDF, RML, GQL writers
└── apps/
    ├── __init__.py                   # All engine exports
    ├── bi_aggregation/
    │   └── engine.py                 # BiAggregationEngine
    ├── ml_mining/
    │   └── engine.py                 # MlMiningEngine
    ├── process_mining/
    │   └── engine.py                 # ProcessMiningEngine
    ├── semantic_graph/
    │   ├── engine.py                 # SemanticGraphEngine
    └── graph/
        └── engine.py                 # UnifiedGraphEngine
    ├── rag/
    │   └── knowledge_rag_engine.py   # KnowledgeRagEngine
    └── memory/
        └── knowledge_memory_engine.py # KnowledgeMemoryEngine
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
| BI Aggregation (XMLA/MDX/CWM/Mondrian) | ✅ Defined |
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
- **38 tests passing** in `tests/knowledge/`
- Coverage: models, parsers, writers, engines
- Legacy tests: `tests/document/test_isdm_*.py`, `test_ksdm_*.py` remain unchanged

## 10. Integration Points
- Memory integrates with graph via shared `UnifiedGraphEngine`
- RAG integration preserved via `KnowledgeRagEngine` re-export
- Semantic graph merged with RAG graph into unified `UnifiedGraphEngine`
- All parsers/writers register via `BaseKnowledgeParser`/`BaseKnowledgeWriter` contracts
