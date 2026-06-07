import importlib.util
from pathlib import Path
from typing import Any, BinaryIO, TextIO

from engines.document.parsers.base import BaseKnowledgeParser, KnowledgeParseError, ParseResult
from engines.document.models.media_types import MEDIA_TYPES
from engines.document.models.ksdm_models import KsdDocument, RdfGraph, RdfTriple

RDFLIB_AVAILABLE = importlib.util.find_spec('rdflib') is not None


class RdfParser(BaseKnowledgeParser):
    supported_format = MEDIA_TYPES["rdf_turtle"]

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
            raise KnowledgeParseError("RDF parsing requires 'rdflib' package. Install with: pip install rdflib")
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
                raise KnowledgeParseError("Unsupported source type")
            triples = []
            for s, p, o in g:
                triples.append(RdfTriple(subject=str(s), predicate=str(p), object_=str(o)))
            rdf_graph = RdfGraph(graph_name=None, triples=triples)
            doc = KsdDocument(rdf_graphs=[rdf_graph])
            return ParseResult(document=doc)
        except ImportError:
            raise KnowledgeParseError("RDF parsing requires 'rdflib' package. Install with: pip install rdflib")
        except Exception as e:
            raise KnowledgeParseError(f"RDF parse failed: {e}")
