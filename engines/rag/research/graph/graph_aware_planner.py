class GraphAwareAnswerPlanner:

    async def create_plan(
        self,
        query,
        raw_evidence,
        graph_edges
    ):

        sections = []

        sections.append({
            "title": "Overview",
            "sources": raw_evidence[:5]
        })

        relation_map = {}

        for edge in graph_edges:

            key = edge.relation

            relation_map.setdefault(key, [])
            relation_map[key].append(edge)

        for rel, edges in relation_map.items():

            sections.append({
                "title": f"Relation: {rel}",
                "sources": edges[:5]
            })

        return sections
