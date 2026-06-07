"""
Knowledge Graph Pipeline for Semantic Graph Layer
=================================================
Pipeline for extracting entities and relations from documents and
structured data to construct knowledge graphs (KSDM documents).

This engine is now a lightweight wrapper that delegates to the
UnifiedGraphEngine for entity/relation extraction, while maintaining
its own parsers/writers for RDF/KSDM formats.
"""
from __future__ import annotations

from typing import Any, Dict, List

from engines.document.models.ksdm_models import KSDMDocument, Entity, Relation, EntityType, RelationType
from engines.document.models.standard import DocumentStandard
from engines.document.models.media_types import MediaType, DocumentFormat, MediaContentKind, MediaRawType
from engines.document.parsers.base import BaseKnowledgeParser
from engines.document.writers.base import BaseKnowledgeWriter, WriteResult
from engines.knowledge.graph.protocols import GraphEngineProtocol


class SemanticGraphEngine:
    """
    Semantic Graph Engine - focuses on RDF/KSDM parsing and writing.
    Delegates entity/relation extraction to UnifiedGraphEngine.
    """

    def __init__(self, unified_engine: GraphEngineProtocol | None = None):
        self._parsers: Dict[str, Any] = {}
        self._writers: Dict[str, Any] = {}
        if unified_engine is not None:
            self.unified_engine = unified_engine
        else:
            from engines.knowledge.graph.engine import UnifiedGraphEngine
            self.unified_engine = UnifiedGraphEngine()

    def register_parser(self, fmt: str, parser: BaseKnowledgeParser) -> None:
        self._parsers[fmt] = parser

    def register_writer(self, fmt: str, writer: BaseKnowledgeWriter) -> None:
        self._writers[fmt] = writer

    async def parse(self, source: str, fmt: str | None = None, **options: Any) -> KSDMDocument:
        """Parse RDF/KSDM format."""
        parser = self._parsers.get(fmt or "rdf_turtle")
        if parser is None:
            raise NotImplementedError("No parser registered for the requested format.")
        return parser.parse(source, **options).document

    async def write(self, document: KSDMDocument, destination: str, fmt: str | None = None, **options: Any) -> WriteResult:
        """Write RDF/KSDM format."""
        writer = self._writers.get(fmt or "rdf_turtle")
        if writer is None:
            raise NotImplementedError("No writer registered for the requested format.")
        await writer.write(document, destination, **options)
        return WriteResult(metadata={"destination": destination, "format": fmt})

    def _extract_text_from_document(self, document: Any) -> str:
        """Extract plain text from a document."""
        if hasattr(document, "raw_text") and document.raw_text:
            return document.raw_text
        return "Sample text for knowledge graph extraction."

    async def process_document(self, document: Any) -> KSDMDocument:
        """
        Process a document and extract a knowledge graph.
        Uses the unified engine's research graph entity extractor.
        """
        text = self._extract_text_from_document(document)
        
        # Use unified engine's entity extractor (which uses LLM + heuristics)
        chunks = [type('Chunk', (), {'text': text, 'chunk_id': 'doc_chunk'})()]
        extracted_entities = await self.unified_engine.entity_extractor.extract(chunks)
        
        # Convert to KSDM entities
        entities = []
        entity_id_map: Dict[str, str] = {}
        for i, ent in enumerate(extracted_entities):
            key = ent.name.lower()
            if key not in entity_id_map:
                entity_id = f"ent_{i}"
                entity_id_map[key] = entity_id
                entities.append(
                    Entity(
                        id=entity_id,
                        type=EntityType.CONCEPT if ent.type == "concept" else EntityType.ITEM,
                        label=ent.name,
                        properties={
                            "confidence": ent.confidence,
                            "source_chunk": ent.source_chunk,
                        },
                    )
                )
        
        # Extract relations using unified engine's graph index
        # For now, use simple co-occurrence based relations
        relations: List[Relation] = []
        for i, ent1 in enumerate(extracted_entities):
            for j, ent2 in enumerate(extracted_entities[i+1:], i+1):
                if ent1.source_chunk == ent2.source_chunk:
                    source_id = entity_id_map.get(ent1.name.lower())
                    target_id = entity_id_map.get(ent2.name.lower())
                    if source_id and target_id:
                        relations.append(
                            Relation(
                                id=f"rel_{len(relations)}",
                                type=RelationType.RELATED_TO,
                                source_id=source_id,
                                target_id=target_id,
                                properties={
                                    "confidence": 0.5,
                                    "source_text": ent1.name,
                                    "target_text": ent2.name,
                                },
                            )
                        )
        
        kg_document = KSDMDocument(
            title=f"Knowledge Graph extracted from {getattr(document, 'title', 'unknown')}",
            document_id=f"kg_{getattr(document, 'document_id', 'unknown')}",
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
                "extraction_method": "unified_engine_llm_heuristic",
                "source_document_id": getattr(document, "document_id", None),
            },
        )
        
        return kg_document


# Backward compatibility aliases
KSDM_Pipeline = SemanticGraphEngine