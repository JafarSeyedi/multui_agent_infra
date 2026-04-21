from typing import Dict, List
from .graph_models import GraphNode, GraphEdge


class MemoryGraphStore:

    def __init__(self) -> None:

        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []

    async def add_node(self, node: GraphNode):

        self.nodes[node.id] = node

    async def add_edge(self, edge: GraphEdge):

        self.edges.append(edge)

    async def neighbors(self, node_id: str):

        results = []

        for e in self.edges:
            if e.source == node_id:
                results.append(self.nodes.get(e.target))

        return results
