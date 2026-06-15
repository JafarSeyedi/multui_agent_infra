from engines.knowledge.graph.models import GraphEdge, GraphNode


class GraphBuilder:

    def __init__(self, llm, graph_store):
        self.llm = llm
        self.store = graph_store

    async def extract(self, text: str):
        prompt = f"""
Extract entities and relationships from the text.

Text:
{text}

Return JSON:

nodes: [{{
id, label, type
}}]

edges: [{{
source, target, relation
}}]
"""
        result = await self.llm.generate_json(prompt)

        nodes = result["nodes"]
        edges = result["edges"]

        for n in nodes:
            await self.store.add_node(GraphNode(**n))

        for e in edges:
            await self.store.add_edge(GraphEdge(**e))
