from __future__ import annotations

import asyncio
import io
from collections import deque
from pathlib import Path
from typing import Any, cast

from engines.document.models.ksdm_models import (
    GraphEdge,
    GraphNode,
    KnowledgeGraph,
    SemanticGraphDocument,
    TransformationModelDocument,
)
from engines.document.models.media_types import MEDIA_TYPES
from engines.document.parsers.base import BaseDocumentParser, ParseResult
from engines.document.writers.base import BaseDocumentWriter


# ---------------------------------------------------------------------------
#  Parser / writer maps
# ---------------------------------------------------------------------------

def _import_parsers() -> dict[str, type[BaseDocumentParser]]:
    from engines.document.parsers.ksdm_parsers.semantic_graph.rdf_parser import (
        RdfParser,
    )
    from engines.document.parsers.ksdm_parsers.semantic_graph.rml_parser import (
        RmlParser,
    )
    return {
        "rdf_turtle": RdfParser,
        "rml_yaml": RmlParser,
    }


def _import_writers() -> dict[str, type[BaseDocumentWriter]]:
    from engines.document.writers.ksdm_writers.semantic_graph.rdf_writer import (
        RdfWriter,
    )
    from engines.document.writers.ksdm_writers.semantic_graph.rml_writer import (
        RmlWriter,
    )
    return {
        "rdf_turtle": RdfWriter,
        "rml_yaml": RmlWriter,
    }


# ---------------------------------------------------------------------------
#  Engine
# ---------------------------------------------------------------------------

class SemanticGraphEngine:
    """Runtime engine for Knowledge Graph / Semantic Graph documents.

    Supports:
    - Loading and parsing RDF (Turtle), RML YAML, and other semantic formats.
    - Graph querying (nodes, edges, traversal, shortest path, subgraph).
    - Conversion and writing to target formats.
    - Validation and statistics.
    """

    def __init__(self, doc: SemanticGraphDocument | None = None):
        self._doc = doc

    # -- Load / Parse -------------------------------------------------------

    async def async_load(
        self,
        source: str | bytes,
        parser_name: str | None = None,
        **options: Any,
    ) -> SemanticGraphDocument | TransformationModelDocument:
        parsers = _import_parsers()

        if parser_name and parser_name in parsers:
            parser_cls = parsers[parser_name]
            p: Any = parser_cls()
        elif isinstance(source, str):
            path = Path(source)
            p = self._detect_parser(path, parsers)
        else:
            raise ValueError(
                "Cannot auto-detect parser for bytes source without parser_name. "
                f"Choose from: {', '.join(parsers.keys())}"
            )

        loop = asyncio.get_running_loop()
        if isinstance(source, str):
            result: ParseResult = await loop.run_in_executor(
                None, p.parse, path, **options
            )
        else:
            buf = io.BytesIO(source)
            result = await loop.run_in_executor(
                None, p.parse, buf, **options
            )
        doc = cast(
            SemanticGraphDocument | TransformationModelDocument,
            result.document,
        )
        self._doc = doc if isinstance(doc, SemanticGraphDocument) else None
        return doc

    def load(
        self,
        source: str | bytes,
        parser_name: str | None = None,
        **options: Any,
    ) -> SemanticGraphDocument | TransformationModelDocument:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(
                self.async_load(source, parser_name, **options)
            )
        raise RuntimeError(
            "Cannot call load() synchronously inside an async context. "
            "Use await engine.async_load() instead."
        )

    async def async_parse(
        self,
        text_or_bytes: str | bytes,
        model_format: str | None = None,
        **options: Any,
    ) -> SemanticGraphDocument | TransformationModelDocument:
        data = (
            text_or_bytes.encode("utf-8")
            if isinstance(text_or_bytes, str)
            else text_or_bytes
        )
        parsers = _import_parsers()

        if model_format is not None:
            parser_cls = parsers.get(model_format)
            if parser_cls is None:
                raise ValueError(
                    f"Unsupported semantic-graph format: {model_format}. "
                    f"Choose from: {', '.join(parsers.keys())}"
                )
            p: Any = parser_cls()
        else:
            text = data.decode("utf-8", errors="replace")
            p = self._detect_parser_from_content(text, data, parsers)

        loop = asyncio.get_running_loop()
        buf = io.BytesIO(data)
        result = await loop.run_in_executor(None, p.parse, buf, **options)
        doc = cast(
            SemanticGraphDocument | TransformationModelDocument,
            result.document,
        )
        self._doc = doc if isinstance(doc, SemanticGraphDocument) else None
        return doc

    def parse(
        self,
        text_or_bytes: str | bytes,
        model_format: str | None = None,
        **options: Any,
    ) -> SemanticGraphDocument | TransformationModelDocument:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(
                self.async_parse(text_or_bytes, model_format, **options)
            )
        raise RuntimeError(
            "Cannot call parse() synchronously inside an async context. "
            "Use await engine.async_parse() instead."
        )

    # -- Graph API ----------------------------------------------------------

    def get_graph(self) -> KnowledgeGraph | None:
        if self._doc is None:
            return None
        return self._doc.knowledge_graph

    def get_node(self, node_id: str) -> GraphNode | None:
        kg = self.get_graph()
        if kg is None:
            return None
        for n in kg.nodes:
            if n.id == node_id:
                return n
        return None

    def find_nodes(
        self,
        label: str | None = None,
        node_type: str | None = None,
    ) -> list[GraphNode]:
        kg = self.get_graph()
        if kg is None:
            return []
        results: list[GraphNode] = []
        for n in kg.nodes:
            if label is not None and n.label != label:
                continue
            if node_type is not None and n.type != node_type:
                continue
            results.append(n)
        return results

    def get_edges(self) -> list[GraphEdge]:
        kg = self.get_graph()
        if kg is None:
            return []
        return list(kg.edges)

    def find_edges(
        self,
        source: str | None = None,
        target: str | None = None,
        relation: str | None = None,
    ) -> list[GraphEdge]:
        kg = self.get_graph()
        if kg is None:
            return []
        results: list[GraphEdge] = []
        for e in kg.edges:
            if source is not None and e.source != source:
                continue
            if target is not None and e.target != target:
                continue
            if relation is not None and e.relation != relation:
                continue
            results.append(e)
        return results

    def neighbors(
        self,
        node_id: str,
        max_depth: int = 1,
    ) -> list[tuple[GraphNode, GraphEdge, int]]:
        kg = self.get_graph()
        if kg is None or max_depth < 1:
            return []

        node_ids: set[str] = set()
        adjacency: dict[str, list[tuple[str, GraphEdge]]] = {}
        for e in kg.edges:
            adjacency.setdefault(e.source, []).append((e.target, e))
            adjacency.setdefault(e.target, []).append((e.source, e))

        node_map = {n.id: n for n in kg.nodes}
        if node_id not in node_map:
            return []

        results: list[tuple[GraphNode, GraphEdge, int]] = []
        queue: deque[tuple[str, int]] = deque()
        queue.append((node_id, 0))
        node_ids.add(node_id)

        while queue:
            current_id, depth = queue.popleft()
            if depth >= max_depth:
                continue
            for neighbor_id, edge in adjacency.get(current_id, []):
                if neighbor_id not in node_ids:
                    node_ids.add(neighbor_id)
                    neighbor_node = node_map.get(neighbor_id)
                    if neighbor_node:
                        results.append((neighbor_node, edge, depth + 1))
                    queue.append((neighbor_id, depth + 1))

        return results

    def shortest_path(
        self,
        source_id: str,
        target_id: str,
    ) -> list[GraphNode] | None:
        kg = self.get_graph()
        if kg is None:
            return None

        adjacency: dict[str, list[str]] = {}
        for e in kg.edges:
            adjacency.setdefault(e.source, []).append(e.target)
            adjacency.setdefault(e.target, []).append(e.source)

        node_map = {n.id: n for n in kg.nodes}
        if source_id not in node_map or target_id not in node_map:
            return None

        if source_id == target_id:
            return [node_map[source_id]]

        visited: set[str] = {source_id}
        queue: deque[list[str]] = deque()
        queue.append([source_id])

        while queue:
            path = queue.popleft()
            current = path[-1]
            for neighbor in adjacency.get(current, []):
                if neighbor == target_id:
                    return [node_map[n] for n in path] + [node_map[neighbor]]
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(path + [neighbor])

        return None

    def subgraph(self, node_ids: list[str]) -> KnowledgeGraph:
        kg = self.get_graph()
        if kg is None or not node_ids:
            return KnowledgeGraph(nodes=[], edges=[])

        id_set = set(node_ids)
        nodes = [n for n in kg.nodes if n.id in id_set]
        edges = [
            e for e in kg.edges
            if e.source in id_set and e.target in id_set
        ]
        return KnowledgeGraph(nodes=nodes, edges=edges)

    def get_statistics(self) -> dict[str, Any]:
        kg = self.get_graph()
        if kg is None:
            return {"status": "no_graph", "n_nodes": 0, "n_edges": 0}
        n_nodes = len(kg.nodes)
        n_edges = len(kg.edges)

        out_degree: dict[str, int] = {}
        in_degree: dict[str, int] = {}
        relation_counts: dict[str, int] = {}
        type_counts: dict[str, int] = {}

        for n in kg.nodes:
            type_counts[n.type] = type_counts.get(n.type, 0) + 1
        for e in kg.edges:
            out_degree[e.source] = out_degree.get(e.source, 0) + 1
            in_degree[e.target] = in_degree.get(e.target, 0) + 1
            relation_counts[e.relation] = relation_counts.get(e.relation, 0) + 1

        return {
            "status": "loaded",
            "n_nodes": n_nodes,
            "n_edges": n_edges,
            "avg_out_degree": round(sum(out_degree.values()) / max(n_nodes, 1), 2),
            "avg_in_degree": round(sum(in_degree.values()) / max(n_nodes, 1), 2),
            "node_types": type_counts,
            "relation_counts": relation_counts,
        }

    def get_metadata(self) -> dict[str, Any]:
        if self._doc is None:
            return {"status": "no_document"}
        return {
            "status": "loaded",
            "title": self._doc.title,
            "document_id": self._doc.document_id,
            "version": self._doc.version,
            "created_at": (
                self._doc.created_at.isoformat()
                if self._doc.created_at
                else None
            ),
            "modified_at": (
                self._doc.modified_at.isoformat()
                if self._doc.modified_at
                else None
            ),
            "has_graph": self._doc.knowledge_graph is not None,
        }

    # -- Write / Convert ----------------------------------------------------

    async def async_convert(
        self,
        target_format: str,
        **options: Any,
    ) -> bytes:
        if self._doc is None:
            raise ValueError("No document loaded.")
        writers = _import_writers()
        writer_cls = writers.get(target_format)
        if writer_cls is None:
            raise ValueError(
                f"Unknown target format: {target_format}. "
                f"Choose from: {', '.join(writers.keys())}"
            )
        writer = writer_cls()
        return await writer.write(self._doc)

    def convert(
        self,
        target_format: str,
        **options: Any,
    ) -> bytes:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.async_convert(target_format, **options))
        raise RuntimeError(
            "Cannot call convert() synchronously inside an async context. "
            "Use await engine.async_convert() instead."
        )

    async def async_write(
        self,
        destination: str,
        format: str | None = None,
        **options: Any,
    ) -> bytes:
        if self._doc is None:
            raise ValueError("No document loaded.")
        if format and format in _import_writers():
            writer = _import_writers()[format]()
        else:
            ext = Path(destination).suffix.lower()
            matched: list[BaseDocumentWriter] = []
            for cls in _import_writers().values():
                w = cls()
                if any(ext.endswith(e) for e in w.get_supported_extensions()):
                    matched.append(w)
            writer = matched[0] if matched else _import_writers()["rdf_turtle"]()
        result = await writer.write(self._doc)
        Path(destination).write_bytes(result)
        return result

    def write(
        self,
        destination: str,
        format: str | None = None,
        **options: Any,
    ) -> bytes:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.async_write(destination, format, **options))
        raise RuntimeError(
            "Cannot call write() synchronously inside an async context. "
            "Use await engine.async_write() instead."
        )

    # -- Validation ---------------------------------------------------------

    def validate(self) -> list[str]:
        warnings: list[str] = []
        if self._doc is None:
            return ["No document loaded"]
        kg = self._doc.knowledge_graph
        if kg is None:
            return warnings

        node_ids: set[str] = set()
        for n in kg.nodes:
            if n.id in node_ids:
                warnings.append(f"Duplicate node id: '{n.id}'")
            node_ids.add(n.id)
            if not n.label:
                warnings.append(f"Node '{n.id}' has no label")
            if not n.type:
                warnings.append(f"Node '{n.id}' has no type")

        for e in kg.edges:
            if e.source not in node_ids:
                warnings.append(f"Edge source '{e.source}' not found in nodes")
            if e.target not in node_ids:
                warnings.append(f"Edge target '{e.target}' not found in nodes")
            if not e.relation:
                warnings.append(
                    f"Edge ({e.source} -> {e.target}) has no relation"
                )

        return warnings

    # -- Internal Helpers ---------------------------------------------------

    @staticmethod
    def _detect_parser(
        path: Path,
        parsers: dict[str, type[BaseDocumentParser]],
    ) -> Any:
        for p_cls in parsers.values():
            p: Any = p_cls()
            if p.can_parse(str(path)):
                return p
        raise ValueError(
            f"Cannot auto-detect parser for '{path}'. "
            f"Specify parser_name."
        )

    @staticmethod
    def _detect_parser_from_content(
        text: str,
        data: bytes,
        parsers: dict[str, type[BaseDocumentParser]],
    ) -> Any:
        if "@prefix" in text or "<http" in text:
            return parsers["rdf_turtle"]()
        if "base_iri" in text or "logicalSources" in text:
            return parsers["rml_yaml"]()
        raise ValueError(
            "Cannot auto-detect format from content. "
            "Specify model_format parameter."
        )


__all__ = [
    "SemanticGraphEngine",
]
