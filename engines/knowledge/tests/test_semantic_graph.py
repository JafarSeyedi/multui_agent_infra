from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from engines.knowledge.graph.models import (
    GraphEdge,
    GraphNode,
    KnowledgeGraph,
)
from engines.knowledge.semantic_graph.models import SemanticGraphDocument
from engines.document.models.media_types import MEDIA_TYPES
from engines.knowledge.semantic_graph import SemanticGraphEngine

# ---------------------------------------------------------------------------
#  Test RDF / Turtle data
# ---------------------------------------------------------------------------

SAMPLE_TTL = """\
@prefix ex: <http://example.org/> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

ex:Alice rdf:type ex:Person ;
         rdfs:label "Alice" ;
         ex:knows ex:Bob ;
         ex:knows ex:Charlie .

ex:Bob rdf:type ex:Person ;
       rdfs:label "Bob" ;
       ex:knows ex:Diana .

ex:Charlie rdf:type ex:Person ;
          rdfs:label "Charlie" .

ex:Diana rdf:type ex:Person ;
        rdfs:label "Diana" .
"""

SIMPLE_TTL = """\
@prefix ex: <http://example.org/> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .

ex:A rdf:type ex:Node .
ex:B rdf:type ex:Node ;
    ex:related ex:A .
"""


# ---------------------------------------------------------------------------
#  Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def rdflib_available() -> bool:
    import importlib.util
    return importlib.util.find_spec("rdflib") is not None


# ---------------------------------------------------------------------------
#  Parse Tests
# ---------------------------------------------------------------------------

class TestParse:

    @pytest.mark.asyncio
    async def test_parse_turtle_string(self, rdflib_available: bool):
        if not rdflib_available:
            pytest.skip("rdflib not installed")
        engine = SemanticGraphEngine()
        doc = await engine.async_parse(SAMPLE_TTL, model_format="rdf_turtle")
        assert isinstance(doc, SemanticGraphDocument)
        assert doc.knowledge_graph is not None
        assert len(doc.knowledge_graph.nodes) >= 4
        assert len(doc.knowledge_graph.edges) >= 3

    @pytest.mark.asyncio
    async def test_parse_turtle_bytes(self, rdflib_available: bool):
        if not rdflib_available:
            pytest.skip("rdflib not installed")
        engine = SemanticGraphEngine()
        doc = await engine.async_parse(
            SIMPLE_TTL.encode("utf-8"), model_format="rdf_turtle"
        )
        assert isinstance(doc, SemanticGraphDocument)
        assert doc.knowledge_graph is not None

    @pytest.mark.asyncio
    async def test_parse_auto_detect(self, rdflib_available: bool):
        if not rdflib_available:
            pytest.skip("rdflib not installed")
        engine = SemanticGraphEngine()
        doc = await engine.async_parse(SAMPLE_TTL)
        assert isinstance(doc, SemanticGraphDocument)
        assert doc.knowledge_graph is not None

    def test_sync_parse(self, rdflib_available: bool):
        if not rdflib_available:
            pytest.skip("rdflib not installed")
        engine = SemanticGraphEngine()
        doc = engine.parse(SAMPLE_TTL, model_format="rdf_turtle")
        assert isinstance(doc, SemanticGraphDocument)

    @pytest.mark.asyncio
    async def test_parse_invalid_format(self):
        engine = SemanticGraphEngine()
        with pytest.raises(ValueError, match="Unsupported semantic-graph format"):
            await engine.async_parse(b"garbage", model_format="nonexistent")


# ---------------------------------------------------------------------------
#  Graph API Tests
# ---------------------------------------------------------------------------

class TestGraphAPI:

    @pytest.fixture(autouse=True)
    def _engine_with_graph(self, rdflib_available: bool, event_loop) -> None:
        if not rdflib_available:
            pytest.skip("rdflib not installed")
        self.engine = SemanticGraphEngine()
        event_loop.run_until_complete(
            self.engine.async_parse(SAMPLE_TTL)
        )

    def test_get_graph(self) -> None:
        kg = self.engine.get_graph()
        assert kg is not None
        assert len(kg.nodes) >= 4

    def test_get_graph_no_doc(self) -> None:
        engine = SemanticGraphEngine()
        assert engine.get_graph() is None

    def test_get_node(self) -> None:
        node = self.engine.get_node("http://example.org/Alice")
        if node:
            assert node.label == "Alice"
        node = self.engine.get_node("nonexistent")
        assert node is None

    def test_find_nodes_by_label(self) -> None:
        nodes = self.engine.find_nodes(label="Bob")
        assert len(nodes) >= 1
        assert nodes[0].id.endswith("Bob")

    def test_find_nodes_by_type(self) -> None:
        nodes = self.engine.find_nodes(node_type="http://example.org/Person")
        assert len(nodes) >= 4

    def test_get_edges(self) -> None:
        edges = self.engine.get_edges()
        assert len(edges) >= 3

    def test_find_edges(self) -> None:
        edges = self.engine.find_edges(relation="http://example.org/knows")
        assert len(edges) >= 3
        alice_knows = self.engine.find_edges(
            source="http://example.org/Alice"
        )
        assert len(alice_knows) >= 2


# ---------------------------------------------------------------------------
#  Traversal / Path Tests
# ---------------------------------------------------------------------------

class TestTraversal:

    @pytest.fixture(autouse=True)
    def _engine_with_graph(self, rdflib_available: bool, event_loop) -> None:
        if not rdflib_available:
            pytest.skip("rdflib not installed")
        self.engine = SemanticGraphEngine()
        event_loop.run_until_complete(
            self.engine.async_parse(SAMPLE_TTL)
        )

    def test_neighbors_depth_1(self) -> None:
        neighbors = self.engine.neighbors(
            "http://example.org/Alice", max_depth=1
        )
        assert len(neighbors) >= 2
        for node, edge, depth in neighbors:
            assert depth == 1
            assert isinstance(node, GraphNode)
            assert isinstance(edge, GraphEdge)

    def test_neighbors_depth_2(self) -> None:
        neighbors = self.engine.neighbors(
            "http://example.org/Alice", max_depth=2
        )
        assert len(neighbors) >= 3

    def test_neighbors_no_doc(self) -> None:
        engine = SemanticGraphEngine()
        assert engine.neighbors("any", max_depth=1) == []

    def test_shortest_path(self) -> None:
        path = self.engine.shortest_path(
            "http://example.org/Alice",
            "http://example.org/Diana",
        )
        assert path is not None
        assert len(path) >= 2
        assert path[0].id.endswith("Alice")
        assert path[-1].id.endswith("Diana")

    def test_shortest_path_same_node(self) -> None:
        path = self.engine.shortest_path(
            "http://example.org/Alice",
            "http://example.org/Alice",
        )
        assert path is not None
        assert len(path) == 1

    def test_shortest_path_no_connection(self) -> None:
        path = self.engine.shortest_path(
            "http://example.org/Alice",
            "http://example.org/Nonexistent",
        )
        assert path is None

    def test_shortest_path_no_doc(self) -> None:
        engine = SemanticGraphEngine()
        assert engine.shortest_path("a", "b") is None

    def test_subgraph(self) -> None:
        sg = self.engine.subgraph([
            "http://example.org/Alice",
            "http://example.org/Bob",
        ])
        assert len(sg.nodes) == 2
        assert len(sg.edges) >= 1

    def test_subgraph_empty(self) -> None:
        sg = self.engine.subgraph([])
        assert len(sg.nodes) == 0
        assert len(sg.edges) == 0

    def test_subgraph_no_doc(self) -> None:
        engine = SemanticGraphEngine()
        sg = engine.subgraph(["a"])
        assert sg is not None
        assert len(sg.nodes) == 0


# ---------------------------------------------------------------------------
#  Statistics / Metadata Tests
# ---------------------------------------------------------------------------

class TestStats:

    @pytest.fixture(autouse=True)
    def _engine_with_graph(self, rdflib_available: bool, event_loop) -> None:
        if not rdflib_available:
            pytest.skip("rdflib not installed")
        self.engine = SemanticGraphEngine()
        event_loop.run_until_complete(
            self.engine.async_parse(SAMPLE_TTL)
        )

    def test_get_statistics(self) -> None:
        stats = self.engine.get_statistics()
        assert stats["status"] == "loaded"
        assert stats["n_nodes"] >= 4
        assert stats["n_edges"] >= 3
        assert "node_types" in stats
        assert "relation_counts" in stats

    def test_get_statistics_no_doc(self) -> None:
        engine = SemanticGraphEngine()
        stats = engine.get_statistics()
        assert stats["status"] == "no_graph"

    def test_get_metadata(self) -> None:
        meta = self.engine.get_metadata()
        assert meta["status"] == "loaded"
        assert meta["has_graph"] is True

    def test_get_metadata_no_doc(self) -> None:
        engine = SemanticGraphEngine()
        meta = engine.get_metadata()
        assert meta["status"] == "no_document"


# ---------------------------------------------------------------------------
#  Validate Tests
# ---------------------------------------------------------------------------

class TestValidate:

    def test_validate_no_doc(self):
        engine = SemanticGraphEngine()
        warnings = engine.validate()
        assert warnings == ["No document loaded"]

    def test_validate_empty_graph(self):
        doc = SemanticGraphDocument(
            title="empty",
            document_id="empty",
            media_type=MEDIA_TYPES["rdf_turtle"],
        )
        engine = SemanticGraphEngine(doc)
        warnings = engine.validate()
        assert warnings == []

    @pytest.mark.asyncio
    async def test_validate_with_orphan_edges(self, rdflib_available: bool):
        if not rdflib_available:
            pytest.skip("rdflib not installed")
        engine = SemanticGraphEngine()
        await engine.async_parse(SAMPLE_TTL)
        warnings = engine.validate()
        for w in warnings:
            assert "not found in nodes" not in w


# ---------------------------------------------------------------------------
#  Convert / Write Tests
# ---------------------------------------------------------------------------

class TestConvertWrite:

    @pytest.mark.asyncio
    async def test_convert_to_rdf(self, rdflib_available: bool):
        if not rdflib_available:
            pytest.skip("rdflib not installed")
        engine = SemanticGraphEngine()
        await engine.async_parse(SAMPLE_TTL)
        result = await engine.async_convert("rdf_turtle")
        assert isinstance(result, bytes)
        assert b"@prefix" in result or b"Alice" in result

    @pytest.mark.asyncio
    async def test_convert_no_doc(self):
        engine = SemanticGraphEngine()
        with pytest.raises(ValueError, match="No document loaded"):
            await engine.async_convert("rdf_turtle")

    @pytest.mark.asyncio
    async def test_convert_invalid_format(self, rdflib_available: bool):
        if not rdflib_available:
            pytest.skip("rdflib not installed")
        engine = SemanticGraphEngine()
        await engine.async_parse(SAMPLE_TTL)
        with pytest.raises(ValueError, match="Unknown target format"):
            await engine.async_convert("nonexistent")

    def test_convert_sync(self, rdflib_available: bool):
        if not rdflib_available:
            pytest.skip("rdflib not installed")
        engine = SemanticGraphEngine()
        engine.parse(SAMPLE_TTL, model_format="rdf_turtle")
        result = engine.convert("rdf_turtle")
        assert isinstance(result, bytes)

    @pytest.mark.asyncio
    async def test_write_roundtrip(self, rdflib_available: bool, tmp_path: Path):
        if not rdflib_available:
            pytest.skip("rdflib not installed")
        engine = SemanticGraphEngine()
        await engine.async_parse(SAMPLE_TTL)
        dest = tmp_path / "test_output.ttl"
        result = await engine.async_write(str(dest))
        assert isinstance(result, bytes)
        assert dest.exists()
        assert dest.stat().st_size > 0

        engine2 = SemanticGraphEngine()
        doc2 = await engine2.async_parse(result, model_format="rdf_turtle")
        assert isinstance(doc2, SemanticGraphDocument)
        assert doc2.knowledge_graph is not None
        assert len(doc2.knowledge_graph.nodes) >= 4


# ---------------------------------------------------------------------------
#  Direct document construction API
# ---------------------------------------------------------------------------

class TestDirectAPI:

    def test_engine_from_document(self):
        kg = KnowledgeGraph(
            nodes=[
                GraphNode(id="n1", label="Node 1", type="test"),
                GraphNode(id="n2", label="Node 2", type="test"),
            ],
            edges=[
                GraphEdge(source="n1", target="n2", relation="connects"),
            ],
        )
        doc = SemanticGraphDocument(
            title="test",
            document_id="test",
            media_type=MEDIA_TYPES["rdf_turtle"],
            knowledge_graph=kg,
        )
        engine = SemanticGraphEngine(doc)
        assert engine.get_graph() is not None
        assert engine.get_node("n1") is not None
        assert len(engine.get_edges()) == 1

    def test_statistics_with_direct_graph(self):
        kg = KnowledgeGraph(
            nodes=[
                GraphNode(id="a", label="A", type="type1"),
                GraphNode(id="b", label="B", type="type1"),
                GraphNode(id="c", label="C", type="type2"),
            ],
            edges=[
                GraphEdge(source="a", target="b", relation="rel1"),
                GraphEdge(source="b", target="c", relation="rel2"),
                GraphEdge(source="a", target="c", relation="rel1"),
            ],
        )
        doc = SemanticGraphDocument(
            title="stats_test",
            document_id="stats_test",
            media_type=MEDIA_TYPES["rdf_turtle"],
            knowledge_graph=kg,
        )
        engine = SemanticGraphEngine(doc)
        stats = engine.get_statistics()
        assert stats["n_nodes"] == 3
        assert stats["n_edges"] == 3
        assert stats["node_types"] == {"type1": 2, "type2": 1}
        assert stats["relation_counts"] == {"rel1": 2, "rel2": 1}

    def test_validate_orphan_edges(self):
        kg = KnowledgeGraph(
            nodes=[
                GraphNode(id="a", label="A", type="t"),
            ],
            edges=[
                GraphEdge(source="a", target="nonexistent", relation="r"),
                GraphEdge(source="nonexistent2", target="a", relation="r"),
            ],
        )
        doc = SemanticGraphDocument(
            title="orphan_test",
            document_id="orphan_test",
            media_type=MEDIA_TYPES["rdf_turtle"],
            knowledge_graph=kg,
        )
        engine = SemanticGraphEngine(doc)
        warnings = engine.validate()
        assert len(warnings) == 2
        assert any("nonexistent" in w for w in warnings)

    def test_traverse_direct_graph(self):
        kg = KnowledgeGraph(
            nodes=[
                GraphNode(id="a", label="A", type="t"),
                GraphNode(id="b", label="B", type="t"),
                GraphNode(id="c", label="C", type="t"),
            ],
            edges=[
                GraphEdge(source="a", target="b", relation="r1"),
                GraphEdge(source="b", target="c", relation="r2"),
            ],
        )
        doc = SemanticGraphDocument(
            title="traverse_test",
            document_id="traverse_test",
            media_type=MEDIA_TYPES["rdf_turtle"],
            knowledge_graph=kg,
        )
        engine = SemanticGraphEngine(doc)
        path = engine.shortest_path("a", "c")
        assert path is not None
        assert len(path) == 3
        assert [n.id for n in path] == ["a", "b", "c"]

        neighbors = engine.neighbors("a", max_depth=2)
        assert len(neighbors) == 2


# ---------------------------------------------------------------------------
#  Edge Cases
# ---------------------------------------------------------------------------

class TestEdgeCases:

    def test_empty_graph_construct(self):
        engine = SemanticGraphEngine()
        assert engine.get_graph() is None
        assert engine.get_node("x") is None
        assert engine.find_nodes(label="x") == []
        assert engine.neighbors("x") == []
        assert engine.shortest_path("a", "b") is None

    def test_find_edges_empty(self):
        engine = SemanticGraphEngine()
        assert engine.find_edges(source="x") == []

    def test_find_edges_filters(self):
        doc = SemanticGraphDocument(
            title="filter",
            document_id="filter",
            media_type=MEDIA_TYPES["rdf_turtle"],
            knowledge_graph=KnowledgeGraph(
                nodes=[
                    GraphNode(id="a", label="A", type="t"),
                    GraphNode(id="b", label="B", type="t"),
                ],
                edges=[
                    GraphEdge(source="a", target="b", relation="r1"),
                ],
            ),
        )
        engine = SemanticGraphEngine(doc)
        assert len(engine.find_edges(relation="r1")) == 1
        assert len(engine.find_edges(relation="r2")) == 0
        assert len(engine.find_edges(source="a")) == 1
        assert len(engine.find_edges(source="b")) == 0
        assert len(engine.find_edges(target="b")) == 1
        assert len(engine.find_edges(target="a")) == 0

    def test_validate_duplicate_ids(self):
        kg = KnowledgeGraph(
            nodes=[
                GraphNode(id="dup", label="A", type="t"),
                GraphNode(id="dup", label="B", type="t"),
            ],
            edges=[],
        )
        doc = SemanticGraphDocument(
            title="dup_test",
            document_id="dup_test",
            media_type=MEDIA_TYPES["rdf_turtle"],
            knowledge_graph=kg,
        )
        engine = SemanticGraphEngine(doc)
        warnings = engine.validate()
        assert any("Duplicate" in w for w in warnings)

    def test_validate_empty_labels(self):
        kg = KnowledgeGraph(
            nodes=[
                GraphNode(id="n1", label="", type=""),
            ],
            edges=[],
        )
        doc = SemanticGraphDocument(
            title="empty_labels",
            document_id="empty_labels",
            media_type=MEDIA_TYPES["rdf_turtle"],
            knowledge_graph=kg,
        )
        engine = SemanticGraphEngine(doc)
        warnings = engine.validate()
        assert any("no label" in w for w in warnings)

    def test_subgraph_preserves_connectivity(self):
        kg = KnowledgeGraph(
            nodes=[
                GraphNode(id="a", label="A", type="t"),
                GraphNode(id="b", label="B", type="t"),
                GraphNode(id="c", label="C", type="t"),
            ],
            edges=[
                GraphEdge(source="a", target="b", relation="r"),
                GraphEdge(source="b", target="c", relation="r"),
            ],
        )
        doc = SemanticGraphDocument(
            title="subgraph_conn",
            document_id="subgraph_conn",
            media_type=MEDIA_TYPES["rdf_turtle"],
            knowledge_graph=kg,
        )
        engine = SemanticGraphEngine(doc)
        sg = engine.subgraph(["a", "c"])
        # a and c are not directly connected, so subgraph has 0 edges
        assert len(sg.nodes) == 2
        assert len(sg.edges) == 0

        sg2 = engine.subgraph(["a", "b"])
        assert len(sg2.nodes) == 2
        assert len(sg2.edges) == 1
