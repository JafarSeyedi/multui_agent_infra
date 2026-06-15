from __future__ import annotations

import importlib.util
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, BinaryIO, TextIO, cast

from engines.document.writers.base import BaseDocument, BaseDocumentWriter
from engines.document.models.media_types import MEDIA_TYPES
from engines.knowledge.semantic_graph.models import SemanticGraphDocument

RDFLIB_AVAILABLE = importlib.util.find_spec('rdflib') is not None


class RdfWriter(BaseDocumentWriter):
    supported_format = MEDIA_TYPES["rdf_turtle"]

    def can_write(self, document) -> bool:
        return isinstance(document, SemanticGraphDocument) and document.knowledge_graph is not None

    async def write(self, document: BaseDocument, destination: str | Path | BinaryIO | TextIO | None = None, **options: Any) -> bytes:
        if not RDFLIB_AVAILABLE:
            raise TypeError("RDF writing requires 'rdflib' package. Install with: pip install rdflib")

        from engines.document.model_tools.model_standard_converters.ksdm_to_rdf_converter import (
            KsdmToRdfConverter,
        )

        from rdflib import Graph as RdfLibGraph, Literal, URIRef

        doc = cast(SemanticGraphDocument, document)
        kg = doc.knowledge_graph
        if kg is None:
            return b""

        rdf_graph = KsdmToRdfConverter.knowledge_graph_to_rdf(kg)
        g = RdfLibGraph()
        for triple in rdf_graph.triples:
            s = URIRef(triple.subject) if triple.subject.startswith('http') else URIRef(f'urn:{triple.subject}')
            p = URIRef(triple.predicate)
            o = URIRef(triple.object_) if not triple.object_.startswith('"') else Literal(triple.object_.strip('"'))
            g.add((s, p, o))

        ttl = g.serialize(format='turtle')
        output_bytes = ttl if isinstance(ttl, bytes) else ttl.encode('utf-8')
        if destination is not None:
            if isinstance(destination, (str, Path)):
                Path(destination).write_bytes(output_bytes)
            else:
                cast(Any, destination).write(output_bytes.decode('utf-8'))
        return output_bytes

    async def write_stream(self, document: BaseDocument) -> AsyncIterator[bytes]:
        yield await self.write(document)

    async def write_to_file(self, document: BaseDocument, target: Path, options: dict[str, Any] | None = None) -> None:
        target.write_bytes(await self.write(document))

    def get_supported_media_types(self) -> list[str]:
        return ["text/turtle"]

    def get_supported_extensions(self) -> list[str]:
        return [".ttl", ".rdf", ".owl"]
