"""
Converter between KSDM KnowledgeGraph (property graph instance model) and
DSDM DataDocument (format-independent tree-structured instance data).

Capabilities:
- KnowledgeGraph → DataDocument: flattens nodes/edges into a tree
- DataDocument → KnowledgeGraph: extracts node/edge objects from a known structure

The DSDM representation uses a flat structure:
  Root (OBJECT)
    ├── nodes (ARRAY of OBJECT)
    │   ├── { id, label, type, url, properties: { ... } }
    ├── edges (ARRAY of OBJECT)
        ├── { source, target, relation, properties: { ... } }
"""
from __future__ import annotations

from typing import Any

from engines.knowledge.models.ksdm_models import (
    KnowledgeGraph,
    GraphNode,
    GraphEdge,
)
from engines.document.models.dsdm_models import (
    DataDocument,
    DataDocumentCapabilities,
    DataNode,
    DataNodeKind,
    DataValue,
    SchemaBinding,
)
from engines.document.models.msdm_models import ScalarType


class KsdmToDsdmConverter:
    """Convert between KSDM KnowledgeGraph and DSDM DataDocument."""

    @staticmethod
    def knowledge_graph_to_data_document(
        kg: KnowledgeGraph,
        title: str = "knowledge_graph",
        document_id: str = "",
        media_type: str | None = None,
    ) -> DataDocument:
        """Convert a KnowledgeGraph into a DSDM DataDocument."""
        from engines.document.models.media_types import MEDIA_TYPES

        root = DataNode(
            node_id="root",
            path="/",
            name="graph",
            kind=DataNodeKind.OBJECT,
        )

        nodes_array = DataNode(
            node_id="nodes",
            path="/nodes",
            name="nodes",
            kind=DataNodeKind.ARRAY,
        )
        for i, node in enumerate(kg.nodes):
            node_node = KsdmToDsdmConverter._graph_node_to_data_node(node, i)
            nodes_array.children.append(node_node)
        root.children.append(nodes_array)

        edges_array = DataNode(
            node_id="edges",
            path="/edges",
            name="edges",
            kind=DataNodeKind.ARRAY,
        )
        for i, edge in enumerate(kg.edges):
            edge_node = KsdmToDsdmConverter._graph_edge_to_data_node(edge, i)
            edges_array.children.append(edge_node)
        root.children.append(edges_array)

        return DataDocument(
            root=root,
            schema_ref=None,
            capabilities=DataDocumentCapabilities(
                supports_comments=False,
                supports_namespaces=False,
                supports_attributes=False,
                ordered_mappings=True,
            ),
            media_type=MEDIA_TYPES["json"] if media_type is None else MEDIA_TYPES.get(media_type, MEDIA_TYPES["json"]),
            title=title,
            document_id=document_id or title,
        )

    @staticmethod
    def data_document_to_knowledge_graph(doc: DataDocument) -> KnowledgeGraph:
        """Extract a KnowledgeGraph from a DSDM DataDocument."""
        nodes: list[GraphNode] = []
        edges: list[GraphEdge] = []

        def find_child(parent: DataNode, name: str) -> DataNode | None:
            for c in parent.children:
                if c.name == name:
                    return c
            return None

        nodes_node = find_child(doc.root, "nodes")
        edges_node = find_child(doc.root, "edges")

        if nodes_node:
            for child in nodes_node.children:
                node = KsdmToDsdmConverter._data_node_to_graph_node(child)
                if node:
                    nodes.append(node)

        if edges_node:
            for child in edges_node.children:
                edge = KsdmToDsdmConverter._data_node_to_graph_edge(child)
                if edge:
                    edges.append(edge)

        return KnowledgeGraph(nodes=nodes, edges=edges)

    @staticmethod
    def _graph_node_to_data_node(node: GraphNode, index: int) -> DataNode:
        node_id = f"node_{index}"
        props_node = DataNode(
            node_id=f"{node_id}_props",
            path=f"/nodes/{node_id}/properties",
            name="properties",
            kind=DataNodeKind.OBJECT,
        )
        for k, v in (node.properties or {}).items():
            props_node.children.append(
                DataNode(
                    node_id=f"{node_id}_prop_{k}",
                    path=f"/nodes/{node_id}/properties/{k}",
                    name=k,
                    kind=DataNodeKind.SCALAR,
                    value=DataValue(
                        scalar_type=KsdmToDsdmConverter._type_of(v),
                        value=v,
                    ),
                )
            )
        return DataNode(
            node_id=node_id,
            path=f"/nodes/{node_id}",
            name=f"node_{node.id}",
            kind=DataNodeKind.OBJECT,
            children=[
                DataNode(
                    node_id=f"{node_id}_id", path=f"/nodes/{node_id}/id", name="id",
                    kind=DataNodeKind.SCALAR,
                    value=DataValue(scalar_type=ScalarType.STRING, value=node.id),
                ),
                DataNode(
                    node_id=f"{node_id}_label", path=f"/nodes/{node_id}/label", name="label",
                    kind=DataNodeKind.SCALAR,
                    value=DataValue(scalar_type=ScalarType.STRING, value=node.label),
                ),
                DataNode(
                    node_id=f"{node_id}_type", path=f"/nodes/{node_id}/type", name="type",
                    kind=DataNodeKind.SCALAR,
                    value=DataValue(scalar_type=ScalarType.STRING, value=node.type),
                ),
                *([DataNode(
                    node_id=f"{node_id}_url", path=f"/nodes/{node_id}/url", name="url",
                    kind=DataNodeKind.SCALAR,
                    value=DataValue(scalar_type=ScalarType.STRING, value=node.url),
                )] if node.url else []),
                props_node,
            ],
        )

    @staticmethod
    def _graph_edge_to_data_node(edge: GraphEdge, index: int) -> DataNode:
        node_id = f"edge_{index}"
        props_node = DataNode(
            node_id=f"{node_id}_props",
            path=f"/edges/{node_id}/properties",
            name="properties",
            kind=DataNodeKind.OBJECT,
        )
        for k, v in (edge.properties or {}).items():
            props_node.children.append(
                DataNode(
                    node_id=f"{node_id}_prop_{k}",
                    path=f"/edges/{node_id}/properties/{k}",
                    name=k,
                    kind=DataNodeKind.SCALAR,
                    value=DataValue(
                        scalar_type=KsdmToDsdmConverter._type_of(v),
                        value=v,
                    ),
                )
            )
        return DataNode(
            node_id=node_id,
            path=f"/edges/{node_id}",
            name=f"edge_{index}",
            kind=DataNodeKind.OBJECT,
            children=[
                DataNode(
                    node_id=f"{node_id}_source", path=f"/edges/{node_id}/source", name="source",
                    kind=DataNodeKind.SCALAR,
                    value=DataValue(scalar_type=ScalarType.STRING, value=edge.source),
                ),
                DataNode(
                    node_id=f"{node_id}_target", path=f"/edges/{node_id}/target", name="target",
                    kind=DataNodeKind.SCALAR,
                    value=DataValue(scalar_type=ScalarType.STRING, value=edge.target),
                ),
                DataNode(
                    node_id=f"{node_id}_relation", path=f"/edges/{node_id}/relation", name="relation",
                    kind=DataNodeKind.SCALAR,
                    value=DataValue(scalar_type=ScalarType.STRING, value=edge.relation),
                ),
                props_node,
            ],
        )

    @staticmethod
    def _data_node_to_graph_node(node: DataNode) -> GraphNode | None:
        if node.kind != DataNodeKind.OBJECT:
            return None
        nid = KsdmToDsdmConverter._get_scalar(node, "id") or ""
        label = KsdmToDsdmConverter._get_scalar(node, "label") or ""
        ntype = KsdmToDsdmConverter._get_scalar(node, "type") or ""
        url = KsdmToDsdmConverter._get_scalar(node, "url")
        props = KsdmToDsdmConverter._get_properties(node)
        return GraphNode(id=nid, label=label, type=ntype, url=url, properties=props)

    @staticmethod
    def _data_node_to_graph_edge(node: DataNode) -> GraphEdge | None:
        if node.kind != DataNodeKind.OBJECT:
            return None
        source = KsdmToDsdmConverter._get_scalar(node, "source") or ""
        target = KsdmToDsdmConverter._get_scalar(node, "target") or ""
        relation = KsdmToDsdmConverter._get_scalar(node, "relation") or ""
        props = KsdmToDsdmConverter._get_properties(node)
        return GraphEdge(source=source, target=target, relation=relation, properties=props)

    @staticmethod
    def _get_scalar(node: DataNode, name: str) -> str | None:
        for c in node.children:
            if c.name == name and c.value is not None:
                v = c.value.value
                return str(v) if v is not None else None
        return None

    @staticmethod
    def _get_properties(node: DataNode) -> dict[str, Any]:
        for c in node.children:
            if c.name == "properties" and c.kind == DataNodeKind.OBJECT:
                return {prop.name or "": prop.value.value if prop.value else None for prop in c.children}
        return {}

    @staticmethod
    def _type_of(value: Any) -> ScalarType:
        if value is None:
            return ScalarType.NULL
        if isinstance(value, bool):
            return ScalarType.BOOLEAN
        if isinstance(value, int):
            return ScalarType.INT
        if isinstance(value, float):
            return ScalarType.DOUBLE
        if isinstance(value, str):
            return ScalarType.STRING
        if isinstance(value, (list, tuple)):
            return ScalarType.ARRAY
        if isinstance(value, dict):
            return ScalarType.MAP
        return ScalarType.STRING
