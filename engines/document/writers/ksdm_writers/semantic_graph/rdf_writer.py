import importlib.util
from pathlib import Path
from typing import Any, BinaryIO, TextIO

from ...base import BaseKnowledgeWriter, BaseDocument
from ....models.media_types import MEDIA_TYPES
from ....models.ksdm_models import KsdDocument

RDFLIB_AVAILABLE = importlib.util.find_spec('rdflib') is not None


class RdfWriter(BaseKnowledgeWriter):
    supported_format = MEDIA_TYPES["rdf_turtle"]

    def can_write(self, document) -> bool:
        return isinstance(document, KsdDocument)

    async def write(self, document: BaseDocument, destination: str | Path | BinaryIO | TextIO | None = None, **options: Any) -> bytes:
        if not RDFLIB_AVAILABLE:
            raise TypeError("RDF writing requires 'rdflib' package. Install with: pip install rdflib")
        from rdflib import Graph as RdfLibGraph, Literal, URIRef
        g = RdfLibGraph()
        for rg in getattr(document, 'rdf_graphs', []):
            for triple in rg.triples:
                s = URIRef(triple.subject) if triple.subject.startswith('http') else URIRef(f'urn:{triple.subject}')
                p = URIRef(triple.predicate)
                o = Literal(triple.object_)
                g.add((s, p, o))
        ttl = g.serialize(format='turtle')
        output_bytes = ttl if isinstance(ttl, bytes) else ttl.encode('utf-8')
        if destination is not None:
            if isinstance(destination, (str, Path)):
                Path(destination).write_bytes(output_bytes)
            else:
                destination.write(output_bytes.decode('utf-8'))  # type: ignore
        return output_bytes
