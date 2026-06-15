import importlib.util
from pathlib import Path
from typing import Any, BinaryIO, TextIO, cast

from engines.document.parsers.base import BaseDocumentParser, ParseResult
from engines.document.models.media_types import MEDIA_TYPES
from engines.knowledge.semantic_graph.models import SemanticGraphDocument
from engines.document.model_tools.model_standard_converters.ksdm_to_rdf_converter import (
    RdfGraph, RdfTriple,
)

RDFLIB_AVAILABLE = importlib.util.find_spec('rdflib') is not None


class RdfParser(BaseDocumentParser):
    supported_format = MEDIA_TYPES["rdf_turtle"]

    async def parse_bytes(self, data: bytes, document_id: str, source_name: str,
                         metadata: dict[str, Any] | None = None,
                         options: Any = None) -> SemanticGraphDocument:
        from io import BytesIO
        buf = BytesIO(data)
        result = self.parse(buf)
        doc = cast(SemanticGraphDocument, result.document)
        doc.document_id = document_id
        return doc

    async def parse_path(self, path: str | Path, document_id: str,
                        metadata: dict[str, Any] | None = None,
                        options: Any = None) -> SemanticGraphDocument:
        result = self.parse(Path(path))
        doc = cast(SemanticGraphDocument, result.document)
        doc.document_id = document_id
        return doc

    async def parse_stream(self, stream: Any, document_id: str,
                          source_name: str, metadata: dict[str, Any] | None = None,
                          options: Any = None) -> SemanticGraphDocument:
        data = b''.join([chunk async for chunk in stream])
        return await self.parse_bytes(data, document_id, source_name, metadata, options)

    def can_parse(self, source: str | Path) -> bool:
        if isinstance(source, str) and source.endswith(('.ttl', '.rdf', '.nt', '.owl', '.jsonld')):
            return True
        try:
            data = Path(source).read_bytes()[:100] if Path(source).exists() else b""
            return b"@prefix" in data or b"<http" in data or b"_:b" in data
        except Exception:
            return False

    def parse(self, source: str | Path | BinaryIO | TextIO, **options: Any) -> ParseResult:
        if not RDFLIB_AVAILABLE:
            raise Exception("RDF parsing requires 'rdflib' package. Install with: pip install rdflib")
        try:
            from rdflib import Graph as RdfLibGraph
            if isinstance(source, (str, Path)):
                g = RdfLibGraph()
                g.parse(str(source), format='turtle')
            elif hasattr(source, 'read'):
                raw = source.read()
                if isinstance(raw, bytes):
                    raw = raw.decode('utf-8')
                g = RdfLibGraph()
                g.parse(data=raw, format='turtle')
            else:
                raise Exception("Unsupported source type")
            triples = []
            for s, p, o in g:
                triples.append(RdfTriple(subject=str(s), predicate=str(p), object_=str(o)))
            rdf_graph = RdfGraph(graph_name=None, triples=triples)

            # Build KnowledgeGraph from triples via converter
            from engines.document.model_tools.model_standard_converters.ksdm_to_rdf_converter import (
                KsdmToRdfConverter,
            )
            kg = KsdmToRdfConverter.rdf_to_knowledge_graph(rdf_graph)

            doc = SemanticGraphDocument(
                knowledge_graph=kg,
                title=str(Path(source).stem) if isinstance(source, (str, Path)) else "Untitled",
                document_id=str(Path(source).stem) if isinstance(source, (str, Path)) else "unknown",
                media_type=MEDIA_TYPES["rdf_turtle"]
            )
            return ParseResult(document=doc)
        except ImportError:
            raise Exception("RDF parsing requires 'rdflib' package. Install with: pip install rdflib")
        except Exception as e:
            raise Exception(f"RDF parse failed: {e}")
