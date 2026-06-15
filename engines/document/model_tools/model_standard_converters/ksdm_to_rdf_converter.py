"""
Converter between KSDM KnowledgeGraph (property graph instance model) and
KSDM RDF triples (RdfGraph).

Mapping rules:
- Each GraphNode → a resource with rdf:type triples and property triples.
  The node's `id` becomes the subject URI, `type`/`label` map to rdf:type.
- Each GraphEdge → a triple with the edge relation as predicate,
  source → target.
- Node properties map to datatype property triples (value as object).
- Edge properties map to reified RDF statements (or annotations on the triple).

Supports two modes:
  1. Full RDF conversion (each node → resource, edge → triple)
  2. Simple triple-only conversion (edges only, nodes are implicit resources)
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from engines.knowledge.graph.models import (
    KnowledgeGraph,
    GraphNode,
    GraphEdge,
)


# Internal RDF triple representation used for converter serialization
class RdfTriple(BaseModel):
    subject: str
    predicate: str
    object_: str
    graph: str | None = None


class RdfGraph(BaseModel):
    graph_name: str | None = None
    triples: list[RdfTriple] = Field(default_factory=list)


class KsdmToRdfConverter:
    """Convert between KSDM KnowledgeGraph and RDF triples."""

    RDF_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
    RDFS_LABEL = "http://www.w3.org/2000/01/rdf-schema#label"

    @staticmethod
    def knowledge_graph_to_rdf(
        kg: KnowledgeGraph,
        graph_name: str | None = None,
        base_uri: str = "http://example.org/kg/",
        include_node_triples: bool = True,
    ) -> RdfGraph:
        """Convert a KnowledgeGraph into RDF triples.

        Args:
            kg: The KnowledgeGraph to convert.
            graph_name: Optional named graph IRI.
            base_uri: Base URI prefix for generating subject IRIs.
            include_node_triples: If True, emit rdf:type and property triples
                                  for each node. If False, only emit edge triples.

        Returns:
            An RdfGraph containing the converted triples.
        """
        triples: list[RdfTriple] = []
        node_iris: dict[str, str] = {}

        for node in kg.nodes:
            node_iri = node.url or f"{base_uri}{node.id}"
            node_iris[node.id] = node_iri

            if include_node_triples:
                triples.append(RdfTriple(
                    subject=node_iri,
                    predicate=KsdmToRdfConverter.RDF_TYPE,
                    object_=f"{base_uri}{node.type}",
                    graph=graph_name,
                ))
                if node.label and node.label != node.type:
                    triples.append(RdfTriple(
                        subject=node_iri,
                        predicate=KsdmToRdfConverter.RDFS_LABEL,
                        object_=f'"{node.label}"',
                        graph=graph_name,
                    ))
                for prop_name, prop_value in (node.properties or {}).items():
                    if prop_value is not None:
                        obj = KsdmToRdfConverter._value_to_rdf_literal(prop_value)
                        triples.append(RdfTriple(
                            subject=node_iri,
                            predicate=f"{base_uri}{prop_name}",
                            object_=obj,
                            graph=graph_name,
                        ))

        for edge in kg.edges:
            src_iri = node_iris.get(edge.source, f"{base_uri}{edge.source}")
            tgt_iri = node_iris.get(edge.target, f"{base_uri}{edge.target}")
            edge_iri = edge.properties.get("iri") if edge.properties else None
            if edge_iri:
                edge_iri = str(edge_iri)
            else:
                edge_iri = f"{base_uri}edge_{edge.source}_{edge.relation}_{edge.target}"

            triples.append(RdfTriple(
                subject=src_iri,
                predicate=f"{base_uri}{edge.relation}",
                object_=tgt_iri,
                graph=graph_name,
            ))

            if edge.properties and any(k != "iri" for k in edge.properties):
                rdf_statement = f"{base_uri}reified/{edge.source}_{edge.relation}_{edge.target}"
                triples.append(RdfTriple(
                    subject=rdf_statement,
                    predicate="http://www.w3.org/1999/02/22-rdf-syntax-ns#subject",
                    object_=src_iri,
                    graph=graph_name,
                ))
                triples.append(RdfTriple(
                    subject=rdf_statement,
                    predicate="http://www.w3.org/1999/02/22-rdf-syntax-ns#predicate",
                    object_=f"{base_uri}{edge.relation}",
                    graph=graph_name,
                ))
                triples.append(RdfTriple(
                    subject=rdf_statement,
                    predicate="http://www.w3.org/1999/02/22-rdf-syntax-ns#object",
                    object_=tgt_iri,
                    graph=graph_name,
                ))
                for prop_name, prop_value in edge.properties.items():
                    if prop_name != "iri" and prop_value is not None:
                        triples.append(RdfTriple(
                            subject=rdf_statement,
                            predicate=f"{base_uri}{prop_name}",
                            object_=KsdmToRdfConverter._value_to_rdf_literal(prop_value),
                            graph=graph_name,
                        ))

        return RdfGraph(graph_name=graph_name, triples=triples)

    @staticmethod
    def rdf_to_knowledge_graph(
        rdf_graph: RdfGraph,
        base_uri: str = "http://example.org/kg/",
    ) -> KnowledgeGraph:
        """Convert RDF triples into a KnowledgeGraph.

        This is a best-effort conversion. It groups triples by subject to
        reconstruct nodes, and extracts edge-like patterns (triples where
        the object is also a subject).
        """
        nodes: dict[str, GraphNode] = {}
        edge_candidates: list[RdfTriple] = []

        subjects: set[str] = set()
        objects: set[str] = set()

        for triple in rdf_graph.triples:
            subjects.add(triple.subject)
            if not triple.object_.startswith('"'):
                objects.add(triple.object_)

        for triple in rdf_graph.triples:
            subj = triple.subject
            if subj not in nodes:
                node_id = subj.replace(base_uri, "")
                ntype = "Resource"
                label = node_id
                props: dict[str, str] = {}
                nodes[subj] = GraphNode(id=node_id, label=label, type=ntype, properties=props)

            node = nodes[subj]
            if triple.predicate == KsdmToRdfConverter.RDF_TYPE:
                node.type = triple.object_.replace(base_uri, "")
            elif triple.predicate == KsdmToRdfConverter.RDFS_LABEL:
                node.label = triple.object_.strip('"')
            else:
                if not triple.object_.startswith('"'):
                    edge_candidates.append(triple)
                else:
                    prop_name = triple.predicate.replace(base_uri, "")
                    node.properties[prop_name] = triple.object_.strip('"')

        edges: list[GraphEdge] = []
        for triple in edge_candidates:
            src = triple.subject
            tgt = triple.object_
            relation = triple.predicate.replace(base_uri, "")
            if tgt in nodes:
                edges.append(GraphEdge(
                    source=src.replace(base_uri, ""),
                    target=tgt.replace(base_uri, ""),
                    relation=relation,
                ))

        return KnowledgeGraph(nodes=list(nodes.values()), edges=edges)

    @staticmethod
    def _value_to_rdf_literal(value: Any) -> str:
        if isinstance(value, bool):
            return f'"{str(value).lower()}"^^http://www.w3.org/2001/XMLSchema#boolean'
        if isinstance(value, int):
            return f'"{value}"^^http://www.w3.org/2001/XMLSchema#integer'
        if isinstance(value, float):
            return f'"{value}"^^http://www.w3.org/2001/XMLSchema#double'
        if isinstance(value, str):
            return f'"{value}"'
        return f'"{value}"'
