"""
Converter between MSDM (ontology/schema layer) and KSDM KnowledgeGraph
(instance-level property graph).

Capabilities:
- MSDMDocument → KnowledgeGraph template (creates example node/edge instances
  from entity definitions)
- KnowledgeGraph → MSDMDocument validation (checks that graph instances conform
  to their MSDM schema definitions)
- Extract node/edge type schemas from MSDM as GraphNode/GraphEdge templates
"""
from __future__ import annotations

from typing import Any

from engines.document.models.msdm_models import (
    MSDMDocument,
    Entity,
    EntityKind,
    Attribute,
    ScalarType,
    ConstraintType,
)
from engines.knowledge.models.ksdm_models import (
    KnowledgeGraph,
    GraphNode,
    GraphEdge,
)


class MsdmToKsdmGraphConverter:
    """Convert between MSDM schema entities and KSDM KnowledgeGraph instances."""

    @staticmethod
    def entity_to_graph_node_template(entity: Entity) -> GraphNode:
        """Create a template GraphNode from an MSDM Entity(kind=GRAPH_NODE)."""
        props: dict[str, Any] = {}
        for attr in entity.attributes:
            props[attr.name] = MsdmToKsdmGraphConverter._default_value(attr)
        return GraphNode(
            id=f"template:{entity.name}",
            label=entity.name,
            type=entity.name,
            properties=props,
        )

    @staticmethod
    def entity_to_graph_edge_template(entity: Entity) -> GraphEdge:
        """Create a template GraphEdge from an MSDM Entity(kind=GRAPH_EDGE)."""
        props: dict[str, Any] = {}
        for attr in entity.attributes:
            props[attr.name] = MsdmToKsdmGraphConverter._default_value(attr)
        return GraphEdge(
            source=f"template:{entity.name}_src",
            target=f"template:{entity.name}_tgt",
            relation=entity.name,
            properties=props,
        )

    @staticmethod
    def msdm_to_knowledge_graph_template(doc: MSDMDocument) -> KnowledgeGraph:
        """Create a KnowledgeGraph with template instances from MSDM entities."""
        nodes: list[GraphNode] = []
        edges: list[GraphEdge] = []
        for entity in doc.entities:
            if entity.kind == EntityKind.GRAPH_NODE:
                nodes.append(MsdmToKsdmGraphConverter.entity_to_graph_node_template(entity))
            elif entity.kind == EntityKind.GRAPH_EDGE:
                edges.append(MsdmToKsdmGraphConverter.entity_to_graph_edge_template(entity))
        return KnowledgeGraph(nodes=nodes, edges=edges)

    @staticmethod
    def validate_graph_against_entity(graph_node: GraphNode, entity: Entity) -> list[str]:
        """Validate a GraphNode instance against an MSDM entity definition."""
        errors: list[str] = []
        entity_attr_map = {a.name: a for a in entity.attributes}
        for attr_name, attr_def in entity_attr_map.items():
            if attr_name not in graph_node.properties:
                is_required = (
                    attr_def.required
                    or any(c.type == ConstraintType.NOT_NULL for c in attr_def.constraints)
                )
                if is_required:
                    errors.append(
                        f"Missing required property '{attr_name}' on node '{graph_node.id}'"
                    )
        return errors

    @staticmethod
    def validate_knowledge_graph(
        kg: KnowledgeGraph, schema: MSDMDocument
    ) -> dict[str, list[str]]:
        """Validate an entire KnowledgeGraph against an MSDM schema.
        Returns a dict of node_id → list of error messages.
        """
        errors: dict[str, list[str]] = {}
        entity_map = {e.name: e for e in schema.entities}

        for node in kg.nodes:
            entity = entity_map.get(node.type) or entity_map.get(node.label)
            if entity:
                node_errors = MsdmToKsdmGraphConverter.validate_graph_against_entity(node, entity)
                if node_errors:
                    errors[node.id] = node_errors
        return errors

    @staticmethod
    def _default_value(attr: Attribute) -> Any:
        base = attr.data_type.base
        if base == ScalarType.STRING:
            return ""
        elif base in (ScalarType.INT, ScalarType.LONG):
            return 0
        elif base in (ScalarType.FLOAT, ScalarType.DOUBLE, ScalarType.DECIMAL):
            return 0.0
        elif base == ScalarType.BOOLEAN:
            return False
        elif base in (ScalarType.ARRAY,):
            return []
        elif base in (ScalarType.MAP, ScalarType.STRUCT):
            return {}
        return None
