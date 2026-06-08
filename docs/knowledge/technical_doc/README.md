# Knowledge Layer — Technical Documentation

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Model Layer](#model-layer)
3. [Parser/Writer Layer](#parserwriter-layer)
4. [Runtime Engine Layer](#runtime-engine-layer)
5. [Unified Graph Engine](#unified-graph-engine)
6. [Memory Integration](#memory-integration)
7. [Media Types Registry](#media-types-registry)
8. [Extension Points](#extension-points)

---

## 1. Architecture Overview

The knowledge layer follows the **MDA2 (Model Driven Architecture)** pattern:
- **PM Model** → Engine implementation executes against the declared model
- **PIM (Platform Independent Model)**: Domain models defined in `isdm_models.py` and `ksdm_models.py`
- **PSM (Platform Specific Model)**: File formats (XMLA, PMML, XES, RDF, etc.)
- **Code**: Generated parser/writer implementations

```
┌─────────────────────────────────────────────────────────────────┐
│                     engines/knowledge/                          │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────┐  │
│  │    Apps     │  │   Parsers    │  │        Writers         │  │
│  │  (Engines)  │←─│              │─→│                        │  │
│  │             │  └──────────────┘  └────────────────────────┘  │
│  │  BiAgg      │  │  bi/         │  │  bi/                   │  │
│  │  MlMining   │  │  ml_mining/  │  │  ml_mining/            │  │
│  │  Process    │  │  process_/   │  │  process_/             │  │
│  │  Semantic   │  │  semantic_/  │  │  semantic_/            │  │
│  │  Graph      │  │              │  │                        │  │
│  │  RAG        │  └──────────────┘  └────────────────────────┘  │
│  │  Memory     │                                                 │
│  └─────────────┘                                                 │
│        ↕                                                          │
│  ┌─────────────┐  ┌─────────────────────────────────────────┐    │
│  │   Models    │  │           media_types.py                │    │
│  │ isdm_models │  │  KNOWLEDGE_MEDIA_TYPES registry         │    │
│  │ ksdm_models │  │  format → {mime, extensions, standard}  │    │
│  └─────────────┘  └─────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Model Layer

### 2.1 BI Aggregation Models (`engines/knowledge/models/isdm_models.py`)

| Class | Purpose |
|-------|---------|
| `BiAggregationKind` | Enum: XMLA_CUBE, MDX_QUERY, CWM_WAREHOUSE, MONDRIAN_SCHEMA |
| `XmlaDiscoverRequest` | XMLA Discover SOAP request parameters |
| `XmlaDiscoverResponse` | XMLA Discover response: rows + schema |
| `MdxAxis` / `MdxQuery` | MDX query structure (cube, axes, measures) |
| `CwmSchema` / `CwmClass` / `CwmAttribute` / `CwmAssociation` | CWM warehouse metamodel |
| `MondrianSchema` / `MondrianDimension` / `MondrianLevel` / `MondrianMeasure` | Mondrian OLAP schema |
| `BiAggregationDocument` | Document container for BI aggregation data |
| `BIAggregatorModel` | Base aggregator model (schedule, sources, targets) |

### 2.2 ML Mining Models

| Class | Purpose |
|-------|---------|
| `MiningModelType` | Enum: DECISION_TREE, NEURAL_NETWORK, CLUSTERING, etc. |
| `PmmlModel` / `PmmlMiningSchema` / `PmmlMiningField` | PMML 4.2 model structure |
| `OnnxModel` / `OnnxGraph` / `OnnxNode` / `OnnxOpsetImport` | ONNX IR structure |
| `MlMiningDocument` | ML mining result container |

### 2.3 Process Mining Models

| Class | Purpose |
|-------|---------|
| `XesEventLog` / `XesTrace` / `XesEvent` / `XesClassifier` / `XesExtension` | XES IEEE 1849-2016 |
| `DmnDecisionTable` / `DmnDecisionRule` / `DmnDecisionAction` | DMN 1.4 decision model |
| `DdDecisionDiscoveryFramework` / `DdDecisionPoint` | DDF decision discovery output |
| `ProcessMiningDocument` | Process mining result container |

### 2.4 KSDM Models (`engines/knowledge/models/ksdm_models.py`)

| Class | Purpose |
|-------|---------|
| `Entity` / `Relation` | Knowledge graph node/edge |
| `KSDMDocument` | Primary KSDM document (entities + relations + ontology) |
| `RdfGraph` / `RdfTriple` | RDF triple-based knowledge representation |
| `RmlMapping` / `RmlLogicalSource` / `RmlSubjectMap` | RDF Mapping Language |
| `GqlSchema` / `GqlNodeType` / `GqlEdgeType` / `GqlProperty` | GQL property graph schema |
| `GraphNode` / `GraphEdge` / `KnowledgeGraph` | Unified graph model (shared with RAG) |

---

## 3. Parser/Writer Layer

### Contract

```python
class BaseDocumentParser(ABC):
    supported_format: KnowledgeMediaType

    @abstractmethod
    def can_parse(self, source: str | Path) -> bool: ...

    @abstractmethod
    def parse(self, source, **options) -> ParseResult: ...
```

```python
class BaseDocumentWriter(ABC):
    supported_format: KnowledgeMediaType

    @abstractmethod
    def can_write(self, document) -> bool: ...

    @abstractmethod
    def write(self, document, destination, **options) -> None: ...
```

### Format Hierarchy

```
KnowledgeMediaType
  ├─ BiAggregationFormat
  │   ├─ XMLA_DISCOVER_XML  → eng/knowledge/parsers/bi/xmla_parser.py
  │   ├─ MDX_QUERY         → eng/knowledge/parsers/bi/mdx_parser.py (stub)
  │   ├─ CWM_XMI           → eng/knowledge/parsers/bi/cwm_parser.py
  │   └─ MONDRIAN_SCHEMA_XML → eng/knowledge/parsers/bi/mondrian_parser.py
  ├─ MlMiningFormat
  │   ├─ PMML_XML          → eng/knowledge/parsers/ml_mining/pmml_parser.py
  │   └─ ONNX_PROTO        → eng/knowledge/parsers/ml_mining/onnx_parser.py
  ├─ ProcessMiningFormat
  │   ├─ XES_XML           → eng/knowledge/parsers/process_mining/xes_parser.py
  │   ├─ DMN_XML           → eng/knowledge/parsers/process_mining/dmn_parser.py
  │   └─ DDF_JSON          → eng/knowledge/parsers/process_mining/ddf_parser.py
  └─ KgPipelineFormat
      ├─ RDF_XML/TURTLE/NTRIPLES/JSONLD → eng/knowledge/parsers/semantic_graph/rdf_parser.py
      ├─ RML_YAML/JSON     → eng/knowledge/parsers/semantic_graph/rml_parser.py
      └─ GQL_QUERY/SCHEMA  → eng/knowledge/parsers/semantic_graph/gql_parser.py
```

---

## 4. Runtime Engine Layer

### BiAggregationEngine
- **Location**: `engines/knowledge/apps/bi_aggregation/engine.py`
- **Responsibility**: BI aggregation job orchestration
- **Registered formats**: xmla_discover_xml, mdx_query, cwm_xmi, mondrian_schema_xml

### MlMiningEngine
- **Location**: `engines/knowledge/apps/ml_mining/engine.py`
- **Responsibility**: ML model training, pattern discovery, association mining
- **Registered formats**: pmml_xml, onnx_proto

### ProcessMiningEngine
- **Location**: `engines/knowledge/apps/process_mining/engine.py`
- **Responsibility**: Process discovery, conformance checking, decision mining
- **Registered formats**: xes_xml, dmn_xml, ddf_json

### SemanticGraphEngine
- **Location**: `engines/knowledge/apps/semantic_graph/engine.py`
- **Responsibility**: RDF/KSDM document parsing and writing
- **Registered formats**: rdf_xml, rdf_turtle, rml_yaml, gql_schema

---

## 5. Unified Graph Engine

**File**: `engines/knowledge/apps/graph/engine.py`

Merges RAG graph functionality (entity extraction, knowledge graph retrieval) with KSDM semantic graph (RDF/KSDM pipeline) into a single interface.

### Capabilities
- `add_node(id, label, type, properties)` — Add node to in-memory graph
- `add_edge(source, target, relation, properties)` — Add relationship
- `parse(source, fmt)` — Parse RDF/RML/GQL into KSDMDocument
- `write(document, destination, fmt)` — Write KSDMDocument to RDF/RML/GQL
- `get_neighbors(node_id)` — Graph traversal (RAG-style)
- `retrieve(entity_id, hops)` — Multi-hop retrieval
- `to_knowledge_graph()` — Export as `KnowledgeGraph` model
- `run_semantic_pipeline(text_or_document)` — Run KSDM pipeline (TODO)

### Integration with Memory
Memory stores use `UnifiedGraphEngine` as shared graph substrate.

---

## 6. Memory Integration

**File**: `engines/knowledge/apps/memory/knowledge_memory_engine.py`

### Design Points
- Memory is currently a stub — implementation should use `UnifiedGraphEngine`
- Memory layers: episodic, semantic, short-term, long-term (folders exist under `engines/memory/`)
- Integration pattern: Memory registers as a knowledge engine with parsers/writers for persistence formats

---

## 7. Media Types Registry

**File**: `engines/knowledge/models/media_types.py`

### KnowledgeMediaType Fields
- `mime`: MIME type string
- `format`: Enum value from format-specific enum
- `standard`: Short standard identifier (isdm_bi, isdm_ml, isdm_process_mining, ksdm)
- `extensions`: List of file extensions
- `description`: Human-readable description

### Registry Size
34 media types across 4 categories:
- BI Aggregation: xmla_discover_xml, mdx_query, cwm_xmi, mondrian_schema_xml
- ML Mining: pmml_xml, onnx_proto
- Process Mining: xes_xml, dmn_xml, ddf_json
- KG Pipeline: rdf_xml, rdf_turtle, rdf_ntriples, rdf_jsonld, rml_yaml, rml_json, gql_query, gql_schema

---

## 8. OSDM Agentic BPMN Extension

The OSDM model (`engines/document/models/osdm_models.py`) has been extended with **agentic BPMN elements** that subclass standard BPMN 2.0 types:

| Agentic Class | BPMN Base | Extension |
|---|---|---|
| `AgenticTask` | `Task` | Reflection strategy, agent binding, trust threshold |
| `AgenticLane` | `Lane` | Agent ID, capabilities, model provider, system prompt |
| `DivergingAgenticGateway` | `Gateway` | Collaboration strategy (voting/role/debate/competition) |
| `MergingAgenticGateway` | `Gateway` | Merge strategy (majority/leader/fastest) |
| `AgenticMessageFlow` | `MessageFlow` | Agent communication protocol, reflection toggle |

Strategy config objects (`CollaborationStrategy`, `MergeStrategy`, `VotingConfig`, `RoleConfig`, `CompetitionConfig`) are plain `@dataclass` values embedded in gateway elements.

### Relationship with Interaction Layer

The BPMN extension models **what** collaboration pattern to use (design-time), while `engines/interaction/` provides the runtime strategy execution (**how**). The `InteractionStrategy` enum in `osdm_models.py` mirrors `engines/interaction/` scenario names for future compiler integration.

See `docs/orchestration/agentic_bpmn_extension.md` for full design rationale and `docs/orchestration/compliance/COMPARISON_AGENTIC_BPMN.md` for overlap analysis.

---

## 9. Extension Points

### Adding a New Format

1. **Define model** in `engines/knowledge/models/ksdm_models.py` or `lsdm_models.py`
2. **Add media type** to `engines/knowledge/models/media_types.py`
3. **Create parser** in `engines/knowledge/parsers/{category}/`
4. **Create writer** in `engines/knowledge/writers/{category}/`
5. **Register** in engine `__init__.py`

### Adding a New Engine

1. Create folder in `engines/knowledge/apps/{engine_name}/`
2. Implement `BaseDocumentParser` and `BaseDocumentWriter` subclasses
3. Import in `engines/knowledge/apps/__init__.py`
4. Add to `engines/knowledge/__init__.py`
