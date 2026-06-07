"""
Unified Graph Engine
====================
Integrates the RAG graph builder (entity extraction, retrieval) and the
semantic graph pipeline (RDF/KSDM pipeline) into a single interface.
"""
from __future__ import annotations

from typing import Any, cast

from engines.document.parsers.base import BaseKnowledgeParser
from engines.document.writers.base import BaseKnowledgeWriter, WriteResult
from engines.document.models.ksdm_models import (
    KSDMDocument, Entity, Relation, EntityType, RelationType,
    GraphNode, GraphEdge, KnowledgeGraph
)
from engines.document.models.media_types import (
    DocumentFormat, MediaContentKind, MediaRawType, MediaType,
)
from engines.document.models.standard import DocumentStandard

from .graph_store import MemoryGraphStore
from .graph_builder import GraphBuilder
from .graph_retriever import GraphRetriever
from .graph_models import GraphNode as RAGGraphNode, GraphEdge as RAGGraphEdge


class UnifiedGraphEngine:
    """
    Unified graph engine combining:
    1. RAG graph capabilities (entity extraction, node/edge storage, retrieval)
    2. Semantic graph capabilities (RDF parsing, KSDM document handling)
    3. Research graph capabilities (GraphIndex, EntityExtractor, GraphPersistence)
    """

    def __init__(self, llm: Any = None) -> None:
        self._parsers: dict[str, BaseKnowledgeParser] = {}
        self._writers: dict[str, BaseKnowledgeWriter] = {}
        
        # Core graph storage (shared between RAG and semantic graph)
        self.graph_store = MemoryGraphStore()
        
        # RAG graph components
        self.graph_builder = GraphBuilder(llm=llm, graph_store=self.graph_store)
        self.graph_retriever = GraphRetriever(graph_store=self.graph_store)
        
        # Research graph components
        from .protocols import EntityExtractorProtocol
        from .research.graph_index import GraphIndex
        from .research.entity_extractor import EntityExtractor
        from .research.graph_persistence import GraphPersistence
        
        self.graph_index = GraphIndex()
        self.entity_extractor: EntityExtractorProtocol = EntityExtractor(llm=llm)
        self.graph_persistence = GraphPersistence()
        
        # Semantic graph components
        from engines.knowledge.semantic_graph.engine import SemanticGraphEngine
        self.semantic_graph_engine = SemanticGraphEngine(unified_engine=self)

    async def parse(self, source: str, fmt: str | None = None, **options: Any) -> Any:
        parser = self._parsers.get(fmt or "rdf_turtle")
        if parser is None:
            raise NotImplementedError(f"No parser registered for format '{fmt}'")
        return cast(Any, parser).parse(source, **options).document

    async def write(self, document: Any, destination: str, fmt: str | None = None, **options: Any) -> WriteResult:
        writer = self._writers.get(fmt or "rdf_turtle")
        if writer is None:
            raise NotImplementedError(f"No writer registered for format '{fmt}'")
        await cast(Any, writer).write(document, destination, **options)
        return WriteResult(metadata={"destination": destination, "format": fmt})

    def register_parser(self, fmt: str, parser: BaseKnowledgeParser) -> None:
        self._parsers[fmt] = parser

    def register_writer(self, fmt: str, writer: BaseKnowledgeWriter) -> None:
        self._writers[fmt] = writer

    # ============================================================
    # RAG Graph Interface
    # ============================================================

    async def extract_entities_rag(self, text: str) -> None:
        """Extract entities and relationships from text using RAG graph builder."""
        await self.graph_builder.extract(text)

    async def retrieve_neighbors(self, entity_id: str, hops: int = 2):
        """Retrieve neighbors from RAG graph."""
        return await self.graph_retriever.retrieve(entity_id, hops)

    async def search_rag(self, query: str, top_k: int = 5):
        """Search RAG graph."""
        return await self.graph_retriever.search(query, top_k)

    # ============================================================
    # Research Graph Interface
    # ============================================================

    async def extract_entities_research(self, chunks) -> list:
        """Extract entities from chunks using research graph extractor."""
        return await self.entity_extractor.extract(chunks)

    def add_entities_to_index(self, entities) -> None:
        """Add entities to research graph index."""
        self.graph_index.add_entities(entities)

    def add_relation_to_index(
        self,
        src: str,
        dst: str,
        relation: str,
        confidence: float,
        evidence_chunk: str,
    ) -> None:
        """Add relation to research graph index."""
        self.graph_index.add_relation(src, dst, relation, confidence, evidence_chunk)

    def get_neighbors_index(self, entity: str, depth: int = 2):
        """Get neighbors from research graph index."""
        return self.graph_index.get_neighbors(entity, depth)

    async def persist_graph(self) -> None:
        """Persist graph to database."""
        for node in self.graph_index.nodes.values():
            self.graph_persistence.save_node(node)
        for edges in self.graph_index.adj.values():
            for edge in edges:
                self.graph_persistence.save_edge(edge)

    # ============================================================
    # Semantic Graph Interface (KSDM/RDF)
    # ============================================================

    async def parse_semantic(self, source: str, fmt: str | None = None, **options: Any) -> KSDMDocument:
        """Parse using semantic graph engine (RDF/KSDM)."""
        return await self.semantic_graph_engine.parse(source, fmt, **options)

    async def write_semantic(self, document: KSDMDocument, destination: str, fmt: str | None = None, **options: Any) -> WriteResult:
        """Write using semantic graph engine (RDF/KSDM)."""
        return await self.semantic_graph_engine.write(document, destination, fmt, **options)

    async def process_document(self, document: Any) -> KSDMDocument:
        """Process a document and extract knowledge graph using semantic graph engine."""
        return await self.semantic_graph_engine.process_document(document)

    # ============================================================
    # Unified Graph Operations
    # ============================================================

    async def add_node(self, node: RAGGraphNode) -> None:
        """Add a node to the unified graph store."""
        await self.graph_store.add_node(node)

    async def add_edge(self, edge: RAGGraphEdge) -> None:
        """Add an edge to the unified graph store."""
        await self.graph_store.add_edge(edge)

    def to_knowledge_graph(self) -> KnowledgeGraph:
        """Convert unified graph to KnowledgeGraph model."""
        nodes = []
        edges = []
        
        for node_id, node in self.graph_store.nodes.items():
            nodes.append(GraphNode(
                id=node.id,
                label=node.label,
                type=node.type,
                url=node.metadata.get("url") if node.metadata else None,
                properties=node.metadata or {},
            ))
        
        for edge in self.graph_store.edges:
            edges.append(GraphEdge(
                source=edge.source,
                target=edge.target,
                relation=edge.relation,
                properties={},
            ))
        
        return KnowledgeGraph(nodes=nodes, edges=edges)

    def to_ksdm_document(self, title: str = "Unified Knowledge Graph") -> KSDMDocument:
        """Convert unified graph to KSDM document."""
        kg = self.to_knowledge_graph()
        
        entities = [
            Entity(
                id=node.id,
                type=EntityType.CONCEPT if node.type == "concept" else EntityType.ITEM,
                label=node.label,
                properties=node.properties,
            )
            for node in kg.nodes
        ]
        
        relations = [
            Relation(
                id=f"rel_{i}",
                source_id=edge.source,
                target_id=edge.target,
                type=RelationType.RELATED_TO,
                properties={"relation": edge.relation},
            )
            for i, edge in enumerate(kg.edges)
        ]
        
        return KSDMDocument(
            title=title,
            document_id=f"kg_unified_{id(self)}",
            media_type=MediaType(
                mime="application/json",
                format=DocumentFormat.JSON,
                standard=DocumentStandard.KSDM,
                extensions=[".json"],
                kind=MediaContentKind.STRUCTURED,
                raw_type=MediaRawType.TEXT,
            ),
            ontology={},
            entities=entities,
            relations=relations,
            attributes={
                "source": "unified_graph_engine",
                "node_count": len(entities),
                "edge_count": len(relations),
            },
        )


# Backward compatibility
GraphEngine = UnifiedGraphEngine