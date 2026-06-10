# Knowledge Layer Extension Plan and Open Issues

Generated: 2026-06-05

## Current State Summary
The Knowledge Layer has been reorganized into `engines/knowledge/` with:
- 3 complete document model hierarchies (BI Aggregation, ML Mining, Process Mining + KSDM)
- LSDM model and parsers/writers (XES, Syslog, CEF, ES Bulk)
- 12 parser stubs + partial implementations
- 11 writer stubs + partial implementations
- 7 runtime engine skeletons
- Unified Graph Engine integrating RAG graph and Semantic Graph
- Agentic BPMN extension in OSDM (5 new element classes, 6 enums, 5 config dataclasses)
- 19 passing tests

---

## OPEN ISSUES

### P1 — Critical / Blocking Production Use

#### [KNG-001] PMML Parser — Full PMML 4.2 Compliance
- **File**: `engines/knowledge/parsers/ml_mining/pmml_parser.py`
- **Description**: Current parser only reads `modelName`, `modelType`, `MiningSchema` header fields. Missing:
  - Full PMML element parsing: LocalTransformations, Regression, TreeModel, NeuralNetwork, SupportVectorMachine, etc.
  - Output field targets and value mapping
  - Model verification/validation
- **Impact**: Cannot fully import existing PMML 4.2 models from PMML-compliant tools (RapidMiner, KNIME, SPSS)
- **Action**: Implement full `PMML-4_2` XML schema coverage using `xml.etree.ElementTree` or `xsdata`
- **Estimate**: Medium

#### [KNG-002] ONNX Parser/Writer — Protobuf Implementation
- **File**: `engines/knowledge/parsers/ml_mining/onnx_parser.py`, `engines/knowledge/writers/ml_mining/onnx_writer.py`
- **Description**: Currently raises `NotImplementedError` (requires `onnx` package). Need to decide:
  - Package dependency: `pip install onnx` mandatory or optional?
  - Protobuf buffer format handling without full onnx dependency (lighter weight)
- **Impact**: Cannot exchange deep learning models with PyTorch/TensorFlow
- **Action**: Implement light protobuf parser or require `onnx` package
- **Decision Needed**: Package strategy

#### [KNG-003] XES Parser — Full IEEE 1849-2016 Support
- **File**: `engines/knowledge/parsers/process_mining/xes_parser.py`
- **Description**: Basic log/trace/event parsing only. Missing:
  - `event@id` attribute support
  - String/date/int/float/boolean/id/list/container extension types
  - Global event/trace attributes
  - Log attributes, extension URIs
- **Impact**: Incomplete process mining pipeline for real event logs
- **Action**: Add extension attribute type handlers and global attributes
- **Estimate**: Medium

#### [KNG-004] RDF Parser/Writer — Full RDF Serialization
- **File**: `engines/knowledge/parsers/semantic_graph/rdf_parser.py`, `engines/knowledge/writers/semantic_graph/rdf_writer.py`
- **Description**: Requires `rdflib` package. Full support needed for:
  - RDF/XML, Turtle, N-Triples, JSON-LD, TriG, N-Quads
  - SPARQL query integration
  - Ontology alignment
- **Impact**: Cannot construct or query knowledge graphs from standard RDF sources
- **Action**: Add rdflib as required dependency or provide fallback parser
- **Estimate**: Large

---

### P2 — Important / Near-term

#### [KNG-005] GQL (ISO/IEC 39075) Parser Implementation
- **File**: `engines/knowledge/parsers/semantic_graph/gql_parser.py`
- **Description**: GQL standard published 2024. Currently stub-only. Need:
  - Property graph schema parsing (DEFINE NODE TYPE, DEFINE EDGE TYPE)
  - Query parsing (MATCH, CREATE, MERGE, etc.)
  - Integration with Neo4j-style property graph model
- **Action**: Implement GQL parser after ISO specification finalized
- **Estimate**: Large

#### [KNG-006] DMN Parser/Writer — Full OMG 1.4 Support
- **File**: `engines/knowledge/parsers/process_mining/dmn_parser.py`, `engines/knowledge/writers/process_mining/dmn_writer.py`
- **Description**: Currently returns empty `DmnDecisionTable`. Need:
  - Full decision table parsing (input/output columns, rules, annotations)
  - Literal expression parsing
  - Business knowledge model support
- **Action**: Implement full DMN 1.4 parser/writer
- **Estimate**: Medium

#### [KNG-007] CWM Parser/Writer — Complete Warehouse Schema
- **File**: `engines/knowledge/parsers/bi/cwm_parser.py`, `engines/knowledge/writers/bi/cwm_writer.py`
- **Description**: Basic CWM XMI parsing only. Need complete CWM 1.1 metamodel:
  - Class, Interface, Package, Operation, Parameter
  - Association, Inheritance, Aggregation
  - Constraints, DataTypes
- **Action**: Implement full CWM 1.1 metamodel mapping
- **Estimate**: Large

#### [KNG-008] UnifiedGraphEngine — Semantic Pipeline Integration
- **File**: `engines/knowledge/apps/graph/engine.py`
- **Description**: `run_semantic_pipeline()` is `NotImplementedError`. Need to integrate:
  - `KSDM_Pipeline` entity/relation extraction
  - RDF parser integration
  - RML mapping execution to populate graph from external data sources
- **Action**: Wire up `KgPipeline` into `UnifiedGraphEngine`
- **Estimate**: Medium

#### [KNG-009] Memory Engine — Storage Backend Integration
- **File**: `engines/knowledge/apps/memory/knowledge_memory_engine.py`
- **Description**: Currently empty stub. Need:
  - Implement actual memory retrieval/storage
  - Integration with `UnifiedGraphEngine` for graph-based memory
  - Temporal reasoning support
- **Action**: Implement knowledge memory engine using `UnifiedGraphEngine`
- **Estimate**: Medium

---

### P3 — Nice to Have / Future

#### [KNG-010] MDX Query Parser/Writer ✅ DONE
- **File**: `engines/knowledge/query_models/parsers/mdx_parser.py`, `writers/mdx_writer.py`
- **Description**: MDX query string parsing and generation for OLAP systems
- **Status**: Implemented with regex-based parsing, axis extraction, roundtrip support

#### [KNG-010a] Query Language Parsers ✅ DONE
- **Files**: `engines/knowledge/query_models/parsers/{dax,jpql,oql,sql_tabular,power_query_m,graphql_query}_parser.py`
- **Description**: DAX, JPQL, OQL, SQL Tabular, M/Power Query, GraphQL query parsers
- **Status**: Implemented with QueryEngine in `engines/knowledge/query_models/`

---

## EXTENSION PLAN

### Phase 1: Core Parser/Writer Completion (Target: Next Sprint)
- [ ] [KNG-001] Full PMML 4.2 parser compliance
- [ ] [KNG-003] Full XES parser (IEEE 1849-2016)
- [ ] [KNG-006] Full DMN 1.4 parser/writer
- [ ] [KNG-011] Mondrian Schema writer validation

### Phase 2: External Standard Integration (Target: +2 Sprints)
- [ ] [KNG-002] ONNX package integration decision + implementation
- [ ] [KNG-004] RDF support with rdflib
- [ ] [KNG-005] GQL ISO 39075 parser (after standard settles)
- [ ] [KNG-007] CWM 1.1 full metamodel

### Phase 3: Engine Integration (Target: +3 Sprints)
- [ ] [KNG-008] Wire up SemanticGraphPipeline into UnifiedGraphEngine
- [ ] [KNG-009] Implement KnowledgeMemoryEngine
- [X] [KNG-010] MDX parser — **COMPLETED**
- [X] [KNG-010a] Query Language Parsers — **COMPLETED**
- [ ] [KNG-013] Document registry integration

### Phase 4: Quality and Documentation (Target: +4 Sprints)
- [ ] [KNG-012] Automated compliance checker
- [ ] Integration tests for end-to-end parser→engine→writer pipelines
- [ ] Performance benchmarks for graph operations
- [ ] User guides for each engine domain

---

## Agentic BPMN Roadmap (OSDM)

### Current (Completed)
- [x] AgenticTask with reflection strategy and agent binding
- [x] AgenticLane with agent metadata (capabilities, model provider, system prompt)
- [x] DivergingAgenticGateway / MergingAgenticGateway with strategy configs
- [x] AgenticMessageFlow with communication protocol
- [x] Design documentation and compliance/overlap docs

### Phase A: Runtime Compiler (Next Sprint)
- [ ] Compiler: `AgenticTask` + `DivergingAgenticGateway` → `NativeOrchestrationBackend.execute(InteractionRequest)`
- [ ] Compiler: `MergeStrategy` → result aggregation in `InteractionResult`
- [ ] Compiler: `AgenticLane` → agent registration in `InteractionStrategy` registry

### Phase B: Visual Notation & Serialization (Target: +2 Sprints)
- [ ] Define BPMN 2.0 extension namespace for agentic attributes
- [ ] XML serialization via `extensionElements`
- [ ] Custom BPMN shape markers for agentic elements

### Phase C: Simplification (Future)
- [ ] Evaluate `AgenticTask` overload — consider `AgentTask` / `SkillTask` / `AgentInteractionTask` split
- [ ] Dynamic agent discovery (capability-based `agent_ids` resolution)

### Phase D: Integration
- [ ] Wire `InteractionStrategy` enum in `osdm_models.py` to `engines.interaction.strategy_registry`
- [ ] Remove duplicate `InteractionStrategy` enum (replace with shared constant or import)
